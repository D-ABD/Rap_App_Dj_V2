from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from django.utils.translation import gettext_lazy as _

from ...models.jury import SuiviJury


# -------------------- Suivi Jury --------------------

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Exemple Suivi Jury",
            value={
                "centre_id": 1,
                "annee": 2024,
                "mois": 5,
                "objectif_jury": 10,
                "jurys_realises": 8,
            },
        )
    ]
)
class SuiviJurySerializer(serializers.ModelSerializer):
    centre_nom = serializers.CharField(source="centre.nom", read_only=True)
    mois_libelle = serializers.CharField(source="get_mois_display", read_only=True)
    periode = serializers.CharField(source="get_periode_display", read_only=True)
    ecart = serializers.IntegerField(read_only=True)
    pourcentage_atteinte = serializers.FloatField(read_only=True)
    objectif_auto = serializers.IntegerField(source="get_objectif_auto", read_only=True)

    class Meta:
        model = SuiviJury
        fields = [
            "id",
            "centre_id",
            "centre_nom",
            "annee",
            "mois",
            "mois_libelle",
            "periode",
            "objectif_jury",
            "jurys_realises",
            "pourcentage_atteinte",
            "objectif_auto",
            "ecart",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_active",
        ]
        read_only_fields = [
            "id",
            "centre_nom",
            "mois_libelle",
            "periode",
            "ecart",
            "pourcentage_atteinte",
            "objectif_auto",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_active",
        ]
        extra_kwargs = {
            "annee": {"help_text": "Année concernée par le suivi (ex: 2024)"},
            "mois": {"help_text": "Mois concerné (1 = janvier, 12 = décembre)"},
            "objectif_jury": {"help_text": "Nombre de jurys prévus pour ce mois"},
            "jurys_realises": {"help_text": "Nombre de jurys effectivement réalisés"},
        }

    def validate_mois(self, value):
        if not (1 <= value <= 12):
            raise serializers.ValidationError(
                "Le mois doit être compris entre 1 et 12."
            )
        return value
