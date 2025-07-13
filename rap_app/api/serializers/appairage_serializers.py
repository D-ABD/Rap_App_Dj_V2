from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field
from django.utils.translation import gettext_lazy as _

from ...models.appairage import Appairage, HistoriqueAppairage, AppairageStatut
from ...models.candidat import Candidat
from ...models.partenaires import Partenaire
from ...models.formations import Formation


@extend_schema_serializer()
class HistoriqueAppairageSerializer(serializers.ModelSerializer):
    statut_display = serializers.CharField(source="get_statut_display", read_only=True)
    auteur_nom = serializers.CharField(source="auteur.get_full_name", read_only=True)
    appairage = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = HistoriqueAppairage
        fields = [
            "id", "date", "statut", "statut_display",
            "commentaire", "auteur", "auteur_nom", "appairage"
        ]
        read_only_fields = ["id", "date", "statut_display", "auteur_nom", "appairage"]


class AppairageBaseSerializer(serializers.ModelSerializer):
    candidat_nom = serializers.CharField(source="candidat.nom_complet", read_only=True)
    partenaire_nom = serializers.CharField(source="partenaire.nom", read_only=True)
    formation_nom = serializers.CharField(source="formation.nom", read_only=True)
    statut_display = serializers.CharField(source="get_statut_display", read_only=True)
    peut_modifier = serializers.SerializerMethodField()

    def get_peut_modifier(self, instance):
        user = self.context.get("request").user if self.context.get("request") else None
        if not user or not user.is_authenticated:
            return False
        return user.role in ["admin", "superadmin", "staff"]


@extend_schema_serializer()
class AppairageSerializer(AppairageBaseSerializer):
    created_by_nom = serializers.CharField(source="created_by.get_full_name", read_only=True)
    historiques = HistoriqueAppairageSerializer(many=True, read_only=True)

    class Meta:
        model = Appairage
        fields = [
            "id", "candidat", "candidat_nom",
            "partenaire", "partenaire_nom",
            "formation", "formation_nom",
            "date_appairage", "statut", "statut_display",
            "commentaire", "retour_partenaire", "date_retour",
            "created_by", "created_by_nom",
            "peut_modifier", "historiques"
        ]
        read_only_fields = [
            "id", "date_appairage", "statut_display",
            "created_by", "created_by_nom", "historiques"
        ]


@extend_schema_serializer()
class AppairageListSerializer(AppairageBaseSerializer):
    class Meta:
        model = Appairage
        fields = [
            "id", "candidat", "candidat_nom",
            "partenaire", "partenaire_nom",
            "formation", "formation_nom",
            "date_appairage", "statut", "statut_display",
            "peut_modifier"
        ]
        read_only_fields = ["id", "date_appairage", "statut_display", "peut_modifier"]


class AppairageCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer utilisé pour créer ou modifier un appairage.
    """

    class Meta:
        model = Appairage
        exclude = ["created_by"]

    def validate_statut(self, value):
        user = self.context["request"].user
        if user.role not in ["admin", "superadmin", "staff"]:
            raise serializers.ValidationError("Vous n’êtes pas autorisé à modifier le statut.")
        return value

    def validate(self, data):
        request = self.context.get("request")
        user = request.user if request else None
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentification requise.")

        candidat = data.get("candidat")
        partenaire = data.get("partenaire")
        formation = data.get("formation")

        if self.instance is None:  # Création uniquement
            if Appairage.objects.filter(candidat=candidat, partenaire=partenaire, formation=formation).exists():
                raise serializers.ValidationError("Cet appairage existe déjà.")

        return data


@extend_schema_serializer()
class AppairageMetaSerializer(serializers.Serializer):
    """
    Fournit les choix de statut pour alimenter le frontend.
    """
    statut_choices = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListSerializer(child=serializers.DictField()))
    def get_statut_choices(self, _):
        return [{"value": k, "label": v} for k, v in AppairageStatut.choices]
