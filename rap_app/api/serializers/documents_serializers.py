from rest_framework import serializers

from ...models.documents import Document

class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer du modèle Document.
    Permet de lire, créer, modifier et supprimer des documents liés à une formation.

    Champs exposés :
    - id : Identifiant unique
    - nom_fichier : Nom visible du fichier
    - fichier : Champ de type fichier (upload)
    - type_document : Type (PDF, image, contrat...)
    - taille_fichier : Taille du fichier (Ko)
    - mime_type : Type MIME détecté
    - source : Source d’origine du document (optionnelle)
    - utilisateur : Utilisateur ayant téléchargé
    - formation : Formation liée
    - extension : Extension du fichier
    - download_url : URL publique pour télécharger le fichier
    - created_at / updated_at : Dates de création et modification
    """
    extension = serializers.ReadOnlyField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'nom_fichier', 'fichier', 'type_document', 'taille_fichier',
            'mime_type', 'source', 'utilisateur', 'formation',
            'created_at', 'updated_at', 'extension', 'download_url'
        ]
        read_only_fields = ['taille_fichier', 'mime_type', 'created_at', 'updated_at', 'extension', 'download_url']

    def get_download_url(self, obj):
        return obj.get_download_url()
