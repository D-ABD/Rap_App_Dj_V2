from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import logging

from .base import BaseModel
from .candidat import Candidat, ResultatPlacementChoices
from .partenaires import Partenaire
from .formations import Formation

logger = logging.getLogger("application.appairages")


# ───────────────────────────────────────────────
# MANAGER PERSONNALISÉ
# ───────────────────────────────────────────────

class AppairageManager(models.Manager):
    """Manager personnalisé pour gérer les filtres logiques d’appairage."""
    def actifs(self):
        return self.filter(activite=AppairageActivite.ACTIF)

    def archives(self):
        return self.filter(activite=AppairageActivite.ARCHIVE)
# ───────────────────────────────────────────────
# ENUM DES STATUTS
# ───────────────────────────────────────────────

class AppairageStatut(models.TextChoices):
    TRANSMIS = "transmis", _("Transmis au partenaire")
    EN_ATTENTE = "en_attente", _("En attente de réponse")
    ACCEPTE = "accepte", _("Accepté")
    REFUSE = "refuse", _("Refusé")
    ANNULE = "annule", _("Annulé")
    A_FAIRE = "a_faire", _("À faire")
    CONTRAT_A_SIGNER = "contrat_a_signer", _("Contrat à signer")
    CONTRAT_EN_ATTENTE = "contrat_en_attente", _("Contrat en attente")
    APPAIRAGE_OK = "appairage_ok", _("Appairage OK")

class AppairageActivite(models.TextChoices): 
    ACTIF = "actif", _("Actif")
    ARCHIVE = "archive", _("Archivé")

# ───────────────────────────────────────────────
# MODÈLE PRINCIPAL
# ───────────────────────────────────────────────

