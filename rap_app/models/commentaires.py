import logging
from datetime import timedelta
from django.db import models
from django.db.models import Q, F, Avg, Count
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from weasyprint import HTML
from .base import BaseModel
from .formations import Formation
import csv
import io
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.http import HttpResponse
from rest_framework.decorators import action

logger = logging.getLogger(__name__)

# ----------------------------------------------------
# Signaux déplacés dans signals/commentaires.py
# ----------------------------------------------------


class CommentaireManager(models.Manager):
    """
    Manager personnalisé pour le modèle Commentaire.
    Fournit des méthodes optimisées pour les requêtes courantes.
    """
    
    def recents(self, days=7):
        """
        Retourne les commentaires postés dans les derniers jours.
        
        Args:
            days (int): Nombre de jours à considérer comme récents
            
        Returns:
            QuerySet: Commentaires récents
        """
        date_limite = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=date_limite)
    
    def for_formation(self, formation_id):
        """
        Retourne tous les commentaires pour une formation donnée.
        
        Args:
            formation_id (int): ID de la formation
            
        Returns:
            QuerySet: Commentaires liés à la formation spécifiée
        """
        return self.filter(formation_id=formation_id).select_related('created_by')
    
    def with_saturation(self):
        """
        Retourne uniquement les commentaires avec une valeur de saturation.
        
        Returns:
            QuerySet: Commentaires avec saturation renseignée
        """
        return self.exclude(saturation__isnull=True)
    
    def search(self, query):
        """
        Recherche dans les commentaires.
        
        Args:
            query (str): Terme de recherche
            
        Returns:
            QuerySet: Commentaires correspondants
        """
        if not query:
            return self.all()
        
        return self.filter(Q(contenu__icontains=query) | 
                          Q(created_by__username__icontains=query) |
                          Q(formation__nom__icontains=query))


