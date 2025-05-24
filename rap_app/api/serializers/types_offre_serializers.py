from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample, extend_schema_field
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
    ],
)
class TypeOffreSerializer(serializers.ModelSerializer):
    """
    🎯 Sérialiseur du modèle TypeOffre.

    Expose les champs utiles pour l’interface frontend, avec validation métier,
    couleurs personnalisables, et types prédéfinis ou personnalisés.
    """

    nom_display = serializers.CharField(source='get_nom_display', read_only=True)
    formations_count = serializers.IntegerField(source='get_formations_count', read_only=True)
    badge_html = serializers.CharField(source='get_badge_html', read_only=True)

    @extend_schema_field(serializers.BooleanField())
    def get_is_personnalise(self, obj) -> bool:
        """Indique si ce type d'offre est personnalisé (champ `autre` renseigné)."""
        return obj.is_personnalise()

    is_personnalise = serializers.SerializerMethodField(help_text="True si le champ 'autre' est renseigné.")

    class Meta:
        model = TypeOffre
        fields = [
            "id", "nom", "nom_display", "autre", "couleur", "badge_html",
            "is_personnalise", "formations_count",
            "created_at", "updated_at", "created_by", "updated_by", "is_active"
        ]
        read_only_fields = [
            "id", "nom_display", "badge_html", "is_personnalise",
            "formations_count", "created_at", "updated_at", "created_by", "updated_by", "is_active"
        ]
        extra_kwargs = {
            "nom": {
                "help_text": "Nom interne du type d'offre (choix prédéfinis).",
                "error_messages": {
                    "required": _("Le champ 'nom' est requis."),
                    "blank": _("Le champ 'nom' ne peut pas être vide."),
                }
            },
            "autre": {
                "help_text": "Texte personnalisé pour les types d'offre marqués comme 'autre'.",
            },
            "couleur": {
                "help_text": "Couleur affichée pour ce type (code hexadécimal, ex: #FF5733).",
            }
        }

    def create(self, validated_data):
        """
        Création avec validation métier (via `full_clean`).
        """
        instance = TypeOffre(**validated_data)
        instance.full_clean()
        instance.save()
        return instance

    def update(self, instance, validated_data):
        """
        Mise à jour avec validation métier.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance
