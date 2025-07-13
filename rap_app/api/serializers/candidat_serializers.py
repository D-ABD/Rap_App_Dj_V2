from rest_framework import serializers, exceptions
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field, OpenApiExample

from ...models.candidat import (
    Candidat,
    HistoriquePlacement,
    ResultatPlacementChoices,
    NIVEAU_CHOICES,
)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Exemple de candidat",
            value={
                "id": 1,
                "nom": "Dupont",
                "prenom": "Alice",
                "email": "alice.dupont@example.com",
                "telephone": "0612345678",
                "ville": "Paris",
                "statut": "accompagnement",
                "formation": 3,
                "date_naissance": "2000-01-01",
                "admissible": True,
            },
        )
    ]
)
class CandidatSerializer(serializers.ModelSerializer):
    age = serializers.IntegerField(read_only=True)
    nom_complet = serializers.CharField(read_only=True)
    nb_appairages = serializers.IntegerField(read_only=True)
    role_utilisateur = serializers.CharField(read_only=True)
    ateliers_resume = serializers.CharField(read_only=True)
    peut_modifier = serializers.SerializerMethodField()

    class Meta:
        model = Candidat
        fields = "__all__"
        read_only_fields = [
            "age", "nom_complet", "nb_appairages",
            "role_utilisateur", "ateliers_resume", "peut_modifier"
        ]

    def get_peut_modifier(self, instance):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None
        if not user:
            return False
        return user.role in ["admin", "superadmin", "staff"] or instance.compte_utilisateur == user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None

        role = getattr(user, "role", None)
        is_staff_or_admin = role in ["staff", "admin", "superadmin"]

        reserved_fields = [
            "notes", "resultat_placement", "responsable_placement",
            "date_placement", "entreprise_placement", "contrat_signe",
            "entreprise_validee", "courrier_rentree", "vu_par",
            "admissible", "entretien_done", "test_is_ok",
            "communication", "experience", "csp", "nb_appairages"
        ]

        if not is_staff_or_admin:
            for field in reserved_fields:
                data.pop(field, None)

        return data


@extend_schema_serializer()
class CandidatListSerializer(serializers.ModelSerializer):
    nom_complet = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    nb_appairages = serializers.IntegerField(read_only=True)
    role_utilisateur = serializers.CharField(read_only=True)
    ateliers_resume = serializers.CharField(read_only=True)
    peut_modifier = serializers.SerializerMethodField()

    class Meta:
        model = Candidat
        fields = [
            "id", "nom", "prenom", "nom_complet", "email", "telephone",
            "ville", "code_postal", "age", "statut", "formation", "evenement", "notes",
            "origine_sourcing", "date_inscription", "date_naissance", "rqth", "type_contrat",
            "disponibilite", "permis_b", "communication", "experience", "csp",
            "entretien_done", "test_is_ok", "admissible", "compte_utilisateur", "role_utilisateur",
            "responsable_placement", "date_placement", "entreprise_placement", "resultat_placement",
            "entreprise_validee", "contrat_signe", "courrier_rentree", "date_rentree", "vu_par",
            "nb_appairages", "ateliers_resume", "peut_modifier"
        ]

    def get_peut_modifier(self, instance):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None
        if not user:
            return False
        return user.role in ["admin", "superadmin", "staff"] or instance.compte_utilisateur == user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None

        role = getattr(user, "role", None)
        is_staff_or_admin = role in ["staff", "admin", "superadmin"]

        reserved_fields = [
            "notes", "resultat_placement", "responsable_placement",
            "date_placement", "entreprise_placement", "contrat_signe",
            "entreprise_validee", "courrier_rentree", "vu_par",
            "admissible", "entretien_done", "test_is_ok",
            "communication", "experience", "csp", "nb_appairages"
        ]

        if not is_staff_or_admin:
            for field in reserved_fields:
                data.pop(field, None)

        return data


class CandidatCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidat
        exclude = [
            "date_inscription", "nb_appairages", "nom_complet",
            "age", "role_utilisateur", "ateliers_resume"
        ]

    def validate(self, data):
        request = self.context.get("request")
        user = request.user if request else None

        if not request or not user or not user.is_authenticated:
            raise exceptions.PermissionDenied("Authentification requise.")

        restricted_fields = [
            "admissible", "notes", "resultat_placement", "responsable_placement",
            "date_placement", "entreprise_placement", "contrat_signe",
            "entreprise_validee", "courrier_rentree", "vu_par"
        ]

        if user.role not in ["admin", "superadmin"]:
            for field in restricted_fields:
                if field in data:
                    raise serializers.ValidationError({
                        field: "Ce champ ne peut être modifié que par un administrateur."
                    })

        return data

    def validate_role_utilisateur(self, value):
        user = self.context["request"].user
        if not user.is_authenticated:
            raise serializers.ValidationError("Authentification requise.")
        if user.role in ["admin", "superadmin"]:
            return value
        if user.role == "staff":
            if value in ["admin", "superadmin"]:
                raise serializers.ValidationError("Le staff ne peut pas attribuer le rôle admin ou superadmin.")
            return value
        raise serializers.ValidationError("Vous n’avez pas l’autorisation de modifier ce rôle.")


@extend_schema_serializer()
class CandidatMetaSerializer(serializers.Serializer):
    statut_choices = serializers.SerializerMethodField()
    type_contrat_choices = serializers.SerializerMethodField()
    disponibilite_choices = serializers.SerializerMethodField()
    resultat_placement_choices = serializers.SerializerMethodField()
    contrat_signe_choices = serializers.SerializerMethodField()
    niveau_choices = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListSerializer(child=serializers.DictField()))
    def get_statut_choices(self, _):
        return [{"value": k, "label": v} for k, v in Candidat.StatutCandidat.choices]

    @extend_schema_field(serializers.ListSerializer(child=serializers.DictField()))
    def get_type_contrat_choices(self, _):
        return [{"value": k, "label": v} for k, v in Candidat.TypeContrat.choices]

    @extend_schema_field(serializers.ListSerializer(child=serializers.DictField()))
    def get_disponibilite_choices(self, _):
        return [{"value": k, "label": v} for k, v in Candidat.Disponibilite.choices]

    @extend_schema_field(serializers.ListSerializer(child=serializers.DictField()))
    def get_resultat_placement_choices(self, _):
        return [{"value": k, "label": v} for k, v in ResultatPlacementChoices.choices]

    @extend_schema_field(serializers.ListSerializer(child=serializers.DictField()))
    def get_contrat_signe_choices(self, _):
        return [{"value": k, "label": v} for k, v in Candidat.ContratSigne.choices]

    @extend_schema_field(serializers.ListSerializer(child=serializers.DictField()))
    def get_niveau_choices(self, _):
        return [{"value": val, "label": f"{val} ★"} for val, _ in NIVEAU_CHOICES]


@extend_schema_serializer()
class HistoriquePlacementSerializer(serializers.ModelSerializer):
    candidat_nom = serializers.CharField(source="candidat.nom_complet", read_only=True)
    entreprise_nom = serializers.CharField(source="entreprise.nom", read_only=True)
    responsable_nom = serializers.CharField(source="responsable.get_full_name", read_only=True)

    class Meta:
        model = HistoriquePlacement
        fields = [
            "id", "candidat", "candidat_nom",
            "entreprise", "entreprise_nom",
            "responsable", "responsable_nom",
            "resultat", "date_placement", "commentaire", "created_at"
        ]
        read_only_fields = ["id", "created_at", "candidat_nom", "entreprise_nom", "responsable_nom"]


class HistoriquePlacementCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoriquePlacement
        fields = [
            "candidat", "entreprise", "responsable",
            "resultat", "date_placement", "commentaire"
        ]


@extend_schema_serializer()
class HistoriquePlacementMetaSerializer(serializers.Serializer):
    resultat_choices = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListSerializer(child=serializers.DictField()))
    def get_resultat_choices(self, _):
        return [{"value": k, "label": v} for k, v in ResultatPlacementChoices.choices]
