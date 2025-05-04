from rest_framework import serializers

from ...models.centres import Centre

class CentreSerializer(serializers.ModelSerializer):
    """
    Serializer complet pour le modèle Centre.

    Ce serializer expose tous les champs utiles du modèle Centre.
    Il permet la sérialisation complète d’un centre, incluant :
    - le nom du centre
    - le code postal (avec validation)
    - les objectifs PrepaComp et Jury
    - les dates de création et modification (lecture seule)
    """

    full_address = serializers.CharField(read_only=True)

    class Meta:
        model = Centre
        fields = [
            "id",
            "nom",
            "code_postal",
            "objectif_annuel_prepa",
            "objectif_hebdomadaire_prepa",
            "objectif_annuel_jury",
            "objectif_mensuel_jury",
            "created_at",
            "updated_at",
            "full_address"
        ]
        read_only_fields = ["created_at", "updated_at", "full_address"]

    def validate_code_postal(self, value):
        """
        Validation personnalisée du code postal :
        Doit être vide ou un code à 5 chiffres.
        """
        if value and len(value) != 5:
            raise serializers.ValidationError("Le code postal doit contenir exactement 5 chiffres.")
        return value
