import bleach
from bleach.css_sanitizer import CSSSanitizer
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils.html import strip_tags
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field, OpenApiExample

from ...models.commentaires import Commentaire

# 🔒 Règles de nettoyage du HTML
ALLOWED_TAGS = ["p", "b", "i", "u", "em", "strong", "ul", "ol", "li", "span", "a", "br"]
ALLOWED_ATTRIBUTES = {
    "span": ["style"],
    "a": ["href", "title", "target"],
}
css_sanitizer = CSSSanitizer(
    allowed_css_properties=[
        "color",
        "background-color",
        "font-weight",
        "font-style",
        "text-decoration",
    ]
)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Commentaire avec saturation",
            value={
                "formation": 1,
                "contenu": "<p><strong>Très bon module</strong>, mais un peu trop dense.</p>",
                "saturation": 80,
            },
            request_only=True,
        ),
        OpenApiExample(
            name="Réponse de succès",
            value={
                "success": True,
                "message": "Commentaire créé avec succès.",
                "data": {
                    "id": 42,
                    "formation": 1,
                    "formation_nom": "Prépa Compétences - Janvier",
                    "num_offre": "OFR-2025-001",
                    "contenu": "<p><strong>Très bon module</strong>, mais un peu trop dense.</p>",
                    "saturation_formation": 72,
                    "taux_saturation": 78,
                    "saturation_commentaires": 74,
                    "auteur": "Jean Dupont",
                    "created_at": "2025-05-12T14:30:00Z",
                },
            },
            response_only=True,
        ),
    ]
)
class CommentaireSerializer(serializers.ModelSerializer):
    """ 🎯 Sérialiseur principal des commentaires — gère le texte enrichi HTML """

    # ✅ Champ HTML modifiable (pas read-only)
    contenu = serializers.CharField(
        allow_blank=False,
        trim_whitespace=False,
        help_text=_("Contenu HTML enrichi du commentaire (gras, italique, listes, etc.)"),
    )

    # Champs calculés
    saturation = serializers.SerializerMethodField()
    centre_nom = serializers.SerializerMethodField()
    statut_nom = serializers.SerializerMethodField()
    type_offre_nom = serializers.SerializerMethodField()
    num_offre = serializers.SerializerMethodField()
    formation_nom = serializers.SerializerMethodField()
    auteur = serializers.SerializerMethodField()
    est_archive = serializers.BooleanField(read_only=True)
    activite = serializers.CharField(read_only=True)
    statut_commentaire = serializers.CharField(read_only=True)

    # Champs de saturation complémentaires
    saturation_formation = serializers.FloatField(read_only=True)
    taux_saturation = serializers.SerializerMethodField()
    saturation_commentaires = serializers.SerializerMethodField()

    class Meta:
        model = Commentaire
        fields = [
            "id",
            "formation",
            "formation_nom",
            "num_offre",
            "centre_nom",
            "statut_nom",
            "type_offre_nom",
            "contenu",
            "est_archive",
            "activite",
            "statut_commentaire",
            "saturation",
            "saturation_formation",
            "taux_saturation",
            "saturation_commentaires",
            "auteur",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "formation": {"required": True},
        }

    # ----------------------------
    # Getters principaux
    # ----------------------------
    @extend_schema_field(str)
    def get_saturation(self, obj):
        if obj.saturation is not None:
            return obj.saturation
        if obj.saturation_formation is not None:
            return obj.saturation_formation
        formation = getattr(obj, "formation", None)
        return getattr(formation, "saturation", None) if formation else None

    @extend_schema_field(str)

    def get_centre_nom(self, obj):
        return getattr(getattr(obj.formation, "centre", None), "nom", None)

    @extend_schema_field(str)

    def get_statut_nom(self, obj):
        return getattr(getattr(obj.formation, "statut", None), "nom", None)

    @extend_schema_field(str)

    def get_type_offre_nom(self, obj):
        return getattr(getattr(obj.formation, "type_offre", None), "nom", None)

    @extend_schema_field(str)

    def get_num_offre(self, obj):
        return getattr(obj.formation, "num_offre", None)

    @extend_schema_field(str)

    def get_formation_nom(self, obj):
        return getattr(obj.formation, "nom", None)

    @extend_schema_field(str)

    def get_auteur(self, obj):
        user = getattr(obj, "created_by", None)
        return getattr(user, "get_full_name", lambda: None)() or getattr(user, "username", None)

    @extend_schema_field(str)

    def get_taux_saturation(self, obj):
        formation = getattr(obj, "formation", None)
        return getattr(formation, "taux_saturation", None) if formation else None

    @extend_schema_field(str)

    def get_saturation_commentaires(self, obj):
        formation = getattr(obj, "formation", None)
        if formation and hasattr(formation, "get_saturation_moyenne_commentaires"):
            return formation.get_saturation_moyenne_commentaires()
        return None

    # ----------------------------
    # Validations
    # ----------------------------
    def validate_contenu(self, value: str) -> str:
        """Nettoie et valide le contenu HTML avant sauvegarde"""
        cleaned = bleach.clean(
            value or "",
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            css_sanitizer=css_sanitizer,
            strip=True,
            strip_comments=True,
        )
        if not strip_tags(cleaned).strip():
            raise serializers.ValidationError(_("Le contenu ne peut pas être vide."))
        return cleaned

    def validate_saturation(self, value):
        if value is not None and not (0 <= value <= 100):
            raise serializers.ValidationError(_("La saturation doit être comprise entre 0 et 100."))
        return value

    # ----------------------------
    # CRUD
    # ----------------------------
    def create(self, validated_data):
        request = self.context.get("request")
        formation = validated_data.get("formation")

        if formation and hasattr(formation, "saturation"):
            validated_data["saturation_formation"] = formation.saturation

        commentaire = Commentaire(**validated_data)
        if request and request.user.is_authenticated:
            commentaire.created_by = request.user

        commentaire.save()
        return commentaire

    def update(self, instance, validated_data):
        """Mise à jour avec nettoyage automatique du HTML"""
        contenu = validated_data.get("contenu", instance.contenu)
        instance.contenu = self.validate_contenu(contenu)

        for attr, value in validated_data.items():
            if attr != "contenu":
                setattr(instance, attr, value)

        instance.save()
        return instance


# ----------------------------
# Métadonnées du module commentaire
# ----------------------------
class CommentaireMetaSerializer(serializers.Serializer):
    saturation_min = serializers.IntegerField(read_only=True)
    saturation_max = serializers.IntegerField(read_only=True)
    preview_default_length = serializers.IntegerField(read_only=True)
    recent_default_days = serializers.IntegerField(read_only=True)

    def to_representation(self, instance=None):
        return {
            "saturation_min": Commentaire.SATURATION_MIN,
            "saturation_max": Commentaire.SATURATION_MAX,
            "preview_default_length": Commentaire.PREVIEW_DEFAULT_LENGTH,
            "recent_default_days": Commentaire.RECENT_DEFAULT_DAYS,
        }
