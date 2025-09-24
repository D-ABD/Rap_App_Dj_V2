# serializers.py (ou ton fichier actuel des serializers Partenaire)
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from django.utils.translation import gettext_lazy as _

from ...models.centres import Centre

from ...models.partenaires import Partenaire

class CentreLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Centre
        fields = ["id", "nom"]


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Partenaire exemple",
            value={
                "nom": "ACME Corp",
                "type": "entreprise",
                "secteur_activite": "Informatique",
                "contact_nom": "Jean Dupont",
                "contact_email": "jean.dupont@acme.fr",
                "contact_telephone": "0601020303",
                "city": "Paris",
                "zip_code": "75001",
                "website": "https://acme.fr",
                "default_centre_id": 3,
            },
            response_only=False,
        )
    ]
)
class PartenaireSerializer(serializers.ModelSerializer):
    # Displays
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    actions_display = serializers.CharField(source="get_actions_display", read_only=True)

    # Centre (lecture = objet light, écriture = *_id)
    default_centre = CentreLiteSerializer(read_only=True)
    default_centre_id = serializers.IntegerField(required=False, allow_null=True)
    default_centre_nom = serializers.CharField(source="default_centre.nom", read_only=True, allow_blank=True)

    # Infos formatées / flags
    full_address = serializers.SerializerMethodField()
    contact_info = serializers.SerializerMethodField()
    has_contact = serializers.SerializerMethodField()
    has_address = serializers.SerializerMethodField()
    has_web = serializers.SerializerMethodField()

    # Auteur
    created_by = serializers.SerializerMethodField()

    # Compteurs (annotés si possible, sinon fallback)
    prospections = serializers.SerializerMethodField()
    appairages = serializers.SerializerMethodField()
    formations = serializers.SerializerMethodField()
    candidats = serializers.SerializerMethodField()

    # Choices plus souple (le modèle autorise null/blank)
    actions = serializers.ChoiceField(
        choices=Partenaire.CHOICES_TYPE_OF_ACTION,
        required=False,
        allow_null=True,   # ⬅️ important côté front
        allow_blank=False, # laisse False si tu envoies null (et pas "")
    )

    class Meta:
        model = Partenaire
        fields = [
            "id", "nom", "type", "type_display",
            "secteur_activite",
            "street_name", "zip_code", "city", "country",
            "contact_nom", "contact_poste", "contact_telephone", "contact_email",
            "website", "social_network_url",
            "actions", "actions_display", "action_description",
            "description", "slug",
            "default_centre", "default_centre_id", "default_centre_nom",  # ⬅️ ajoutés
            "created_by",
            "created_at", "updated_at", "is_active",
            "full_address", "contact_info", "has_contact", "has_address", "has_web",
            "prospections", "appairages", "formations", "candidats",
        ]
        read_only_fields = [
            "id", "slug", "created_at", "updated_at", "is_active",
            "type_display", "actions_display",
            "full_address", "contact_info", "has_contact", "has_address", "has_web",
            "created_by",
            "default_centre", "default_centre_nom",  # lecture seule
        ]

    # ===== Helpers affichage =====
    def get_created_by(self, obj):
        if obj.created_by:
            return {
                "id": obj.created_by.id,
                "full_name": obj.created_by.get_full_name() or obj.created_by.username,
            }
        return None

    def get_full_address(self, obj): return obj.get_full_address()
    def get_contact_info(self, obj): return obj.get_contact_info()
    def get_has_contact(self, obj): return obj.has_contact_info()
    def get_has_address(self, obj): return obj.has_address
    def get_has_web(self, obj): return obj.has_web_presence

    # ===== Compteurs robustes (annotation > fallback) =====
    def get_prospections(self, obj):
        count = getattr(obj, "prospections_count", None)
        if count is None:
            rel = getattr(obj, "prospections", None)
            count = rel.count() if rel is not None else 0
        return {"count": int(count)}

    def get_appairages(self, obj):
        count = getattr(obj, "appairages_count", None)
        if count is None:
            rel = getattr(obj, "appairages", None)
            count = rel.count() if rel is not None else 0
        return {"count": int(count)}

    def get_formations(self, obj):
        ann = getattr(obj, "formations_count", None)
        if ann is not None:
            return {"count": int(ann)}
        ids = set()
        app_rel = getattr(obj, "appairages", None)
        if app_rel is not None and hasattr(app_rel, "values_list"):
            ids.update(app_rel.filter(formation__isnull=False).values_list("formation_id", flat=True))
        pros_rel = getattr(obj, "prospections", None)
        if pros_rel is not None and hasattr(pros_rel, "values_list"):
            ids.update(pros_rel.filter(formation__isnull=False).values_list("formation_id", flat=True))
        direct_rel = getattr(obj, "formation_set", None)
        if direct_rel is not None and hasattr(direct_rel, "values_list"):
            ids.update(direct_rel.values_list("id", flat=True))
        return {"count": len(ids)}

    def get_candidats(self, obj):
        count = getattr(obj, "candidats_count", None)
        if count is None:
            rel = getattr(obj, "appairages", None)
            if rel is not None and hasattr(rel, "values"):
                count = rel.values("candidat_id").distinct().count()
            else:
                count = 0
        return {"count": int(count)}

    # ===== CRUD (laisse passer default_centre_id vers le modèle) =====
    def create(self, validated_data):
        return Partenaire.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance



class PartenaireChoiceSerializer(serializers.Serializer):
    value = serializers.CharField(help_text="Valeur interne (ex: 'entreprise')")
    label = serializers.CharField(help_text="Libellé lisible (ex: 'Entreprise')")


class PartenaireChoicesResponseSerializer(serializers.Serializer):
    types = PartenaireChoiceSerializer(many=True)
    actions = PartenaireChoiceSerializer(many=True)
                                                                                                                                                                                                                                                                                                                           