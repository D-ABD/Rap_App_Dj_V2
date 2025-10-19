import logging
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .base import BaseModel
from .appairage import Appairage

logger = logging.getLogger(__name__)


# ============================================================
# 🔍 QuerySet & Manager personnalisés
# ============================================================

class CommentaireAppairageQuerySet(models.QuerySet):
    """QuerySet personnalisé pour les commentaires d’appairage."""

    def actifs(self):
        """Commentaires non archivés."""
        return self.filter(statut_commentaire=CommentaireAppairage.STATUT_ACTIF)

    def archives(self):
        """Commentaires archivés."""
        return self.filter(statut_commentaire=CommentaireAppairage.STATUT_ARCHIVE)


class CommentaireAppairageManager(models.Manager.from_queryset(CommentaireAppairageQuerySet)):
    """Manager avec filtres prêts à l’emploi (actifs / archives)."""
    pass


# ============================================================
# 💬 Modèle principal
# ============================================================

class CommentaireAppairage(BaseModel):
    """
    💬 Commentaire lié à un appairage.
    Permet de documenter les échanges ou suivis autour d'une mise en relation.
    Peut être archivé logiquement (statut_commentaire).
    """

    # --- Constantes de statut ---
    STATUT_ACTIF = "actif"
    STATUT_ARCHIVE = "archive"

    STATUT_CHOICES = [
        (STATUT_ACTIF, _("Actif")),
        (STATUT_ARCHIVE, _("Archivé")),
    ]

    # --- Relations & contenu ---
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
        help_text=_("Statut de l’appairage figé au moment où le commentaire a été créé."),
    )

    # 🗂️ statut logique du commentaire
    statut_commentaire = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default=STATUT_ACTIF,
        db_index=True,
        verbose_name=_("Statut du commentaire"),
        help_text=_("Permet d’archiver ou de restaurer logiquement un commentaire."),
    )

    # --- Manager custom ---
    objects = CommentaireAppairageManager()

    class Meta:
        verbose_name = _("Commentaire d’appairage")
        verbose_name_plural = _("Commentaires d’appairages")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["appairage"]),
            models.Index(fields=["created_by"]),
            models.Index(fields=["statut_commentaire"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        auteur = getattr(self.created_by, "username", "anonyme")
        return f"Commentaire #{self.pk} – appairage #{self.appairage_id} – {auteur}"

    # ============================================================
    # 💾 Sauvegarde & validation
    # ============================================================

    def clean(self):
        super().clean()
        if not (self.body or "").strip():
            raise ValidationError({"body": _("Le commentaire ne peut pas être vide.")})

    def save(self, *args, user=None, **kwargs):
        """
        💾 Capture le statut de l’appairage à la création,
        gère created_by / updated_by, et valide avant enregistrement.
        """
        self.full_clean()

        if not self.pk and self.appairage:
            self.statut_snapshot = self.appairage.statut

        if user and hasattr(user, "pk"):
            if not self.pk and not self.created_by:
                self.created_by = user
            else:
                self.updated_by = user

        with transaction.atomic():
            super().save(*args, **kwargs)

        logger.debug(
            "💬 CommentaireAppairage #%s sauvegardé pour Appairage #%s (user=%s)",
            self.pk,
            self.appairage_id,
            getattr(user, "id", None),
        )

    # ============================================================
    # 🔁 Archivage logique
    # ============================================================

    def archiver(self, save: bool = True):
        """Archive logiquement le commentaire."""
        if self.statut_commentaire != self.STATUT_ARCHIVE:
            self.statut_commentaire = self.STATUT_ARCHIVE
            if save:
                self.save(update_fields=["statut_commentaire"])
            logger.info("CommentaireAppairage #%s archivé", self.pk)

    def desarchiver(self, save: bool = True):
        """Restaure un commentaire archivé."""
        if self.statut_commentaire != self.STATUT_ACTIF:
            self.statut_commentaire = self.STATUT_ACTIF
            if save:
                self.save(update_fields=["statut_commentaire"])
            logger.info("CommentaireAppairage #%s désarchivé", self.pk)

    # --- Aliases rétro-compatibles ---
    def archive(self):
        return self.archiver()

    def restore(self):
        return self.desarchiver()

    @property
    def est_archive(self) -> bool:
        """Retourne True si le commentaire est archivé."""
        return self.statut_commentaire == self.STATUT_ARCHIVE

    @property
    def activite(self) -> str:
        """Alias rétro-compatible pour le ViewSet."""
        return "archivee" if self.est_archive else "active"

    # ============================================================
    # 🧰 Helpers
    # ============================================================

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
            "statut_commentaire": self.statut_commentaire,
            "date": self.created_at.strftime("%d/%m/%Y") if self.created_at else None,
            "heure": self.created_at.strftime("%H:%M") if self.created_at else None,
            "is_recent": self.created_at and self.created_at.date() == now.date(),
            "is_edited": self.updated_at and self.updated_at > self.created_at,
            "est_archive": self.est_archive,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
 