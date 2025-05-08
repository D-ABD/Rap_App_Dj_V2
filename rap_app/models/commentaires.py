import logging
from datetime import timedelta
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils import timezone
from .base import BaseModel
from .formations import Formation

logger = logging.getLogger(__name__)

"""
🎯 Signaux liés aux commentaires de formation.

Ce module contient les signaux `post_save` et `post_delete` pour le modèle `Commentaire`.
Il met automatiquement à jour :
- le champ `dernier_commentaire` dans le modèle `Formation`
- le champ `saturation` si fourni
"""

class Commentaire(BaseModel):
    """
    💬 Modèle représentant un commentaire associé à une formation.

    Un commentaire est rédigé par un utilisateur (ou anonyme) et lié à une formation.
    Il peut contenir un contenu libre, une saturation exprimée en %, et des métadonnées utiles.
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
        help_text="Texte du commentaire (le HTML est automatiquement nettoyé)"
    )

    saturation = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Niveau de saturation (%)",
        help_text="Pourcentage de saturation perçue dans la formation (entre 0 et 100)"
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
        """
        🔁 Représentation textuelle du commentaire.
        """
        auteur = self.created_by.username if self.created_by else "Anonyme"
        return f"Commentaire de {auteur} sur {self.formation.nom} ({self.created_at.strftime('%d/%m/%Y')})"

    def save(self, *args, **kwargs):
        """
        💾 Sauvegarde le commentaire après nettoyage et validation.

        - Supprime tout HTML du contenu via `strip_tags`.
        - Vérifie et contraint la valeur de `saturation` entre 0 et 100.
        - Appelle ensuite la méthode `save()` du `BaseModel`.

        Args:
            *args: Arguments positionnels pour `super().save()`.
            **kwargs: Arguments nommés pour `super().save()`.

        Returns:
            None
        """
        if self.saturation is not None:
            self.saturation = max(0, min(100, self.saturation))

        self.contenu = strip_tags(self.contenu)
        super().save(*args, **kwargs)



    # === Propriétés utiles ===

    @property
    def auteur_nom(self) -> str:
        """
        🔍 Retourne le nom complet de l'auteur ou 'Anonyme' si non renseigné.
        """
        if not self.created_by:
            return "Anonyme"
        full = f"{self.created_by.first_name} {self.created_by.last_name}".strip()
        return full or self.created_by.username

    @property
    def date_formatee(self) -> str:
        """
        📅 Retourne la date de création formatée (jour/mois/année).
        """
        return self.created_at.strftime('%d/%m/%Y')

    @property
    def heure_formatee(self) -> str:
        """
        🕒 Retourne l'heure de création formatée (heure:minute).
        """
        return self.created_at.strftime('%H:%M')

    # === Méthodes utilitaires ===

    def get_content_preview(self, length=50) -> str:
        """
        📝 Récupère un aperçu tronqué du contenu du commentaire.

        Args:
            length (int): Nombre de caractères à afficher avant troncature.

        Returns:
            str: Contenu court avec '...'
        """
        return self.contenu if len(self.contenu) <= length else f"{self.contenu[:length]}..."

    def is_recent(self, days=7) -> bool:
        """
        ⏱️ Indique si le commentaire a été posté récemment.

        Args:
            days (int): Nombre de jours à considérer pour 'récent'.

        Returns:
            bool: True si récent, sinon False.
        """
        return self.created_at >= timezone.now() - timedelta(days=days)

    # === Méthodes de classe ===

    @classmethod
    def get_all_commentaires(cls, formation_id=None, auteur_id=None, search_query=None, order_by="-created_at"):
        """
        📊 Récupère dynamiquement les commentaires selon des filtres.

        Args:
            formation_id (int, optional): ID de la formation concernée.
            auteur_id (int, optional): ID de l'auteur.
            search_query (str, optional): Filtre sur le contenu (texte libre).
            order_by (str, optional): Champ de tri, par défaut date décroissante.

        Returns:
            QuerySet: Liste filtrée de commentaires.
        """
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
        """
        📅 Récupère les commentaires récents dans une période donnée.

        Args:
            days (int): Nombre de jours à considérer comme récents.
            limit (int): Nombre maximum de commentaires à retourner.

        Returns:
            QuerySet: Commentaires récents les plus récents d'abord.
        """
        date_limite = timezone.now() - timedelta(days=days)
        return cls.objects.select_related('formation', 'created_by')\
            .filter(created_at__gte=date_limite)\
            .order_by('-created_at')[:limit]

    def to_serializable_dict(self):
        """
        📦 Retourne une représentation sérialisable du commentaire.

        Returns:
            dict: Dictionnaire des champs exposables du commentaire.
        """
        return {
            "id": self.pk,
            "formation_id": self.formation_id,
            "formation_nom": self.formation.nom,
            "contenu": self.get_content_preview(),
            "saturation": self.saturation,
            "auteur": self.auteur_nom,
            "date": self.date_formatee,
            "heure": self.heure_formatee,
        }

    from django.urls import reverse

    def get_absolute_url(self):
        """
        🔗 Retourne l'URL vers la vue de détail du commentaire.

        Returns:
            str: URL de détail correspondant à ce commentaire.
        """
        return reverse("commentaire-detail", kwargs={"pk": self.pk})
