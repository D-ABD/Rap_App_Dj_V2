# serializers/commentaire_serializer.py
from rest_framework import serializers

from ...models.commentaires import Commentaire

class CommentaireSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Commentaire.

    Ce serializer expose toutes les informations nécessaires pour afficher et créer
    un commentaire dans l'interface utilisateur.

    Champs :
    - id : identifiant unique
    - formation : ID de la formation associée (clé étrangère)
    - utilisateur : ID de l’utilisateur ayant posté le commentaire
    - contenu : contenu textuel du commentaire
    - saturation : (optionnel) valeur numérique de saturation
    - date_creation : date/heure de création du commentaire (lecture seule)
    """

    class Meta:
        model = Commentaire
        fields = [
            'id',
            'formation',
            'utilisateur',
            'contenu',
            'saturation',
            'date_creation',
        ]
        read_only_fields = ['id', 'date_creation']
