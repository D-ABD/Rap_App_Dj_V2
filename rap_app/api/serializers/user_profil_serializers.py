from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field, OpenApiExample
from django.utils.translation import gettext_lazy as _
from django.apps import apps

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
                "avatar": None
            },
            response_only=False,
        ),
    ],
)
class CustomUserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    # ✅ formation en écriture (ID seulement)
    formation = serializers.PrimaryKeyRelatedField(
        queryset=Formation.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
        help_text="ID de la formation à associer (pour candidat/stagiaire)"
    )

    # ✅ formation_info en lecture (détail formation liée)
    formation_info = serializers.SerializerMethodField(read_only=True)

    # ✅ centres : écriture = liste d'IDs (admin/superadmin), lecture = centres_info
    # (ListField pour éviter un import direct du modèle Centre et rester agnostique de l'app_label)
    centres = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        write_only=True,
        help_text="IDs des centres autorisés pour l'utilisateur (admin/superadmin uniquement)"
    )
    centres_info = serializers.SerializerMethodField(read_only=True)

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

    def get_centres_info(self, obj):
        try:
            return [{"id": c.id, "nom": getattr(c, "nom", str(c))} for c in obj.centres.all()]
        except Exception:
            return []

    class Meta:
        model = CustomUser
        fields = [
            "id", "email", "username", "first_name", "last_name", "phone", "bio",
            "avatar", "avatar_url", "role", "role_display",
            "is_active", "date_joined", "full_name",
            "formation",          # champ écrivable (ID)
            "formation_info",     # champ lecture seule (détails)
            "centres",            # écriture (IDs)
            "centres_info",       # lecture
        ]
        read_only_fields = [
            "id", "avatar_url", "role_display", "date_joined", "full_name",
            "formation_info", "centres_info"
        ]

        extra_kwargs = {
            "email": {
                "required": True,
                "error_messages": {
                    "required": _("Création échouée : l'adresse email est requise."),
                    "blank": _("Création échouée : l'adresse email ne peut pas être vide."),
                },
                "help_text": "Adresse email utilisée pour se connecter",
            },
            "username": {
                "required": True,
                "error_messages": {
                    "required": _("Création échouée : le nom d'utilisateur est requis."),
                    "blank": _("Création échouée : le nom d'utilisateur ne peut pas être vide."),
                },
                "help_text": "Nom d'utilisateur unique",
            },
            "role": {
                "help_text": "Rôle attribué à cet utilisateur",
            },
            "avatar": {
                "help_text": "Image de profil",
            },
            "bio": {
                "help_text": "Bio ou description libre",
            },
            "phone": {
                "help_text": "Numéro de téléphone mobile",
            },
        }

    # -- Helpers internes pour la gestion des centres --

    def _is_admin_user(self, user) -> bool:
        return bool(
            getattr(user, "is_superuser", False) or
            (hasattr(user, "is_admin") and callable(user.is_admin) and user.is_admin())
        )

    def _get_centre_model(self):
        """
        Résout dynamiquement le modèle Centre à partir du FK Formation.centre,
        ce qui évite d'avoir à importer le modèle et de dépendre de l'app_label.
        """
        try:
            centre_field = Formation._meta.get_field("centre")
            # Django 3.2+ : related_model, sinon remote_field.model
            return getattr(centre_field, "related_model", None) or getattr(centre_field.remote_field, "model", None)
        except Exception:
            return None

    def _assign_centres(self, user, centre_ids: list[int]):
        CentreModel = self._get_centre_model()
        if not CentreModel:
            raise serializers.ValidationError({"centres": "Modèle 'Centre' introuvable via Formation.centre."})

        # Validation d'existence
        centres_qs = CentreModel.objects.filter(id__in=centre_ids)
        found_ids = set(centres_qs.values_list("id", flat=True))
        missing = [cid for cid in centre_ids if cid not in found_ids]
        if missing:
            raise serializers.ValidationError({"centres": f"IDs inexistants: {missing}"})

        user.centres.set(centres_qs)

    # -- CRUD --

    def create(self, validated_data):
        """
        ➕ Crée un utilisateur avec le gestionnaire `create_user`
        """
        centres_ids = validated_data.pop("centres", None)
        user = CustomUser.objects.create_user(**validated_data)

        # Attribution des centres : réservé à admin/superadmin
        if centres_ids is not None:
            request = self.context.get("request")
            if request and self._is_admin_user(request.user):
                self._assign_centres(user, centres_ids)
            elif request:
                raise serializers.ValidationError(
                    {"centres": "Seul un admin/superadmin peut affecter des centres."}
                )
        return user

    def update(self, instance, validated_data):
        """
        ✏️ Met à jour l'utilisateur (infos personnelles)
        """
        centres_ids = validated_data.pop("centres", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Modification des centres : réservé à admin/superadmin
        if centres_ids is not None:
            request = self.context.get("request")
            if request and self._is_admin_user(request.user):
                self._assign_centres(instance, centres_ids)
            elif request:
                raise serializers.ValidationError(
                    {"centres": "Seul un admin/superadmin peut modifier les centres."}
                )
        return instance

    def validate_role(self, value):
        request = self.context.get("request")
        current_user = request.user if request else None

        if not current_user:
            return value  # Cas improbable, mais sécurité minimale

        # Empêcher de définir un rôle plus élevé que le sien
        if value == "superadmin" and current_user.role != "superadmin":
            raise serializers.ValidationError("Seul un superadmin peut attribuer ce rôle.")
        if value == "admin" and current_user.role not in ["superadmin", "admin"]:
            raise serializers.ValidationError("Seul un admin ou un superadmin peut attribuer ce rôle.")

        # Fix: self.instance peut être None en création
        if self.instance and current_user.id == self.instance.id and value != current_user.role:
            raise serializers.ValidationError("Tu ne peux pas changer ton propre rôle.")

        return value


class RoleChoiceSerializer(serializers.Serializer):
    value = serializers.CharField(help_text="Identifiant du rôle (ex: 'admin')")
    label = serializers.CharField(help_text="Libellé du rôle (ex: 'Administrateur')")


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'first_name', 'last_name']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        return CustomUser.objects.create_user(
            is_active=False,  # 🛑 création inactif
            role='stagiaire',  # 👤 rôle par défaut
            **validated_data
        )


class UserFilterSet(filters.FilterSet):
    role = filters.CharFilter(field_name="role", lookup_expr="exact")
    is_active = filters.BooleanFilter(field_name="is_active")
    date_joined_min = filters.DateFilter(field_name="date_joined", lookup_expr="gte")
    date_joined_max = filters.DateFilter(field_name="date_joined", lookup_expr="lte")

    class Meta:
        model = CustomUser
        fields = ["role", "is_active", "date_joined"]
