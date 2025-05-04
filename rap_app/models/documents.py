import logging
import os
import magic  # Nécessite l'installation de python-magic
from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.html import escape
from .base import BaseModel
from .formations import Formation, User

# Configuration du logger
logger = logging.getLogger(__name__)

class Document(BaseModel):
    """
    Modèle représentant un document associé à une formation.
    
    Ce modèle permet de stocker et gérer différents types de documents
    (PDF, images, contrats...) avec validation de type et gestion automatique
    des fichiers physiques.
    
    Fonctionnalités:
    - Validation automatique du type de fichier par extension et contenu MIME
    - Calcul automatique de la taille du fichier
    - Suppression automatique des anciens fichiers lors d'un remplacement
    - Suppression automatique du fichier physique lors de la suppression de l'objet
    """

    # Définition des types de documents acceptés
    PDF = 'pdf'
    IMAGE = 'image'
    CONTRAT = 'contrat'
    AUTRE = 'autre'

    TYPE_DOCUMENT_CHOICES = [
        (PDF, 'PDF'),
        (IMAGE, 'Image'),
        (CONTRAT, 'Contrat signé'),
        (AUTRE, 'Autre'),
    ]

    # Champs du modèle
    formation = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Formation associée"
    )
    
    nom_fichier = models.CharField(
        max_length=255,
        verbose_name="Nom du fichier",
        db_index=True,
        help_text="Nom du fichier tel qu'il apparaîtra dans l'interface"
    )
    
    fichier = models.FileField(
        upload_to='formations/documents/',
        verbose_name="Fichier",
        help_text="Fichier à télécharger (types acceptés selon la catégorie)"
    )
    
    source = models.TextField(
        null=True, blank=True,
        verbose_name="Source du document",
        help_text="Source ou origine du document (optionnel)"
    )
    
    type_document = models.CharField(
        max_length=20,
        choices=TYPE_DOCUMENT_CHOICES,
        default=AUTRE,
        verbose_name="Type de document",
        help_text="Catégorie du document déterminant les types de fichiers acceptés"
    )
    
    taille_fichier = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Taille du fichier (Ko)",
        help_text="Taille du fichier en Ko (calculée automatiquement)"
    )
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Téléchargé par",
        help_text="Utilisateur ayant téléchargé le document"
    )
    
    # Métadonnées détectées
    mime_type = models.CharField(
        max_length=100,
        blank=True, null=True,
        verbose_name="Type MIME",
        help_text="Type MIME détecté automatiquement"
    )

    def __str__(self):
        """
        Représentation lisible du document dans l'admin ou les logs.
        Affiche un nom tronqué s'il est trop long, suivi du type de document.
        """
        nom_tronque = self.nom_fichier[:50] + ('...' if len(self.nom_fichier) > 50 else '')
        return f"{nom_tronque} ({self.get_type_document_display()})"

    def clean(self):
        """
        Validation personnalisée à l'enregistrement:
        - Vérifie la correspondance entre type et extension
        - Valide le contenu MIME si possible
        - Nettoie le nom du fichier pour éviter les injections
        """
        super().clean()
        
        # Validation du fichier si présent
        if self.fichier and self.type_document:
            # Validation de l'extension
            validate_file_extension(self.fichier, self.type_document)
            
            # Validation du contenu MIME
            try:
                mime_type = magic.from_buffer(self.fichier.read(2048), mime=True)
                self.fichier.seek(0)  # Réinitialiser le pointeur
                self.mime_type = mime_type
                
                # Vérifier la cohérence du type MIME avec le type de document
                valid_mime_types = {
                    'pdf': ['application/pdf'],
                    'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
                    'contrat': ['application/pdf', 'application/msword', 
                               'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
                    'autre': []  # Pas de restriction pour "Autre"
                }
                
                if (self.type_document != Document.AUTRE and 
                    valid_mime_types.get(self.type_document) and 
                    mime_type not in valid_mime_types.get(self.type_document)):
                    logger.warning(
                        f"Type MIME incohérent: '{mime_type}' pour un document de type '{self.type_document}'"
                    )
            except Exception as e:
                logger.warning(f"Impossible de valider le type MIME: {str(e)}")
                
        # Nettoyage du nom du fichier
        if self.nom_fichier:
            # Échapper les caractères spéciaux pour éviter les injections
            self.nom_fichier = escape(self.nom_fichier)
        
        # Taille maximale
        if self.fichier and hasattr(self.fichier, 'size'):
            taille_ko = self.fichier.size // 1024
        if taille_ko > 10 * 1024:  # 10 Mo
            raise ValidationError("Le fichier est trop volumineux (max. 10 Mo).")

    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save() pour:
        - Exécuter les validations personnalisées
        - Calculer automatiquement la taille du fichier
        - Journaliser les opérations
        """
        is_new = self.pk is None
        
        # Exécuter la validation
        self.full_clean()
        
        # Calcul de la taille du fichier
        if self.fichier and hasattr(self.fichier, 'size'):
            self.taille_fichier = max(1, self.fichier.size // 1024)  # Au moins 1 Ko
        
        # Journalisation
        if is_new:
            logger.info(
                f"Création d'un nouveau document '{self.nom_fichier}' "
                f"({self.get_type_document_display()}) "
                f"pour la formation #{self.formation_id if self.formation else 'N/A'}"
            )
        else:
            logger.info(f"Mise à jour du document #{self.pk}: '{self.nom_fichier}'")
        
        super().save(*args, **kwargs)
        
    def get_file_extension(self):
        """Retourne l'extension du fichier."""
        if self.fichier:
            _, ext = os.path.splitext(self.fichier.name)
            return ext.lower()
        return ""
    
    def get_icon_class(self):
        """
        Retourne une classe d'icône selon le type de document,
        utile pour l'affichage dans l'interface.
        """
        icons = {
            self.PDF: "fa-file-pdf",
            self.IMAGE: "fa-file-image",
            self.CONTRAT: "fa-file-contract",
            self.AUTRE: "fa-file",
        }
        return icons.get(self.type_document, "fa-file")
    
    def get_download_url(self):
        """Retourne l'URL de téléchargement du document."""
        if self.fichier:
            return self.fichier.url
        return None
    
    @property
    def extension(self):
        return self.get_file_extension().replace('.', '')
    

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['nom_fichier']),
            models.Index(fields=['formation']),
            models.Index(fields=['type_document']),
        ]


