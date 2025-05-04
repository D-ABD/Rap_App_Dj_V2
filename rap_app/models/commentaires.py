import logging
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.html import strip_tags
from .base import BaseModel
from .formations import Formation
from django.contrib.auth import get_user_model

# Configuration du logger
logger = logging.getLogger(__name__)

User = get_user_model()


class Commentaire(BaseModel):
    """
    Modèle représentant un commentaire associé à une formation.
    
    Ce modèle permet de stocker les commentaires des utilisateurs sur les formations,
    avec éventuellement une indication du niveau de saturation si le commentaire
    concerne le remplissage de la formation.
    
    Relations:
    - Lié à une formation (ForeignKey vers Formation)
    - Lié à un utilisateur qui a créé le commentaire (ForeignKey vers User)
    
    Champs spécifiques:
    - contenu: Texte du commentaire
    - saturation: Valeur en pourcentage (optionnelle)
    """

    formation = models.ForeignKey(
        Formation, 
        on_delete=models.CASCADE, 
        related_name="commentaires", 
        verbose_name="Formation"
    )
    
    utilisateur = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True, 
        related_name="commentaires", 
        verbose_name="Utilisateur associé"
    )
    
    contenu = models.TextField(
        verbose_name="Contenu du commentaire"
    )
    
    saturation = models.PositiveIntegerField(
        null=True, 
        blank=True,
        verbose_name="Niveau de saturation (%)"
    )

    def __str__(self):
        """
        Retourne une représentation lisible du commentaire.
        """
        username = self.utilisateur.username if self.utilisateur else "Anonyme"
        return f"Commentaire de {username} sur {self.formation.nom} ({self.created_at.strftime('%d/%m/%Y')})"

    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour ajouter des logs et validations.
        """
        is_new = self.pk is None
        
        # Validation du niveau de saturation
        if self.saturation is not None and (self.saturation < 0 or self.saturation > 100):
            logger.warning(f"Tentative de définir une saturation invalide ({self.saturation}%) pour le commentaire.")
            self.saturation = max(0, min(100, self.saturation))  # Limiter entre 0 et 100
        
        # Nettoyer le contenu des balises HTML potentiellement dangereuses
        cleaned_content = strip_tags(self.contenu)
        if cleaned_content != self.contenu:
            logger.info(f"Nettoyage des balises HTML du commentaire")
            self.contenu = cleaned_content
        
        # Journalisation
        if is_new:
            user_str = self.utilisateur.username if self.utilisateur else "Anonyme"
            formation_str = self.formation.nom if self.formation else "N/A"
            logger.info(
                f"Création d'un commentaire par {user_str} sur formation '{formation_str}'. "
                f"Saturation: {self.saturation}%"
            )
        else:
            logger.info(f"Mise à jour du commentaire #{self.pk}")
        
        super().save(*args, **kwargs)

    def get_content_preview(self, length=50):
        """
        Retourne un aperçu du contenu du commentaire limité à une certaine longueur.
        """
        if len(self.contenu) <= length:
            return self.contenu
        return f"{self.contenu[:length]}..."

    def is_recent(self, days=7):
        """
        Vérifie si le commentaire a été créé récemment (dans les X derniers jours).
        """
        from django.utils import timezone
        from datetime import timedelta
        return self.created_at >= (timezone.now() - timedelta(days=days))

    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['formation', '-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['formation']),
        ]


    @classmethod
    def get_all_commentaires(cls, formation_id=None, utilisateur_id=None, search_query=None, order_by="-created_at"):
        """
        Récupère tous les commentaires avec options de filtres.
        
        Paramètres:
        - formation_id: Filtrer par formation spécifique
        - utilisateur_id: Filtrer par utilisateur spécifique
        - search_query: Recherche textuelle dans le contenu
        - order_by: Champ de tri (défaut: commentaires les plus récents en premier)
        """
        logger.debug(
            f"Recherche de commentaires avec filtres: "
            f"formation_id={formation_id}, utilisateur_id={utilisateur_id}, "
            f"search_query='{search_query}', tri par {order_by}"
        )
        
        queryset = cls.objects.select_related('formation', 'utilisateur').order_by(order_by)

        filters = Q()
        if formation_id:
            filters &= Q(formation_id=formation_id)
        if utilisateur_id:
            filters &= Q(utilisateur_id=utilisateur_id)
        if search_query:
            filters &= Q(contenu__icontains=search_query)

        queryset = queryset.filter(filters)
        count = queryset.count()
        
        logger.debug(f"Recherche de commentaires: {count} résultats trouvés")
        
        return queryset if queryset.exists() else cls.objects.none()  # Évite l'erreur avec un queryset vide


@receiver(post_save, sender=Commentaire)
def update_formation_saturation(sender, instance, **kwargs):
    """
    Met à jour la saturation et le dernier commentaire après un ajout.
    
    Ce signal est déclenché après chaque sauvegarde d'un commentaire et
    met à jour les informations associées dans la formation concernée.
    """
    if instance.formation:
        updates = {}

        if instance.saturation is not None:
            updates['saturation'] = instance.saturation
            logger.info(
                f"Mise à jour de la saturation de la formation #{instance.formation.id} "
                f"'{instance.formation.nom}' à {instance.saturation}%"
            )

        dernier_commentaire = Commentaire.objects.filter(formation=instance.formation).order_by('-created_at').first()
        updates['dernier_commentaire'] = dernier_commentaire.contenu if dernier_commentaire else ""

        if updates:
            Formation.objects.filter(id=instance.formation.id).update(**updates)
            logger.debug(f"Formation #{instance.formation.id} mise à jour suite à un commentaire")


@receiver(post_delete, sender=Commentaire)
def handle_commentaire_delete(sender, instance, **kwargs):
    """
    Met à jour la formation après la suppression d'un commentaire.
    
    Ce signal est déclenché après la suppression d'un commentaire et
    met à jour le dernier commentaire affiché dans la formation.
    """
    if instance.formation:
        logger.info(f"Commentaire #{instance.pk} supprimé, mise à jour de la formation #{instance.formation.id}")
        
        dernier_commentaire = Commentaire.objects.filter(formation=instance.formation).order_by('-created_at').first()
        Formation.objects.filter(id=instance.formation.id).update(
            dernier_commentaire=dernier_commentaire.contenu if dernier_commentaire else ""
        )
        
        logger.debug(
            f"Dernier commentaire de la formation #{instance.formation.id} mis à jour "
            f"après suppression d'un commentaire"
        )

