# rap_app/api/serializers/commentaires_serializers.py

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from django.utils.translation import gettext_lazy as _
from django.utils.html import strip_tags

from ...models.commentaires import Commentaire


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Commentaire avec saturation",
            value={
                "formation": 1,
                "contenu": "Très bon module, mais un peu trop dense.",
                "saturation": 80
            },
            request_only=True
        ),
        OpenApiExample(
            name="Réponse de succès",
            value={
                "success": True,
                "message": "Commentaire créé avec succès.",
                "data": {
                    "id": 42,
                    "formation_id": 1,
                    "formation_nom": "Prépa Compétences - Janvier",
                    "contenu": "Très bon module, mais un peu trop dense.",
                    "saturation": 80,
                    "auteur": "Jean Dupont",
                    "date": "12/05/2025",
                    "heure": "14:30",
                    "is_recent": True,
                    "is_edited": False,
                    "created_at": "2025-05-12T14:30:00Z",
                    "updated_at": "2025-05-12T14:30:00Z"
                }
            },
            response_only=True
        )
    ]
)
class CommentaireSerializer(serializers.ModelSerializer):
    """
    💬 Serializer principal pour les commentaires de formation.
    """
    class Meta:
        model = Commentaire
        fields = ["id", "formation", "contenu", "saturation", "created_at", "updated_at"]
        extra_kwargs = {
            "formation": {"required": True},
            "contenu": {
                "required": True,
                "error_messages": {
                    "blank": _("Création échouée : le champ 'contenu' est requis.")
                }
            },
            "saturation": {
                "required": False
            },
        }

    def validate_contenu(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError(_("Le contenu ne peut pas être vide."))
        return value

    def validate_saturation(self, value):
        if value is not None and not (0 <= value <= 100):
            raise serializers.ValidationError(_("La saturation doit être comprise entre 0 et 100."))
        return value

    def to_representation(self, instance):
        view = self.context.get("view", None)
        if view and hasattr(view, "action") and view.action in ["retrieve", "create", "update"]:
            return {
                "success": True,
                "message": f"Commentaire {'récupéré' if view.action == 'retrieve' else 'traité'} avec succès.",
                "data": instance.to_serializable_dict(include_full_content=True)
            }
        return instance.to_serializable_dict()

    def create(self, validated_data):
        request = self.context.get("request")
        commentaire = Commentaire(**validated_data)
        if request and request.user.is_authenticated:
            commentaire.created_by = request.user
        commentaire.save()
        return commentaire

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
