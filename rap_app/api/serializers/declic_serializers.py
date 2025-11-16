# rap_app/api/serializers/declic_serializers.py
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer

from ...models.centres import Centre
from ...models.declic import Declic


# -------------------------------------------------------------------
# 🔹 CENTRE
# -------------------------------------------------------------------
@extend_schema_serializer(
    examples=[{
        "id": 1,
        "nom": "Centre de Lille",
        "departement": "59",
        "code_postal": "59000",
    }]
)
class CentreLightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Centre
        fields = ["id", "nom", "departement", "code_postal"]


# -------------------------------------------------------------------
# 📊 DÉCLIC — ATELIERS UNIQUEMENT (version corrigée)
# -------------------------------------------------------------------
class DeclicSerializer(serializers.ModelSerializer):

    centre = CentreLightSerializer(read_only=True)
    centre_id = serializers.PrimaryKeyRelatedField(
        queryset=Centre.objects.all(),
        source="centre",
        write_only=True,
    )
    centre_nom = serializers.CharField(source="centre.nom", read_only=True)

    # ---- Champs calculés ----
    taux_presence_atelier = serializers.SerializerMethodField()
    objectif_annuel = serializers.SerializerMethodField()
    taux_atteinte_annuel = serializers.SerializerMethodField()
    reste_a_faire = serializers.SerializerMethodField()

    type_declic_display = serializers.CharField(
        source="get_type_declic_display",
        read_only=True
    )

    date_display = serializers.SerializerMethodField()

    class Meta:
        model = Declic
        fields = [
            "id",
            "type_declic",
            "type_declic_display",

            "date_declic",
            "date_display",

            "centre",
            "centre_id",
            "centre_nom",

            # --- Réels (UNIQUEMENT ATELIERS) ---
            "nb_inscrits_declic",
            "nb_presents_declic",
            "nb_absents_declic",

            # --- Taux ateliers ---
            "taux_presence_atelier",

            # --- Objectifs ---
            "objectif_annuel",
            "taux_atteinte_annuel",
            "reste_a_faire",

            # --- Divers ---
            "commentaire",

            # Méta
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]

    # -------------------------------------------------------
    # 🗓️ Affichage
    # -------------------------------------------------------
    def get_date_display(self, obj):
        return obj.date_declic.strftime("%d/%m/%Y")

    # -------------------------------------------------------
    # 📊 Taux ateliers
    # -------------------------------------------------------
    def get_taux_presence_atelier(self, obj):
        total = obj.nb_presents_declic + obj.nb_absents_declic
        return round(obj.nb_presents_declic / total * 100, 1) if total else 0
    

    # -------------------------------------------------------
    # 🎯 Objectifs
    # -------------------------------------------------------
    def get_objectif_annuel(self, obj):
        return obj.objectif_annuel

    def get_taux_atteinte_annuel(self, obj):
        return obj.taux_atteinte_annuel

    def get_reste_a_faire(self, obj):
        return obj.reste_a_faire

    # -------------------------------------------------------
    # CRUD
    # -------------------------------------------------------
    def create(self, validated_data):
        user = self.context.get("request").user
        instance = Declic(**validated_data)
        instance.save(user=user)
        return instance

    def update(self, instance, validated_data):
        user = self.context.get("request").user
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(user=user)
        return instance
