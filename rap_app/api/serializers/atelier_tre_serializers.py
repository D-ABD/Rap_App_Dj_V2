
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field
from django.utils.translation import gettext_lazy as _

from ...models.atelier_tre import AtelierTRE, ParticipationAtelierTRE


# --- Participation Serializers ---

@extend_schema_serializer()
class ParticipationAtelierTRESerializer(serializers.ModelSerializer):
    """
    🎟️ Détail d’une participation à un atelier TRE (candidat, présence, commentaire).
    """
    candidat_nom = serializers.CharField(source="candidat.nom_complet", read_only=True)

    class Meta:
        model = ParticipationAtelierTRE
        fields = ["id", "candidat", "candidat_nom", "present", "commentaire_individuel"]
        read_only_fields = ["id", "candidat_nom"]


class ParticipationAtelierTRECreateUpdateSerializer(serializers.ModelSerializer):
    """
    ✍️ Création ou mise à jour d'une participation à un atelier TRE.
    """
    class Meta:
        model = ParticipationAtelierTRE
        fields = ["candidat", "ateliertre", "present", "commentaire_individuel"]


# --- Atelier Serializers ---

class _AtelierTREPermissionsMixin:
    def get_peut_modifier(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        return user and user.is_authenticated and user.role in ["admin", "superadmin", "staff"]

    def get_peut_supprimer(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        return user and user.is_authenticated and user.role in ["admin", "superadmin"]


@extend_schema_serializer()
class AtelierTRESerializer(serializers.ModelSerializer, _AtelierTREPermissionsMixin):
    """
    🎓 Affichage complet d’un atelier TRE avec ses participations et statistiques.
    """
    type_atelier_display = serializers.CharField(source="get_type_atelier_display", read_only=True)
    nb_participants_prevus = serializers.IntegerField(read_only=True)
    nb_participants_presents = serializers.IntegerField(read_only=True)
    participations = ParticipationAtelierTRESerializer(source="participationateliertre_set", many=True, read_only=True)
    peut_modifier = serializers.SerializerMethodField()
    peut_supprimer = serializers.SerializerMethodField()

    class Meta:
        model = AtelierTRE
        fields = [
            "id", "type_atelier", "type_atelier_display",
            "date", "remarque", "nb_participants_prevus",
            "nb_participants_presents", "participations",
            "created_by", "peut_modifier", "peut_supprimer"
        ]
        read_only_fields = [
            "id", "created_by", "nb_participants_prevus",
            "nb_participants_presents", "type_atelier_display"
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["date"] = instance.date.strftime("%Y-%m-%d") if instance.date else None
        return rep


@extend_schema_serializer()
class AtelierTREListSerializer(serializers.ModelSerializer, _AtelierTREPermissionsMixin):
    """
    📋 Vue simplifiée d’un atelier TRE pour la liste (avec stats et droits).
    """
    type_atelier_display = serializers.CharField(source="get_type_atelier_display", read_only=True)
    nb_participants_prevus = serializers.IntegerField(read_only=True)
    nb_participants_presents = serializers.IntegerField(read_only=True)
    peut_modifier = serializers.SerializerMethodField()
    peut_supprimer = serializers.SerializerMethodField()

    class Meta:
        model = AtelierTRE
        fields = [
            "id", "type_atelier", "type_atelier_display",
            "date", "nb_participants_prevus", "nb_participants_presents",
            "peut_modifier", "peut_supprimer"
        ]
        read_only_fields = [
            "id", "type_atelier_display", "nb_participants_prevus", "nb_participants_presents"
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["date"] = instance.date.strftime("%Y-%m-%d") if instance.date else None
        return rep


class AtelierTRECreateUpdateSerializer(serializers.ModelSerializer):
    """
    🛠️ Utilisé pour créer ou modifier un atelier TRE.
    """
    class Meta:
        model = AtelierTRE
        exclude = ["created_by"]

    def validate(self, data):
        user = self.context["request"].user
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentification requise.")
        return data


@extend_schema_serializer()
class AtelierTREMetaSerializer(serializers.Serializer):
    """
    ℹ️ Fournit les choix disponibles pour le formulaire (type_atelier).
    """
    type_atelier_choices = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListSerializer(child=serializers.DictField()))
    def get_type_atelier_choices(self, _):
        return [{"value": k, "label": v} for k, v in AtelierTRE.TypeAtelier.choices]
