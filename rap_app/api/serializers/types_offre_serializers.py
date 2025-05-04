from rest_framework import serializers

from ...models.types_offre import TypeOffre

class TypeOffreSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle TypeOffre.

    Ce serializer expose tous les champs utiles pour l'affichage et l'édition des types d'offres,
    y compris les champs personnalisés comme la couleur, le badge HTML, et l'indication de type personnalisé.
    """

    is_personnalise = serializers.BooleanField(read_only=True)
    badge_html = serializers.CharField(source="get_badge_html", read_only=True)
    formations_count = serializers.IntegerField(source="get_formations_count", read_only=True)

    class Meta:
        model = TypeOffre
        fields = [
            "id",
            "nom",
            "autre",
            "couleur",
            "is_personnalise",
            "badge_html",
            "formations_count",
            "created_at",
            "updated_at",
        ]
