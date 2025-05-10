import os
import magic
import logging
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.conf import settings
from django.urls import reverse
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property

from .base import BaseModel
from .formations import Formation
from .formations import HistoriqueFormation  # nécessaire pour le logging historique

logger = logging.getLogger("application.documents")

# ----------------------------------------------------
# Signaux déplacés dans un fichier signals/
# ----------------------------------------------------

class DocumentManager(models.Manager):
    """
    Manager personnalisé pour le modèle Document.
    Fournit des méthodes utilitaires pour les requêtes courantes.
    """
    
    def by_type(self, type_doc):
        """
        Retourne les documents filtrés par type.
        
        Args:
            type_doc (str): Type de document (PDF, IMAGE, etc.)
            
        Returns:
            QuerySet: Documents du type spécifié
        """
        return self.filter(type_document=type_doc)
    
    def for_formation(self, formation_id):
        """
        Retourne les documents d'une formation.
        
        Args:
            formation_id (int): ID de la formation
            
        Returns:
            QuerySet: Documents liés à la formation
        """
        return self.filter(formation_id=formation_id)
    
    def pdfs(self):
        """
        Raccourci pour récupérer tous les documents PDF.
        
        Returns:
            QuerySet: Tous les documents de type PDF
        """
        return self.filter(type_document=Document.PDF)
    
    def images(self):
        """
        Raccourci pour récupérer toutes les images.
        
        Returns:
            QuerySet: Tous les documents de type IMAGE
        """
        return self.filter(type_document=Document.IMAGE)
    
    def contrats(self):
        """
        Raccourci pour récupérer tous les contrats.
        
        Returns:
            QuerySet: Tous les documents de type CONTRAT
        """
        return self.filter(type_document=Document.CONTRAT)
    
    def with_mime_and_size(self):
        """
        Pré-filtre les documents avec MIME et taille.
        Utile pour les listes de documents.
        
        Returns:
            QuerySet: Documents avec informations complètes
        """
        return self.exclude(mime_type__isnull=True).exclude(taille_fichier__isnull=True)


# ===============================
# ✅ Validation d'extension
# ===============================
def validate_file_extension(value, type_doc=None):
    """
    ✅ Valide l'extension d'un fichier selon son type de document.

    Args:
        value (File): Le fichier à valider.
        type_doc (str): Le type de document défini dans les choix.

    Raises:
        ValidationError: Si l'extension est invalide pour ce type.
    """
    ext = os.path.splitext(value.name)[1].lower()
    valides = {
        Document.PDF: ['.pdf'],
        Document.IMAGE: ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
        Document.CONTRAT: ['.pdf', '.doc', '.docx'],
        Document.AUTRE: []
    }

    if not type_doc or type_doc == Document.AUTRE:
        return

    if ext not in valides.get(type_doc, []):
        raise ValidationError(
            f"Extension invalide pour {type_doc}. "
            f"Attendu : {', '.join(valides.get(type_doc))}"
        )

def filepath_for_document(instance, filename):
    """
    Détermine le chemin de sauvegarde pour un document.
    Organise les fichiers par type et par formation.
    
    Args:
        instance (Document): Instance du document
        filename (str): Nom du fichier original
        
    Returns:
        str: Chemin relatif pour le stockage du fichier
    """
    # Sécuriser le nom de fichier
    base_name, ext = os.path.splitext(filename)
    safe_name = "".join([c for c in base_name if c.isalnum() or c in ' ._-']).strip()
    safe_name = safe_name.replace(' ', '_')
    
    # Chemin avec type de document et ID formation
    formation_id = getattr(instance.formation, 'id', 'unknown')
    return f'formations/documents/{instance.type_document}/{formation_id}/{safe_name}{ext}'


