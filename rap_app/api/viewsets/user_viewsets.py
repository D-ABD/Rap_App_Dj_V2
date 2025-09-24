from rest_framework import viewsets, status, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.db.models import Q

from ...utils.filters import UserFilterSet
from ..permissions import ReadWriteAdminReadStaff
from ..serializers.user_profil_serializers import (
    CustomUserSerializer,
    RegistrationSerializer,
    RoleChoiceSerializer,
)
from ...models.custom_user import CustomUser
from ...models.logs import LogUtilisateur
from ...models.candidat import Candidat
from ...models.formations import Formation


@extend_schema_view(
    list=extend_schema(
        summary="Liste des utilisateurs",
        description="Récupère tous les utilisateurs actifs, avec filtrage, recherche et tri.",
        tags=["Utilisateurs"],
        responses={200: OpenApiResponse(response=CustomUserSerializer)},
    ),
    retrieve=extend_schema(
        summary="Détail d'un utilisateur",
        description="Récupère les informations détaillées d’un utilisateur par ID.",
        tags=["Utilisateurs"],
        responses={200: OpenApiResponse(response=CustomUserSerializer)},
    ),
    create=extend_schema(
        summary="Créer un utilisateur",
        description="Crée un nouvel utilisateur avec un rôle, un email et d'autres champs.",
        tags=["Utilisateurs"],
        responses={201: OpenApiResponse(description="Utilisateur créé avec succès.")},
    ),
    update=extend_schema(
        summary="Mettre à jour un utilisateur",
        description="Modifie les champs d’un utilisateur existant.",
        tags=["Utilisateurs"],
        responses={200: OpenApiResponse(description="Utilisateur mis à jour avec succès.")},
    ),
    destroy=extend_schema(
        summary="Supprimer un utilisateur",
        description="Supprime logiquement un utilisateur (is_active = False).",
        tags=["Utilisateurs"],
        responses={204: OpenApiResponse(description="Utilisateur supprimé avec succès.")},
    ),
)
class RegisterView(APIView):
    def get_permissions(self):
        # Ouvert à tous pour l'inscription
        return [AllowAny()]

    def post(self, request):
        print("📥 RegisterView POST data:", request.data)
        print("🔐 User:", request.user, "- Authenticated:", request.user.is_authenticated)
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Compte créé. En attente de validation.",
                    "user": {"email": user.email},
                },
                status=status.HTTP_201_CREATED,
            )
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


def _ensure_candidate_for_user(user: CustomUser, formation_id: int | None) -> Candidat:
    """
    Garantit l'existence d'un Candidat lié à l'utilisateur.
    - Si formation_id est fourni et existe, l’associe.
    - Sinon laisse la formation inchangée / None.
    """
    candidat, created = Candidat.objects.get_or_create(
        compte_utilisateur=user,
        defaults={
            "nom": (user.last_name or "").strip() or None,
            "prenom": (user.first_name or "").strip() or None,
            "email": user.email or None,
        },
    )

    if formation_id:
        try:
            f = Formation.objects.get(pk=formation_id)
            candidat.formation = f
        except Formation.DoesNotExist:
            pass

    candidat.save()
    return candidat


