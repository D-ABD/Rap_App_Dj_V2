import logging
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from ..api.roles import is_staff_or_staffread
from .base import BaseModel
from .prospection import Prospection

logger = logging.getLogger(__name__)


class ProspectionCommentQuerySet(models.QuerySet):
    """QuerySet personnalisé pour filtrer les commentaires."""

    def actifs(self):
        """Commentaires non archivés."""
        return self.filter(statut_commentaire="actif")

    def archives(self):
        """Commentaires archivés."""
        return self.filter(statut_commentaire="archive")

    def visibles_pour_candidat(self):
        """Commentaires visibles par le candidat."""
        return self.actifs().filter(is_internal=False)


class ProspectionCommentManager(models.Manager):
    """Manager rattaché au QuerySet personnalisé."""

    def get_queryset(self):
        return ProspectionCommentQuerySet(self.model, using=self._db)

    def actifs(self):
        return self.get_queryset().actifs()

    def archives(self):
        return self.get_queryset().archives()

    def visibles_pour_candidat(self):
        return self.get_queryset().visibles_pour_candidat()


class ProspectionComment(BaseModel):
    """
    Commentaire rattaché à une Prospection.
    - is_internal=True : visible staff/admin uniquement.
    - is_internal=False : visible également par le candidat propriétaire de la prospection.
    - statut_commentaire : permet d’archiver ou de restaurer un commentaire sans le supprimer.
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

    STATUT_CHOICES = [
        ("actif", _("Actif")),
        ("archive", _("Archivé")),
    ]
    statut_commentaire = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="actif",
        db_index=True,
        verbose_name=_("Statut du commentaire"),
        help_text=_("Permet d’archiver logiquement un commentaire sans le supprimer."),
    )

    objects = ProspectionCommentManager()

    class Meta:
        verbose_name = _("Commentaire de prospection")
        verbose_name_plural = _("Commentaires de prospection")
        ordering = ["-updated_at", "-created_at"]
        indexes = [
            models.Index(fields=["prospection"]),
            models.Index(fields=["is_internal"]),
            models.Index(fields=["statut_commentaire"]),
            models.Index(fields=["created_by"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        who = getattr(self.created_by, "username", "anonyme")
        return f"Commentaire #{self.pk} – prosp #{self.prospection_id} – {who}"

    def clean(self) -> None:
        super().clean()
        if not (self.body or "").strip():
            raise ValidationError({"body": _("Le commentaire ne peut pas être vide.")})

    def save(self, *args, **kwargs):
        self.full_clean()
        with transaction.atomic():
            return super().save(*args, **kwargs)


    # === États / Helpers ===
    def archiver(self, save: bool = True):
        """Archive logiquement le commentaire."""
        self.statut_commentaire = "archive"
        if save:
            self.save(update_fields=["statut_commentaire"])
        logger.info("Commentaire #%s archivé", self.pk)

    def desarchiver(self, save: bool = True):
        """Restaure un commentaire archivé."""
        self.statut_commentaire = "actif"
        if save:
            self.save(update_fields=["statut_commentaire"])
        logger.info("Commentaire #%s désarchivé", self.pk)

    # ------------------------------------------------------------------
    # 🧩 Compatibilité ViewSet (alias pour activite / archive / restore)
    # ------------------------------------------------------------------
    @property
    def activite(self) -> str:
        """Alias rétro-compatible pour le ViewSet."""
        return "archivee" if self.est_archive else "active"

    def archive(self):
        """Alias de archiver() pour compatibilité."""
        return self.archiver()

    def restore(self):
        """Alias de desarchiver() pour compatibilité."""
        return self.desarchiver()

    @property
    def est_archive(self) -> bool:
        """Retourne True si le commentaire est archivé."""
        return self.statut_commentaire == "archive"

    @property
    def is_visible_for_candidate(self) -> bool:
        # visible côté candidat seulement si non interne et actif
        return not self.is_internal and not self.est_archive

    def is_visible_to(self, user) -> bool:
        """Détermine si un utilisateur donné peut voir ce commentaire."""
        if not user or not user.is_authenticated:
            return False
        if is_staff_or_staffread(user) or getattr(user, "is_admin", False) or getattr(user, "is_superuser", False):
            return True
        if hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire():
            return (
                not self.is_internal
                and not self.est_archive
                and self.prospection.owner_id == user.id
            )
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
 