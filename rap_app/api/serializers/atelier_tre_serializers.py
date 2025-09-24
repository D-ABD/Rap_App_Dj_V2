# api/serializers/atelier_tre_serializers.py
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer
from ...models.atelier_tre import AtelierTRE
from ...models.candidat import Candidat
from ...models.centres import Centre

class CandidatMiniSerializer(serializers.ModelSerializer):
    nom = serializers.CharField(source="nom_complet", read_only=True)
    class Meta:
        model = Candidat
        fields = ["id", "nom"]

class CentreMiniSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="nom", read_only=True)
    class Meta:
        model = Centre
        fields = ["id", "label"]

@extend_schema_serializer()
class AtelierTRESerializer(serializers.ModelSerializer):
    # Affichages
    type_atelier_display = serializers.SerializerMethodField(read_only=True)
    nb_inscrits = serializers.SerializerMethodField(read_only=True)

    # Écriture
    centre = serializers.PrimaryKeyRelatedField(
        queryset=Centre.objects.all(), allow_null=True, required=False
    )
    candidats = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Candidat.objects.all(), required=False
    )

    # Lecture conviviale
    centre_detail = CentreMiniSerializer(source="centre", read_only=True)
    candidats_detail = CandidatMiniSerializer(source="candidats", many=True, read_only=True)

    class Meta:
        model = AtelierTRE
        fields = [
            "id",
            "type_atelier", "type_atelier_display",
            "date_atelier",
            "centre", "centre_detail",
            "candidats", "candidats_detail",
            "nb_inscrits",
            "created_by", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "type_atelier_display", "nb_inscrits",
            "created_by", "created_at", "updated_at",
        ]

    def get_type_atelier_display(self, obj) -> str:
        return obj.get_type_atelier_display()

    def get_nb_inscrits(self, obj) -> int:
        # 1) annotation de la vue si dispo
        annotated = getattr(obj, "nb_inscrits_calc", None)
        if isinstance(annotated, int):
            return annotated
        # 2) fallback: compte M2M (ok sur détail)
        try:
            return obj.candidats.count()
        except Exception:
            return 0

    def validate(self, data):
        # Laisse tel quel (ou rends date obligatoire si tu veux)
        return data

@extend_schema_serializer()
class AtelierTREMetaSerializer(serializers.Serializer):
    type_atelier_choices = serializers.SerializerMethodField()
    centre_choices = serializers.SerializerMethodField()
    candidat_choices = serializers.SerializerMethodField()

    def get_type_atelier_choices(self, _):
        return [{"value": v, "label": l} for v, l in AtelierTRE.TypeAtelier.choices]

    def get_centre_choices(self, _):
        qs = Centre.objects.order_by("nom").values_list("id", "nom")
        return [{"value": i, "label": n} for i, n in qs]

    def get_candidat_choices(self, _):
        qs = Candidat.objects.order_by("nom", "prenom").values_list("id", "nom", "prenom")
        return [{"value": i, "label": f"{n} {p}".strip()} for i, n, p in qs]
