from rest_framework import serializers
from ...models.evenements import Evenement

class EvenementSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Evenement.
    
    Fournit tous les champs nécessaires pour la gestion complète des événements,
    avec affichage lisible des types d'événements et taux de participation calculé.
    """

    type_evenement_display = serializers.CharField(source='get_type_evenement_display', read_only=True)
    status = serializers.CharField(source='get_status_display', read_only=True)
    participation_rate = serializers.SerializerMethodField()
    formation_nom = serializers.CharField(source='formation.nom', read_only=True)

    class Meta:
        model = Evenement
        fields = [
            'id', 'formation', 'formation_nom',
            'type_evenement', 'type_evenement_display',
            'details', 'event_date', 'description_autre',
            'lieu', 'participants_prevus', 'participants_reels',
            'participation_rate', 'status',
            'created_at', 'updated_at',
        ]

    def get_participation_rate(self, obj):
        """
        Calcule le taux de participation si possible.
        """
        return obj.get_participation_rate()
