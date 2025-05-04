import logging
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .base import BaseModel
from .formations import Formation

# Configuration du logger avec un nom plus spécifique
logger = logging.getLogger("application.evenements")

class Evenement(BaseModel):
    """
    Modèle représentant un événement lié à une formation.
    
    Ce modèle permet de suivre différents types d'événements organisés dans le cadre
    des formations, comme les réunions d'information, job dating, forums, etc.
    
    Attributes:
        formation: Référence à la formation associée à cet événement
        type_evenement: Catégorie de l'événement (présentiel, distanciel, etc.)
        details: Informations complémentaires sur l'événement
        event_date: Date prévue pour l'événement
        description_autre: Précision obligatoire si le type d'événement est 'Autre'
        lieu: Emplacement où se déroule l'événement
        participants_prevus: Nombre de participants attendus
        participants_reels: Nombre de participants réels après l'événement
    """

    # Constantes pour les types d'événements - utilisation d'une énumération pour plus de clarté
    class TypeEvenement(models.TextChoices):
        INFO_PRESENTIEL = 'info_collective_presentiel', 'Information collective présentiel'
        INFO_DISTANCIEL = 'info_collective_distanciel', 'Information collective distanciel'
        JOB_DATING = 'job_dating', 'Job dating'
        EVENEMENT_EMPLOI = 'evenement_emploi', 'Événement emploi'
        FORUM = 'forum', 'Forum'
        JPO = 'jpo', 'Journée Portes Ouvertes (JPO)'
        AUTRE = 'autre', 'Autre'
    
    # Pour garantir la rétrocompatibilité avec le code existant
    INFO_PRESENTIEL = TypeEvenement.INFO_PRESENTIEL.value
    INFO_DISTANCIEL = TypeEvenement.INFO_DISTANCIEL.value
    JOB_DATING = TypeEvenement.JOB_DATING.value
    EVENEMENT_EMPLOI = TypeEvenement.EVENEMENT_EMPLOI.value
    FORUM = TypeEvenement.FORUM.value
    JPO = TypeEvenement.JPO.value
    AUTRE = TypeEvenement.AUTRE.value
    
    # Conservation de la liste des choix pour rétrocompatibilité
    TYPE_EVENEMENT_CHOICES = TypeEvenement.choices

    formation = models.ForeignKey(
        Formation, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,  
        related_name="evenements",
        verbose_name="Formation associée",
        help_text="Formation à laquelle cet événement est rattaché"
    )
    
    type_evenement = models.CharField(
        max_length=100, 
        choices=TypeEvenement.choices, 
        verbose_name="Type d'événement",
        db_index=True,
        help_text="Catégorie de l'événement"
    )
    
    details = models.TextField(
        null=True,  
        blank=True, 
        verbose_name="Détails de l'événement",
        help_text="Informations complémentaires sur l'événement"
    )
    
    event_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="Date de l'événement",
        help_text="Date prévue pour l'événement"
    )
    
    description_autre = models.CharField(
        max_length=255,  
        null=True,  
        blank=True,  
        verbose_name="Description pour 'Autre' événement",
        help_text="Précision obligatoire si le type d'événement est 'Autre'"
    )
    
    lieu = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Lieu",
        help_text="Emplacement où se déroule l'événement"
    )
    
    participants_prevus = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Participants prévus",
        help_text="Nombre de participants attendus"
    )
    
    participants_reels = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Participants réels",
        help_text="Nombre de participants réels (à remplir après l'événement)"
    )

    def clean(self):
        """
        Validation personnalisée :
        - Si l'événement est de type "Autre", la description doit être remplie.
        - Vérification que la date n'est pas trop ancienne.
        - Validation des participants réels par rapport aux participants prévus.
        """
        today = timezone.now().date()
        
        # Validation du type "Autre"
        if self.type_evenement == self.AUTRE and not self.description_autre:
            raise ValidationError({
                'description_autre': "Veuillez fournir une description pour l'événement de type 'Autre'."
            })
            
        # Avertissement pour les dates trop anciennes (plus d'un an)
        if self.event_date and self.event_date < today - timezone.timedelta(days=365):
            logger.warning(
                f"Événement ID={self.pk}: Date très ancienne détectée ({self.event_date}, plus d'un an)"
            )
        
        # Validation des participants réels vs prévus (si les deux sont renseignés)
        if self.participants_prevus and self.participants_reels and self.participants_reels > self.participants_prevus * 1.5:
            logger.warning(
                f"Événement ID={self.pk}: Nombre de participants réels ({self.participants_reels}) "
                f"très supérieur aux prévisions ({self.participants_prevus})"
            )

    def save(self, *args, **kwargs):
        """
        Personnalisation de la sauvegarde :
        - Vérifie les règles de validation
        - Journalise les opérations avec plus de détails
        - Utilise une transaction pour garantir l'intégrité
        """
        is_new = not self.pk
        
        # Utilisation de transaction.atomic pour garantir l'intégrité
        with transaction.atomic():
            # Validation (full_clean applique les validateurs du modèle)
            self.full_clean()
            
            # Récupération de l'objet original pour comparaison (si non-nouveau)
            original = None
            if not is_new:
                try:
                    original = Evenement.objects.get(pk=self.pk)
                except Evenement.DoesNotExist:
                    pass
            
            # Journalisation détaillée
            if is_new:
                logger.info(
                    f"Création d'un nouvel événement de type '{self.get_type_evenement_display()}' "
                    f"pour le {self.event_date.strftime('%d/%m/%Y') if self.event_date else 'date non spécifiée'} "
                    f"(formation: {self.formation.nom if self.formation else 'N/A'})"
                )
            elif original:
                self._log_changes(original)
            
            # Sauvegarde du modèle
            super().save(*args, **kwargs)
    
    def _log_changes(self, original):
        """
        Méthode auxiliaire pour journaliser les changements de façon structurée.
        
        Args:
            original: Instance originale de l'objet avant modification
        """
        changes = []
        
        # Détection des changements pour les champs principaux
        fields_to_check = {
            'type_evenement': {
                'display': lambda obj: obj.get_type_evenement_display(), 
                'label': 'type'
            },
            'event_date': {
                'display': lambda obj: obj.event_date.strftime('%d/%m/%Y') if obj.event_date else 'non spécifiée',
                'label': 'date'
            },
            'formation': {
                'display': lambda obj: obj.formation.nom if obj.formation else 'N/A',
                'label': 'formation'
            },
            'lieu': {
                'display': lambda obj: obj.lieu if obj.lieu else 'non spécifié',
                'label': 'lieu'
            },
            'participants_prevus': {
                'display': lambda obj: str(obj.participants_prevus) if obj.participants_prevus is not None else 'non spécifié',
                'label': 'participants prévus'
            },
            'participants_reels': {
                'display': lambda obj: str(obj.participants_reels) if obj.participants_reels is not None else 'non spécifié',
                'label': 'participants réels'
            }
        }
        
        # Vérification de chaque champ
        for field, config in fields_to_check.items():
            old_value = getattr(original, field)
            new_value = getattr(self, field)
            
            if old_value != new_value:
                old_display = config['display'](original)
                new_display = config['display'](self)
                changes.append(f"{config['label']}: '{old_display}' → '{new_display}'")
        
        # Journalisation des changements si nécessaire
        if changes:
            logger.info(f"Modification de l'événement #{self.pk}: {', '.join(changes)}")
    
    def is_past(self):
        """
        Indique si l'événement est passé.
        
        Returns:
            bool: True si l'événement est passé, False sinon
        """
        if not self.event_date:
            return False
        return self.event_date < timezone.now().date()
    
    def is_today(self):
        """
        Indique si l'événement a lieu aujourd'hui.
        
        Returns:
            bool: True si l'événement est aujourd'hui, False sinon
        """
        if not self.event_date:
            return False
        return self.event_date == timezone.now().date()
    
    def is_coming_soon(self, days=7):
        """
        Indique si l'événement est imminent (dans les X prochains jours).
        
        Args:
            days (int): Nombre de jours à considérer comme "imminent"
            
        Returns:
            bool: True si l'événement est imminent, False sinon
        """
        if not self.event_date:
            return False
        today = timezone.now().date()
        return today < self.event_date <= today + timezone.timedelta(days=days)
    
    def get_status_display(self):
        """
        Retourne l'état actuel de l'événement (passé, aujourd'hui, à venir).
        
        Returns:
            str: Status textuel de l'événement
        """
        if self.is_past():
            return "Passé"
        elif self.is_today():
            return "Aujourd'hui"
        else:
            return "À venir"
    
    def get_participation_rate(self):
        """
        Calcule le taux de participation si les données sont disponibles.
        
        Returns:
            float: Pourcentage de participation ou None si données insuffisantes
        """
        if not self.participants_prevus or not self.participants_reels or self.participants_prevus <= 0:
            return None
        return round((self.participants_reels / self.participants_prevus) * 100, 1)
    
    @property
    def status_color(self):
        """
        Retourne une classe CSS en fonction du statut de l'événement.
        Utile pour les templates.
        
        Returns:
            str: Classe CSS correspondant au statut
        """
        if self.is_past():
            return "text-secondary"
        elif self.is_today():
            return "text-danger"
        elif self.is_coming_soon():
            return "text-warning"
        else:
            return "text-primary"

    class Meta:
        verbose_name = "Événement"
        verbose_name_plural = "Événements"
        ordering = ['-event_date']
        indexes = [
            models.Index(fields=['event_date']),
            models.Index(fields=['type_evenement']),
            models.Index(fields=['formation']),
        ]

    def __str__(self):
        """
        Retourne une représentation lisible de l'événement.
        Exemple : "Job dating - 22/03/2025"
        
        Returns:
            str: Représentation textuelle de l'événement
        """
        type_event = self.get_type_evenement_display() if self.type_evenement else "Type inconnu"
        
        if self.type_evenement == self.AUTRE and self.description_autre:
            type_event = self.description_autre
            
        date_str = self.event_date.strftime('%d/%m/%Y') if self.event_date else "Date inconnue"
        return f"{type_event} - {date_str}"


