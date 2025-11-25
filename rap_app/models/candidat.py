import logging
import unicodedata
import re
from datetime import date
from django.core.validators import RegexValidator

from django.conf import settings
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

from .custom_user import CustomUser
from .formations import Formation
from .base import BaseModel
from .evenements import Evenement
# ⚠️ pas d'import Appairage ici pour éviter les imports circulaires ;
#    on référence le modèle via la chaîne "Appairage" dans le FK.

logger = logging.getLogger("application.candidats")

NIVEAU_CHOICES = [(i, f"{i} ★") for i in range(1, 6)]


def slugify_username(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w.@+-]", "", value)
    return value.lower()


def generate_unique_username(base: str) -> str:
    User = get_user_model()
    username = base
    suffix = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}_{suffix}"
        suffix += 1
    return username



class ResultatPlacementChoices(models.TextChoices):
    ADMIS = "admis", _("Admis")
    NON_ADMIS = "non_admis", _("Non admis")
    SECOND_ENTRETIEN = "second_entretien", _("Second entretien")
    EN_ATTENTE = "en_attente", _("En attente")
    ABANDON_CANDIDAT = "abandon_candidat", _("Abandon candidat")
    ABANDON_ETS = "abandon_ets", _("Abandon entreprise")
    DEJA_PLACE = "deja_place", _("Déjà placé")
    ABSENT = "absent", _("Absent")
    APPAIRAGE_EN_COURS = "appairage_en_cours", _("Appairage en cours")


