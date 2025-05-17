# serializers/custom_user_serializers.py

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from django.utils.translation import gettext_lazy as _

from ...models.custom_user import CustomUser

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Utilisateur standard",
            value={
                "email": "jane.doe@example.com",
                "username": "janedoe",
                "first_name": "Jane",
                "last_name": "Doe",
                "phone": "0601020304",
                "role": "stagiaire",
                "bio": "Stagiaire motivée",
                "avatar": None
            },
            response_only=False,
        ),
    ]
)
class CustomUserSerializer(serializers.ModelSerializer):
    """
    🎯 Serializer principal pour les utilisateurs.
    Utilise `to_serializable_dict()` pour exposer les données enrichies.
    """

    role_display = serializers.CharField(source='get_role_display', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    avatar_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id", "email", "username", "first_name", "last_name", "phone", "bio",
            "avatar", "avatar_url", "role", "role_display",
            "is_active", "date_joined", "full_name"
        ]
        read_only_fields = ["id", "avatar_url", "role_display", "date_joined", "full_name"]
        extra_kwargs = {
            "email": {
                "required": True,
                "error_messages": {
                    "required": _("Création échouée : l'adresse email est requise."),
                    "blank": _("Création échouée : l'adresse email ne peut pas être vide."),
                },
                "help_text": "Adresse email unique utilisée pour se connecter",
            },
            "username": {
                "required": True,
                "error_messages": {
                    "required": _("Création échouée : le nom d'utilisateur est requis."),
                    "blank": _("Création échouée : le nom d'utilisateur ne peut pas être vide."),
                },
                "help_text": "Nom d'utilisateur unique pour cet utilisateur",
            },
            "role": {
                "help_text": "Rôle de l'utilisateur dans l'application",
            },
            "avatar": {
                "help_text": "Image de profil de l'utilisateur",
            },
            "bio": {
                "help_text": "Texte de présentation ou bio",
            },
            "phone": {
                "help_text": "Numéro de téléphone portable",
            },
        }

    def get_avatar_url(self, obj):
        """
        🖼️ Retourne l'URL complète de l'avatar de l'utilisateur.
        """
        return obj.avatar_url()

    def to_representation(self, instance):
        """
        🎁 Structure uniforme de sortie API
        """
        return {
            "success": True,
            "message": "Utilisateur récupéré avec succès.",
            "data": instance.to_serializable_dict(include_sensitive=True),
        }

    def create(self, validated_data):
        """
        ➕ Crée un utilisateur à partir des données validées
        """
        user = CustomUser.objects.create_user(**validated_data)
        return user  # ⛔ Pas de dictionnaire ici


    def update(self, instance, validated_data):
        """
        ✏️ Mise à jour d'un utilisateur
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return {
            "success": True,
            "message": "Utilisateur mis à jour avec succès.",
            "data": instance.to_serializable_dict(include_sensitive=True),
        }
