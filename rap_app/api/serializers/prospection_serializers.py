from rest_framework import serializers
from ...models.prospection import Prospection, HistoriqueProspection
from ...models.company import Company
from ...models.formations import Formation

class HistoriqueProspectionSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'historique des prospections.
    Utilisé pour afficher l'évolution des statuts dans l'UI.
    """
    class Meta:
        model = HistoriqueProspection
        fields = '__all__'
        read_only_fields = ['date_modification']


class ProspectionSerializer(serializers.ModelSerializer):
    """
    Sérialiseur principal pour le modèle Prospection.
    Inclut les détails de l'entreprise, formation, et historique.
    """
    historiques = HistoriqueProspectionSerializer(many=True, read_only=True)

    class Meta:
        model = Prospection
        fields = '__all__'
        read_only_fields = ['date_prospection']