class Candidat(BaseModel):
    class StatutCandidat(models.TextChoices):
        EN_ATTENTE_ENTRETIEN = "att_entretien", _("En attente d'entretien")
        EN_ATTENTE_RENTREE = "att_rentee", _("En attente de rentrée")  # (valeur conservée pour rétro-compatibilité)
        EN_ATTENTE_COMMISSION = "att_commission", _("En attente de commission")
        EN_ACCOMPAGNEMENT = "accompagnement", _("En accompagnement")
        EN_APPAIRAGE = "appairage", _("En appairage")
        EN_FORMATION = "formation", _("En formation")
        ABANDON = "abandon", _("Abandon")
        AUTRE = "autre", _("Autre")

    class TypeContrat(models.TextChoices):
        APPRENTISSAGE = "apprentissage", _("Apprentissage")
        PROFESSIONNALISATION = "professionnalisation", _("Professionnalisation")
        SANS_CONTRAT = "sans_contrat", _("Sans contrat")
        POEI_POEC  = "poei_poec", _("POEI / POEC")
        CRIF = "crif", _("Crif")
        AUTRE = "autre", _("Autre")

    class Disponibilite(models.TextChoices):
        IMMEDIATE = "immediate", _("Immédiate")
        DEUX_TROIS_MOIS = "2_3_mois", _("2-3 mois")
        SIX_MOIS = "6_mois", _("6 mois")

    class ContratSigne(models.TextChoices):
        EN_COURS = "en_cours", _("En cours")
        OUI = "oui", _("Oui")
        NON = "non", _("Non")

    # ✅ Nouveau : statut du CV
    class CVStatut(models.TextChoices):
        OUI = "oui", _("Oui")
        EN_COURS = "en_cours", _("En cours")
        A_MODIFIER = "a_modifier", _("À modifier")

    # ----------------- Identité & contact -----------------
    # --- État civil ---
    sexe = models.CharField(max_length=1, choices=[("M", "Masculin"), ("F", "Féminin")], blank=True, null=True)
    nom_naissance = models.CharField(max_length=100, blank=True, null=True)
    nom = models.CharField(max_length=100, verbose_name=_("Nom d'usage"))
    prenom = models.CharField(max_length=100, verbose_name=_("Prénom"))
    date_naissance = models.DateField(null=True, blank=True, verbose_name=_("Date de naissance"))
    departement_naissance = models.CharField(max_length=3, blank=True, null=True)
    commune_naissance = models.CharField(max_length=100, blank=True, null=True)
    pays_naissance = models.CharField(max_length=100,blank=True,null=True,verbose_name=_("Pays de naissance"),default="France",)    
    nationalite = models.CharField(max_length=100, blank=True, null=True, default="Française")
    nir = models.CharField(max_length=15, blank=True, null=True, verbose_name=_("Numéro de sécurité sociale (NIR)"))
    


    # --- Contact ---
    email = models.EmailField(blank=True, null=True, verbose_name=_("Email"))
    phone_regex = RegexValidator(
    regex=r'^0\d{9}$',
    message=_("Le numéro doit comporter 10 chiffres et commencer par 0 (ex : 0612345678)."),
    )
    telephone = models.CharField(validators=[phone_regex], max_length=10, blank=True, null=True, verbose_name=_("Téléphone"))
   
    # --- Adresse détaillée ---
    street_number = models.CharField(max_length=10, blank=True, null=True, verbose_name=_("Numéro de voie"),)
    street_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Nom de la rue"),)
    street_complement = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Complément d'adresse"),)
    ville = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Ville"))
    code_postal = models.CharField(max_length=10, blank=True, null=True, verbose_name=_("Code postal"))

    compte_utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidat_associe",
        verbose_name=_("Compte utilisateur"),
        null=True, blank=True,   # ✅ garder temporairement nullable
    )

    # ----------------- Statut & formation -----------------
    entretien_done = models.BooleanField(default=False, verbose_name=_("Entretien réalisé"))
    test_is_ok = models.BooleanField(default=False, verbose_name=_("Test d'entrée réussi"))

    # ✅ Nouveau champ : statut du CV
    cv_statut = models.CharField(
        max_length=15,
        choices=CVStatut.choices,
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("CV"),
    )

    statut = models.CharField(
        max_length=30,
        choices=StatutCandidat.choices,
        default=StatutCandidat.AUTRE,
        verbose_name=_("Statut"),
        db_index=True,
    )

    formation = models.ForeignKey(
        Formation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="candidats",
        verbose_name=_("Formation"),
    )
    evenement = models.ForeignKey(
        Evenement,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="candidats",
        verbose_name=_("Événement"),
    )

    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    origine_sourcing = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Origine du sourcing"))

    date_inscription = models.DateTimeField(auto_now_add=True, verbose_name=_("Date d’inscription"), db_index=True)
    rqth = models.BooleanField(default=False, verbose_name=_("RQTH"))

    type_contrat = models.CharField(
        max_length=30, choices=TypeContrat.choices, blank=True, null=True, verbose_name=_("Type de contrat")
    )
    disponibilite = models.CharField(
        max_length=30, choices=Disponibilite.choices, blank=True, null=True, verbose_name=_("Disponibilité")
    )
    permis_b = models.BooleanField(default=False, verbose_name=_("Permis B"))

    communication = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Communication (étoiles)"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        choices=NIVEAU_CHOICES,
    )
    experience = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Expérience (étoiles)"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        choices=NIVEAU_CHOICES,
    )
    csp = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("CSP (étoiles)"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        choices=NIVEAU_CHOICES,
    )

    vu_par = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="candidats_vus",
        verbose_name=_("Vu par (staff)"),
    )
    # ----------------- Champs Contrats -----------------

    # --- Situation particulière ---
    regime_social = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Régime social (Sécurité sociale)"),)
    sportif_haut_niveau = models.BooleanField(default=False, verbose_name=_("Sportif de haut niveau?"),)
    equivalence_jeunes = models.BooleanField(default=False, verbose_name=_("Equivalence jeune?"),)
    extension_boe = models.BooleanField(default=False, verbose_name=_("Extension BOE?"),)
    situation_actuelle = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Situation avant ce contrat"),
        help_text=_("Ex. demandeur d’emploi, lycéen, salarié…"),
    )
    # --- Parcours scolaire ---
    dernier_diplome_prepare = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Dernier diplôme préparé"),
    )
    diplome_plus_eleve_obtenu = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Diplôme ou titre le plus élevé obtenu"),
    )
    derniere_classe = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Dernière classe fréquentée"),
    )
    intitule_diplome_prepare = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Intitulé du diplôme préparé"),
    )
    situation_avant_contrat = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Situation avant le contrat"),
    )

    # --- Projet professionnel ---
    projet_creation_entreprise = models.BooleanField(default=False)

    # --- Représentant légal ---
    representant_lien = models.CharField(
    max_length=50,
    blank=True,
    null=True,
    verbose_name=_("Lien avec le candidat"),
    help_text=_("Ex. père, mère, tuteur, autre"),
    )
    representant_nom_naissance = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name=_("Nom de naissance du représentant légal"),
    )
    representant_prenom = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name=_("Prénom du représentant légal"),
    )
    representant_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_("Courriel du représentant légal"),
    )
    representant_street_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Adresse du représentant légal"),
    )
    representant_zip_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name=_("Code postal du représentant légal"),
    )
    representant_city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Commune du représentant légal"),
    )


    # ----------------- Champs "placement" (gardés pour le front) -----------------
    responsable_placement = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="candidats_gérés",
        verbose_name=_("Responsable placement"),
    )
    date_placement = models.DateField(null=True, blank=True, verbose_name=_("Date de placement"))
    entreprise_placement = models.ForeignKey(
        "Partenaire",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="placements",
        verbose_name=_("Entreprise de placement"),
    )
    resultat_placement = models.CharField(
        max_length=30,
        choices=ResultatPlacementChoices.choices,
        null=True,
        blank=True,
        verbose_name=_("Résultat du placement"),
    )
    entreprise_validee = models.ForeignKey(
        "Partenaire",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="entreprises_validees",
        verbose_name=_("Entreprise validée"),
    )
    contrat_signe = models.CharField(
        max_length=10, choices=ContratSigne.choices, null=True, blank=True, verbose_name=_("Contrat signé")
    )

    inscrit_gespers = models.BooleanField(
        default=False,
        verbose_name=_("Inscrit GESPERS"),
        help_text="Indique si le candidat est inscrit dans GESPERS."
    )

    courrier_rentree = models.BooleanField(default=False, verbose_name=_("Courrier de rentrée envoyé"))
    date_rentree = models.DateField(null=True, blank=True, verbose_name=_("Date de rentrée"))
    admissible = models.BooleanField(default=False, verbose_name=_("Admissible"))

    numero_osia = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        unique=True,  # un OSIA unique au niveau base (autorise plusieurs NULL)
        help_text="Numéro OSIA du contrat signé",
    )

    # ----------------- Nouveau: pointeur vers l'appairage courant -----------------
    placement_appairage = models.ForeignKey(
        "Appairage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="as_current_for",
        verbose_name=_("Appairage courant (placement)"),
    )

    class Meta:
        verbose_name = _("Candidat")
        verbose_name_plural = _("Candidats")
        ordering = ["-date_inscription"]
        indexes = [
            models.Index(fields=["evenement"]),
            models.Index(fields=["nom", "prenom"]),
            # Petit plus pour les filtres/tri par appairage courant
            models.Index(fields=["placement_appairage"]),
        ]

    # ----------------- Lifecycle / utils -----------------

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ⚠️ ne PAS utiliser getattr (les FKs sont stockés en *_id dans __dict__)
        init = {}
        for f in self._meta.concrete_fields:
            init[f.name] = self.__dict__.get(f.attname, None)
        self._initial = init

    def __str__(self):
        return self.nom_complet

    def __repr__(self):
        return f"<Candidat id={self.pk} nom='{self.nom}' prenom='{self.prenom}'>"

    @property
    def cv_statut_display(self):
        return self.get_cv_statut_display() if self.cv_statut else None

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}".strip()

    @property
    def age(self):
        if self.date_naissance:
            today = date.today()
            return today.year - self.date_naissance.year - (
                (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
            )
        return None

    @property
    def nb_appairages(self) -> int:
        return self.appairages.count()

    # --------- Accesseurs pratiques depuis l'appairage courant ---------

    @property
    def placement_statut(self):
        a = getattr(self, "placement_appairage", None)
        return getattr(a, "statut", None) if a else None

    @property
    def placement_statut_display(self):
        a = getattr(self, "placement_appairage", None)
        return a.get_statut_display() if a else None

    @property
    def placement_partenaire(self):
        a = getattr(self, "placement_appairage", None)
        return getattr(a, "partenaire", None) if a else None

    @property
    def placement_partenaire_nom(self):
        p = self.placement_partenaire
        return getattr(p, "nom", None) if p else None

    @property
    def placement_responsable(self):
        a = getattr(self, "placement_appairage", None)
        if not a:
            return None
        return getattr(a, "created_by", None) or getattr(a, "updated_by", None)

    @property
    def placement_responsable_nom(self):
        u = self.placement_responsable
        if not u:
            return None
        full = u.get_full_name()
        return full or getattr(u, "email", None) or getattr(u, "username", None)

    # -------------------------------------------------------------------

    def valider_comme_stagiaire(self):
        if not self.admissible:
            raise ValidationError(_("Ce candidat n'est pas admissible."))
        if not self.compte_utilisateur:
            raise ValidationError(_("Ce candidat n’a pas de compte utilisateur associé."))
        self.compte_utilisateur.role = CustomUser.ROLE_STAGIAIRE
        self.compte_utilisateur.save()
        return self.compte_utilisateur

    def valider_comme_candidatuser(self):
        """
        Valide le candidat comme utilisateur 'ROLE_CANDIDAT_USER'.
        NE CRÉE PAS d'utilisateur automatiquement.
        """
        if not self.compte_utilisateur:
            raise ValidationError(
                _("Impossible de valider comme candidat : aucun compte utilisateur n'est associé.")
            )

        user = self.compte_utilisateur
        user.role = CustomUser.ROLE_CANDIDAT_USER
        user.save()
        return user

    @property
    def est_valide_comme_stagiaire(self) -> bool:
        return bool(self.compte_utilisateur and self.compte_utilisateur.role == CustomUser.ROLE_STAGIAIRE)

    @property
    def est_valide_comme_candidatuser(self):
        return bool(self.compte_utilisateur and self.compte_utilisateur.role == CustomUser.ROLE_CANDIDAT_USER)

    @property
    def role_utilisateur(self):
        if self.compte_utilisateur:
            return self.compte_utilisateur.get_role_display()
        return "-"

    def clean(self):
        super().clean()
        if not self.nom or not self.prenom:
            logger.warning(f"⚠️ Candidat incomplet : nom ou prénom manquant (id={self.pk})")
        if self.statut == self.StatutCandidat.AUTRE:
            logger.info(f"ℹ️ Candidat #{self.pk} a un statut 'autre'")

    def save(self, *args, **kwargs):
        """
        - Remonte `user` à BaseModel.save(user=...) pour setter created_by/updated_by
        - Log les changements
        - Crée un HistoriquePlacement si les infos de placement changent
          (et, à la création, seulement si au moins un champ de placement est renseigné)
        """
        # On récupère (et enlève) le user pour le passer à BaseModel.save
        user = kwargs.pop("user", None)

        # IMPORTANT : on détecte si c'est un update partiel (update_fields)
        update_fields = kwargs.get("update_fields", None)

        is_new = self.pk is None
        original = None if is_new else self.__class__.objects.filter(pk=self.pk).first()

        # ✅ Validation complète UNIQUEMENT si ce n'est pas un update partiel
        #    → évite de re-valider l'unicité de compte_utilisateur
        if update_fields is None:
            self.full_clean()

        with transaction.atomic():
            # IMPORTANT : propager user à BaseModel.save
            super().save(*args, user=user, **kwargs)

            if original:
                self._log_changes()

            champs_placement = [
                "entreprise_placement_id",
                "resultat_placement",
                "date_placement",
                "responsable_placement_id",
                "contrat_signe",
            ]

            if original:
                changed = any(getattr(original, f) != getattr(self, f) for f in champs_placement)
            else:
                def _is_set(v):
                    return v not in (None, "", False)
                changed = any(_is_set(getattr(self, f)) for f in champs_placement)

            if changed:
                HistoriquePlacement.objects.create(
                    candidat=self,
                    date_placement=self.date_placement or date.today(),
                    entreprise=self.entreprise_placement,
                    resultat=self.resultat_placement or ResultatPlacementChoices.EN_ATTENTE,
                    responsable=self.responsable_placement,
                    commentaire="📌 Historique créé automatiquement à la modification du placement.",
                )

    def delete(self, *args, **kwargs):
        logger.warning(f"❌ Suppression du candidat : {self} (id={self.pk})")
        user = self.compte_utilisateur
        super().delete(*args, **kwargs)
        if user:
            user.delete()


    def _log_changes(self):
        changements = []
        for champ in self._initial:
            old = self._initial.get(champ)
            new = getattr(self, champ)
            if old != new:
                changements.append(f"{champ}: '{old}' → '{new}'")
        if changements:
            logger.info(f"✏️ Candidat modifié (id={self.pk}) – changements : " + "; ".join(changements))

    @property
    def ateliers_effectues(self):
        return self.ateliers_tre.count()

    @property
    def ateliers_labels(self):
        return [a.get_type_atelier_display() for a in self.ateliers_tre.all()]

    @property
    def ateliers_resume(self):
        return ", ".join(self.ateliers_labels)

    def lier_utilisateur(self, mot_de_passe: str = "Temporaire123"):
        User = get_user_model()
        if self.compte_utilisateur:
            raise ValueError("Ce candidat a déjà un compte utilisateur.")
        if not self.email:
            raise ValueError("Ce candidat n’a pas d’adresse email définie.")
        if User.objects.filter(email=self.email).exists():
            raise ValueError("Un utilisateur avec cette adresse email existe déjà.")
        utilisateur = User.objects.create_user(
            email=self.email, password=mot_de_passe, first_name=self.prenom, last_name=self.nom
        )
        self.compte_utilisateur = utilisateur
        self.save()
        return utilisateur


class HistoriquePlacement(BaseModel):
    candidat = models.ForeignKey(
        "Candidat", on_delete=models.CASCADE, related_name="historique_placements", verbose_name=_("Candidat")
    )
    date_placement = models.DateField(verbose_name=_("Date du placement"))
    entreprise = models.ForeignKey(
        "Partenaire",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="placements_historique",
        verbose_name=_("Entreprise"),
    )
    resultat = models.CharField(max_length=30, choices=ResultatPlacementChoices.choices, verbose_name=_("Résultat"))
    responsable = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="placements_realises",
        verbose_name=_("Responsable"),
    )
    commentaire = models.TextField(blank=True, null=True, verbose_name=_("Commentaire"))

    class Meta:
        verbose_name = _("Historique de placement")
        verbose_name_plural = _("Historique de placements")
        ordering = ["-date_placement"]

    def __str__(self):
        return f"{self.candidat} – {self.date_placement} – {self.resultat}"
