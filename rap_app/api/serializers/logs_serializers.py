from rest_framework import serializers
from ...models.logs import LogUtilisateur
from django.contrib.auth import get_user_model

User = get_user_model()

class LogUtilisateurSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle LogUtilisateur.

    Ce serializer expose tous les champs utiles pour afficher ou filtrer
    les logs utilisateurs côté frontend.
    """

    utilisateur_nom = serializers.SerializerMethodField()

    class Meta:
        model = LogUtilisateur
        fields = [
            'id', 'utilisateur', 'utilisateur_nom', 'modele',
            'object_id', 'action', 'details', 'date'
        ]
        read_only_fields = ['id', 'date']

    def get_utilisateur_nom(self, obj):
        """Retourne le nom complet ou l'email de l'utilisateur."""
        if obj.utilisateur:
            return obj.utilisateur.get_full_name() or obj.utilisateur.email
        return None
