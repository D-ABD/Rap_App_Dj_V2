from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from django.utils.translation import gettext_lazy as _

from ...models.formations import Formation
from ...models.prospection import Prospection, ProspectionChoices, HistoriqueProspection


# ---------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------
class BaseProspectionSerializer(serializers.ModelSerializer):
    # Identités liées
    partenaire_nom = serializers.CharField(source="partenaire.nom", read_only=True)

    # Utiliser Prospection.centre (pas formation.centre)
    centre = serializers.PrimaryKeyRelatedField(read_only=True)
    centre_nom = serializers.CharField(source="centre.nom", read_only=True)

    formation_nom = serializers.CharField(source="formation.nom", read_only=True)
    num_offre = serializers.CharField(source="formation.num_offre", read_only=True)

    # Commentaires (annotés dans queryset)
    last_comment = serializers.CharField(read_only=True)
    last_comment_at = serializers.DateTimeField(read_only=True)
    last_comment_id = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    # Displays
    statut_display = serializers.CharField(source="get_statut_display", read_only=True)
    objectif_display = serializers.CharField(source="get_objectif_display", read_only=True)
    motif_display = serializers.CharField(source="get_motif_display", read_only=True)
    type_prospection_display = serializers.CharField(source="get_type_prospection_display", read_only=True)

    # Moyen de contact (champ direct du modèle)
    moyen_contact = serializers.ChoiceField(
        choices=ProspectionChoices.MOYEN_CONTACT_CHOICES,
        required=False,
        allow_null=True,
    )
    moyen_contact_display = serializers.CharField(source="get_moyen_contact_display", read_only=True)

    # Calculés
    is_active = serializers.BooleanField(read_only=True)
    relance_necessaire = serializers.BooleanField(read_only=True)

    # Méta
    created_by = serializers.StringRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    owner = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),
        required=False,
        allow_null=True,
    )
    owner_username = serializers.StringRelatedField(source="owner", read_only=True)

    # Partenaire (confort)
    partenaire_ville = serializers.SerializerMethodField()
    partenaire_tel = serializers.SerializerMethodField()
    partenaire_email = serializers.SerializerMethodField()

    # Formation (confort)
    formation_date_debut = serializers.DateField(source="formation.start_date", read_only=True, allow_null=True)
    formation_date_fin = serializers.DateField(source="formation.end_date", read_only=True, allow_null=True)
    type_offre_display = serializers.SerializerMethodField()
    formation_statut_display = serializers.SerializerMethodField()
    places_disponibles = serializers.SerializerMethodField()

    def get_partenaire_ville(self, obj):
        p = getattr(obj, "partenaire", None)
        return getattr(p, "city", None) if p else None

    def get_partenaire_tel(self, obj):
        p = getattr(obj, "partenaire", None)
        return getattr(p, "contact_telephone", None) if p else None

    def get_partenaire_email(self, obj):
        p = getattr(obj, "partenaire", None)
        return getattr(p, "contact_email", None) if p else None

    def get_type_offre_display(self, obj):
        f = getattr(obj, "formation", None)
        to = getattr(f, "type_offre", None) if f else None
        return getattr(to, "nom", None) if to else None

    def get_formation_statut_display(self, obj):
        f = getattr(obj, "formation", None)
        st = getattr(f, "statut", None) if f else None
        return getattr(st, "nom", None) if st else None

    def get_places_disponibles(self, obj):
        f = getattr(obj, "formation", None)
        return int(f.places_disponibles) if f and f.places_disponibles is not None else None


