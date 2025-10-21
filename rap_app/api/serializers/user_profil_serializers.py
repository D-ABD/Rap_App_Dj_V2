from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field, OpenApiExample
from django.utils.translation import gettext_lazy as _
from django.apps import apps
from drf_spectacular.types import OpenApiTypes

from ...models.formations import Formation
from ..serializers.formations_serializers import FormationLightSerializer
from ...models.custom_user import CustomUser
from django_filters import rest_framework as filters


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Utilisateur standard",
            value={
                "email": "jane.doe@example.com",
                "username": "janedoe",
                "first_name": "Jane",
                "last_name": "Doe",
                "phone": "0601020304",
                "role": "stagiaire",
                "bio": "Stagiaire motivée",
                "avatar": None,
            },
            response_only=False,
        ),
    ],
)
class CustomUserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    # ✅ formation (liaison simple)
    formation = serializers.PrimaryKeyRelatedField(
        queryset=Formation.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
        help_text="ID de la formation à associer (pour candidat/stagiaire)",
    )
    formation_info = serializers.SerializerMethodField(read_only=True)

    # ✅ centres en écriture / lecture
    centres = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        write_only=True,
        help_text="IDs des centres autorisés (admin/superadmin uniquement)",
    )
    centres_info = serializers.SerializerMethodField(read_only=True)

    # ✅ Ajout du champ calculé « centre »
    centre = serializers.SerializerMethodField(read_only=True)

    # ✅ flags supplémentaires
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    is_admin = serializers.SerializerMethodField()
    is_staff_read = serializers.SerializerMethodField()

    # ------------------------------------------------------
    # Champs calculés
    # ------------------------------------------------------
    @extend_schema_field(OpenApiTypes.STR)
    def get_is_admin(self, obj):
        return bool(getattr(obj, "is_admin", None) and callable(obj.is_admin) and obj.is_admin())

    @extend_schema_field(OpenApiTypes.STR)
    def get_is_staff_read(self, obj):
        return obj.role == "staff_read"

    @extend_schema_field(OpenApiTypes.STR)
    def get_formation_info(self, obj):
        try:
            if hasattr(obj, "candidat_associe") and obj.candidat_associe.formation:
                return FormationLightSerializer(obj.candidat_associe.formation).data
        except Exception:
            return None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_avatar_url(self, obj) -> str | None:
        return obj.avatar_url()

    avatar_url = serializers.SerializerMethodField(read_only=True, help_text="URL de l'avatar")

    @extend_schema_field(OpenApiTypes.STR)
    def get_centres_info(self, obj):
        try:
            return [{"id": c.id, "nom": getattr(c, "nom", str(c))} for c in obj.centres.all()]
        except Exception:
            return []

    @extend_schema_field(OpenApiTypes.STR)
    def get_centre(self, obj):
        """
        🔹 Retourne le centre principal de l'utilisateur :
        - Staff/admin → premier centre de user.centres
        - Candidat/stagiaire → centre de sa formation
        - Sinon → None
        """
        try:
            # 1️⃣ Staff/admin avec centres multiples
            if hasattr(obj, "centres") and obj.centres.exists():
                c = obj.centres.first()
                return {"id": c.id, "nom": c.nom}

            # 2️⃣ Candidat lié à une formation
            if hasattr(obj, "candidat_associe") and obj.candidat_associe.formation:
                f = obj.candidat_associe.formation
                if f.centre:
                    return {"id": f.centre.id, "nom": f.centre.nom}
        except Exception:
            pass

        return None

    # ------------------------------------------------------
    # Métadonnées
    # ------------------------------------------------------
    class Meta:
        model = CustomUser
        fields = [
            "id", "email", "username", "first_name", "last_name", "phone", "bio",
            "avatar", "avatar_url", "role", "role_display",
            "is_active", "date_joined", "full_name",
            "is_staff", "is_superuser", "is_admin", "is_staff_read",
            "formation", "formation_info",
            "centres", "centres_info",
            "centre",   "consent_rgpd", "consent_date",
        ]
        read_only_fields = [
            "id", "avatar_url", "role_display", "date_joined", "full_name",
            "formation_info", "centres_info", "centre","consent_date"
            "is_staff", "is_superuser", "is_admin", "is_staff_read",
        ]

        extra_kwargs = {
            "email": {
                "required": True,
                "error_messages": {
                    "required": _("Création échouée : l'adresse email est requise."),
                    "blank": _("Création échouée : l'adresse email ne peut pas être vide."),
                },
            },
            "username": {
                "required": True,
                "error_messages": {
                    "required": _("Création échouée : le nom d'utilisateur est requis."),
                    "blank": _("Création échouée : le nom d'utilisateur ne peut pas être vide."),
                },
            },
        }

    # ------------------------------------------------------
    # Helpers internes (inchangés)
    # ------------------------------------------------------
    @extend_schema_field(OpenApiTypes.STR)
    def _is_admin_user(self, user) -> bool:
        return bool(
            getattr(user, "is_superuser", False)
            or (hasattr(user, "is_admin") and callable(user.is_admin) and user.is_admin())
        )

    @extend_schema_field(OpenApiTypes.STR)
    def _get_centre_model(self):
        try:
            centre_field = Formation._meta.get_field("centre")
            return getattr(centre_field, "related_model", None) or getattr(centre_field.remote_field, "model", None)
        except Exception:
            return None

    @extend_schema_field(OpenApiTypes.STR)
    def _assign_centres(self, user, centre_ids: list[int]):
        CentreModel = self._get_centre_model()
        if not CentreModel:
            raise serializers.ValidationError({"centres": "Modèle 'Centre' introuvable via Formation.centre."})

        centres_qs = CentreModel.objects.filter(id__in=centre_ids)
        found_ids = set(centres_qs.values_list("id", flat=True))
        missing = [cid for cid in centre_ids if cid not in found_ids]
        if missing:
            raise serializers.ValidationError({"centres": f"IDs inexistants: {missing}"})

        user.centres.set(centres_qs)

    # ------------------------------------------------------
    # CRUD (inchangé)
    # ------------------------------------------------------
    @extend_schema_field(OpenApiTypes.STR)
    def create(self, validated_data):
        centres_ids = validated_data.pop("centres", None)
        user = CustomUser.objects.create_user(**validated_data)
        if centres_ids is not None:
            request = self.context.get("request")
            if request and self._is_admin_user(request.user):
                self._assign_centres(user, centres_ids)
            elif request:
                raise serializers.ValidationError(
                    {"centres": "Seul un admin/superadmin peut affecter des centres."}
                )
        return user

    @extend_schema_field(OpenApiTypes.STR)
    def update(self, instance, validated_data):
        centres_ids = validated_data.pop("centres", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if centres_ids is not None:
            request = self.context.get("request")
            if request and self._is_admin_user(request.user):
                self._assign_centres(instance, centres_ids)
            elif request:
                raise serializers.ValidationError(
                    {"centres": "Seul un admin/superadmin peut modifier les centres."}
                )
        return instance

    @extend_schema_field(OpenApiTypes.STR)
    def validate_role(self, value):
        request = self.context.get("request")
        current_user = request.user if request else None
        if not current_user:
            return value
        if value == "superadmin" and current_user.role != "superadmin":
            raise serializers.ValidationError("Seul un superadmin peut attribuer ce rôle.")
        if value == "admin" and current_user.role not in ["superadmin", "admin"]:
            raise serializers.ValidationError("Seul un admin ou un superadmin peut attribuer ce rôle.")
        if self.instance and current_user.id == self.instance.id and value != current_user.role:
            raise serializers.ValidationError("Tu ne peux pas changer ton propre rôle.")
        return value


class RoleChoiceSerializer(serializers.Serializer):
    value = serializers.CharField(help_text="Identifiant du rôle (ex: 'admin')")
    label = serializers.CharField(help_text="Libellé du rôle (ex: 'Administrateur')")


from django.utils import timezone

class RegistrationSerializer(serializers.ModelSerializer):
    consent_rgpd = serializers.BooleanField(
        required=True,
        help_text="Consentement explicite au traitement des données personnelles (RGPD)."
    )

    class Meta:
        model = CustomUser
        fields = ["email", "password", "first_name", "last_name", "consent_rgpd"]
        extra_kwargs = {"password": {"write_only": True}}

    @extend_schema_field(OpenApiTypes.STR)
    def validate_consent_rgpd(self, value):
        if not value:
            raise serializers.ValidationError(
                "Vous devez accepter la politique de confidentialité (RGPD)."
            )
        return value

    @extend_schema_field(OpenApiTypes.STR)
    def create(self, validated_data):
        # Extraire et retirer le champ RGPD
        consent_rgpd = validated_data.pop("consent_rgpd", False)

        # Créer l'utilisateur
        user = CustomUser.objects.create_user(
            is_active=False,  # en attente de validation admin
            role="stagiaire",
            **validated_data
        )

        # Enregistrer le consentement
        if consent_rgpd:
            user.consent_rgpd = True
            user.consent_date = timezone.now()
            user.save(update_fields=["consent_rgpd", "consent_date"])

        return user


class UserFilterSet(filters.FilterSet):
    role = filters.CharFilter(field_name="role", lookup_expr="exact")
    is_active = filters.BooleanFilter(field_name="is_active")
    date_joined_min = filters.DateFilter(field_name="date_joined", lookup_expr="gte")
    date_joined_max = filters.DateFilter(field_name="date_joined", lookup_expr="lte")

    class Meta:
        model = CustomUser
        fields = ["role", "is_active", "date_joined"]
