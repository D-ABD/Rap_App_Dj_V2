from rest_framework import serializers

from ...models.prepacomp import PrepaCompGlobal, Semaine

class SemaineSerializer(serializers.ModelSerializer):
    """
    Sérialiseur du modèle Semaine.
    Inclut tous les champs utiles pour affichage et statistiques.
    """

    taux_adhesion = serializers.SerializerMethodField()
    taux_transformation = serializers.SerializerMethodField()
    pourcentage_objectif = serializers.SerializerMethodField()
    nom_mois = serializers.SerializerMethodField()
    ateliers_nommés = serializers.SerializerMethodField()

    class Meta:
        model = Semaine
        fields = '__all__'

    def get_taux_adhesion(self, obj):
        return round(obj.taux_adhesion(), 1)

    def get_taux_transformation(self, obj):
        return round(obj.taux_transformation(), 1)

    def get_pourcentage_objectif(self, obj):
        return round(obj.pourcentage_objectif(), 1)

    def get_nom_mois(self, obj):
        return obj.nom_mois()

    def get_ateliers_nommés(self, obj):
        return obj.ateliers_nommés


class PrepaCompGlobalSerializer(serializers.ModelSerializer):
    """
    Sérialiseur du modèle PrepaCompGlobal.
    Fournit les informations de bilan annuel d’un centre.
    """

    taux_transformation = serializers.SerializerMethodField()
    taux_objectif_annee = serializers.SerializerMethodField()

    class Meta:
        model = PrepaCompGlobal
        fields = '__all__'

    def get_taux_transformation(self, obj):
        return round(obj.taux_transformation(), 1)

    def get_taux_objectif_annee(self, obj):
        return round(obj.taux_objectif_annee(), 1)
