from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from django.utils.translation import gettext_lazy as _
from ...models.logs import LogUtilisateur

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Exemple de log",
            value={
                "id": 1,
                "action": "modification",
                "model": "formation",
                "object_id": 42,
                "details": "Mise à jour du nom",
                "user": "admin",
                "date": "2024-01-01 12:00"
            },
            response_only=True
        )
    ]
)
class LogUtilisateurSerializer(serializers.ModelSerializer):
    """
    📄 Serializer en lecture seule pour les logs utilisateur.
    Utilise `to_dict()` pour exposer les champs enrichis.
    """
    id = serializers.IntegerField(read_only=True)
    action = serializers.CharField(read_only=True, help_text="Type d'action réalisée.")
    model = serializers.SerializerMethodField(help_text="Nom du modèle concerné.")
    object_id = serializers.IntegerField(read_only=True, help_text="Identifiant de l'objet concerné.")
    details = serializers.CharField(read_only=True, help_text="Détail de l'action enregistrée.")
    user = serializers.SerializerMethodField(help_text="Utilisateur ayant réalisé l'action.")
    date = serializers.SerializerMethodField(help_text="Date et heure de l'action.")

    class Meta:
        model = LogUtilisateur
        fields = [
            "id", "action", "model", "object_id", "details", "user", "date"
        ]
        read_only_fields = fields

    def get_model(self, obj):
        return obj.content_type.model if obj.content_type else None

    def get_user(self, obj):
        return obj.created_by.username if obj.created_by else "Système"

    def get_date(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M")
