import logging
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .candidat import Candidat
from .partenaires import Partenaire
from .formations import Formation

logger = logging.getLogger("application.appairages")


class AppairageStatut(models.TextChoices):
    TRANSMIS = "transmis", _("Transmis au partenaire")
    EN_ATTENTE = "en_attente", _("En attente de réponse")
    ACCEPTE = "accepte", _("Accepté")
    REFUSE = "refuse", _("Refusé")
    ANNULE = "annule", _("Annulé")


class Appairage(models.Model):
    """
    🔗 Mise en relation entre un candidat et un partenaire dans le cadre d'une formation.
    """
    candidat = models.ForeignKey(Candidat, on_delete=models.CASCADE, related_name="appairages")
    partenaire = models.ForeignKey(Partenaire, on_delete=models.CASCADE, related_name="appairages")
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="appairages", null=True, blank=True)

    date_appairage = models.DateTimeField(default=timezone.now, verbose_name=_("Date de mise en relation"))

    statut = models.CharField(
        max_length=20,
        choices=AppairageStatut.choices,
        default=AppairageStatut.TRANSMIS,
        verbose_name=_("Statut de l'appairage")
    )

    commentaire = models.TextField(blank=True, null=True, verbose_name=_("Commentaire"))
    retour_partenaire = models.TextField(blank=True, null=True, verbose_name=_("Retour du partenaire"))
    date_retour = models.DateTimeField(default=timezone.now, verbose_name=_("Date du retour du partenaire"))

    class Meta:
        verbose_name = _("Appairage")
        verbose_name_plural = _("Appairages")
        ordering = ["-date_appairage"]
        constraints = [
            models.UniqueConstraint(fields=["candidat", "partenaire", "formation"], name="unique_appairage")
        ]

    def __str__(self):
        return f"{self.candidat} → {self.partenaire} ({self.get_statut_display()})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        original = None if is_new else Appairage.objects.filter(pk=self.pk).first()

        with transaction.atomic():
            super().save(*args, **kwargs)

            if is_new:
                logger.info(f"🟢 Appairage créé : {self}")
                HistoriqueAppairage.objects.create(
                    appairage=self,
                    statut=self.statut,
                    auteur=getattr(self, "_user", None),
                    commentaire="Création de l’appairage"
                )
            elif original:
                self._log_changes(original)

    def delete(self, *args, **kwargs):
        logger.warning(f"❌ Suppression appairage : {self}")
        return super().delete(*args, **kwargs)

    def _log_changes(self, original):
        changements = []

        if self.statut != original.statut:
            changements.append(f"Statut : '{original.get_statut_display()}' → '{self.get_statut_display()}'")
            HistoriqueAppairage.objects.create(
                appairage=self,
                statut=self.statut,
                auteur=getattr(self, "_user", None),
                commentaire="Changement de statut"
            )

        if self.retour_partenaire != original.retour_partenaire:
            changements.append("Retour partenaire modifié")

        if self.commentaire != original.commentaire:
            changements.append("Commentaire modifié")

        if changements:
            logger.info(f"✏️ Appairage modifié (id={self.pk}) – " + "; ".join(changements))

class HistoriqueAppairage(models.Model):
    appairage = models.ForeignKey(Appairage, on_delete=models.CASCADE, related_name="historiques")
    date = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=AppairageStatut.choices)
    commentaire = models.TextField(blank=True, verbose_name=_("Commentaire"))
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Auteur")
    )

    class Meta:
        verbose_name = _("Historique d’appairage")
        verbose_name_plural = _("Historiques d’appairages")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.appairage} – {self.get_statut_display()} ({self.date.strftime('%d/%m/%Y')})"
