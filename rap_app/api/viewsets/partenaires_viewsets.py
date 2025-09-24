from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission, SAFE_METHODS
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, filters as dj_filters
from django.db.models import Count, Q

from ...api.permissions import IsOwnerOrStaffOrAbove, RestrictToUserOwnedQuerysetMixin
from ...models.partenaires import Partenaire
from ..serializers.partenaires_serializers import PartenaireChoicesResponseSerializer, PartenaireSerializer
from ...models.logs import LogUtilisateur


# -------------------- permission locale --------------------

class PartenaireAccessPermission(BasePermission):
    """
    - Admin/staff/superuser : OK
    - Sinon :
        - OK si créateur
        - OK en LECTURE si attribué via une prospection (prospections.owner = user)
    Les droits d'édition/suppression restent limités par la vue (créateur uniquement).
    """
    message = "Accès restreint."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False) or (
            hasattr(user, "is_admin") and callable(user.is_admin) and user.is_admin()
        ):
            return True

        if getattr(obj, "created_by_id", None) == user.id:
            return True

        if request.method in SAFE_METHODS and hasattr(obj, "prospections"):
            try:
                return obj.prospections.filter(owner=user).exists()
            except Exception:
                return False

        return False


class InlinePartenaireFilter(FilterSet):
    type = dj_filters.CharFilter(lookup_expr="exact")
    is_active = dj_filters.BooleanFilter()
    city = dj_filters.CharFilter(lookup_expr="icontains")
    secteur_activite = dj_filters.CharFilter(lookup_expr="icontains")
    created_by = dj_filters.NumberFilter()
    # ✅ filtrer par centre par défaut du partenaire
    centre_id = dj_filters.NumberFilter(field_name="default_centre_id")

    has_appairages = dj_filters.BooleanFilter(method="filter_has_appairages")
    has_prospections = dj_filters.BooleanFilter(method="filter_has_prospections")
    has_formations = dj_filters.BooleanFilter(method="filter_has_formations")
    has_candidats = dj_filters.BooleanFilter(method="filter_has_candidats")

    class Meta:
        model = Partenaire
        fields = [
            "type",
            "is_active",
            "city",
            "secteur_activite",
            "created_by",
            "centre_id",
            "has_appairages",
            "has_prospections",
            "has_formations",
            "has_candidats",
        ]

    def _bool(self, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return None
        s = str(value).strip().lower()
        return s in {"1", "true", "yes", "y", "on"}

    def filter_has_appairages(self, queryset, name, value):
        b = self._bool(value)
        if b is None:
            return queryset
        return queryset.filter(appairages_count__gt=0) if b else queryset.filter(appairages_count=0)

    def filter_has_prospections(self, queryset, name, value):
        b = self._bool(value)
        if b is None:
            return queryset
        return queryset.filter(prospections_count__gt=0) if b else queryset.filter(prospections_count=0)

    def filter_has_formations(self, queryset, name, value):
        b = self._bool(value)
        if b is None:
            return queryset
        return queryset.filter(formations_count__gt=0) if b else queryset.filter(formations_count=0)

    def filter_has_candidats(self, queryset, name, value):
        b = self._bool(value)
        if b is None:
            return queryset
        return queryset.filter(candidats_count__gt=0) if b else queryset.filter(candidats_count=0)


@extend_schema_view(
    list=extend_schema(
        summary="Lister les partenaires",
        tags=["Partenaires"],
        responses={200: OpenApiResponse(response=PartenaireSerializer)}
    ),
    retrieve=extend_schema(
        summary="Détail d’un partenaire",
        tags=["Partenaires"],
        responses={200: OpenApiResponse(response=PartenaireSerializer)}
    ),
    create=extend_schema(
        summary="Créer un partenaire",
        tags=["Partenaires"],
        responses={201: OpenApiResponse(description="Création réussie")}
    ),
    update=extend_schema(
        summary="Modifier un partenaire",
        tags=["Partenaires"],
        responses={200: OpenApiResponse(description="Mise à jour réussie")}
    ),
    destroy=extend_schema(
        summary="Supprimer un partenaire",
        tags=["Partenaires"],
        responses={204: OpenApiResponse(description="Suppression réussie")}
    ),
)
class PartenaireViewSet(RestrictToUserOwnedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = PartenaireSerializer
    # ✅ utilise la permission locale pour autoriser la lecture des partenaires attribués via prospection
    permission_classes = [PartenaireAccessPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = InlinePartenaireFilter
    ordering_fields = ["nom", "created_at", "default_centre__nom"]  # ✅ tri centre
    ordering = ["nom"]
    search_fields = [
        "nom",
        "secteur_activite",
        "street_name",
        "zip_code",
        "city",
        "country",
        "contact_nom",
        "contact_poste",
        "contact_email",
        "contact_telephone",
        "website",
        "social_network_url",
        "description",
        "action_description",
        "actions",
        "created_by__first_name",
        "created_by__last_name",
        "created_by__username",
        "default_centre__nom",  # ✅ recherche centre
    ]

    # -------------------- helpers scope --------------------

    def _is_admin_like(self, user) -> bool:
        return getattr(user, "is_superuser", False) or (hasattr(user, "is_admin") and user.is_admin())

    def _staff_centre_ids(self, user):
        if self._is_admin_like(user):
            return None  # accès global
        if getattr(user, "is_staff", False):
            return list(user.centres.values_list("id", flat=True))
        return []  # non-staff

    def _scoped_for_staff(self, qs, user):
        """
        Staff :
        - partenaires liés à AU MOINS une formation d'un de ses centres (via appairages/prospections)
        - OU partenaires dont le default_centre ∈ ses centres
        - OU partenaires qu'il a créés
        """
        centre_ids = self._staff_centre_ids(user)
        if centre_ids is None:
            return qs  # admin/superadmin

        if not centre_ids:
            return qs.filter(created_by=user)

        return qs.filter(
            Q(appairages__formation__centre_id__in=centre_ids) |
            Q(prospections__formation__centre_id__in=centre_ids) |
            Q(default_centre_id__in=centre_ids) |
            Q(created_by=user)
        ).distinct()

    def _user_can_access_partenaire(self, partenaire, user) -> bool:
        """Vérifie qu'un staff est dans le périmètre du partenaire."""
        if self._is_admin_like(user):
            return True
        if not getattr(user, "is_staff", False):
            # non-staff : déjà géré par permission/queryset
            return True
        centre_ids = set(user.centres.values_list("id", flat=True))
        if not centre_ids:
            return partenaire.created_by_id == user.id
        linked = (
            partenaire.appairages.filter(formation__centre_id__in=centre_ids).exists()
            or partenaire.prospections.filter(formation__centre_id__in=centre_ids).exists()
            or (partenaire.default_centre_id in centre_ids)
        )
        return linked or (partenaire.created_by_id == user.id)

    # -------------------- queryset --------------------

    def get_queryset(self):
        user = self.request.user

        qs = (
            Partenaire.objects
            .filter(is_active=True)
            .select_related("created_by", "default_centre")   # ✅ pas de N+1 centre
            .annotate(
                prospections_count=Count("prospections", distinct=True),
                appairages_count=Count("appairages", distinct=True),
                # Formations (distinct) via appairages + prospections
                formations_count=Count(
                    "appairages__formation",
                    filter=Q(appairages__formation__isnull=False),
                    distinct=True,
                ) + Count(
                    "prospections__formation",
                    filter=Q(prospections__formation__isnull=False),
                    distinct=True,
                ),
                # Candidats distincts (via appairages)
                candidats_count=Count("appairages__candidat", distinct=True),
            )
        )

        if self._is_admin_like(user):
            return qs
        if getattr(user, "is_staff", False):
            return self._scoped_for_staff(qs, user)

        # ✅ Candidat·e : créés par lui/elle + attribués via prospection (owner=user)
        return qs.filter(Q(created_by=user) | Q(prospections__owner=user)).distinct()

    # -------------------- endpoints utilitaires --------------------

    @action(detail=False, methods=["get"], url_path="choices")
    def choices(self, request):
        types = [{"value": k, "label": v} for k, v in Partenaire.TYPE_CHOICES]
        actions = [{"value": k, "label": v} for k, v in Partenaire.CHOICES_TYPE_OF_ACTION]
        ser = PartenaireChoicesResponseSerializer(instance={"types": types, "actions": actions})
        return Response(ser.data)

    @extend_schema(summary="🔽 Filtres disponibles pour les partenaires", tags=["Partenaires"])
    @action(detail=False, methods=["get"], url_path="filter-options")
    def filter_options(self, request):
        """
        Options de filtre basées sur le queryset **déjà scopé** de l'utilisateur.
        """
        qs = self.filter_queryset(self.get_queryset())

        villes = (
            qs.exclude(city__isnull=True)
              .exclude(city="")  # ✅ évite l’avertissement Pylance
              .values_list("city", flat=True)
              .distinct()
        )
        secteurs = (
            qs.exclude(secteur_activite__isnull=True)
              .exclude(secteur_activite="")  # ✅ évite l’avertissement Pylance
              .values_list("secteur_activite", flat=True)
              .distinct()
        )
        users = (
            qs.exclude(created_by__isnull=True)
              .values("created_by").distinct()
              .values("created_by", "created_by__first_name", "created_by__last_name")
        )
        # ✅ centres par défaut disponibles
        centres = (
            qs.filter(default_centre__isnull=False)
              .values("default_centre_id", "default_centre__nom")
              .distinct()
        )

        return Response({
            "cities": [{"value": v, "label": v} for v in villes],
            "secteurs": [{"value": s, "label": s} for s in secteurs],
            "users": [
                {
                    "id": u["created_by"],
                    "full_name": " ".join(filter(None, [u.get("created_by__first_name"), u.get("created_by__last_name")])).strip()
                }
                for u in users if u["created_by"]
            ],
            "centres": [
                {"id": c["default_centre_id"], "nom": c["default_centre__nom"]}
                for c in centres
            ],
        })

    # -------------------- CRUD --------------------

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_CREATE,
            user=self.request.user,
            details="Création d'un partenaire"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(created_by=request.user)
        LogUtilisateur.log_action(
            instance=instance, action=LogUtilisateur.ACTION_CREATE,
            user=request.user, details="Création d'un partenaire"
        )
        return Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()  # respecte le scope via get_queryset()
        user = request.user

        # Non-staff non-admin : ne peut modifier que ses partenaires
        if not getattr(user, "is_staff", False) and not getattr(user, "is_superuser", False):
            if instance.created_by_id != user.id:
                raise PermissionDenied("Vous ne pouvez modifier que vos propres partenaires.")

        # Staff : doit être dans son périmètre (liens centres) ou owner
        if getattr(user, "is_staff", False) and not self._is_admin_like(user):
            if not self._user_can_access_partenaire(instance, user):
                raise PermissionDenied("Partenaire hors de votre périmètre (centres).")

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        LogUtilisateur.log_action(
            instance=instance, action=LogUtilisateur.ACTION_UPDATE,
            user=request.user, details="Modification d'un partenaire"
        )
        return Response(self.get_serializer(instance).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()  # respecte le scope
        user = request.user

        if not getattr(user, "is_staff", False) and not getattr(user, "is_superuser", False):
            if instance.created_by_id != user.id:
                raise PermissionDenied("Vous ne pouvez supprimer que vos propres partenaires.")

        if getattr(user, "is_staff", False) and not self._is_admin_like(user):
            if not self._user_can_access_partenaire(instance, user):
                raise PermissionDenied("Partenaire hors de votre périmètre (centres).")

        instance.is_active = False
        instance.save()
        LogUtilisateur.log_action(
            instance=instance, action=LogUtilisateur.ACTION_DELETE,
            user=request.user, details="Suppression logique d'un partenaire"
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    # -------------------- détail enrichi --------------------

    @extend_schema(
        summary="Détail d’un partenaire avec relations",
        description="Statistiques sur prospections, formations (via appairages/prospections), appairages et candidats.",
        tags=["Partenaires"],
        responses={200: PartenaireSerializer}
    )
    @action(detail=True, methods=["get"], url_path="with-relations")
    def retrieve_with_relations(self, request, pk=None):
        partenaire = self.get_object()  # déjà scopé
        data = self.get_serializer(partenaire).data

        # Harmonisation: renvoie des objets {count}
        data["prospections"] = {"count": partenaire.prospections.count()}
        data["appairages"] = {"count": partenaire.appairages.count()}

        # Formations distinctes via appairages + prospections
        app_ids = set(
            partenaire.appairages.filter(formation__isnull=False).values_list("formation_id", flat=True)
        )
        pros_ids = set(
            partenaire.prospections.filter(formation__isnull=False).values_list("formation_id", flat=True)
        )
        data["formations"] = {"count": len(app_ids.union(pros_ids))}

        # Candidats distincts
        data["candidats"] = {"count": partenaire.appairages.values("candidat_id").distinct().count()}
        return Response(data)
