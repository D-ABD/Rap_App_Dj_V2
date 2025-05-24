from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field, OpenApiExample
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
            response_only=True,
            description="Exemple d'entrée dans l'historique des actions utilisateur"
        )
    ]
)
class LogUtilisateurSerializer(serializers.ModelSerializer):
    """
    Serializer en lecture seule pour les logs utilisateur.

    Fournit une vue enrichie des logs, incluant des champs calculés pour :
    - le modèle concerné (`get_model`)
    - l'utilisateur ayant réalisé l'action (`get_user`)
    - la date de l'action formatée (`get_date`)
    """
    
    id = serializers.IntegerField(read_only=True)
    action = serializers.CharField(read_only=True, help_text="Type d'action réalisée (création, modification, suppression).")
    model = serializers.SerializerMethodField(help_text="Nom du modèle concerné par l'action.")
    object_id = serializers.IntegerField(read_only=True, help_text="Identifiant de l'objet modifié.")
    details = serializers.CharField(read_only=True, help_text="Détails de l'action enregistrée.")
    user = serializers.SerializerMethodField(help_text="Nom de l'utilisateur ayant effectué l'action.")
    date = serializers.SerializerMethodField(help_text="Date et heure de l'action (format : AAAA-MM-JJ HH:MM).")

    class Meta:
        model = LogUtilisateur
        fields = [
            "id", "action", "model", "object_id", "details", "user", "date"
        ]
        read_only_fields = fields

    @extend_schema_field(str)
    def get_model(self, obj) -> str:
        """Retourne le nom du modèle concerné (ex: 'formation')"""
        return obj.content_type.model if obj.content_type else ""

    @extend_schema_field(str)
    def get_user(self, obj) -> str:
        """Retourne le nom d'utilisateur ayant effectué l'action"""
        return obj.created_by.username if obj.created_by else "Système"

    @extend_schema_field(str)
    def get_date(self, obj) -> str:
        """Retourne la date de l'action formatée (YYYY-MM-DD HH:MM)"""
        return obj.created_at.strftime("%Y-%m-%d %H:%M") if obj.created_at else ""
