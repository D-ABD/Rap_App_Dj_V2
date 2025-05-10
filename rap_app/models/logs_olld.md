from __future__ import annotations
from django.db import connection

from django.apps import apps
from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from typing import Optional, Dict, Any, TYPE_CHECKING
import logging

from ..models.base import BaseModel

logger = logging.getLogger(__name__)

# Typage correct de l'utilisateur pour l'autocomplétion statique
if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser
    UserType = AbstractBaseUser
else:
    UserType = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL).remote_field.model


def table_exists(table_name: str) -> bool:
    """
    Vérifie si une table existe dans la base de données.
    Utile pour éviter les erreurs pendant les migrations/tests initiaux.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
            [table_name]
        )
        return cursor.fetchone()[0]


class LogUtilisateurManager(models.Manager):
    def for_object(self, obj: models.Model):
        """Récupère tous les logs liés à un objet donné."""
        content_type = ContentType.objects.get_for_model(obj)
        return self.filter(content_type=content_type, object_id=obj.pk)

    def actions_by_user(self, user: UserType, limit: Optional[int] = None):
        """Récupère les actions effectuées par un utilisateur."""
        qs = self.filter(created_by=user).order_by('-created_at')
        return qs[:limit] if limit else qs

    def recent_actions(self, limit: int = 50):
        """Récupère les dernières actions effectuées dans le système."""
        return self.select_related('content_type', 'created_by').order_by('-created_at')[:limit]


class LogUtilisateur(BaseModel):
    """
    🧾 Journalisation simple des actions utilisateur sur les objets.

    Ce modèle permet de tracer : action, objet cible, utilisateur, date et détails.
    """

    # Actions communes
    ACTION_CREATE = 'création'
    ACTION_UPDATE = 'modification'
    ACTION_DELETE = 'suppression'
    ACTION_VIEW = 'consultation'

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    action = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    objects = LogUtilisateurManager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Log utilisateur")
        verbose_name_plural = _("Logs utilisateur")

    def __str__(self) -> str:
        return f"{self.action} - {self.content_type.model} #{self.object_id}"

    def to_serializable_dict(self) -> Dict[str, Any]:
        """Représentation JSON-friendly du log utilisateur."""
        return {
            "id": self.pk,
            "action": self.action,
            "model": self.content_type.model if self.content_type else None,
            "object_id": self.object_id,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "utilisateur": {
                "id": self.created_by.pk if self.created_by else None,
                "username": self.created_by.username if self.created_by else "Système"
            },
        }

    @classmethod
    def log_action(
        cls,
        instance: models.Model,
        action: str,
        user: Optional[UserType] = None,
        details: str = ""
    ) -> Optional[LogUtilisateur]:
        """
        Méthode utilitaire pour créer un log utilisateur sécurisé (protégé en cas de migrations).
        """
        if not apps.ready or not instance or not getattr(instance, 'pk', None):
            return None

        # 🔒 Vérifie que la table existe avant d’insérer
        if not table_exists(cls._meta.db_table):
            logger.warning(f"[Log] Table {cls._meta.db_table} absente — log ignoré")
            return None

        try:
            content_type = ContentType.objects.get_for_model(instance)
        except ContentType.DoesNotExist:
            logger.warning(f"[Log] ContentType manquant pour {instance.__class__.__name__} — log ignoré")
            return None

        try:
            log = cls(
                content_type=content_type,
                object_id=instance.pk,
                action=action,
                details=details,
                created_by=user
            )
            log.save()
            return log
        except Exception as e:
            logger.error(f"Erreur lors de la création du log: {e}", exc_info=True)
            return None
