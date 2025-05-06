import logging
from django.db import models
from django.db.models import Q
from django.utils.html import strip_tags
from .base import BaseModel
from .formations import Formation

logger = logging.getLogger(__name__)

class Commentaire(BaseModel):
    """
    Modèle représentant un commentaire associé à une formation.
    """

    # === Champs relationnels ===
    formation = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        related_name="commentaires",
        verbose_name="Formation",
        help_text="Formation à laquelle ce commentaire est associé"
    )

    # === Champs principaux ===
    contenu = models.TextField(
        verbose_name="Contenu du commentaire",
        help_text="Texte du commentaire (sans HTML)"
    )

    saturation = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Niveau de saturation (%)",
        help_text="Pourcentage de saturation mentionné dans le commentaire (0-100)"
    )

    # === Méta options ===
    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['formation', '-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['formation', 'created_at']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        auteur = self.created_by.username if self.created_by else "Anonyme"
        return f"Commentaire de {auteur} sur {self.formation.nom} ({self.created_at.strftime('%d/%m/%Y')})"

    def save(self, *args, **kwargs):
        """ Nettoie et valide les données, journalise les actions. """
        is_new = self.pk is None

        # Validation saturation
        if self.saturation is not None and (self.saturation < 0 or self.saturation > 100):
            logger.warning(f"Saturation invalide ({self.saturation}%) — corrigée.")
            self.saturation = max(0, min(100, self.saturation))

        # Nettoyage HTML
        cleaned = strip_tags(self.contenu)
        if cleaned != self.contenu:
            logger.info("Contenu nettoyé des balises HTML.")
            self.contenu = cleaned

        # Log action
        if is_new:
            logger.info(f"Commentaire créé par {self.created_by or 'Anonyme'} sur {self.formation}")
        else:
            logger.info(f"Commentaire #{self.pk} mis à jour")

        super().save(*args, **kwargs)

    # === Propriétés utiles ===

    @property
    def auteur_nom(self) -> str:
        if not self.created_by:
            return "Anonyme"
        full = f"{self.created_by.first_name} {self.created_by.last_name}".strip()
        return full or self.created_by.username

    @property
    def date_formatee(self) -> str:
        return self.created_at.strftime('%d/%m/%Y')

    @property
    def heure_formatee(self) -> str:
        return self.created_at.strftime('%H:%M')

    # === Méthodes utilitaires ===

    def get_content_preview(self, length=50) -> str:
        return self.contenu if len(self.contenu) <= length else f"{self.contenu[:length]}..."

    def is_recent(self, days=7) -> bool:
        from django.utils import timezone
        from datetime import timedelta
        return self.created_at >= timezone.now() - timedelta(days=days)

    # === Méthodes de classe ===

    @classmethod
    def get_all_commentaires(cls, formation_id=None, auteur_id=None, search_query=None, order_by="-created_at"):
        """ Récupère les commentaires filtrés. """
        logger.debug(f"Chargement des commentaires filtrés")

        queryset = cls.objects.select_related('formation', 'created_by').order_by(order_by)
        filters = Q()

        if formation_id:
            filters &= Q(formation_id=formation_id)
        if auteur_id:
            filters &= Q(created_by_id=auteur_id)
        if search_query:
            filters &= Q(contenu__icontains=search_query)

        queryset = queryset.filter(filters)
        logger.debug(f"{queryset.count()} commentaire(s) trouvé(s)")
        return queryset if queryset.exists() else cls.objects.none()

    @classmethod
    def get_recent_commentaires(cls, days=7, limit=5):
        from django.utils import timezone
        from datetime import timedelta
        date_limite = timezone.now() - timedelta(days=days)
        return cls.objects.select_related('formation', 'created_by')\
            .filter(created_at__gte=date_limite)\
            .order_by('-created_at')[:limit]
