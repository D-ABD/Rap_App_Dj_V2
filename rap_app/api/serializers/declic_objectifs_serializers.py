from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer

from ...models.centres import Centre
from ...models.declic import ObjectifDeclic


# -------------------------------------------------------------------
# 🔹 CENTRE (résumé)
# -------------------------------------------------------------------
@extend_schema_serializer(
    examples=[
        {"id": 1, "nom": "Centre de Lille", "departement": "59", "code_postal": "59000"}
    ]
)
class CentreLightSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour représenter un centre."""

    class Meta:
        model = Centre
        fields = ["id", "nom", "departement", "code_postal"]


# -------------------------------------------------------------------
# 🎯 OBJECTIFS DÉCLIC
# -------------------------------------------------------------------
@extend_schema_serializer(
    examples=[
        {
            "id": 12,
            "centre": {
                "id": 3,
                "nom": "Centre de Roubaix",
                "departement": "59",
                "code_postal": "59100",
            },
            "annee": 2025,
            "valeur_objectif": 120,
            "commentaire": "Objectif ambitieux pour l’année 2025",
            "departement": "59",
            "taux_prescription": 80.5,
            "taux_presence": 72.3,
            "taux_adhesion": 65.0,
            "taux_atteinte": 60.4,
            "reste_a_faire": 48,
            "data_declic": {
                "places": 150,
                "prescriptions": 120,
                "presents": 72,
                "adhesions": 47,
            },
        }
    ]
)
class ObjectifDeclicSerializer(serializers.ModelSerializer):
    """
    Serializer complet pour le modèle ObjectifDeclic.
    Inclut les calculs dynamiques (taux, reste à faire, etc.)
    et le centre associé sous forme simplifiée.
    """

    centre = CentreLightSerializer(read_only=True)
    centre_id = serializers.PrimaryKeyRelatedField(
        source="centre", queryset=Centre.objects.all(), write_only=True
    )

    # 🔹 Champs calculés dynamiques
    data_declic = serializers.SerializerMethodField()
    taux_prescription = serializers.SerializerMethodField()
    taux_presence = serializers.SerializerMethodField()
    taux_adhesion = serializers.SerializerMethodField()
    taux_atteinte = serializers.SerializerMethodField()
    reste_a_faire = serializers.SerializerMethodField()

    class Meta:
        model = ObjectifDeclic
        fields = [
            "id",
            "centre",
            "centre_id",
            "departement",
            "annee",
            "valeur_objectif",
            "commentaire",

            # Champs calculés
            "data_declic",
            "taux_prescription",
            "taux_presence",
            "taux_adhesion",
            "taux_atteinte",
            "reste_a_faire",
        ]
        read_only_fields = [
            "data_declic",
            "taux_prescription",
            "taux_presence",
            "taux_adhesion",
            "taux_atteinte",
            "reste_a_faire",
        ]

    # -------------------------------------------------------------------
    # 🔹 Méthodes : lecture directe des propriétés du modèle
    # -------------------------------------------------------------------
    def get_data_declic(self, obj):
        return getattr(obj, "data_declic", {}) or {}

    def get_taux_prescription(self, obj):
        return getattr(obj, "taux_prescription", None)

    def get_taux_presence(self, obj):
        return getattr(obj, "taux_presence", None)

    def get_taux_adhesion(self, obj):
        return getattr(obj, "taux_adhesion", None)

    def get_taux_atteinte(self, obj):
        return getattr(obj, "taux_atteinte", None)

    def get_reste_a_faire(self, obj):
        return getattr(obj, "reste_a_faire", None)

    # -------------------------------------------------------------------
    # 🔹 Create / Update
    # -------------------------------------------------------------------
    def create(self, validated_data):
        user = self.context["request"].user if "request" in self.context else None
        centre = validated_data.get("centre")
        if centre and hasattr(centre, "code_postal"):
            validated_data["departement"] = (centre.code_postal or "")[:2]
        instance = ObjectifDeclic(**validated_data)
        instance.save(user=user)
        return instance

    def update(self, instance, validated_data):
        user = self.context["request"].user if "request" in self.context else None
        centre = validated_data.get("centre", getattr(instance, "centre", None))
        if centre and hasattr(centre, "code_postal"):
            validated_data["departement"] = (centre.code_postal or "")[:2]
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(user=user)
        return instance
