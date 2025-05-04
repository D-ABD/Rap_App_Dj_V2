# serializers/vae_serializers.py

from rest_framework import serializers

from ...models.vae_jury import VAE, HistoriqueStatutVAE, SuiviJury

class SuiviJurySerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle SuiviJury.

    Fournit toutes les données nécessaires pour afficher le suivi des jurys
    par centre, mois et année.
    """
    centre_nom = serializers.CharField(source='centre.nom', read_only=True)

    class Meta:
        model = SuiviJury
        fields = '__all__'


class VAESerializer(serializers.ModelSerializer):
    """
    Serializer principal pour les VAE individuelles.

    Inclut les informations générales, le statut, et les métadonnées.
    """
    centre_nom = serializers.CharField(source='centre.nom', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = VAE
        fields = '__all__'


class HistoriqueStatutVAESerializer(serializers.ModelSerializer):
    """
    Serializer pour l'historique des statuts d'une VAE.
    """
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = HistoriqueStatutVAE
        fields = '__all__'
