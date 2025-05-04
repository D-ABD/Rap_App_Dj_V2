import logging
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.urls import reverse
from .base import BaseModel

# Configuration du logger
logger = logging.getLogger("application.partenaires")

class PartenaireManager(models.Manager):
    """
    Manager personnalisé pour le modèle Partenaire avec des méthodes utilitaires.
    
    Ce manager fournit des méthodes de requête optimisées et des raccourcis
    pour les opérations courantes sur les partenaires.
    """
    
    def get_with_formations(self):
        """
        Retourne tous les partenaires avec le nombre de formations associées.
        
        Returns:
            QuerySet: Partenaires annotés avec le nombre de formations
        """
        return self.annotate(nb_formations=models.Count('formations'))
    
    def actifs(self):
        """
        Retourne uniquement les partenaires associés à au moins une formation.
        
        Returns:
            QuerySet: Partenaires actifs (avec formations)
        """
        return self.filter(formations__isnull=False).distinct()
    
    def par_secteur(self, secteur):
        """
        Filtre les partenaires par secteur d'activité.
        
        Args:
            secteur (str): Secteur d'activité à rechercher
            
        Returns:
            QuerySet: Partenaires filtrés par secteur
        """
        return self.filter(secteur_activite__icontains=secteur)
    
    def recherche(self, terme):
        """
        Recherche des partenaires par nom, secteur ou description.
        
        Args:
            terme (str): Terme de recherche
            
        Returns:
            QuerySet: Partenaires correspondant à la recherche
        """
        if not terme:
            return self.all()
            
        return self.filter(
            models.Q(nom__icontains=terme) |
            models.Q(secteur_activite__icontains=terme) |
            models.Q(description__icontains=terme) |
            models.Q(contact_nom__icontains=terme)
        )


class Partenaire(BaseModel):
    """
    Modèle représentant un partenaire.
    
    Ce modèle permet de gérer les entreprises et organisations partenaires
    qui collaborent aux formations et événements.
    
    Attributes:
        nom: Nom officiel du partenaire
        secteur_activite: Secteur d'activité principal du partenaire
        contact_nom: Nom de la personne de contact principale
        contact_poste: Poste occupé par le contact
        contact_telephone: Numéro de téléphone du contact
        contact_email: Adresse email du contact
        description: Description de la relation avec le partenaire
    """

    nom = models.CharField(
        max_length=255, 
        verbose_name="Nom du partenaire", 
        unique=True,
        help_text="Nom officiel de l'entreprise ou de l'organisation partenaire"
    )
    
    secteur_activite = models.CharField(
        max_length=255, 
        verbose_name="Secteur d'activité",
        blank=True, 
        null=True,
        help_text="Domaine d'activité principal du partenaire (ex: Santé, IT, Formation...)"
    )
    
    contact_nom = models.CharField(
        max_length=255,
        verbose_name="Nom du contact",
        blank=True, 
        null=True,
        help_text="Nom de la personne à contacter chez le partenaire"
    )
    
    contact_poste = models.CharField(
        max_length=255,
        verbose_name="Poste du contact",
        blank=True, 
        null=True,
        help_text="Fonction occupée par le contact au sein de l'organisation"
    )
    
    contact_telephone = models.CharField(
        max_length=20, 
        verbose_name="Téléphone du contact", 
        blank=True, 
        null=True,
        help_text="Numéro de téléphone direct du contact"
    )
    
    contact_email = models.EmailField(
        verbose_name="Email du contact", 
        blank=True, 
        null=True,
        help_text="Adresse email professionnelle du contact"
    )
    
    description = models.TextField(
        verbose_name="Description de la relation", 
        blank=True, 
        null=True,
        help_text="Informations sur le partenariat et l'historique de la relation"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='partenaires_crees',
        verbose_name="Créé par",
        help_text="Utilisateur ayant créé ce partenaire"
    )
    # Ajout d'un slug pour des URLs plus propres et SEO-friendly
    slug = models.SlugField(
        max_length=255, 
        unique=True, 
        blank=True, 
        null=True,
        verbose_name="Slug",
        help_text="Identifiant unique pour les URLs (généré automatiquement)"
    )

    # Managers
    objects = models.Manager()  # Manager par défaut pour compatibilité
    partenaires = PartenaireManager()  # Manager personnalisé

    def clean(self):
        """
        Validation personnalisée:
        - Vérification de la présence d'informations de contact
        - Validation du format de téléphone
        """
        super().clean()
        
        # Vérifier qu'au moins une information de contact est présente
        if all(not field for field in [
            self.contact_nom, self.contact_telephone, self.contact_email
        ]):
            logger.warning(f"Partenaire {self.nom} créé sans aucune information de contact")
        
        # Validation simple du format de téléphone
        if self.contact_telephone and not self.contact_telephone.replace('+', '').replace(' ', '').isdigit():
            raise ValidationError({
                'contact_telephone': "Le numéro de téléphone doit contenir uniquement des chiffres, des espaces ou le symbole +"
            })

    def save(self, *args, **kwargs):
        """
        Personnalisation de la sauvegarde:
        - Génération automatique du slug s'il n'existe pas
        - Normalisation des données
        - Journalisation
        """
        # Création du slug s'il n'existe pas déjà
        if not self.slug:
            self.slug = slugify(self.nom)
            
            # Vérification de l'unicité du slug
            counter = 1
            original_slug = self.slug
            while Partenaire.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        # Normalisation des données
        if self.nom:
            self.nom = self.nom.strip()
        if self.contact_email:
            self.contact_email = self.contact_email.lower().strip()
        
        # Journalisation
        is_new = not self.pk
        if is_new:
            logger.info(f"Création d'un nouveau partenaire: {self.nom}")
        else:
            logger.info(f"Mise à jour du partenaire: {self.nom} (ID: {self.pk})")
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Retourne l'URL pour accéder à une instance particulière du partenaire.
        
        Returns:
            str: URL absolue vers le détail du partenaire
        """
        return reverse('partenaire-detail', kwargs={'pk': self.pk})
    
    def get_formations_count(self):
        """
        Retourne le nombre de formations associées au partenaire.
        
        Returns:
            int: Nombre de formations liées
        """
        return self.formations.count()
    
    def has_contact_info(self):
        """
        Vérifie si le partenaire a des informations de contact.
        
        Returns:
            bool: True si au moins une information de contact est présente
        """
        return any([self.contact_nom, self.contact_telephone, self.contact_email])
    
    def __str__(self):
        """
        Représentation lisible du partenaire.
        
        Returns:
            str: Nom du partenaire
        """
        return self.nom

    class Meta:
        verbose_name = "Partenaire"
        verbose_name_plural = "Partenaires"
        ordering = ['nom']
        indexes = [
            models.Index(fields=['nom']),  # Index pour optimiser la recherche par nom
            models.Index(fields=['secteur_activite']),  # Index pour le filtrage par secteur
            models.Index(fields=['slug']),  # Index pour les recherches par slug
        ]