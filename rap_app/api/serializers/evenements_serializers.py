from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from django.utils.translation import gettext_lazy as _

from ...models.evenements import Evenement

from drf_spectacular.utils import extend_schema_field
@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Exemple d'événement",
            value={
                "id": 1,
                "formation_id": 12,
                "formation_nom": "Prépa CléA",
                "type_evenement": "forum",
                "type_evenement_display": "Forum",
                "description_autre": None,
                "details": "Stand avec brochures",
                "event_date": "2025-06-15",
                "event_date_formatted": "15/06/2025",
                "lieu": "Centre Paris",
                "participants_prevus": 20,
                "participants_reels": 18,
                "taux_participation": 90.0,
                "status": "soon",
                "status_label": "Bientôt",
                "status_color": "text-warning",
                "created_at": "2025-05-11T10:00:00",
                "updated_at": "2025-05-12T15:00:00"
            },
            response_only=True
        )
    ]
)
class EvenementSerializer(serializers.ModelSerializer):
    """
    📅 Serializer principal pour les événements liés à une formation.
    Inclut toutes les données utiles pour affichage et analyse dans l'interface.
    """

    formation_nom = serializers.CharField(source="formation.nom", read_only=True)
    type_evenement_display = serializers.CharField(source="get_type_evenement_display", read_only=True)
    event_date_formatted = serializers.SerializerMethodField()
    taux_participation = serializers.FloatField(read_only=True)
    status = serializers.CharField(source="get_temporal_status", read_only=True)
    status_label = serializers.CharField(read_only=True)
    status_color = serializers.CharField(read_only=True)

    class Meta:
        model = Evenement
        fields = [
            "id", "formation_id", "formation_nom",
            "type_evenement", "type_evenement_display", "description_autre",
            "details", "event_date", "event_date_formatted", "lieu",
            "participants_prevus", "participants_reels", "taux_participation",
            "status", "status_label", "status_color",
            "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "formation_nom", "type_evenement_display",
            "event_date_formatted", "taux_participation",
            "status", "status_label", "status_color",
            "created_at", "updated_at"
        ]
    @extend_schema_field(serializers.IntegerField())
    def get_event_date_formatted(self, obj):
        return obj.event_date.strftime('%d/%m/%Y') if obj.event_date else None

    def to_representation(self, instance):
        return {
            "success": True,
            "message": "Événement récupéré avec succès.",
            "data": instance.to_serializable_dict()
        }
    def validate(self, data):
        """
        Validation personnalisée :
        - Si type = 'autre', alors description_autre obligatoire
        """
        type_evenement = data.get("type_evenement")
        description_autre = data.get("description_autre")

        if type_evenement == Evenement.TypeEvenement.AUTRE and not description_autre:
            raise serializers.ValidationError({
                "description_autre": _("Une description est requise pour le type 'autre'.")
            })

        return data
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer

@extend_schema_serializer(
    examples=[
        {
            "value": "job_dating",
            "label": "Job dating"
        }
    ]
)
class EvenementChoiceSerializer(serializers.Serializer):
    value = serializers.CharField(
        help_text="Clé technique du type d'événement (ex: 'forum', 'job_dating')"
    )
    label = serializers.CharField(
        help_text="Nom lisible affiché pour le type d'événement"
    )
