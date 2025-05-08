import logging
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.urls import reverse

from .base import BaseModel
from .formations import Formation

logger = logging.getLogger("application.evenements")

class Evenement(BaseModel):
    """
    📅 Modèle représentant un événement lié à une formation (job dating, forum, etc.).
    Permet de suivre les types d'événements, leur date, lieu, et le nombre de participants.
    """

    class TypeEvenement(models.TextChoices):
        INFO_PRESENTIEL = 'info_collective_presentiel', 'Information collective présentiel'
        INFO_DISTANCIEL = 'info_collective_distanciel', 'Information collective distanciel'
        JOB_DATING = 'job_dating', 'Job dating'
        EVENEMENT_EMPLOI = 'evenement_emploi', 'Événement emploi'
        FORUM = 'forum', 'Forum'
        JPO = 'jpo', 'Journée Portes Ouvertes'
        AUTRE = 'autre', 'Autre'

    formation = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="evenements",
        verbose_name="Formation",
        help_text="Formation associée à l'événement"
    )

    type_evenement = models.CharField(
        max_length=100,
        choices=TypeEvenement.choices,
        db_index=True,
        verbose_name="Type d'événement",
        help_text="Catégorie de l'événement (ex : forum, job dating, etc.)"
    )

    description_autre = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Description personnalisée",
        help_text="Détail du type si 'Autre' est sélectionné"
    )

    details = models.TextField(
        blank=True,
        null=True,
        verbose_name="Détails complémentaires",
        help_text="Détails ou informations supplémentaires"
    )

    event_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de l'événement",
        help_text="Date prévue pour l'événement"
    )

    lieu = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Lieu",
        help_text="Lieu où se déroule l'événement"
    )

    participants_prevus = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Participants prévus",
        help_text="Nombre de personnes attendues"
    )

    participants_reels = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Participants réels",
        help_text="Nombre de participants présents"
    )

    class Meta:
        verbose_name = "Événement"
        verbose_name_plural = "Événements"
        ordering = ['-event_date']
        indexes = [
            models.Index(fields=['event_date']),
            models.Index(fields=['type_evenement']),
            models.Index(fields=['formation']),
        ]

    def __str__(self):
        label = self.description_autre if self.type_evenement == self.TypeEvenement.AUTRE and self.description_autre else self.get_type_evenement_display()
        date_str = self.event_date.strftime('%d/%m/%Y') if self.event_date else "Date inconnue"
        return f"{label} - {date_str} - {self.status_label}"

    def get_absolute_url(self):
        """
        🔗 Retourne l'URL de détail de l'événement.
        """
        return reverse("evenement-detail", kwargs={"pk": self.pk})

    def to_serializable_dict(self):
        """
        📦 Retourne une représentation API de l'événement.
        """
        return {
            "id": self.pk,
            "formation": self.formation.nom if self.formation else None,
            "type_evenement": self.get_type_evenement_display(),
            "description_autre": self.description_autre,
            "details": self.details,
            "event_date": self.event_date.strftime('%Y-%m-%d') if self.event_date else None,
            "lieu": self.lieu,
            "prevus": self.participants_prevus,
            "reels": self.participants_reels,
            "status": self.get_temporal_status(),
            "url": self.get_absolute_url()
        }

    def clean(self):
        today = timezone.now().date()
        if self.type_evenement == self.TypeEvenement.AUTRE and not self.description_autre:
            raise ValidationError({'description_autre': "Veuillez décrire l'événement de type 'Autre'."})
        if self.event_date and self.event_date < today - timezone.timedelta(days=365):
            logger.warning(f"Date ancienne pour l'événement #{self.pk} : {self.event_date}")
        if self.participants_prevus and self.participants_reels:
            if self.participants_reels > self.participants_prevus * 1.5:
                logger.warning(f"Participants réels dépassent les prévisions pour l'événement #{self.pk}")

    def save(self, *args, **kwargs):
        """
        💾 Sauvegarde l'événement avec nettoyage, validation, et journalisation des modifications.

        - Valide les champs (`full_clean`)
        - Utilise `transaction.atomic` pour la cohérence
        - Logue les différences si modification détectée
        - Permet le suivi utilisateur via `user=...` dans `kwargs`
        """
        user = kwargs.pop("user", None)
        is_new = self.pk is None
        original = None if is_new else self.__class__.objects.filter(pk=self.pk).first()

        self.full_clean()

        with transaction.atomic():
            super().save(*args, user=user, **kwargs)
            if is_new:
                logger.info(f"Nouvel événement '{self}' créé.")
            elif original:
                self._log_changes(original)

    def _log_changes(self, original):
        """
        📝 Enregistre les modifications détectées par comparaison avec l'instance originale.

        Args:
            original (Evenement): Ancienne version de l'objet avant modification.
        """
        fields = ['type_evenement', 'event_date', 'formation', 'lieu', 'participants_prevus', 'participants_reels']
        changes = [
            f"{field}: '{getattr(original, field)}' → '{getattr(self, field)}'"
            for field in fields if getattr(original, field) != getattr(self, field)
        ]
        if changes:
            logger.info(f"Modification de l'événement #{self.pk} : {', '.join(changes)}")



    def get_temporal_status(self, days: int = 7) -> str:
        """
        🧭 Retourne le statut temporel de l'événement.
        """
        if not self.event_date:
            return "unknown"
        today = timezone.now().date()
        if self.event_date < today:
            return "past"
        if self.event_date == today:
            return "today"
        if self.event_date <= today + timezone.timedelta(days=days):
            return "soon"
        return "future"

    @property
    def status_label(self) -> str:
        return {
            "past": "Passé",
            "today": "Aujourd'hui",
            "soon": "À venir",
            "future": "À venir"
        }.get(self.get_temporal_status(), "Inconnu")

    @property
    def status_color(self) -> str:
        return {
            "past": "text-secondary",
            "today": "text-danger",
            "soon": "text-warning",
            "future": "text-primary"
        }.get(self.get_temporal_status(), "text-muted")

    def get_participation_rate(self) -> float | None:
        """
        📊 Calcule le taux de participation si possible.
        """
        if self.participants_prevus and self.participants_reels and self.participants_prevus > 0:
            return round((self.participants_reels / self.participants_prevus) * 100, 1)
        return None