class Commentaire(BaseModel):
    """
    💬 Modèle représentant un commentaire associé à une formation.

    Un commentaire est rédigé par un utilisateur (ou anonyme) et lié à une formation.
    Il peut contenir un contenu libre, une saturation exprimée en %, et des métadonnées utiles.
    
    Attributs:
        formation (Formation): Formation commentée (relation ForeignKey)
        contenu (str): Texte du commentaire
        saturation (int, optional): Niveau de saturation perçue (0-100%)
        
    Propriétés:
        auteur_nom (str): Nom de l'auteur ou "Anonyme"
        date_formatee (str): Date formatée (JJ/MM/AAAA)
        heure_formatee (str): Heure formatée (HH:MM)
        is_recent (bool): Indique si le commentaire est récent
        
    Méthodes:
        get_content_preview: Aperçu tronqué du contenu
        is_recent: Vérifie si le commentaire est récent
        to_serializable_dict: Dict sérialisable du commentaire
    """
    
    # Constantes pour éviter les valeurs magiques
    SATURATION_MIN = 0
    SATURATION_MAX = 100
    PREVIEW_DEFAULT_LENGTH = 50
    RECENT_DEFAULT_DAYS = 7

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
        help_text="Pourcentage de saturation perçue dans la formation (entre 0 et 100)",
        validators=[
            MinValueValidator(SATURATION_MIN, message="La saturation ne peut pas être négative"),
            MaxValueValidator(SATURATION_MAX, message="La saturation ne peut pas dépasser 100%")
        ]
    )
    
    saturation_formation = models.PositiveIntegerField(
    null=True,
    blank=True,
    verbose_name="Saturation de la formation (copiée)",
    help_text="Valeur de la saturation de la formation au moment du commentaire"
    )

    # === Managers === 
    objects = models.Manager()  # Manager par défaut
    custom = CommentaireManager()  # Manager personnalisé

    # === Méta options ===
    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['formation', '-created_at']
        indexes = [
            models.Index(fields=['created_at'], name='comment_created_idx'),
            models.Index(fields=['formation', 'created_at'], name='comment_form_date_idx'),
            models.Index(fields=['created_by'], name='comment_author_idx'),
            models.Index(fields=['saturation'], name='comment_satur_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(saturation__isnull=True) | Q(saturation__gte=0) & Q(saturation__lte=100),
                name='commentaire_saturation_range'
            )
        ]

    def __str__(self):
        """
        🔁 Représentation textuelle du commentaire.
        """
        auteur = self.created_by.username if self.created_by else "Anonyme"
        return f"Commentaire de {auteur} sur {self.formation.nom} ({self.created_at.strftime('%d/%m/%Y')})"
        
    def __repr__(self):
        """
        Représentation technique pour le débogage.
        """
        return f"<Commentaire(id={self.pk}, formation={self.formation_id}, auteur={self.created_by_id})>"

    def clean(self):
        """
        Validation métier spécifique pour le commentaire.
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        super().clean()
        
        # Validation de la saturation
        if self.saturation is not None:
            if self.saturation < self.SATURATION_MIN or self.saturation > self.SATURATION_MAX:
                raise ValidationError({
                    'saturation': f"La saturation doit être comprise entre {self.SATURATION_MIN} et {self.SATURATION_MAX}%"
                })
        
        # Validation du contenu (non vide)
        if not self.contenu.strip():
            raise ValidationError({
                'contenu': "Le contenu ne peut pas être vide"
            })

    def save(self, *args, **kwargs):
        """
        💾 Sauvegarde le commentaire après nettoyage et validation.

        - Vérifie et contraint la valeur de `saturation` entre 0 et 100.
        - Copie la saturation de la formation (si disponible).
        - Validation des données métier via `clean()`.
        """

        # ✅ NE PAS nettoyer ici : on suppose que le frontend a déjà validé/sécurisé le HTML
        pass

        # Clamp de la saturation
        if self.saturation is not None:
            self.saturation = max(self.SATURATION_MIN, min(self.SATURATION_MAX, self.saturation))

        # Copier la saturation de la formation (au moment de la création)
        if self.formation and hasattr(self.formation, 'saturation'):
            self.saturation_formation = self.formation.saturation

        # Validation métier
        self.clean()

        is_new = self.pk is None

        super().save(*args, **kwargs)

        logger.debug(f"Commentaire #{self.pk} {'créé' if is_new else 'mis à jour'} pour la formation #{self.formation_id}")
        
    def delete(self, *args, **kwargs):
        """
        🗑️ Supprime le commentaire et met à jour la formation associée.
        
        Args:
            *args: Arguments positionnels pour `super().delete()`.
            **kwargs: Arguments nommés pour `super().delete()`.
            update_formation (bool, optional): Mettre à jour les infos de la formation
            
        Returns:
            tuple: Résultat de la suppression
        """
        # Récupérer et supprimer le paramètre update_formation
        update_formation = kwargs.pop('update_formation', True)
        
        # Conserver une référence à la formation
        formation = self.formation if update_formation else None
        
        # Supprimer l'objet
        result = super().delete(*args, **kwargs)
        
        # Mettre à jour la formation si demandé
        if update_formation and formation:
            self.update_formation_static(formation)
            
        logger.debug(f"Commentaire #{self.pk} supprimé pour la formation #{self.formation_id}")
        
        return result

    def update_formation(self):
        """
        🔄 Met à jour les informations de la formation liée à ce commentaire.
        
        Met à jour:
        - Le champ dernier_commentaire de la formation
        - La saturation moyenne si applicable
        - Le compteur de commentaires
        
        Notes:
            Cette méthode ne devrait généralement pas être appelée directement.
        """
        # Assurez-vous que cette méthode existe dans votre modèle Formation
        if hasattr(self.formation, 'update_from_commentaires'):
            self.formation.update_from_commentaires()
        else:
            # Implémentation de secours si la méthode n'existe pas
            from django.db.models import Avg
            
            # Mise à jour du dernier commentaire
            self.formation.dernier_commentaire = (
                Commentaire.objects.filter(formation=self.formation)
                .order_by('-created_at')
                .first()
            )
            
            # Calcul de la saturation moyenne
            saturation_avg = (
                Commentaire.objects.filter(formation=self.formation, saturation__isnull=False)
                .aggregate(Avg('saturation'))
                .get('saturation__avg')
            )
            
            # Mise à jour de la formation
            if hasattr(self.formation, 'saturation_moyenne'):
                self.formation.saturation_moyenne = saturation_avg
                
            # Compter les commentaires
            if hasattr(self.formation, 'nb_commentaires'):
                self.formation.nb_commentaires = (
                    Commentaire.objects.filter(formation=self.formation).count()
                )
                
            # Sauvegarder la formation (avec update_fields si possible)
            update_fields = ['dernier_commentaire']
            if hasattr(self.formation, 'saturation_moyenne'):
                update_fields.append('saturation_moyenne')
            if hasattr(self.formation, 'nb_commentaires'):
                update_fields.append('nb_commentaires')
                
            self.formation.save(update_fields=update_fields)

    @staticmethod
    def update_formation_static(formation):
        """
        🔄 Version statique de update_formation.
        Utilisée lors de la suppression d'un commentaire.
        
        Args:
            formation (Formation): La formation à mettre à jour
        """
        # Assurez-vous que cette méthode existe dans votre modèle Formation
        if hasattr(formation, 'update_from_commentaires'):
            formation.update_from_commentaires()
        else:
            # Implémentation de secours similaire à update_formation
            from django.db.models import Avg
            
            # Mise à jour du dernier commentaire
            formation.dernier_commentaire = (
                Commentaire.objects.filter(formation=formation)
                .order_by('-created_at')
                .first()
            )
            
            # Calcul de la saturation moyenne
            saturation_avg = (
                Commentaire.objects.filter(formation=formation, saturation__isnull=False)
                .aggregate(Avg('saturation'))
                .get('saturation__avg')
            )
            
            # Mise à jour de la formation
            if hasattr(formation, 'saturation_moyenne'):
                formation.saturation_moyenne = saturation_avg
                
            # Compter les commentaires
            if hasattr(formation, 'nb_commentaires'):
                formation.nb_commentaires = (
                    Commentaire.objects.filter(formation=formation).count()
                )
                
            # Sauvegarder la formation
            update_fields = ['dernier_commentaire']
            if hasattr(formation, 'saturation_moyenne'):
                update_fields.append('saturation_moyenne')
            if hasattr(formation, 'nb_commentaires'):
                update_fields.append('nb_commentaires')
                
            formation.save(update_fields=update_fields)

    # === Propriétés utiles ===

    @property
    def auteur_nom(self) -> str:
        """
        🔍 Retourne le nom complet de l'auteur ou 'Anonyme' si non renseigné.
        
        Returns:
            str: Nom complet de l'auteur ou "Anonyme"
        """
        if not self.created_by:
            return "Anonyme"
        full = f"{self.created_by.first_name} {self.created_by.last_name}".strip()
        return full or self.created_by.username

    @property
    def date_formatee(self) -> str:
        """
        📅 Retourne la date de création formatée (jour/mois/année).
        
        Returns:
            str: Date formatée (JJ/MM/AAAA)
        """
        return self.created_at.strftime('%d/%m/%Y')

    @property
    def heure_formatee(self) -> str:
        """
        🕒 Retourne l'heure de création formatée (heure:minute).
        
        Returns:
            str: Heure formatée (HH:MM)
        """
        return self.created_at.strftime('%H:%M')
        
    @property 
    def contenu_sans_html(self) -> str:
        """
        🧹 Retourne le contenu nettoyé de tout HTML.
        
        Returns:
            str: Contenu sans HTML
        """
        return strip_tags(self.contenu)

    @property
    def formation_nom(self) -> str:
        """
        🏫 Retourne le nom de la formation associée.
        
        Returns:
            str: Nom de la formation
        """
        return self.formation.nom if self.formation else "Formation inconnue"

    # === Méthodes utilitaires ===

    def get_content_preview(self, length=None) -> str:
        """
        📝 Récupère un aperçu tronqué du contenu du commentaire.

        Args:
            length (int, optional): Nombre de caractères à afficher avant troncature.
                Si None, utilise la valeur par défaut PREVIEW_DEFAULT_LENGTH.

        Returns:
            str: Contenu court avec '...' si nécessaire
        """
        length = length or self.PREVIEW_DEFAULT_LENGTH
        return self.contenu if len(self.contenu) <= length else f"{self.contenu[:length]}..."

    def is_recent(self, days=None) -> bool:
        """
        ⏱️ Indique si le commentaire a été posté récemment.

        Args:
            days (int, optional): Nombre de jours à considérer pour 'récent'.
                Si None, utilise la valeur par défaut RECENT_DEFAULT_DAYS.

        Returns:
            bool: True si récent, sinon False.
        """
        days = days or self.RECENT_DEFAULT_DAYS
        return self.created_at >= timezone.now() - timedelta(days=days)
        
    def is_edited(self) -> bool:
        """
        ✏️ Indique si le commentaire a été modifié après sa création.
        
        Returns:
            bool: True si modifié, False sinon
        """
        # Tolérance de 1 minute entre création et modification
        tolerance = timedelta(minutes=1)
        return self.updated_at and (self.updated_at - self.created_at > tolerance)

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
    def get_recent_commentaires(cls, days=None, limit=5):
        """
        📅 Récupère les commentaires récents dans une période donnée.

        Args:
            days (int, optional): Nombre de jours à considérer comme récents.
                Si None, utilise la valeur par défaut RECENT_DEFAULT_DAYS.
            limit (int): Nombre maximum de commentaires à retourner.

        Returns:
            QuerySet: Commentaires récents les plus récents d'abord.
        """
        days = days or cls.RECENT_DEFAULT_DAYS
        date_limite = timezone.now() - timedelta(days=days)
        return cls.objects.select_related('formation', 'created_by')\
            .filter(created_at__gte=date_limite)\
            .order_by('-created_at')[:limit]
            
    @classmethod
    def get_saturation_stats(cls, formation_id=None):
        """
        📊 Récupère des statistiques sur la saturation.
        
        Args:
            formation_id (int, optional): Si fourni, filtre par formation
            
        Returns:
            dict: Statistiques de saturation (moyenne, min, max, count)
        """
        queryset = cls.objects.filter(saturation__isnull=False)
        
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
            
        stats = queryset.aggregate(
            avg=Avg('saturation'),
            min=models.Min('saturation'),
            max=models.Max('saturation'),
            count=Count('id')
        )
        
        return stats

    def to_serializable_dict(self, include_full_content=False):
        formation = self.formation

        """
        📦 Retourne une représentation sérialisable du commentaire.

        Args:
            include_full_content (bool): Si True, inclut le contenu complet
                                        sinon, inclut seulement un aperçu

        Returns:
            dict: Dictionnaire des champs exposables du commentaire.
        """
        return {
            "id": self.pk,
            "formation_id": formation.id if formation else None,
            "formation_nom": formation.nom if formation else "N/A",
            "num_offre": getattr(formation, "num_offre", None),
            "centre_nom": getattr(formation.centre, "nom", None) if getattr(formation, "centre", None) else None,
            "start_date": formation.start_date.isoformat() if getattr(formation, "start_date", None) else None,
            "end_date": formation.end_date.isoformat() if getattr(formation, "end_date", None) else None,
            "type_offre": formation.type_offre.nom if getattr(formation, "type_offre", None) else None,
            "statut": formation.statut.nom if getattr(formation, "statut", None) else None,
            "contenu": self.contenu if include_full_content else self.get_content_preview(),
            "saturation": self.saturation,
            "saturation_formation": self.saturation_formation,  # ✅ valeur historique au moment du commentaire
            "auteur": self.auteur_nom,
            "date": self.date_formatee,
            "heure": self.heure_formatee,
            "is_recent": self.is_recent(),
            "is_edited": self.is_edited(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
    def get_edit_url(self):
        """
        ✏️ Retourne l'URL vers la vue de modification du commentaire.
        
        Returns:
            str: URL d'édition pour ce commentaire
        """
        return reverse("commentaire-edit", kwargs={"pk": self.pk})
        
    def get_delete_url(self):
        """
        🗑️ Retourne l'URL vers la vue de suppression du commentaire.
        
        Returns:
            str: URL de suppression pour ce commentaire
        """
        return reverse("commentaire-delete", kwargs={"pk": self.pk})
    
    @action(detail=False, methods=["get"], url_path="export-pdf")
    def export_pdf(self, request):
        ids = request.GET.getlist("ids")
        commentaires = self.queryset.filter(id__in=ids)

        html_string = render_to_string("commentaires/export_pdf.html", {"commentaires": commentaires})
        pdf_file = HTML(string=html_string).write_pdf()

        return HttpResponse(
            pdf_file,
            content_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="commentaires.pdf"'}
        )



