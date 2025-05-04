# serializers/statut_serializers.py
from rest_framework import serializers
from ...models.statut import Statut


class StatutSerializer(serializers.ModelSerializer):
    """
    Serializer principal pour le modèle Statut.

    Ce serializer expose tous les champs du modèle, y compris la logique
    de représentation lisible via `get_nom_display`.
    """
    nom_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Statut
        fields = [
            'id',
            'nom',
            'nom_display',
            'couleur',
            'description_autre',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_nom_display(self, obj):
        """Retourne le nom lisible du statut (ex : 'Formation en cours')."""
        return obj.get_nom_display()
