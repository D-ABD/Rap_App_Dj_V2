from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from ...models.documents import Document, validate_file_extension
from ...models.formations import Formation


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Exemple de document PDF",
            value={
                "id": 42,
                "nom_fichier": "programme.pdf",
                "type_document": "pdf",
                "type_document_display": "PDF",
                "taille_fichier": 512,
                "taille_readable": "512 Ko",
                "mime_type": "application/pdf",
                "extension": "pdf",
                "icon_class": "fa-file-pdf",
                "download_url": "/media/formations/documents/pdf/12/programme.pdf",
                "formation": 12,
                "created_at": "2025-05-11T10:00:00",
                "created_by": "admin"
            },
            response_only=True,
        )
    ]
)
class DocumentSerializer(serializers.ModelSerializer):
    """
    📄 Serializer principal pour les documents liés à une formation.
    """

    type_document_display = serializers.CharField(source="get_type_document_display", read_only=True)
    taille_readable = serializers.CharField(read_only=True)
    extension = serializers.CharField(read_only=True)
    icon_class = serializers.CharField(read_only=True)
    download_url = serializers.CharField(read_only=True)
    created_by = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Document
        fields = [
            "id", "nom_fichier", "fichier", "type_document",
            "type_document_display", "taille_fichier", "taille_readable",
            "mime_type", "extension", "icon_class", "download_url",
            "formation", "created_at", "created_by"
        ]
        read_only_fields = [
            "id", "type_document_display", "taille_readable", "extension", "icon_class",
            "download_url", "mime_type", "taille_fichier", "created_at", "created_by"
        ]
        extra_kwargs = {
            "nom_fichier": {"help_text": "Nom lisible du document (sera nettoyé automatiquement)"},
            "fichier": {"help_text": "Fichier téléversé (PDF, image, doc...)"},
            "type_document": {"help_text": "Catégorie du document (PDF, Image, Contrat...)"},
            "formation": {"help_text": "ID de la formation liée à ce document"},
        }

    def validate(self, data):
        """
        Valide la cohérence type / extension et taille.
        """
        fichier = data.get("fichier")
        type_doc = data.get("type_document")

        if fichier and type_doc:
            try:
                validate_file_extension(fichier, type_doc)
            except ValidationError as e:
                raise serializers.ValidationError({"fichier": str(e)})

        return data

    def to_representation(self, instance):
        return {
            "success": True,
            "message": "Document récupéré avec succès.",
            "data": instance.to_serializable_dict()
        }
