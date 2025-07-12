import logging
from datetime import date
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import unicodedata
import re
from django.core.validators import MinValueValidator, MaxValueValidator

from .custom_user import CustomUser

from .formations import Formation
from .base import BaseModel
from .evenements import Evenement

logger = logging.getLogger("application.candidats")
NIVEAU_CHOICES = [(i, f"{i} ★") for i in range(1, 6)]

def slugify_username(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w.@+-]", "", value)  # Seuls caractères autorisés
    return value.lower()
class Candidat(BaseModel):
    """
    👤 Représente un candidat.
    """

    class StatutCandidat(models.TextChoices):
        EN_ACCOMPAGNEMENT = "accompagnement", _("En accompagnement")
        EN_FORMATION = "formation", _("En formation")
        EN_APPAIRAGE = "appairage", _("En appairage")
        EN_EMPLOI = "emploi", _("En emploi")
        ABANDON = "abandon", _("Abandon")
        AUTRE = "autre", _("Autre")

    class TypeContrat(models.TextChoices):
        APPRENTISSAGE = "apprentissage", _("Apprentissage")
        PROFESSIONNALISATION = "professionnalisation", _("Professionnalisation")
        SANS_CONTRAT = "sans_contrat", _("Sans contrat")
        POEI = "poei", _("POEI")
        POEC = "poec", _("POEC")
        AUTRE = "autre", _("Autre")

    class Disponibilite(models.TextChoices):
        IMMEDIATE = "immediate", _("Immédiate")
        DEUX_TROIS_MOIS = "2_3_mois", _("2-3 mois")
        SIX_MOIS = "6_mois", _("6 mois")

    class ResultatPlacement(models.TextChoices):
        ADMIS = "admis", _("Admis")
        NON_ADMIS = "non_admis", _("Non admis")
        SECOND_ENTRETIEN = "second_entretien", _("Second entretien")
        EN_ATTENTE = "en_attente", _("En attente")
        ABANDON_CANDIDAT = "abandon_candidat", _("Abandon candidat")
        ABANDON_ETS = "abandon_ets", _("Abandon entreprise")
        DEJA_PLACE = "deja_place", _("Déjà placé")
        ABSENT = "absent", _("Absent")

    class ContratSigne(models.TextChoices):
        EN_COURS = "en_cours", _("En cours")
        OUI = "oui", _("Oui")
        NON = "non", _("Non")

    nom = models.CharField(max_length=100, verbose_name=_("Nom"))
    prenom = models.CharField(max_length=100, verbose_name=_("Prénom"))
    email = models.EmailField(blank=True, null=True, verbose_name=_("Email"))
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Téléphone"))
    ville = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Ville"))
    code_postal = models.CharField(max_length=10, blank=True, null=True, verbose_name=_("Code postal"))

    compte_utilisateur = models.OneToOneField(
        "CustomUser",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="candidat_associe",
        verbose_name=_("Compte utilisateur"),
        help_text=_("Compte utilisateur associé à ce candidat")
    )

    entretien_done = models.BooleanField(
        default=False,
        verbose_name=_("Entretien réalisé"),
        help_text=_("Le candidat a-t-il passé un entretien ?")
    )

    test_is_ok = models.BooleanField(
        default=False,
        verbose_name=_("Test d'entrée réussi"),
        help_text=_("Le candidat a-t-il réussi les tests d'entrée ?")
    )

    statut = models.CharField(
        max_length=30,
        choices=StatutCandidat.choices,
        default=StatutCandidat.EN_ACCOMPAGNEMENT,
        verbose_name=_("Statut du candidat"),
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

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes"),
        help_text=_("Notes libres concernant le candidat")
    )

    origine_sourcing = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Origine du sourcing"),
        help_text=_("Comment le contact a été établi avec le candidat")
    )

    date_inscription = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date d’inscription"),
        db_index=True,
    )

    # Champs ajoutés
    date_naissance = models.DateField(
        null=True, blank=True, verbose_name=_("Date de naissance")
    )

    rqth = models.BooleanField(
        default=False,
        verbose_name=_("RQTH"),
        help_text=_("Reconnaissance qualité travailleur handicapé"),
    )

    type_contrat = models.CharField(
        max_length=30,
        choices=TypeContrat.choices,
        blank=True,
        null=True,
        verbose_name=_("Type de contrat"),
    )

    disponibilite = models.CharField(
        max_length=30,
        choices=Disponibilite.choices,
        blank=True,
        null=True,
        verbose_name=_("Disponibilité"),
    )

    permis_b = models.BooleanField(
        default=False,
        verbose_name=_("Permis B"),
    )


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

    responsable_placement = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="candidats_gérés",
        verbose_name=_("Responsable placement"),
    )

    date_placement = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date de placement"),
    )

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
        choices=ResultatPlacement.choices,
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
        max_length=10,
        choices=ContratSigne.choices,
        null=True,
        blank=True,
        verbose_name=_("Contrat signé"),
    )

    courrier_rentree = models.BooleanField(
        default=False,
        verbose_name=_("Courrier de rentrée envoyé"),
    )

    date_rentree = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date de rentrée"),
    )

    admissible = models.BooleanField(
        default=False,
        verbose_name=_("Admissible"),
    )

    class Meta:
        verbose_name = _("Candidat")
        verbose_name_plural = _("Candidats")
        ordering = ["-date_inscription"]
        indexes = [
            models.Index(fields=["evenement"]),
            models.Index(fields=["nom", "prenom"]),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initial = {f.name: getattr(self, f.name) for f in self._meta.fields}

    def __str__(self):
        return self.nom_complet

    def __repr__(self):
        return f"<Candidat id={self.pk} nom='{self.nom}' prenom='{self.prenom}'>"

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
    

    def valider_comme_stagiaire(self):
        """
        Crée ou met à jour un compte utilisateur stagiaire à partir de ce candidat.
        Lève une erreur si le candidat n’est pas admissible.
        """
        if not self.admissible:
            raise ValidationError(_("Ce candidat n'est pas admissible."))

        if self.compte_utilisateur:
            user = self.compte_utilisateur
            user.role = CustomUser.ROLE_STAGIAIRE
            user.save()
        else:
            email = f"{self.prenom.lower()}.{self.nom.lower()}@exemple.com"
            username = f"{self.prenom.lower()}_{self.nom.lower()}"
            user = CustomUser.objects.create_user_with_role(
                email=email,
                username=username,
                password="changeme123",
                role=CustomUser.ROLE_STAGIAIRE,
                first_name=self.prenom,
                last_name=self.nom,
            )
            self.compte_utilisateur = user
            self.save()

        return user
    
    @property
    def est_valide_comme_stagiaire(self) -> bool:
        return bool(self.compte_utilisateur and self.compte_utilisateur.role == CustomUser.ROLE_STAGIAIRE)

    @property
    def est_valide_comme_candidatuser(self):
        return bool(self.compte_utilisateur and self.compte_utilisateur.role == CustomUser.ROLE_CANDIDAT_USER)

        
    def valider_comme_candidatuser(self):
        """
        Crée ou met à jour un compte utilisateur avec le rôle candidatuser à partir de ce candidat.
        """
        if self.compte_utilisateur:
            user = self.compte_utilisateur
            user.role = CustomUser.ROLE_CANDIDAT_USER
            user.save()
        else:
            base_email = f"{self.prenom}.{self.nom}".lower().replace(" ", "")
            base_username = slugify_username(f"{self.prenom}_{self.nom}")

            email = f"{base_email}@exemple.com"
            username = base_username

            user = CustomUser.objects.create_user_with_role(
                email=email,
                username=username,
                password="changeme123",
                role=CustomUser.ROLE_CANDIDAT_USER,
                first_name=self.prenom,
                last_name=self.nom,
            )
            self.compte_utilisateur = user
            self.save()

        return user
    

    @property
    def role_utilisateur(self):
        if self.compte_utilisateur:
            return self.compte_utilisateur.get_role_display()
        return "-"

    def clean(self):
        super().clean()
        logger.debug(f"🔍 Validation du candidat : {self}")
        if not self.nom or not self.prenom:
            logger.warning(f"⚠️ Candidat incomplet : nom ou prénom manquant (id={self.pk})")
        if self.statut == self.StatutCandidat.AUTRE:
            logger.info(f"ℹ️ Candidat #{self.pk} a un statut 'autre'")
        if self.compte_utilisateur and not self.email:
            raise ValidationError(_("Un compte utilisateur nécessite une adresse email."))

    def save(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        is_new = self.pk is None
        original = None if is_new else self.__class__.objects.filter(pk=self.pk).first()

        logger.debug(f"{'🆕 Création' if is_new else '✏️ Mise à jour'} du candidat : {self}")
        self.full_clean()

        with transaction.atomic():
            super().save(*args, **kwargs)

            if is_new:
                logger.info(f"🟢 Nouveau candidat créé : {self} (id={self.pk})")
            else:
                self._log_changes()

                # Création auto de l'historique placement
                if original:
                    champs_placement = [
                        "entreprise_placement_id",
                        "resultat_placement",
                        "date_placement",
                        "responsable_placement_id",
                        "contrat_signe",
                    ]
                    if any(getattr(original, champ) != getattr(self, champ) for champ in champs_placement):
                        HistoriquePlacement.objects.create(
                            candidat=self,
                            date=self.date_placement or date.today(),
                            entreprise=self.entreprise_placement,
                            resultat=self.resultat_placement or HistoriquePlacement.ResultatPlacement.EN_ATTENTE,
                            responsable=self.responsable_placement,
                            commentaire="📌 Historique créé automatiquement à la modification du placement."
                        )

    def delete(self, *args, **kwargs):
        logger.warning(f"❌ Suppression du candidat : {self} (id={self.pk})")
        super().delete(*args, **kwargs)

    def _log_changes(self):
        changements = []
        for champ in self._initial:
            old = self._initial.get(champ)
            new = getattr(self, champ)
            if old != new:
                changements.append(f"{champ}: '{old}' → '{new}'")
        if changements:
            logger.info(f"✏️ Candidat modifié (id={self.pk}) – changements : " + "; ".join(changements))
        else:
            logger.debug(f"✅ Aucun changement détecté pour le candidat (id={self.pk})")

    @property
    def ateliers_effectues(self):
        return self.ateliers_tre_collectifs.count()

    @property
    def ateliers_labels(self):
        return [a.get_type_atelier_display() for a in self.ateliers_tre_collectifs.all()]

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
            email=self.email,
            password=mot_de_passe,
            first_name=self.prenom,
            last_name=self.nom
        )

        self.compte_utilisateur = utilisateur
        self.save()
        return utilisateur





class HistoriquePlacement(BaseModel):
    """
    📈 Historique des tentatives ou résultats de placement pour un candidat.
    """

    class ResultatPlacement(models.TextChoices):
        ADMIS = "admis", _("Admis")
        NON_ADMIS = "non_admis", _("Non admis")
        SECOND_ENTRETIEN = "second_entretien", _("Second entretien")
        EN_ATTENTE = "en_attente", _("En attente")
        ABANDON_CANDIDAT = "abandon_candidat", _("Abandon candidat")
        ABANDON_ETS = "abandon_ets", _("Abandon entreprise")
        DEJA_PLACE = "deja_place", _("Déjà placé")
        ABSENT = "absent", _("Absent")

    candidat = models.ForeignKey(
        "Candidat",
        on_delete=models.CASCADE,
        related_name="historique_placements",
        verbose_name=_("Candidat"),
    )

    date = models.DateField(verbose_name=_("Date du placement"))

    entreprise = models.ForeignKey(
        "Partenaire",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="placements_historique",
        verbose_name=_("Entreprise"),
    )

    resultat = models.CharField(
        max_length=30,
        choices=ResultatPlacement.choices,
        verbose_name=_("Résultat"),
    )

    responsable = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="placements_realises",
        verbose_name=_("Responsable"),
    )

    commentaire = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Commentaire"),
        help_text=_("Détails complémentaires sur le placement")
    )

    class Meta:
        verbose_name = _("Historique de placement")
        verbose_name_plural = _("Historique de placements")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.candidat} – {self.date} – {self.resultat}"
