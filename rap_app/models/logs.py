from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from .base import BaseModel
import logging

logger = logging.getLogger(__name__)

class LogUtilisateur(BaseModel):
    """
    🧾 Log des actions utilisateur sur les objets du système.

    Ce modèle trace :
    - L’objet ciblé via content_type et object_id (GenericForeignKey)
    - L’utilisateur ayant effectué l’action (via created_by hérité)
    - La nature de l’action et ses détails éventuels
    """

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="logs_utilisateurs",  # ⚠️ correction ici
        verbose_name="Type d'objet",
        help_text="Type de modèle concerné par cette action"
    )

    object_id = models.PositiveIntegerField(
        verbose_name="Identifiant de l'objet",
        help_text="ID de l'objet concerné par l'action",
        null=True, blank=True  # ⚠️ valeur par défaut souple
    )

    content_object = GenericForeignKey('content_type', 'object_id')

    action = models.CharField(
        max_length=255,
        verbose_name="Action réalisée",
        help_text="Type d'action effectuée (création, suppression, modification, etc.)"
    )

    details = models.TextField(
        blank=True,
        null=True,
        verbose_name="Détails de l'action",
        help_text="Informations complémentaires concernant l'action"
    )

    class Meta:
        verbose_name = "Log utilisateur"
        verbose_name_plural = "Logs utilisateurs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["object_id"]),
            models.Index(fields=["content_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.action} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        """
        💾 Sauvegarde du log avec utilisateur optionnel et journalisation.
        """
        user = kwargs.pop("user", None)
        if user and not self.created_by:
            self.created_by = user

        if getattr(settings, 'ENABLE_MODEL_LOGGING', settings.DEBUG):
            logger.info(f"LogUtilisateur: {self.action} par {user or self.created_by} sur {self.content_type} #{self.object_id}")

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        🔗 URL vers la vue de détail de ce log.
        """
        return reverse("logutilisateur-detail", kwargs={"pk": self.pk})

    def to_serializable_dict(self):
        """
        📦 Représentation JSON-friendly de l’objet.

        Returns:
            dict: Données sérialisables
        """
        return {
            "id": self.pk,
            "action": self.action,
            "model": self.content_type.model,
            "object_id": self.object_id,
            "details": self.details,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M'),
            "utilisateur": self.created_by.username if self.created_by else "Système"
        }

    @classmethod
    def log_action(cls, instance, action: str, user=None, details: str = ""):
        """
        📥 Méthode de classe pour créer un log utilisateur lié à un objet.

        Args:
            instance (models.Model): L'objet concerné.
            action (str): Description de l'action (ex: "Création").
            user (User, optional): L'utilisateur ayant déclenché l'action.
            details (str, optional): Informations supplémentaires.
        """
        if not instance.pk:
            raise ValueError("Impossible de loguer une action sur un objet non sauvegardé.")

        cls.objects.create(
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.pk,
            action=action,
            details=details,
            created_by=user
        )
        