# ---------------------------------------------------------------------
# R/W
# ---------------------------------------------------------------------
@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Exemple de prospection",
            value={
                "partenaire": 1,
                "formation": 2,
                "date_prospection": "2025-05-10T14:00:00",
                "type_prospection": "premier_contact",
                "motif": "partenariat",
                "statut": "en_cours",
                "objectif": "presentation_offre",
                "commentaire": "Entretien en cours",
                "relance_prevue": "2025-05-20",
                "moyen_contact": "email",
            },
            response_only=False,
        )
    ]
)
class ProspectionSerializer(BaseProspectionSerializer):
    formation = serializers.PrimaryKeyRelatedField(
        queryset=Formation.objects.all(),
        required=False,
        allow_null=True,
    )
    relance_prevue = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = Prospection
        fields = [
            "id",
            "partenaire",
            "partenaire_nom",
            "formation",
            "formation_nom",
            "centre",            # PK du centre (RO)
            "centre_nom",        # libellé centre (RO)
            "num_offre",
            "date_prospection",
            "type_prospection",
            "type_prospection_display",
            "motif",
            "motif_display",
            "statut",
            "statut_display",
            "objectif",
            "objectif_display",
            "commentaire",
            "relance_prevue",
            "moyen_contact",
            "moyen_contact_display",
            "is_active",
            "relance_necessaire",
            "created_by",
            "created_at",
            "updated_at",
            "owner",
            "owner_username",
            "last_comment",
            "last_comment_at",
            "last_comment_id",
            "comments_count",
            "partenaire_ville",
            "partenaire_tel",
            "partenaire_email",
            "formation_date_debut",
            "formation_date_fin",
            "type_offre_display",
            "formation_statut_display",
            "places_disponibles",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "partenaire_nom",
            "formation_nom",
            "centre",
            "centre_nom",
            "num_offre",
            "statut_display",
            "objectif_display",
            "type_prospection_display",
            "motif_display",
            "is_active",
            "relance_necessaire",
            "owner_username",
            "partenaire_ville",
            "partenaire_tel",
            "partenaire_email",
            "formation_date_debut",
            "formation_date_fin",
            "type_offre_display",
            "formation_statut_display",
            "places_disponibles",
            "moyen_contact_display",
        ]

    def validate(self, data):
        # ✅ On ne force plus "acceptée ⇒ contrat" (règle retirée du modèle)
        if (
            data.get("statut") in [ProspectionChoices.STATUT_REFUSEE, ProspectionChoices.STATUT_ANNULEE]
            and not data.get("commentaire")
        ):
            raise serializers.ValidationError(
                {"commentaire": _("Un commentaire est requis pour les statuts refusé ou annulé.")}
            )
        return data

    def validate_date_prospection(self, value):
        if value > timezone.now():
            raise serializers.ValidationError(_("La date de prospection ne peut pas être dans le futur."))
        return value

    def validate_relance_prevue(self, value):
        if value and value < timezone.now().date():
            raise serializers.ValidationError(_("La date de relance prévue doit être dans le futur."))
        return value


# ---------------------------------------------------------------------
# List / Detail
# ---------------------------------------------------------------------
class ProspectionListSerializer(BaseProspectionSerializer):
    class Meta:
        model = Prospection
        fields = [
            "id",
            "partenaire",
            "partenaire_nom",
            "formation",
            "formation_nom",
            "centre",
            "centre_nom",
            "num_offre",
            "date_prospection",
            "type_prospection",
            "type_prospection_display",
            "motif",
            "motif_display",
            "statut",
            "statut_display",
            "objectif",
            "objectif_display",
            "commentaire",
            "relance_prevue",
            "moyen_contact",
            "moyen_contact_display",
            "is_active",
            "relance_necessaire",
            "created_by",
            "created_at",
            "updated_at",
            "owner",
            "owner_username",
            "last_comment",
            "last_comment_at",
            "last_comment_id",
            "comments_count",
            "partenaire_ville",
            "partenaire_tel",
            "partenaire_email",
            "formation_date_debut",
            "formation_date_fin",
            "type_offre_display",
            "formation_statut_display",
            "places_disponibles",
        ]


class ProspectionDetailSerializer(ProspectionSerializer):
    class Meta(ProspectionSerializer.Meta):
        read_only_fields = ProspectionSerializer.Meta.fields


