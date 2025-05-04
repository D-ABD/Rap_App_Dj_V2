import logging
from django.db import models
from django.utils.timezone import now  # Utilise Django timezone pour éviter les problèmes UTC

# Configuration du logger pour ce module
logger = logging.getLogger(__name__)

class BaseModel(models.Model):
    """
    Modèle de base abstrait pour tous les modèles de l'application.
    
    Ce modèle fournit deux champs de date/heure automatiques :
    - created_at : Enregistre la date et l'heure de création de l'objet
    - updated_at : Mise à jour automatique à chaque modification de l'objet
    
    L'utilisation de ce modèle comme classe parente permet de :
    1. Standardiser le suivi temporel des données
    2. Éviter la duplication de code dans chaque modèle
    3. Faciliter les requêtes basées sur les dates (filtrage, tri)
    
    Exemple d'usage :
        class MonModele(BaseModel):
            nom = models.CharField(max_length=100)
            # ... autres champs ...
    """

    created_at = models.DateTimeField(
        default=now, 
        editable=False, 
        verbose_name="Date de création",
        help_text="Date et heure de création de l'enregistrement"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Dernière mise à jour",
        help_text="Date et heure de la dernière modification"
    )
    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour ajouter des logs
        et des validations supplémentaires si nécessaire.
        """
        # Déterminer s'il s'agit d'une création ou d'une mise à jour
        is_new = self.pk is None
        
        # Log l'opération
        if is_new:
            logger.debug(f"Création d'un nouvel objet {self.__class__.__name__}")
        else:
            logger.debug(f"Mise à jour de l'objet {self.__class__.__name__} #{self.pk}")
            
        # Appel à la méthode save parente
        super().save(*args, **kwargs)
        
        # Log après sauvegarde
        logger.debug(f"Objet {self.__class__.__name__} #{self.pk} sauvegardé avec succès")

    class Meta:
        abstract = True  # Empêche Django de créer une table pour ce modèle