# Optimisation des signaux pour les mises à jour des compteurs
@receiver(post_save, sender=Evenement)
def update_nombre_evenements(sender, instance, **kwargs):
    """
    Met à jour le nombre d'événements dans la formation associée après sauvegarde.
    
    Cette fonction est déclenché par un signal post_save pour maintenir
    automatiquement à jour le compteur dans le modèle Formation.
    
    Args:
        sender: Classe du modèle qui a déclenché le signal
        instance: Instance de l'objet qui a été sauvé
        kwargs: Arguments supplémentaires fournis par le signal
    """
    _update_formation_counter(instance)

@receiver(post_delete, sender=Evenement)
def update_nombre_evenements_after_delete(sender, instance, **kwargs):
    """
    Met à jour le nombre d'événements après suppression.
    
    Cette fonction est déclenchée par un signal post_delete pour maintenir
    automatiquement à jour le compteur dans le modèle Formation.
    
    Args:
        sender: Classe du modèle qui a déclenché le signal
        instance: Instance de l'objet qui a été supprimé
        kwargs: Arguments supplémentaires fournis par le signal
    """
    _update_formation_counter(instance)

def _update_formation_counter(instance):
    """
    Fonction d'aide pour mettre à jour le compteur d'événements.
    
    Cette fonction factorise le code commun aux signaux post_save et post_delete.
    Elle utilise une transaction pour garantir l'intégrité des données.
    
    Args:
        instance: Instance de l'événement qui a déclenché la mise à jour
    """
    if hasattr(instance, 'formation') and instance.formation:
        formation_id = instance.formation.id
        
        try:
            with transaction.atomic():
                # Recalcule le nombre d'événements de façon optimisée avec annotate
                count = Evenement.objects.filter(formation_id=formation_id).count()
                
                # Mise à jour avec update pour éviter les problèmes de concurrence
                Formation.objects.filter(id=formation_id).update(nombre_evenements=count)
                
                logger.debug(
                    f"Mise à jour du compteur d'événements pour la formation #{formation_id}: {count} événements"
                )
                
        except Exception as e:
            logger.error(
                f"Erreur lors de la mise à jour du compteur d'événements pour formation #{formation_id}: {str(e)}",
                exc_info=True
            )