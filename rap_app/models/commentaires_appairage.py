import logging
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .base import BaseModel
from .appairage import Appairage

logger = logging.getLogger(__name__)


class CommentaireAppairage(BaseModel):
    """
    💬 Commentaire lié à un appairage.
    Permet de documenter les échanges ou suivis autour d'une mise en relation.
    """

    appairage = models.ForeignKey(
        Appairage,
        on_delete=models.CASCADE,
        related_name="commentaires",
        verbose_name=_("Appairage"),
    )
    body = models.TextField(verbose_name=_("Commentaire"))

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commentaires_appairages",
        verbose_name=_("Auteur"),
    )

    # 📌 snapshot du statut de l’appairage au moment du commentaire
    statut_snapshot = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=_("Statut au moment du commentaire"),
        help_text="Statut de l’appairage figé au moment où le commentaire a été créé",
    )

    class Meta:
        verbose_name = _("Commentaire d’appairage")
        verbose_name_plural = _("Commentaires d’appairages")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Commentaire #{self.pk} sur {self.appairage}"

    def save(self, *args, user=None, **kwargs):
        """
        💾 Lors de la création, capture aussi le statut de l'appairage
        et gère automatiquement created_by / updated_by hérités de BaseModel.
        """
        if not self.pk and self.appairage:
            self.statut_snapshot = self.appairage.statut

        # Gestion created_by / updated_by
        if user and hasattr(user, "pk"):
            if not self.pk and not self.created_by:
                self.created_by = user
            else:
                self.updated_by = user

        super().save(*args, **kwargs)

        logger.debug(
            f"💬 CommentaireAppairage #{self.pk} sauvegardé "
            f"pour Appairage #{self.appairage_id} (user={getattr(user, 'id', None)})"
        )

    # ──────────────── Helpers ────────────────
    def auteur_nom(self):
        if self.created_by:
            return self.created_by.get_full_name() or self.created_by.username
        return "Anonyme"

    def to_serializable_dict(self, include_full_content=True) -> dict:
        now = timezone.now()
        return {
            "id": self.pk,
            "appairage_id": self.appairage_id,
            "body": self.body if include_full_content else (self.body[:120] + "…" if self.body else ""),
            "auteur": self.auteur_nom(),
            "statut_snapshot": self.statut_snapshot,
            "date": self.created_at.strftime("%d/%m/%Y") if self.created_at else None,
            "heure": self.created_at.strftime("%H:%M") if self.created_at else None,
            "is_recent": self.created_at and self.created_at.date() == now.date(),
            "is_edited": self.updated_at and self.updated_at > self.created_at,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
 