class Appairage(BaseModel):
    """
    Mise en relation entre un candidat et un partenaire dans le cadre d'une formation.
    Le snapshot sur le candidat est recalculé à partir du dernier appairage (date desc, pk desc).
    """

    objects = AppairageManager()  # ✅ activation du manager custom

    candidat = models.ForeignKey(Candidat, on_delete=models.CASCADE, related_name="appairages")
    partenaire = models.ForeignKey(Partenaire, on_delete=models.CASCADE, related_name="appairages")
    formation = models.ForeignKey(
        Formation, on_delete=models.CASCADE, related_name="appairages",
        null=True, blank=True
    )

    date_appairage = models.DateTimeField(default=timezone.now, verbose_name=_("Date de mise en relation"))

    statut = models.CharField(
        max_length=30,  # 🔧 augmenté à 30 pour anticiper les valeurs futures
        choices=AppairageStatut.choices,
        default=AppairageStatut.TRANSMIS,
        verbose_name=_("Statut de l'appairage"),
    )

    activite = models.CharField(
        max_length=10,
        choices=AppairageActivite.choices,
        default=AppairageActivite.ACTIF,
        verbose_name=_("Activité"),
        db_index=True,
    )


    retour_partenaire = models.TextField(blank=True, null=True, verbose_name=_("Retour du partenaire"))
    date_retour = models.DateTimeField(blank=True, null=True, verbose_name=_("Date du retour du partenaire"))

    class Meta:
        verbose_name = _("Appairage")
        verbose_name_plural = _("Appairages")
        ordering = ["-date_appairage"]
        constraints = [
            models.UniqueConstraint(fields=["candidat", "partenaire", "formation"], name="unique_appairage")
        ]
        indexes = [
            models.Index(fields=["candidat"]),
            models.Index(fields=["partenaire"]),
            models.Index(fields=["formation"]),
            models.Index(fields=["statut"]),
            models.Index(fields=["activite"]),  
            models.Index(fields=["date_appairage"]),
        ]


    def __str__(self):
        return f"{self.candidat} → {self.partenaire} ({self.get_statut_display()})"

    # ───────────────────────────────────────────────
    # MÉTHODES UTILITAIRES
    # ───────────────────────────────────────────────

    def get_formation_identite_complete(self):
        return self.formation.get_formation_identite_complete() if self.formation else None

    def get_formation_identite_bref(self):
        return self.formation.get_formation_identite_bref() if self.formation else None

    def set_user(self, user):
        """Stocke l’utilisateur actif pour l’historique et les synchronisations."""
        self._user = user

    # ───────────────────────────────────────────────
    # ARCHIVAGE
    # ───────────────────────────────────────────────

    def archiver(self, user=None):
        """Marque cet appairage comme archivé."""
        if self.activite != AppairageActivite.ARCHIVE:
            self.activite = AppairageActivite.ARCHIVE
            self.save(user=user, update_fields=["activite"])
            logger.info("📦 Appairage #%s archivé (%s → %s)", self.pk, self.candidat, self.partenaire)

    def desarchiver(self, user=None):
        """Rend cet appairage à nouveau actif."""
        if self.activite != AppairageActivite.ACTIF:
            self.activite = AppairageActivite.ACTIF
            self.save(user=user, update_fields=["activite"])
            logger.info("♻️ Appairage #%s désarchivé (%s → %s)", self.pk, self.candidat, self.partenaire)

    @classmethod
    def archiver_pour_formation(cls, formation, user=None):
        """Archive tous les appairages liés à une formation donnée."""
        apps = cls.objects.filter(formation=formation, activite=AppairageActivite.ACTIF)
        for app in apps:
            app.archiver(user=user)

    @classmethod
    def desarchiver_pour_formation(cls, formation, user=None):
        """Désarchive tous les appairages d’une formation donnée."""
        apps = cls.objects.filter(formation=formation, activite=AppairageActivite.ARCHIVE)
        for app in apps:
            app.desarchiver(user=user)

    # ───────────────────────────────────────────────
    # SYNCHRONISATION & SNAPSHOT
    # ───────────────────────────────────────────────

    _STATUS_PRIORITY = {
        AppairageStatut.APPAIRAGE_OK: 100,
        AppairageStatut.ACCEPTE: 90,
        AppairageStatut.CONTRAT_A_SIGNER: 80,
        AppairageStatut.CONTRAT_EN_ATTENTE: 70,
        AppairageStatut.EN_ATTENTE: 60,
        AppairageStatut.TRANSMIS: 50,
        AppairageStatut.A_FAIRE: 40,
        AppairageStatut.REFUSE: 10,
        AppairageStatut.ANNULE: 0,
    }

    _STATUS_TO_RESULTAT = {
        AppairageStatut.APPAIRAGE_OK: ResultatPlacementChoices.ADMIS,
        AppairageStatut.ACCEPTE: ResultatPlacementChoices.ADMIS,
        AppairageStatut.CONTRAT_A_SIGNER: ResultatPlacementChoices.EN_ATTENTE,
        AppairageStatut.CONTRAT_EN_ATTENTE: ResultatPlacementChoices.EN_ATTENTE,
        AppairageStatut.EN_ATTENTE: ResultatPlacementChoices.EN_ATTENTE,
        AppairageStatut.TRANSMIS: ResultatPlacementChoices.APPAIRAGE_EN_COURS,
        AppairageStatut.A_FAIRE: ResultatPlacementChoices.EN_ATTENTE,
        AppairageStatut.REFUSE: ResultatPlacementChoices.NON_ADMIS,
        AppairageStatut.ANNULE: ResultatPlacementChoices.ABANDON_ETS,
    }



    _ACCEPTED_STATUSES = {AppairageStatut.APPAIRAGE_OK, AppairageStatut.ACCEPTE}
    _CONTRACT_STATUSES = {
        AppairageStatut.CONTRAT_A_SIGNER,
        AppairageStatut.CONTRAT_EN_ATTENTE,
        AppairageStatut.APPAIRAGE_OK,
    }



    def _last_appairage_for(self, candidat: Candidat):
        """Retourne le dernier appairage du candidat (date puis pk)."""
        return (
            type(self)
            .objects.filter(candidat=candidat)
            .order_by("-date_appairage", "-pk")
            .select_related("partenaire", "created_by", "updated_by")
            .first()
        )

    def _sync_candidat_snapshot(self, candidat: Candidat):
        """
        Alimente le candidat depuis son DERNIER appairage
        et met à jour son statut si nécessaire.
        """
        try:
            if not candidat:
                return

            last = self._last_appairage_for(candidat)

            if not last:
                new_vals = dict(
                    entreprise_placement=None,
                    responsable_placement=None,
                    resultat_placement=None,
                    date_placement=None,
                    entreprise_validee=None,
                    contrat_signe=None,
                    # 🔁 si plus d’appairages → statut remis à "AUTRE"
                    statut=Candidat.StatutCandidat.AUTRE,
                )
            else:
                resultat = self._STATUS_TO_RESULTAT.get(last.statut)
                responsable = getattr(last, "created_by", None) or getattr(last, "updated_by", None)
                entreprise = (
                    last.partenaire if last.statut not in (AppairageStatut.REFUSE, AppairageStatut.ANNULE) else None
                )
                entreprise_validee = last.partenaire if last.statut in self._ACCEPTED_STATUSES else None
                contrat = Candidat.ContratSigne.EN_COURS if last.statut in self._CONTRACT_STATUSES else None
                date_pl = last.date_appairage.date() if last.date_appairage else timezone.now().date()

                new_vals = dict(
                    entreprise_placement=entreprise,
                    responsable_placement=responsable,
                    resultat_placement=resultat,
                    date_placement=date_pl,
                    entreprise_validee=entreprise_validee,
                    contrat_signe=contrat,
                    # 🔁 si appairage actif → statut candidat mis à EN_APPAIRAGE
                    statut=Candidat.StatutCandidat.EN_APPAIRAGE,
                )

            dirty = False
            for field, value in new_vals.items():
                if getattr(candidat, field) != value:
                    setattr(candidat, field, value)
                    dirty = True

            if dirty:
                user = getattr(self, "_user", None)
                try:
                    candidat.save(user=user)
                except TypeError:
                    candidat.save()
                logger.info(
                    "🔁 Snapshot candidat #%s mis à jour depuis dernier appairage: statut=%s, entreprise=%s, resultat=%s",
                    candidat.pk,
                    candidat.get_statut_display(),
                    getattr(candidat.entreprise_placement, "nom", None),
                    candidat.resultat_placement,
                )
        except Exception:
            logger.exception(
                "Sync candidat (dernier appairage) impossible (candidat id=%s)",
                getattr(candidat, "pk", None),
            )

    # ──────────────────────────────────────────────────────────────────────
    # Surcharges save/delete
    # ──────────────────────────────────────────────────────────────────────
    def save(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        is_new = self.pk is None

        original = None
        original_candidat_id = None
        if not is_new:
            original = (
                type(self)
                .objects.only("id", "candidat_id", "statut", "retour_partenaire")
                .get(pk=self.pk)
            )
            original_candidat_id = original.candidat_id

        with transaction.atomic():
            if user:
                self.set_user(user)

            super().save(*args, user=user, **kwargs)

            if is_new:
                logger.info("🟢 Appairage créé : %s", self)
                HistoriqueAppairage.objects.create(
                    appairage=self,
                    statut=self.statut,
                    auteur=getattr(self, "_user", None),
                    commentaire="Création de l’appairage",
                )
            else:
                self._log_changes(original)

            self._sync_candidat_snapshot(self.candidat)

            if not is_new and original_candidat_id and original_candidat_id != self.candidat_id:
                try:
                    old_cand = Candidat.objects.get(pk=original_candidat_id)
                    self._sync_candidat_snapshot(old_cand)
                except Candidat.DoesNotExist:
                    pass

    def delete(self, *args, **kwargs):
        cand = self.candidat
        with transaction.atomic():
            logger.warning("❌ Suppression appairage : %s", self)
            super().delete(*args, **kwargs)
            self._sync_candidat_snapshot(cand)

    def _log_changes(self, original):
        changements = []

        if self.statut != original.statut:
            changements.append(f"Statut : '{original.get_statut_display()}' → '{self.get_statut_display()}'")
            HistoriqueAppairage.objects.create(
                appairage=self,
                statut=self.statut,
                auteur=getattr(self, "_user", None),
                commentaire="Changement de statut",
            )

        if self.retour_partenaire != original.retour_partenaire:
            changements.append("Retour partenaire modifié")

        if changements:
            logger.info("✏️ Appairage modifié (id=%s) – %s", self.pk, "; ".join(changements))


class HistoriqueAppairage(models.Model):
    appairage = models.ForeignKey(
        Appairage,
        on_delete=models.CASCADE,
        related_name="historiques",
    )
    date = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(
        max_length=30,
        choices=AppairageStatut.choices,
    )
    commentaire = models.TextField(blank=True, verbose_name=_("Commentaire"))

    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Auteur"),
    )

    class Meta:
        verbose_name = _("Historique d’appairage")
        verbose_name_plural = _("Historiques d’appairages")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.appairage} – {self.get_statut_display()} ({self.date.strftime('%d/%m/%Y')})"

    def archiver(self, user=None):
        if self.activite != AppairageActivite.ARCHIVE:
            self.activite = AppairageActivite.ARCHIVE
            self.save(user=user, update_fields=["activite"])
            HistoriqueAppairage.objects.create(
                appairage=self,
                statut=self.statut,
                auteur=user,
                commentaire="Appairage archivé",
            )
            logger.info("📦 Appairage #%s archivé (%s → %s)", self.pk, self.candidat, self.partenaire)

    def desarchiver(self, user=None):
        if self.activite != AppairageActivite.ACTIF:
            self.activite = AppairageActivite.ACTIF
            self.save(user=user, update_fields=["activite"])
            HistoriqueAppairage.objects.create(
                appairage=self,
                statut=self.statut,
                auteur=user,
                commentaire="Appairage désarchivé",
            )
            logger.info("♻️ Appairage #%s désarchivé (%s → %s)", self.pk, self.candidat, self.partenaire)