# -------------------- VALIDATION --------------------
def validate_file_extension(value, type_doc=None):
    """
    Fonction utilitaire pour valider l'extension du fichier en fonction du type_document.
    
    Arguments:
        value: Le fichier à valider
        type_doc: Le type de document attendu (pdf, image, contrat, autre)
    
    Lève une ValidationError si l'extension ne correspond pas au type attendu.
    """
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = {
        'pdf': ['.pdf'],
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
        'contrat': ['.pdf', '.doc', '.docx'],
        'autre': []  # Autorise tout pour "Autre"
    }
    
    # Si aucun type n'est fourni ou si c'est "autre", on accepte le fichier
    if not type_doc or type_doc == Document.AUTRE:
        return
    
    # Vérifie si l'extension correspond au type fourni
    if ext not in valid_extensions.get(type_doc, []):
        error_msg = (f"Le fichier {value.name} ne correspond pas au type "
                    f"{dict(Document.TYPE_DOCUMENT_CHOICES).get(type_doc, type_doc)}. "
                    f"Extensions acceptées: {', '.join(valid_extensions.get(type_doc, []))}")
        logger.warning(f"Validation d'extension échouée: {error_msg}")
        raise ValidationError(error_msg)
    
    logger.debug(f"Extension validée pour le fichier {value.name}: {ext} (type: {type_doc})")


# -------------------- SIGNALS --------------------
@receiver(pre_save, sender=Document)
def supprimer_fichier_ancien(sender, instance, **kwargs):
    """
    Avant la sauvegarde: supprime l'ancien fichier si un nouveau est fourni.
    Permet d'éviter l'accumulation inutile de fichiers obsolètes.
    """
    if instance.pk:
        try:
            ancien_document = Document.objects.get(pk=instance.pk)
            if ancien_document.fichier and ancien_document.fichier != instance.fichier:
                ancien_fichier_path = os.path.join(settings.MEDIA_ROOT, ancien_document.fichier.name)
                if os.path.exists(ancien_fichier_path):
                    os.remove(ancien_fichier_path)
                    logger.info(f"Ancien fichier supprimé: {ancien_document.fichier.name}")
        except Document.DoesNotExist:
            logger.warning(f"Impossible de trouver l'ancien document #{instance.pk} pour supprimer le fichier")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'ancien fichier: {str(e)}")
    


@receiver(post_delete, sender=Document)
def supprimer_fichier_apres_suppression(sender, instance, **kwargs):
    """
    Après suppression d'un Document: supprime le fichier du disque dur (media).
    """
    if instance.fichier:
        fichier_path = os.path.join(settings.MEDIA_ROOT, instance.fichier.name)
        try:
            if os.path.exists(fichier_path):
                os.remove(fichier_path)
                logger.info(f"Fichier supprimé après suppression du document: {instance.fichier.name}")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du fichier {fichier_path}: {str(e)}")