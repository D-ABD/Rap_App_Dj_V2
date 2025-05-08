import os
import magic
import logging
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.conf import settings
from django.urls import reverse

from .base import BaseModel
from .formations import Formation
from .formations import HistoriqueFormation  # nécessaire pour le logging historique

logger = logging.getLogger("application.documents")

# ===============================
# ✅ Validation d’extension
# ===============================
def validate_file_extension(value, type_doc=None):
    """
    ✅ Valide l'extension d’un fichier selon son type de document.

    Args:
        value (File): Le fichier à valider.
        type_doc (str): Le type de document défini dans les choix.

    Raises:
        ValidationError: Si l'extension est invalide pour ce type.
    """
    ext = os.path.splitext(value.name)[1].lower()
    valides = {
        'pdf': ['.pdf'],
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
        'contrat': ['.pdf', '.doc', '.docx'],
        'autre': []
    }

    if not type_doc or type_doc == Document.AUTRE:
        return

    if ext not in valides.get(type_doc, []):
        raise ValidationError(
            f"Extension invalide pour {type_doc}. "
            f"Attendu : {', '.join(valides.get(type_doc))}"
        )


# ===============================
# 📎 Modèle Document
# ===============================
class Document(BaseModel):
    """
    📎 Modèle représentant un document lié à une formation.

    Permet de stocker et valider des fichiers (PDF, images, contrats),
    tout en enregistrant leur ajout dans l'historique de la formation.
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

    # === Champs principaux ===
    formation = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Formation associée",
        help_text="Formation à laquelle ce document est rattaché"
    )

    nom_fichier = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="Nom du fichier",
        help_text="Nom lisible du fichier (sera nettoyé automatiquement)"
    )

    fichier = models.FileField(
        upload_to='formations/documents/',
        verbose_name="Fichier",
        help_text="Fichier à téléverser (PDF, image, etc.). Max : 10 Mo"
    )

    type_document = models.CharField(
        max_length=20,
        choices=TYPE_DOCUMENT_CHOICES,
        default=AUTRE,
        verbose_name="Type de document",
        help_text="Catégorie du document selon son usage ou son format"
    )

    source = models.TextField(
        blank=True,
        null=True,
        verbose_name="Source",
        help_text="Texte optionnel indiquant la provenance du document"
    )

    taille_fichier = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Taille (Ko)",
        help_text="Taille du fichier en kilo-octets (calculée automatiquement)"
    )

    mime_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Type MIME",
        help_text="Type MIME détecté automatiquement (ex : application/pdf)"
    )

    # === Meta ===
    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['nom_fichier']),
            models.Index(fields=['formation']),
            models.Index(fields=['type_document']),
        ]

    # === Représentation ===
    def __str__(self):
        nom = self.nom_fichier[:50]
        return f"{nom}{'...' if len(self.nom_fichier) > 50 else ''} ({self.get_type_document_display()})"

    def get_absolute_url(self):
        """🔗 URL vers la page de détail du document."""
        return reverse("document-detail", kwargs={"pk": self.pk})

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

    def get_download_url(self):
        """🔗 URL de téléchargement du fichier."""
        return self.fichier.url if self.fichier else None

    @property
    def extension(self):
        """🧩 Extension du fichier sans point (ex: 'pdf')."""
        return self.get_file_extension().replace('.', '')

    def to_serializable_dict(self):
        """📦 Dictionnaire JSON/API du document."""
        return {
            "id": self.pk,
            "nom_fichier": self.nom_fichier,
            "type_document": self.get_type_document_display(),
            "taille": self.taille_fichier,
            "mime": self.mime_type,
            "url": self.get_download_url(),
            "formation_id": self.formation_id,
        }

    def clean(self):
        """
        🧹 Nettoyage et validation :
        - Extension valide
        - Taille max
        - Nom échappé
        - Type MIME détecté
        """
        super().clean()

        if self.fichier:
            validate_file_extension(self.fichier, self.type_document)

            try:
                self.mime_type = magic.from_buffer(self.fichier.read(2048), mime=True)
                self.fichier.seek(0)
            except Exception:
                pass

            taille_ko = self.fichier.size // 1024
            if taille_ko > 10 * 1024:
                raise ValidationError("Le fichier est trop volumineux (max. 10 Mo).")

        if self.nom_fichier:
            self.nom_fichier = escape(self.nom_fichier)

    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        💾 Sauvegarde le document :
        - Validation complète (`clean`)
        - Calcul taille fichier
        - HistoriqueFormation (si nouveau)
        - Log d’ajout
        """
        is_new = self.pk is None
        self.full_clean()

        if self.fichier and hasattr(self.fichier, 'size'):
            self.taille_fichier = max(1, self.fichier.size // 1024)

        super().save(*args, **kwargs)

        if is_new and self.formation:
            HistoriqueFormation.objects.create(
                formation=self.formation,
                champ_modifie="document",
                ancienne_valeur="—",
                nouvelle_valeur=self.nom_fichier,
                commentaire=f"Ajout du document « {self.nom_fichier} »",
                created_by=self.created_by
            )
            logger.info(f"[Document] Document ajouté : {self.nom_fichier} (formation #{self.formation_id})")
