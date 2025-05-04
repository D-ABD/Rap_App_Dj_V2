from rest_framework import serializers
from ...models.formations import Formation
from ...models.statut import Statut
from ...models.types_offre import TypeOffre
from ...models.centres import Centre

class FormationSerializer(serializers.ModelSerializer):
    """
    Serializer principal pour les formations.

    Fournit toutes les données de la formation, y compris :
    - Informations générales (nom, dates, centres, type, statut)
    - Statistiques de participation
    - Méthodes calculées utiles pour l'interface
    """

    centre_nom = serializers.CharField(source="centre.nom", read_only=True)
    type_offre_nom = serializers.CharField(source="type_offre.get_nom_display", read_only=True)
    statut_nom = serializers.CharField(source="statut.get_nom_display", read_only=True)
    statut_couleur = serializers.CharField(source="get_status_color", read_only=True)

    total_places = serializers.IntegerField(source="get_total_places", read_only=True)
    total_inscrits = serializers.IntegerField(source="get_total_inscrits", read_only=True)
    taux_transformation = serializers.FloatField(source="get_taux_transformation", read_only=True)
    taux_saturation = serializers.FloatField(source="get_taux_saturation", read_only=True)
    places_disponibles = serializers.IntegerField(source="get_places_disponibles", read_only=True)

    class Meta:
        model = Formation
        fields = [
            'id', 'nom', 'centre', 'centre_nom', 'type_offre', 'type_offre_nom',
            'statut', 'statut_nom', 'statut_couleur',
            'start_date', 'end_date', 'num_kairos', 'num_offre', 'num_produit',
            'prevus_crif', 'prevus_mp', 'inscrits_crif', 'inscrits_mp',
            'assistante', 'cap', 'convocation_envoie', 'entresformation',
            'nombre_candidats', 'nombre_entretiens', 'nombre_evenements',
            'dernier_commentaire', 'utilisateur',
            'total_places', 'total_inscrits', 'taux_transformation', 'taux_saturation',
            'places_disponibles', 'created_at', 'updated_at'
        ]
