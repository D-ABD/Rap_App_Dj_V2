from rest_framework import serializers
from ...models.partenaires import Partenaire

class PartenaireSerializer(serializers.ModelSerializer):
    """
    Serializer du modèle Partenaire.
    Fournit toutes les informations nécessaires pour l'affichage et l'édition
    d'un partenaire dans l'interface utilisateur.
    """
    nb_formations = serializers.IntegerField(
        source='formations.count', read_only=True,
        help_text="Nombre de formations associées à ce partenaire."
    )

    class Meta:
        model = Partenaire
        fields = [
            'id', 'nom', 'secteur_activite', 'contact_nom', 'contact_poste',
            'contact_telephone', 'contact_email', 'description',
            'slug', 'created_at', 'updated_at', 'nb_formations'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']
