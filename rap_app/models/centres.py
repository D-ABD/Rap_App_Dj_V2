import logging
from django.db import models
from django.core.validators import RegexValidator
from django.urls import reverse
from .base import BaseModel

# Configuration du logger pour ce module
logger = logging.getLogger(__name__)

class Centre(BaseModel):
    """
    Modèle représentant un centre de formation.

    Hérite de `BaseModel` qui ajoute les champs :
    - `created_at` : Date et heure de création de l'enregistrement.
    - `updated_at` : Date et heure de la dernière modification.

    Champs spécifiques :
    - `nom` : Nom du centre de formation (obligatoire et unique).
    - `code_postal` : Code postal du centre (optionnel).
      * Doit contenir exactement 5 chiffres (validation par regex).
    
    Méthodes :
    - `__str__` : Retourne le nom du centre.
    - `get_absolute_url` : Retourne l'URL du détail du centre.
    - `full_address` : Retourne l'adresse complète (utile pour affichage futur).

    Options du modèle :
    - `verbose_name` : Nom affiché au singulier dans l'interface d'administration.
    - `verbose_name_plural` : Nom affiché au pluriel dans l'interface d'administration.
    - `ordering` : Trie les centres par nom par défaut.
    - `indexes` : Ajoute des index sur `nom` et `code_postal` pour optimiser les recherches.
    """

    nom = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Nom du centre",
        help_text="Nom complet du centre de formation (doit être unique)"
    )

    code_postal = models.CharField(
        max_length=5,
        null=True,
        blank=True,
        verbose_name="Code postal",
        help_text="Code postal à 5 chiffres du centre",
        validators=[
            RegexValidator(
                regex=r'^\d{5}$',
                message="Le code postal doit contenir exactement 5 chiffres"
            )
        ]
    )

    """Champs pour le model prepa et vae_jury"""
    objectif_annuel_prepa = models.PositiveIntegerField(null=True, blank=True)
    objectif_hebdomadaire_prepa = models.PositiveIntegerField(default=0, blank=True, null=True)
    objectif_annuel_jury = models.PositiveIntegerField(default=0)
    objectif_mensuel_jury = models.PositiveIntegerField(default=0)
    def __str__(self):
        """Retourne le nom du centre pour une meilleure lisibilité."""
        return self.nom

    def get_absolute_url(self):
        """
        Retourne l'URL du détail du centre.
        Utile pour les vues génériques et les redirections après une création/modification.
        """
        return reverse('centre-detail', kwargs={'pk': self.pk})

    def full_address(self):
        """
        Retourne une version complète de l'adresse (utile si d'autres champs d'adresse sont ajoutés).
        """
        address = self.nom
        if self.code_postal:
            address += f" ({self.code_postal})"
        return address
        
    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour inclure des validations supplémentaires
        et journaliser les opérations sur les centres.
        """
        is_new = self.pk is None
        
        # Création
        if is_new:
            logger.info(f"Création d'un nouveau centre: {self.nom}")
        # Modification
        else:
            old_centre = Centre.objects.get(pk=self.pk)
            modifications = []
            
            if old_centre.nom != self.nom:
                modifications.append(f"nom: '{old_centre.nom}' → '{self.nom}'")
            
            if old_centre.code_postal != self.code_postal:
                modifications.append(f"code_postal: '{old_centre.code_postal}' → '{self.code_postal}'")
                
            if modifications:
                logger.info(f"Modification du centre #{self.pk}: {', '.join(modifications)}")
        
            # Calculer automatiquement l'objectif hebdomadaire si non défini
            if self.objectif_annuel_prepa and not self.objectif_hebdomadaire_prepa:
                self.objectif_hebdomadaire_prepa = self.objectif_annuel_prepa // 52

        # Appel à la méthode parente
        super().save(*args, **kwargs)
        
        # Log après sauvegarde
        if is_new:
            logger.info(f"Centre #{self.pk} '{self.nom}' créé avec succès")

    class Meta:
        verbose_name = "Centre"
        verbose_name_plural = "Centres"
        ordering = ['nom']
        indexes = [
            models.Index(fields=['nom']),
            models.Index(fields=['code_postal']),
        ]