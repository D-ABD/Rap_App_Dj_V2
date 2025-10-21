# serializers.py (ou ton fichier actuel des serializers Partenaire)
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field, OpenApiExample
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
    default_centre_id = serializers.PrimaryKeyRelatedField(
        source="default_centre",            # <— lie au vrai champ du modèle
        queryset=Centre.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,                    # <— pour écriture uniquement
    )
    default_centre_nom = serializers.CharField(
        source="default_centre.nom", read_only=True, allow_blank=True
    )


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

    # Choices plus souple
    actions = serializers.ChoiceField(
        choices=Partenaire.CHOICES_TYPE_OF_ACTION,
        required=False,
        allow_null=True,
        allow_blank=False,
    )

    # ✅ Nouveau champ
    was_reused = serializers.SerializerMethodField(read_only=True)

    @extend_schema_field(str)

    def get_was_reused(self, obj):
        return getattr(obj, "_was_reused", False)

    class Meta:
        model = Partenaire
        fields = [
            # --- Identité ---
            "id", "nom", "type", "type_display", "secteur_activite", "was_reused",

            # --- Adresse ---
            "street_number", "street_name", "street_complement",
            "zip_code", "city", "country",

            # --- Coordonnées générales ---
            "telephone", "email",

            # --- Contact principal ---
            "contact_nom", "contact_poste", "contact_telephone", "contact_email",

            # --- Web ---
            "website", "social_network_url",

            # --- Détails / actions ---
            "actions", "actions_display", "action_description", "description",

            # --- Données employeur ---
            "siret", "type_employeur", "employeur_specifique",
            "code_ape", "effectif_total", "idcc", "assurance_chomage_speciale",

            # --- Maîtres d’apprentissage ---
            "maitre1_nom_naissance", "maitre1_prenom", "maitre1_date_naissance",
            "maitre1_courriel", "maitre1_emploi_occupe",
            "maitre1_diplome_titre", "maitre1_niveau_diplome",

            "maitre2_nom_naissance", "maitre2_prenom", "maitre2_date_naissance",
            "maitre2_courriel", "maitre2_emploi_occupe",
            "maitre2_diplome_titre", "maitre2_niveau_diplome",

            # --- Métadonnées ---
            "slug", "default_centre", "default_centre_id", "default_centre_nom",
            "created_by", "created_at", "updated_at", "is_active",

            # --- Champs calculés ---
            "full_address", "contact_info", "has_contact", "has_address", "has_web",

            # --- Statistiques ---
            "prospections", "appairages", "formations", "candidats",
        ]

        read_only_fields = [
            "id", "slug", "created_at", "updated_at", "is_active",
            "type_display", "actions_display",
            "full_address", "contact_info", "has_contact", "has_address", "has_web",
            "created_by", "default_centre", "default_centre_nom", "was_reused",
        ]

    # ===== Helpers affichage =====
    @extend_schema_field(str)
    def get_created_by(self, obj):
        if obj.created_by:
            return {
                "id": obj.created_by.id,
                "full_name": obj.created_by.get_full_name() or obj.created_by.username,
            }
        return None

    @extend_schema_field(str)

    def get_full_address(self, obj): return obj.get_full_address()
    @extend_schema_field(str)
    def get_contact_info(self, obj): return obj.get_contact_info()
    @extend_schema_field(str)
    def get_has_contact(self, obj): return obj.has_contact_info()
    @extend_schema_field(str)
    def get_has_address(self, obj): return obj.has_address
    @extend_schema_field(str)
    def get_has_web(self, obj): return obj.has_web_presence

    # ===== Compteurs robustes =====
    @extend_schema_field(str)
    def get_prospections(self, obj):
        count = getattr(obj, "prospections_count", None)
        if count is None:
            rel = getattr(obj, "prospections", None)
            count = rel.count() if rel is not None else 0
        return {"count": int(count)}

    @extend_schema_field(str)

    def get_appairages(self, obj):
        count = getattr(obj, "appairages_count", None)
        if count is None:
            rel = getattr(obj, "appairages", None)
            count = rel.count() if rel is not None else 0
        return {"count": int(count)}

    @extend_schema_field(str)

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

    @extend_schema_field(str)

    def get_candidats(self, obj):
        count = getattr(obj, "candidats_count", None)
        if count is None:
            rel = getattr(obj, "appairages", None)
            if rel is not None and hasattr(rel, "values"):
                count = rel.values("candidat_id").distinct().count()
            else:
                count = 0
        return {"count": int(count)}

    # ===== CRUD =====
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
                                                                                                                                                                                                                                                                                                                           