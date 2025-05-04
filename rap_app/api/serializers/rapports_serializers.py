# rap_app_project/rap_app/api/serializers/rapports_serializers.py

from rest_framework import serializers
from ...models.rapports import Rapport

class RapportSerializer(serializers.ModelSerializer):
    """
    Serializer complet du modèle Rapport.

    Ce serializer permet de :
    - Lister les rapports
    - Créer ou modifier un rapport
    - Voir les détails d’un rapport
    """

    type_rapport_display = serializers.CharField(source='get_type_rapport_display', read_only=True)
    periode_display = serializers.CharField(source='get_periode_display', read_only=True)
    format_display = serializers.CharField(source='get_format_display', read_only=True)

    class Meta:
        model = Rapport
        fields = [
            'id', 'nom', 'type_rapport', 'type_rapport_display', 'periode', 'periode_display',
            'date_debut', 'date_fin', 'format', 'format_display', 'centre', 'type_offre',
            'statut', 'formation', 'donnees', 'date_generation', 'utilisateur', 'temps_generation'
        ]
        read_only_fields = ['date_generation', 'utilisateur', 'temps_generation']
