from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field, OpenApiExample
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
    ],
)
class CustomUserSerializer(serializers.ModelSerializer):
    """
    🎯 Sérialiseur du modèle CustomUser.
    Affiche les infos publiques du profil + avatar + rôle + noms.
    """

    role_display = serializers.CharField(source='get_role_display', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_avatar_url(self, obj) -> str | None:
        """
        🖼️ Retourne l'URL publique de l'avatar (ou None).
        """
        return obj.avatar_url()

    avatar_url = serializers.SerializerMethodField(read_only=True, help_text="URL de l'avatar (image de profil)")

    class Meta:
        model = CustomUser
        fields = [
            "id", "email", "username", "first_name", "last_name", "phone", "bio",
            "avatar", "avatar_url", "role", "role_display",
            "is_active", "date_joined", "full_name"
        ]
        read_only_fields = [
            "id", "avatar_url", "role_display", "date_joined", "full_name"
        ]
        extra_kwargs = {
            "email": {
                "required": True,
                "error_messages": {
                    "required": _("Création échouée : l'adresse email est requise."),
                    "blank": _("Création échouée : l'adresse email ne peut pas être vide."),
                },
                "help_text": "Adresse email utilisée pour se connecter",
            },
            "username": {
                "required": True,
                "error_messages": {
                    "required": _("Création échouée : le nom d'utilisateur est requis."),
                    "blank": _("Création échouée : le nom d'utilisateur ne peut pas être vide."),
                },
                "help_text": "Nom d'utilisateur unique",
            },
            "role": {
                "help_text": "Rôle attribué à cet utilisateur",
            },
            "avatar": {
                "help_text": "Image de profil",
            },
            "bio": {
                "help_text": "Bio ou description libre",
            },
            "phone": {
                "help_text": "Numéro de téléphone mobile",
            },
        }

    def create(self, validated_data):
        """
        ➕ Crée un utilisateur avec le gestionnaire `create_user`
        """
        user = CustomUser.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        """
        ✏️ Met à jour l'utilisateur (infos personnelles)
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