class CustomUserViewSet(viewsets.ModelViewSet):
    """
    👤 ViewSet complet pour la gestion des utilisateurs.
    Fournit les actions CRUD + une action `me` pour l’utilisateur connecté.
    """

    queryset = CustomUser.objects.select_related("candidat_associe__formation")
    serializer_class = CustomUserSerializer
    permission_classes = [ReadWriteAdminReadStaff]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = UserFilterSet
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering_fields = ["email", "date_joined", "role"]
    ordering = ["-date_joined"]

    def get_serializer_class(self):
        return CustomUserSerializer

    # ---------- Scopage par centres pour les STAFF ----------
    def _restrict_users_to_staff_centres(self, qs):
        """
        Admin/Superadmin : accès global.
        Staff : uniquement les users rattachés à au moins UN des centres du staff.
        (via M2M user.centres OU via la formation.centre du candidat associé)
        """
        u = self.request.user
        if getattr(u, "is_superuser", False) or (hasattr(u, "is_admin") and u.is_admin()):
            return qs

        if getattr(u, "is_staff", False):
            centre_ids = u.centres.values_list("id", flat=True)
            if not centre_ids:
                return qs.none()
            return qs.filter(
                Q(centres__in=centre_ids) |
                Q(candidat_associe__formation__centre_id__in=centre_ids)
            ).distinct()

        # Non-staff : la permission globale ReadWriteAdminReadStaff les bloque déjà en écriture.
        # En lecture, on renvoie None pour rester strict.
        return qs.none()

    def get_queryset(self):
        base = super().get_queryset().filter(is_active=True)
        return self._restrict_users_to_staff_centres(base)

    # -------------------------------------------------------

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_DELETE,
            user=request.user,
            details="Suppression logique de l'utilisateur",
        )
        return Response(
            {
                "success": True,
                "message": "Utilisateur supprimé avec succès.",
                "data": None,
            },
            status=status.HTTP_204_NO_CONTENT,
        )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user: CustomUser = serializer.save()

        role = serializer.validated_data.get("role") or user.role
        formation_id = request.data.get("formation")
        try:
            formation_id = int(formation_id) if formation_id is not None else None
        except (TypeError, ValueError):
            formation_id = None

        if role in ["candidat", "stagiaire"]:
            _ensure_candidate_for_user(user, formation_id)

        LogUtilisateur.log_action(
            instance=user,
            action=LogUtilisateur.ACTION_CREATE,
            user=request.user,
            details="Création d’un utilisateur",
        )

        return Response(
            {
                "success": True,
                "message": "Utilisateur créé avec succès.",
                "data": user.to_serializable_dict(include_sensitive=True),
            },
            status=status.HTTP_201_CREATED,
        )

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance: CustomUser = self.get_object()

        print("🔁 Requête PATCH reçue pour l'utilisateur:", instance.id)
        print("📦 Données brutes reçues:", request.data)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            print("❌ Erreurs de validation:", serializer.errors)
            return Response(
                {"success": False, "message": "Erreur de validation", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user: CustomUser = serializer.save()
        print(f"✅ Utilisateur mis à jour : {user.email}")

        new_role = serializer.validated_data.get("role", user.role)
        formation_id = request.data.get("formation")
        try:
            formation_id = int(formation_id) if formation_id is not None else None
        except (TypeError, ValueError):
            formation_id = None

        if new_role in ["candidat", "stagiaire"]:
            _ensure_candidate_for_user(user, formation_id)

        LogUtilisateur.log_action(
            instance=user,
            action=LogUtilisateur.ACTION_UPDATE,
            user=request.user,
            details="Mise à jour d'un utilisateur",
        )

        return Response(
            {
                "success": True,
                "message": "Utilisateur mis à jour avec succès.",
                "data": user.to_serializable_dict(include_sensitive=True),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="me", permission_classes=[permissions.IsAuthenticated])
    @extend_schema(
        summary="Mon profil utilisateur",
        description="Retourne les informations complètes de l’utilisateur actuellement connecté.",
        tags=["Utilisateurs"],
        responses={200: OpenApiResponse(response=CustomUserSerializer)},
    )
    def me(self, request):
        user = request.user
        return Response(
            {
                "success": True,
                "message": "Profil utilisateur chargé avec succès.",
                "data": user.to_serializable_dict(include_sensitive=True),
            }
        )

    @action(detail=False, methods=["get"], url_path="roles", permission_classes=[permissions.IsAuthenticated])
    @extend_schema(
        summary="Liste des rôles utilisateurs",
        description="Retourne tous les rôles disponibles dans l'application, sous forme clé/valeur.",
        tags=["Utilisateurs"],
        responses={
            200: OpenApiResponse(
                response=dict,
                description="Rôles disponibles pour la création ou modification d’un utilisateur.",
            )
        },
    )
    def roles(self, request):
        return Response(
            {
                "success": True,
                "message": "Liste des rôles récupérée avec succès.",
                "data": CustomUser.get_role_choices_display(),
            }
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            {"success": True, "message": "Utilisateur récupéré avec succès.", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="liste-simple")
    @extend_schema(
        summary="Liste simple des utilisateurs (id + nom complet)",
        description="Retourne une liste allégée des utilisateurs actifs pour les filtres (id, nom).",
        tags=["Utilisateurs"],
    )
    def liste_simple(self, request):
        users = self.get_queryset().only("id", "first_name", "last_name", "email").order_by("first_name")
        data = [{"id": u.id, "nom": f"{u.first_name} {u.last_name}".strip() or u.email} for u in users]
        return Response({"success": True, "data": data})

    @action(detail=False, methods=["get"], url_path="filtres")
    def get_user_filtres(self, request):
        """
        🔍 Retourne les options dynamiques pour les filtres utilisateurs
        (rôle, statut, formation, centre, type d'offre)
        - Staff : limité aux centres autorisés
        - Admin/Superadmin : global
        """
        roles = [{"value": value, "label": label} for value, label in CustomUser.ROLE_CHOICES]

        formations_qs = Formation.objects.select_related("centre", "type_offre").order_by("nom")
        u = request.user
        if getattr(u, "is_staff", False) and not getattr(u, "is_superuser", False) and not (
            hasattr(u, "is_admin") and u.is_admin()
        ):
            centre_ids = u.centres.values_list("id", flat=True)
            formations_qs = formations_qs.filter(centre_id__in=centre_ids)

        formation_options = [
            {
                "value": f.id,
                "label": f.nom,
                "centre": f.centre.nom if f.centre else None,
                "type_offre": f.type_offre.nom if f.type_offre else None,
            }
            for f in formations_qs
        ]

        centres = [{"value": f.centre.id, "label": f.centre.nom} for f in formations_qs if f.centre]
        types_offre = [{"value": f.type_offre.id, "label": f.type_offre.nom} for f in formations_qs if f.type_offre]

        def unique(items):
            seen = set()
            out = []
            for i in items:
                if i["value"] not in seen:
                    seen.add(i["value"])
                    out.append(i)
            return out

        return Response(
            {
                "success": True,
                "data": {
                    "role": roles,
                    "is_active": [{"value": "true", "label": "Actif"}, {"value": "false", "label": "Inactif"}],
                    "formation": [{"value": f["value"], "label": f["label"]} for f in formation_options],
                    "centre": unique(centres),
                    "type_offre": unique(types_offre),
                },
            }
        )


class RoleChoicesView(APIView):
    @extend_schema(
        responses={200: RoleChoiceSerializer(many=True)},
        summary="Liste des rôles utilisateurs disponibles",
        description="Retourne tous les rôles utilisables avec leurs identifiants et libellés.",
    )
    def get(self, request):
        data = [{"value": value, "label": label} for value, label in CustomUser.ROLE_CHOICES]
        return Response(data)
