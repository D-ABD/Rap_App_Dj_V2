import os
import magic
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now

from .base import BaseModel
from .formations import Formation

class Document(BaseModel):
    """
    Représente un document lié à une formation.
    Valide automatiquement les extensions, types MIME et tailles.
    """

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

    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="documents", verbose_name="Formation associée")
    nom_fichier = models.CharField(max_length=255, db_index=True, verbose_name="Nom du fichier")
    fichier = models.FileField(upload_to='formations/documents/', verbose_name="Fichier")
    source = models.TextField(blank=True, null=True, verbose_name="Source")
    type_document = models.CharField(max_length=20, choices=TYPE_DOCUMENT_CHOICES, default=AUTRE, verbose_name="Type de document")
    taille_fichier = models.PositiveIntegerField(blank=True, null=True, verbose_name="Taille (Ko)")
    mime_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Type MIME")

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['nom_fichier']),
            models.Index(fields=['formation']),
            models.Index(fields=['type_document']),
        ]

    def __str__(self):
        nom = self.nom_fichier[:50]
        return f"{nom}{'...' if len(self.nom_fichier) > 50 else ''} ({self.get_type_document_display()})"

    def clean(self):
        """Validation du fichier, MIME, taille, nom."""
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

    def save(self, *args, **kwargs):
        """Valide, calcule la taille, sauvegarde."""
        self.full_clean()
        if self.fichier and hasattr(self.fichier, 'size'):
            self.taille_fichier = max(1, self.fichier.size // 1024)
        super().save(*args, **kwargs)

    def get_file_extension(self):
        return os.path.splitext(self.fichier.name)[1].lower() if self.fichier else ""

    def get_icon_class(self):
        return {
            self.PDF: "fa-file-pdf",
            self.IMAGE: "fa-file-image",
            self.CONTRAT: "fa-file-contract",
            self.AUTRE: "fa-file",
        }.get(self.type_document, "fa-file")

    def get_download_url(self):
        return self.fichier.url if self.fichier else None

    @property
    def extension(self):
        return self.get_file_extension().replace('.', '')


def validate_file_extension(value, type_doc=None):
    """Valide l'extension d’un fichier selon son type."""
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
def log_action(instance, action: str, user=None, details: str = ""):
    """Crée une entrée de log utilisateur pour un modèle donné."""
    from ..models.logs import LogUtilisateur

    LogUtilisateur.objects.create(
        utilisateur=user or getattr(instance, 'utilisateur', None),
        modele=instance.__class__.__name__,
        object_id=instance.pk,
        action=action,
        details=details,
        content_type=ContentType.objects.get_for_model(instance),
        date=now()
    )

