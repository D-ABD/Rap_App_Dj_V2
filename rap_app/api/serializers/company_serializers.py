
# serializers/company_serializer.py
from rest_framework import serializers

from ...models.company import Company

class CompanySerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Company.

    Ce serializer permet de :
    - Créer ou modifier une entreprise
    - Afficher les détails d'une entreprise
    - Utilisé pour le listing dans les interfaces

    Champs :
    - id : identifiant unique (lecture seule)
    - name : nom de l'entreprise
    - secteur : domaine d'activité
    - adresse : adresse postale
    - telephone : numéro de téléphone
    - email : adresse email
    - description : remarques ou notes internes
    """

    class Meta:
        model = Company
        fields = [
            'id',
            'name',
            'secteur',
            'adresse',
            'telephone',
            'email',
            'description',
        ]
        read_only_fields = ['id']
