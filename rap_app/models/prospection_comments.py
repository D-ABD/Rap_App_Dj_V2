import logging
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from .base import BaseModel
from .prospection import Prospection

logger = logging.getLogger(__name__)


class ProspectionComment(BaseModel):
    """
    Commentaire rattaché à une Prospection.
    - is_internal=True : visible staff/admin uniquement.
    - is_internal=False : visible également par le candidat propriétaire de la prospection.
    """
    prospection = models.ForeignKey(
        Prospection,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("Prospection"),
    )
    body = models.TextField(verbose_name=_("Commentaire"))
    is_internal = models.BooleanField(
        default=False,
        verbose_name=_("Interne (staff uniquement)"),
    )

    class Meta:
        verbose_name = _("Commentaire de prospection")
        verbose_name_plural = _("Commentaires de prospection")
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["prospection"]),
            models.Index(fields=["is_internal"]),
            models.Index(fields=["created_by"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        who = getattr(self.created_by, "username", "anonyme")
        return f"Comment #{self.pk} – prosp #{self.prospection_id} – {who}"

    def clean(self) -> None:
        super().clean()
        if not (self.body or "").strip():
            raise ValidationError({"body": _("Le commentaire ne peut pas être vide.")})

    def save(self, *args, **kwargs):
        self.full_clean()
        with transaction.atomic():
            return super().save(*args, **kwargs)

    @property
    def is_visible_for_candidate(self) -> bool:
        # visible côté candidat seulement si non interne
        return not self.is_internal

    # Helper d'accès unitaire (facultatif, réutilisable)
    def is_visible_to(self, user) -> bool:
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "is_staff", False) or getattr(user, "is_admin", False) or getattr(user, "is_superuser", False):
            return True
        if hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire():
            return (not self.is_internal) and (self.prospection.owner_id == user.id)
        return False
    
    @property
    def prospection_text(self) -> str:
        """
        Texte lisible de la prospection rattachée, ex: 'Partenaire • Formation'.
        Fallback sur '#<id>' si les noms ne sont pas disponibles.
        """
        try:
            partner = getattr(self.prospection, "partenaire_nom", None)
            formation = getattr(self.prospection, "formation_nom", None)
        except Exception:
            partner = formation = None

        parts = [p for p in (partner, formation) if p]
        return " • ".join(parts) if parts else f"#{self.prospection_id}"
