# rap_app/api/serializers/prepa_serializers.py
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field, extend_schema_serializer

from ...models.centres import Centre
from ...models.prepa import Prepa


# -------------------------------------------------------------------
# 🔹 CENTRE (résumé)
# -------------------------------------------------------------------
@extend_schema_serializer(
    examples=[{
        "id": 1, "nom": "Centre de Lille",
        "departement": "59", "code_postal": "59000"
    }]
)
class CentreLightSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour représenter un centre."""

    class Meta:
        model = Centre
        fields = ["id", "nom", "departement", "code_postal"]


# -------------------------------------------------------------------
# 📊 PREPA – SÉANCES / ATELIERS
# -------------------------------------------------------------------
@extend_schema_serializer(
    examples=[
        {
            "id": 45,
            "type_prepa": "info_collective",
            "type_prepa_display": "Information collective",
            "date_prepa": "2025-09-12",
            "centre": {
                "id": 2, "nom": "Centre de Lille",
                "departement": "59", "code_postal": "59000"
            },
            "centre_nom": "Centre de Lille",

            "nb_presents_info": 10,
            "nb_absents_info": 2,
            "nb_adhesions": 8,

            "nb_presents_prepa": 8,
            "nb_absents_prepa": 2,

            "taux_presence_info": 83.3,
            "taux_presence_atelier": None,
            "taux_presence_global": 83.3,
        }
    ]
)
class PrepaSerializer(serializers.ModelSerializer):
    """📊 Serializer principal Prépa (IC + ateliers)."""

    centre = CentreLightSerializer(read_only=True)
    centre_id = serializers.PrimaryKeyRelatedField(
        queryset=Centre.objects.all(),
        source="centre",
        write_only=True,
        help_text="Identifiant du centre concerné."
    )
    centre_nom = serializers.CharField(source="centre.nom", read_only=True)

    # ---------------- Champs calculés (backend) ----------------
    taux_prescription = serializers.SerializerMethodField()
    taux_presence_info = serializers.SerializerMethodField()
    taux_presence_atelier = serializers.SerializerMethodField()
    taux_presence_global = serializers.SerializerMethodField()
    taux_adhesion = serializers.SerializerMethodField()
    taux_presence_prepa = serializers.SerializerMethodField()
    objectif_annuel = serializers.SerializerMethodField()
    taux_atteinte_annuel = serializers.SerializerMethodField()
    reste_a_faire = serializers.SerializerMethodField()

    # Champs d'affichage
    type_prepa_display = serializers.CharField(source="get_type_prepa_display", read_only=True)
    date_display = serializers.SerializerMethodField()

    # Champs unifiés
    inscrits = serializers.SerializerMethodField()
    presents = serializers.SerializerMethodField()
    absents = serializers.SerializerMethodField()
    adhesions_ic = serializers.SerializerMethodField()

    class Meta:
        model = Prepa
        fields = [
            "id",
            "type_prepa", "type_prepa_display",
            "date_prepa", "date_display",
            "centre", "centre_id", "centre_nom",

            # Champs réels
            "nombre_places_ouvertes",
            "nombre_prescriptions",
            "nb_presents_info",
            "nb_absents_info",
            "nb_adhesions",
            "nb_inscrits_prepa",
            "nb_presents_prepa",
            "nb_absents_prepa",

            # Unifiés
            "inscrits", "presents", "absents", "adhesions_ic",

            # Taux
            "taux_prescription",
            "taux_presence_info",
            "taux_presence_atelier",
            "taux_presence_global",
            "taux_adhesion",
            "taux_presence_prepa",

            # Objectifs
            "objectif_annuel",
            "taux_atteinte_annuel",
            "reste_a_faire",

            # Métadonnées
            "commentaire",
            "created_at", "updated_at",
            "created_by", "updated_by",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]


    # ---------------- Affichage ----------------
    @extend_schema_field(serializers.CharField)
    def get_date_display(self, obj):
        return obj.date_prepa.strftime("%d/%m/%Y") if obj.date_prepa else ""


    # ----------------------- TAUX -----------------------
    @extend_schema_field(serializers.FloatField)
    def get_taux_prescription(self, obj):
        return obj.taux_prescription


    @extend_schema_field(serializers.FloatField)
    def get_taux_presence_info(self, obj):
        """Taux IC uniquement."""
        if obj.type_prepa != Prepa.TypePrepa.INFO_COLLECTIVE:
            return None
        total = (obj.nb_presents_info or 0) + (obj.nb_absents_info or 0)
        return round(obj.nb_presents_info / total * 100, 1) if total else None


    @extend_schema_field(serializers.FloatField)
    def get_taux_presence_atelier(self, obj):
        """Taux atelier uniquement."""
        if obj.type_prepa == Prepa.TypePrepa.INFO_COLLECTIVE:
            return None
        total = (obj.nb_presents_prepa or 0) + (obj.nb_absents_prepa or 0)
        return round(obj.nb_presents_prepa / total * 100, 1) if total else None


    @extend_schema_field(serializers.FloatField)
    def get_taux_presence_global(self, obj):
        """Taux présence global (IC ou atelier)."""
        return (
            self.get_taux_presence_info(obj)
            if obj.type_prepa == Prepa.TypePrepa.INFO_COLLECTIVE
            else self.get_taux_presence_atelier(obj)
        )


    @extend_schema_field(serializers.FloatField)
    def get_taux_adhesion(self, obj):
        return obj.taux_adhesion


    @extend_schema_field(serializers.FloatField)
    def get_taux_presence_prepa(self, obj):
        return obj.taux_presence_prepa


    # ---------------- OBJECTIFS ----------------
    @extend_schema_field(serializers.IntegerField)
    def get_objectif_annuel(self, obj):
        return obj.objectif_annuel or 0

    @extend_schema_field(serializers.FloatField)
    def get_taux_atteinte_annuel(self, obj):
        return obj.taux_atteinte_annuel

    @extend_schema_field(serializers.IntegerField)
    def get_reste_a_faire(self, obj):
        return obj.reste_a_faire


    # ---------------- Champs unifiés ----------------
    @extend_schema_field(serializers.IntegerField)
    def get_inscrits(self, obj):
        return (
            obj.nombre_prescriptions
            if obj.type_prepa == Prepa.TypePrepa.INFO_COLLECTIVE
            else obj.nb_inscrits_prepa
        )

    @extend_schema_field(serializers.IntegerField)
    def get_presents(self, obj):
        return (
            obj.nb_presents_info
            if obj.type_prepa == Prepa.TypePrepa.INFO_COLLECTIVE
            else obj.nb_presents_prepa
        )

    @extend_schema_field(serializers.IntegerField)
    def get_absents(self, obj):
        return (
            obj.nb_absents_info
            if obj.type_prepa == Prepa.TypePrepa.INFO_COLLECTIVE
            else obj.nb_absents_prepa
        )

    @extend_schema_field(serializers.IntegerField)
    def get_adhesions_ic(self, obj):
        return obj.nb_adhesions if obj.type_prepa == Prepa.TypePrepa.INFO_COLLECTIVE else 0


    # ---------------- CRUD ----------------
    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        instance = Prepa(**validated_data)
        instance.save(user=user)
        return instance

    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(user=user)
        return instance


    # ---------------- Validation ----------------
    def validate(self, attrs):
        """Valide la cohérence des données IC."""
        type_prepa = attrs.get("type_prepa", getattr(self.instance, "type_prepa", None))

        if type_prepa == Prepa.TypePrepa.INFO_COLLECTIVE:
            if attrs.get("nombre_places_ouvertes", 0) == 0:
                raise serializers.ValidationError(
                    "Les informations collectives doivent avoir un nombre de places ouvert > 0."
                )

        return attrs
