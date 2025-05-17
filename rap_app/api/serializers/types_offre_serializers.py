# serializers/typeoffre_serializers.py

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from django.utils.translation import gettext_lazy as _

from ...models.types_offre import TypeOffre

 

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Type d'offre standard",
            value={
                "nom": "crif",
                "autre": "",
                "couleur": "#4e73df",
            },
            response_only=False,
        ),
        OpenApiExample(
            name="Type d'offre personnalisé",
            value={
                "nom": "autre",
                "autre": "Bilan de compétences",
                "couleur": "#20c997",
            },
            response_only=False,
        )
    ]
)
class TypeOffreSerializer(serializers.ModelSerializer):
    """
    🎯 Serializer principal pour les types d'offre.

    Gère les champs enrichis, les validations personnalisées et l'affichage API-friendly.
    Utilise `to_serializable_dict()` pour structurer la sortie.
    """

    nom_display = serializers.CharField(source='get_nom_display', read_only=True)
    formations_count = serializers.IntegerField(source='get_formations_count', read_only=True)
    badge_html = serializers.CharField(source='get_badge_html', read_only=True)
    is_personnalise = serializers.SerializerMethodField()

    class Meta:
        model = TypeOffre
        fields = [
            "id", "nom", "nom_display", "autre", "couleur", "badge_html",
            "is_personnalise", "formations_count", "created_at", "updated_at", "created_by", "updated_by", "is_active"
        ]
        read_only_fields = ["id", "nom_display", "badge_html", "is_personnalise", "formations_count", "created_at", "updated_at", "created_by", "updated_by", "is_active"]
        extra_kwargs = {
            "nom": {
                "help_text": "Type d'offre parmi les choix disponibles (ex: CRIF, Alternance, Autre)",
                "error_messages": {
                    "required": _("Le champ 'nom' est requis."),
                    "blank": _("Le champ 'nom' ne peut pas être vide."),
                }
            },
            "autre": {
                "help_text": "Description personnalisée si le type est 'Autre'",
            },
            "couleur": {
                "help_text": "Code couleur hexadécimal (ex: #FF5733)",
            }
        }

    def get_is_personnalise(self, obj):
        return obj.is_personnalise()

    def to_representation(self, instance):
        """
        🎁 Structure de sortie API : success + message + data
        """
        return {
            "success": True,
            "message": "Type d'offre récupéré avec succès.",
            "data": instance.to_serializable_dict(),
        }

    def create(self, validated_data):
        instance = TypeOffre(**validated_data)
        instance.full_clean()  # ✅ Validation personnalisée (champ "autre", format couleur, etc.)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()  # ✅ Validation personnalisée
        instance.save()
        return {
            "success": True,
            "message": "Type d'offre mis à jour avec succès.",
            "data": instance.to_serializable_dict(),
        }