# ===============================
# 📎 Modèle Document
# ===============================
class Document(BaseModel):
    """
    📎 Modèle représentant un document lié à une formation.

    Permet de stocker et valider des fichiers (PDF, images, contrats),
    tout en enregistrant leur ajout dans l'historique de la formation.
    
    Attributs:
        formation (Formation): Formation à laquelle ce document est rattaché
        nom_fichier (str): Nom lisible du fichier
        fichier (FileField): Fichier téléversé
        type_document (str): Type de document (PDF, IMAGE, CONTRAT, AUTRE)
        source (str, optional): Provenance du document
        taille_fichier (int, optional): Taille du fichier en kilo-octets
        mime_type (str, optional): Type MIME détecté automatiquement
        
    Propriétés:
        extension (str): Extension du fichier sans point
        icon_class (str): Classe CSS pour l'icône selon le type
        human_size (str): Taille du fichier formatée en Ko/Mo
        
    Méthodes:
        get_download_url(): URL de téléchargement du fichier
        (): URL vers la page de détail du document
        to_serializable_dict(): Représentation JSON du document
    """

    # === Constantes de type de document ===
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
    
    # Constantes pour les valeurs max
    MAX_FILENAME_LENGTH = 255
    MAX_FILE_SIZE_KB = 10 * 1024  # 10 Mo
    MAX_MIME_LENGTH = 100

    # === Champs principaux ===
    formation = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name=_("Formation associée"),
        help_text=_("Formation à laquelle ce document est rattaché")
    )

    nom_fichier = models.CharField(
        max_length=MAX_FILENAME_LENGTH,
        db_index=True,
        verbose_name=_("Nom du fichier"),
        help_text=_("Nom lisible du fichier (sera nettoyé automatiquement)")
    )

    fichier = models.FileField(
        upload_to=filepath_for_document,
        verbose_name=_("Fichier"),
        help_text=_(f"Fichier à téléverser (PDF, image, etc.). Max : {MAX_FILE_SIZE_KB//1024} Mo")
    )

    type_document = models.CharField(
        max_length=20,
        choices=TYPE_DOCUMENT_CHOICES,
        default=AUTRE,
        db_index=True,
        verbose_name=_("Type de document"),
        help_text=_("Catégorie du document selon son usage ou son format")
    )

    source = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Source"),
        help_text=_("Texte optionnel indiquant la provenance du document")
    )

    taille_fichier = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Taille (Ko)"),
        help_text=_("Taille du fichier en kilo-octets (calculée automatiquement)")
    )

    mime_type = models.CharField(
        max_length=MAX_MIME_LENGTH,
        blank=True,
        null=True,
        verbose_name=_("Type MIME"),
        help_text=_("Type MIME détecté automatiquement (ex : application/pdf)")
    )
    
    # Managers
    objects = models.Manager()
    custom = DocumentManager()

    # === Meta ===
    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['nom_fichier'], name='doc_filename_idx'),
            models.Index(fields=['formation'], name='doc_formation_idx'),
            models.Index(fields=['type_document'], name='doc_type_idx'),
            models.Index(fields=['created_at'], name='doc_created_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(nom_fichier__isnull=False) & ~models.Q(nom_fichier=''),
                name='doc_filename_not_empty'
            )
        ]

    # === Représentation ===
    def __str__(self):
        """Représentation textuelle du document."""
        max_length = 50
        nom = self.nom_fichier[:max_length]
        return f"{nom}{'...' if len(self.nom_fichier) > max_length else ''} ({self.get_type_document_display()})"
    
    def __repr__(self):
        """Représentation technique pour le débogage."""
        return f"<Document(id={self.pk}, type='{self.type_document}', formation_id={self.formation_id})>"


    def get_file_extension(self):
        """📎 Retourne l'extension du fichier (ex: '.pdf')."""
        return os.path.splitext(self.fichier.name)[1].lower() if self.fichier else ""

    def get_icon_class(self):
        """🎨 Classe FontAwesome correspondant au type de document."""
        return {
            self.PDF: "fa-file-pdf",
            self.IMAGE: "fa-file-image",
            self.CONTRAT: "fa-file-contract",
            self.AUTRE: "fa-file",
        }.get(self.type_document, "fa-file")
        
    @property
    def icon_class(self):
        """Propriété pour l'icône CSS."""
        return self.get_icon_class()

    def get_download_url(self):
        """🔗 URL de téléchargement du fichier."""
        return self.fichier.url if self.fichier else None

    @property
    def extension(self):
        """🧩 Extension du fichier sans point (ex: 'pdf')."""
        return self.get_file_extension().replace('.', '')
        
    @property
    def human_size(self):
        """
        Retourne la taille du fichier dans un format lisible.
        
        Returns:
            str: Taille du fichier formatée (ex: "512 Ko", "2.5 Mo")
        """
        if not self.taille_fichier:
            return "Inconnu"
            
        if self.taille_fichier < 1024:
            return f"{self.taille_fichier} Ko"
        else:
            return f"{self.taille_fichier/1024:.1f} Mo"
    
    @cached_property
    def is_viewable_in_browser(self):
        """
        Indique si le document peut être affiché dans le navigateur.
        
        Returns:
            bool: True si le document est un PDF ou une image
        """
        return (
            self.type_document in [self.PDF, self.IMAGE] or
            (self.mime_type and (
                self.mime_type.startswith('image/') or 
                self.mime_type == 'application/pdf'
            ))
        )

    def to_serializable_dict(self):
        """📦 Dictionnaire JSON/API du document."""
        return {
            "id": self.pk,
            "nom_fichier": self.nom_fichier,
            "type_document": self.type_document,
            "type_document_display": self.get_type_document_display(),
            "taille_fichier": self.taille_fichier,
            "taille_readable": self.human_size,
            "mime_type": self.mime_type,
            "extension": self.extension,
            "icon_class": self.get_icon_class(),
            "download_url": self.get_download_url(),
            "formation_id": self.formation_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": str(self.created_by) if self.created_by else None,
        }

    def clean(self):
        """
        🧹 Nettoyage et validation :
        - Extension valide
        - Taille max
        - Nom échappé
        - Type MIME détecté
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        super().clean()

        # Validation du nom de fichier
        if not self.nom_fichier or not self.nom_fichier.strip():
            raise ValidationError({"nom_fichier": "Le nom du fichier ne peut pas être vide."})
        
        self.nom_fichier = escape(self.nom_fichier.strip())

        # Validation du fichier
        if self.fichier:
            # Validation de l'extension selon le type
            validate_file_extension(self.fichier, self.type_document)

            # Détection du MIME type
            try:
                self.mime_type = magic.from_buffer(self.fichier.read(2048), mime=True)
                self.fichier.seek(0)
            except Exception as e:
                logger.warning(f"Impossible de détecter le MIME type pour {self.nom_fichier}: {e}")
                # Ne pas bloquer la validation si la détection échoue

            # Validation de la taille
            try:
                taille_ko = self.fichier.size // 1024
                if taille_ko > self.MAX_FILE_SIZE_KB:
                    raise ValidationError({
                        "fichier": f"Le fichier est trop volumineux (max. {self.MAX_FILE_SIZE_KB//1024} Mo)."
                    })
                self.taille_fichier = max(1, taille_ko)  # Au moins 1 Ko pour éviter les 0
            except AttributeError:
                # Si size n'est pas disponible, on ne bloque pas
                pass

    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        💾 Sauvegarde le document :
        - Validation complète (`clean`)
        - Calcul taille fichier
        - HistoriqueFormation (si nouveau)
        - Log d'ajout
        
        Args:
            *args: Arguments positionnels pour super().save()
            **kwargs: Arguments nommés pour super().save()
            skip_history (bool, optional): Si True, ne pas créer d'historique
        """
        # Extraire le paramètre skip_history
        skip_history = kwargs.pop('skip_history', False)
        
        is_new = self.pk is None
        
        # Valider les données
        self.full_clean()

        # Calculer la taille si non définie
        if not self.taille_fichier and self.fichier and hasattr(self.fichier, 'size'):
            self.taille_fichier = max(1, self.fichier.size // 1024)

        # Sauvegarder
        super().save(*args, **kwargs)

        # Créer un enregistrement dans l'historique si c'est un nouveau document
        if is_new and self.formation and not skip_history:
            try:
                HistoriqueFormation.objects.create(
                    formation=self.formation,
                    champ_modifie="document",
                    ancienne_valeur="—",
                    nouvelle_valeur=self.nom_fichier,
                    commentaire=f"Ajout du document « {self.nom_fichier} »",
                    created_by=self.created_by
                )
                logger.info(f"[Document] Document ajouté : {self.nom_fichier} (formation #{self.formation_id})")
            except Exception as e:
                logger.error(f"[Document] Erreur lors de la création de l'historique : {e}")
                # Ne pas bloquer la sauvegarde si l'historique échoue
    
    def delete(self, *args, **kwargs):
        """
        🗑️ Supprime le document avec journalisation et historique.
        
        Args:
            *args: Arguments positionnels pour super().delete()
            **kwargs: Arguments nommés pour super().delete(), y compris user
            skip_history (bool, optional): Si True, ne pas créer d'historique
        """
        # Extraire les paramètres personnalisés
        skip_history = kwargs.pop('skip_history', False)
        user = kwargs.pop('user', None) or getattr(self, 'created_by', None)
        
        # Garder une référence à la formation et au nom avant suppression
        formation = self.formation
        nom_fichier = self.nom_fichier
        
        # Supprimer le document
        result = super().delete(*args, **kwargs)
        
        # Créer un enregistrement dans l'historique
        if formation and not skip_history:
            try:
                HistoriqueFormation.objects.create(
                    formation=formation,
                    champ_modifie="document",
                    ancienne_valeur=nom_fichier,
                    nouvelle_valeur="—",
                    commentaire=f"Suppression du document « {nom_fichier} »",
                    created_by=user
                )
                logger.info(f"[Document] Document supprimé : {nom_fichier} (formation #{formation.id})")
            except Exception as e:
                logger.error(f"[Document] Erreur lors de la création de l'historique de suppression : {e}")
        
        return result
    
    @classmethod
    def get_extensions_by_type(cls, type_doc=None):
        """
        Retourne les extensions valides pour un type de document.
        
        Args:
            type_doc (str, optional): Type de document, ou None pour tous
            
        Returns:
            dict: Dictionnaire des extensions valides par type
        """
        extensions = {
            cls.PDF: ['.pdf'],
            cls.IMAGE: ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
            cls.CONTRAT: ['.pdf', '.doc', '.docx'],
            cls.AUTRE: []
        }
        
        if type_doc:
            return {type_doc: extensions.get(type_doc, [])}
        return extensions
        
    @classmethod
    def get_mime_types_by_type(cls, type_doc=None):
        """
        Retourne les types MIME valides pour un type de document.
        
        Args:
            type_doc (str, optional): Type de document, ou None pour tous
            
        Returns:
            dict: Dictionnaire des types MIME valides par type
        """
        mime_types = {
            cls.PDF: ['application/pdf'],
            cls.IMAGE: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
            cls.CONTRAT: ['application/pdf', 'application/msword', 
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            cls.AUTRE: []
        }
        
        if type_doc:
            return {type_doc: mime_types.get(type_doc, [])}
        return mime_types
    
    @classmethod
    def get_by_formation_and_type(cls, formation_id, type_doc=None):
        """
        Récupère les documents d'une formation filtrés par type.
        
        Args:
            formation_id (int): ID de la formation
            type_doc (str, optional): Type de document, ou None pour tous
            
        Returns:
            QuerySet: Documents filtrés
        """
        queryset = cls.objects.filter(formation_id=formation_id)
        
        if type_doc:
            queryset = queryset.filter(type_document=type_doc)
            
        return queryset.order_by('-created_at')