# ---------------------------------------------------------------------
# Historiques
# ---------------------------------------------------------------------
class HistoriqueProspectionSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(source="prospection.owner", read_only=True)
    owner_username = serializers.StringRelatedField(source="prospection.owner", read_only=True)

    type_prospection_display = serializers.CharField(source="get_type_prospection_display", read_only=True)
    ancien_statut_display = serializers.CharField(source="get_ancien_statut_display", read_only=True)
    nouveau_statut_display = serializers.CharField(source="get_nouveau_statut_display", read_only=True)
    moyen_contact_display = serializers.CharField(source="get_moyen_contact_display", read_only=True)

    champ_modifie = serializers.CharField(read_only=True)
    ancienne_valeur = serializers.CharField(read_only=True, allow_null=True)
    nouvelle_valeur = serializers.CharField(read_only=True, allow_null=True)

    jours_avant_relance = serializers.IntegerField(read_only=True)
    relance_urgente = serializers.BooleanField(read_only=True)
    est_recent = serializers.BooleanField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)

    type_prospection = serializers.ChoiceField(choices=ProspectionChoices.TYPE_PROSPECTION_CHOICES)
    ancien_statut = serializers.ChoiceField(choices=ProspectionChoices.PROSPECTION_STATUS_CHOICES)
    nouveau_statut = serializers.ChoiceField(choices=ProspectionChoices.PROSPECTION_STATUS_CHOICES)
    moyen_contact = serializers.ChoiceField(choices=ProspectionChoices.MOYEN_CONTACT_CHOICES, required=False)

    class Meta:
        model = HistoriqueProspection
        fields = [
            "id",
            "prospection",
            "date_modification",
            "champ_modifie",
            "ancienne_valeur",
            "nouvelle_valeur",
            "ancien_statut",
            "ancien_statut_display",
            "nouveau_statut",
            "nouveau_statut_display",
            "type_prospection",
            "type_prospection_display",
            "commentaire",
            "resultat",
            "prochain_contact",
            "moyen_contact",
            "moyen_contact_display",
            "jours_avant_relance",
            "relance_urgente",
            "est_recent",
            "created_by",
            "owner",
            "owner_username",
        ]
        read_only_fields = [
            "id",
            "date_modification",
            "champ_modifie",
            "ancienne_valeur",
            "nouvelle_valeur",
            "ancien_statut_display",
            "nouveau_statut_display",
            "type_prospection_display",
            "moyen_contact_display",
            "jours_avant_relance",
            "relance_urgente",
            "est_recent",
            "created_by",
            "owner",
            "owner_username",
        ]


# ---------------------------------------------------------------------
# Payloads utilitaires / endpoints custom
# ---------------------------------------------------------------------
class ChangerStatutSerializer(serializers.Serializer):
    statut = serializers.ChoiceField(choices=ProspectionChoices.PROSPECTION_STATUS_CHOICES)
    commentaire = serializers.CharField(required=False, allow_blank=True)
    moyen_contact = serializers.ChoiceField(choices=ProspectionChoices.MOYEN_CONTACT_CHOICES, required=False)
    # Nouveau nom privilégié :
    relance_prevue = serializers.DateField(required=False)
    # Compat legacy :
    prochain_contact = serializers.DateField(required=False)

    def validate(self, data):
        if data.get("prochain_contact") and not data.get("relance_prevue"):
            data["relance_prevue"] = data["prochain_contact"]
        return data


class EnumChoiceSerializer(serializers.Serializer):
    value = serializers.CharField(help_text="Valeur brute utilisée en base")
    label = serializers.CharField(help_text="Libellé affiché (traduction)")


class ProspectionChoiceListSerializer(serializers.Serializer):
    statut = EnumChoiceSerializer(many=True)
    objectif = EnumChoiceSerializer(many=True)
    type_prospection = EnumChoiceSerializer(many=True)
    motif = EnumChoiceSerializer(many=True)
    moyen_contact = EnumChoiceSerializer(many=True)
    owners = serializers.ListField()
    partenaires = EnumChoiceSerializer(many=True)
