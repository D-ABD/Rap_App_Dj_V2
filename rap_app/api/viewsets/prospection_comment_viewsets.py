# apps/.../api/viewsets/prospection_comment_viewsets.py
import logging
from django.db.models import Q
from rest_framework import viewsets, filters
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
)
from rest_framework.decorators import action

from django.template.loader import render_to_string
from weasyprint import HTML
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from io import BytesIO
from django.http import HttpResponse
from django.utils import timezone as dj_timezone
import datetime

from ..paginations import RapAppPagination
from ..serializers.prospection_serializers import HistoriqueProspectionSerializer
from ...models.prospection import HistoriqueProspection
from ...models.prospection_comments import ProspectionComment
from ..serializers.prospection_comment_serializers import ProspectionCommentSerializer
from ..permissions import IsOwnerOrStaffOrAbove
from ..roles import (
    is_candidate,
    is_staff_like,
    is_admin_like,
    is_staff_or_staffread,
    staff_centre_ids,
    role_of,
)

logger = logging.getLogger("PROSPECTION_COMMENT")


@extend_schema_view(
    list=extend_schema(
        summary="📋 Liste des commentaires de prospection",
        tags=["ProspectionComments"],
        parameters=[
            OpenApiParameter("prospection", int, description="Filtrer par prospection ID"),
            OpenApiParameter("is_internal", bool, description="Filtrer par interne/public"),
            OpenApiParameter("created_by", int, description="Filtrer par auteur (ID)"),
            OpenApiParameter("partenaire_nom", str, description="Filtrer par nom de partenaire (icontains)"),
            OpenApiParameter("formation_nom", str, description="Filtrer par nom de formation (icontains)"),
            OpenApiParameter("created_by_username", str, description="Filtrer par username auteur (icontains)"),
            OpenApiParameter("search", str, description="Recherche (body, auteur, partenaire, formation)"),
            OpenApiParameter("ordering", str, description="created_at, -created_at, id, -id"),
        ],
        responses={200: OpenApiResponse(response=ProspectionCommentSerializer(many=True))},
    ),
    retrieve=extend_schema(summary="🔍 Détail d’un commentaire", tags=["ProspectionComments"]),
    create=extend_schema(summary="➕ Créer un commentaire", tags=["ProspectionComments"]),
    update=extend_schema(summary="✏️ Modifier un commentaire", tags=["ProspectionComments"]),
    partial_update=extend_schema(summary="✏️ Modifier partiellement un commentaire", tags=["ProspectionComments"]),
    destroy=extend_schema(summary="🗑️ Supprimer un commentaire", tags=["ProspectionComments"]),
)
class ProspectionCommentViewSet(viewsets.ModelViewSet):
    queryset = ProspectionComment.objects.select_related(
        "prospection",
        "prospection__partenaire",
        "prospection__formation",
        "prospection__owner",
        "prospection__created_by",
        "created_by",
    )
    serializer_class = ProspectionCommentSerializer
    permission_classes = [IsOwnerOrStaffOrAbove]
    pagination_class = None

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        "prospection",
        "is_internal",
        "created_by",
        "prospection__owner",
        "prospection__partenaire",
    ]
    search_fields = [
        "body",
        "created_by__username",
        "prospection__partenaire__nom",
        "prospection__formation__nom",
        "prospection__owner__username",
    ]
    ordering_fields = ["created_at", "id"]
    ordering = ["-created_at"]

    def get_queryset(self):
        base = ProspectionComment.objects.select_related(
            "prospection",
            "prospection__owner",
            "prospection__created_by",
            "prospection__partenaire",
            "prospection__formation",
            "prospection__formation__centre",
            "created_by",
        )

        u = getattr(self.request, "user", None)
        if not getattr(u, "is_authenticated", False):
            logger.info("[LIST] anon → 0")
            return base.none()

        qs = base

        if is_candidate(u):
            qs = qs.filter(prospection__owner_id=u.id).filter(
                Q(is_internal=False) | Q(created_by_id=u.id)
            )
            logger.info("[LIST] candidate user=%s → scoped count=%s", u.id, qs.count())

        elif is_admin_like(u):
            logger.info("[LIST] admin-like user=%s → FULL", u.id)

        elif is_staff_like(u):
            centre_ids = staff_centre_ids(u) or []
            if centre_ids:
                qs = qs.filter(
                    Q(prospection__formation__centre_id__in=centre_ids)
                    | Q(prospection__owner=u)
                    | Q(prospection__created_by=u)
                    | Q(created_by=u)
                ).distinct()
            else:
                qs = qs.filter(
                    Q(prospection__owner=u) | Q(prospection__created_by=u) | Q(created_by=u)
                ).distinct()
            logger.info("[LIST] staff user=%s centres=%s → count=%s", u.id, centre_ids, qs.count())

        else:
            logger.info("[LIST] other user=%s → 0", getattr(u, "id", None))
            return base.none()

        qp = self.request.query_params
        part_nom = (qp.get("partenaire_nom") or "").strip()
        form_nom = (qp.get("formation_nom") or "").strip()
        author_username = (qp.get("created_by_username") or "").strip()

        if part_nom:
            qs = qs.filter(prospection__partenaire__nom__icontains=part_nom)
        if form_nom:
            qs = qs.filter(prospection__formation__nom__icontains=form_nom)
        if author_username:
            qs = qs.filter(created_by__username__icontains=author_username)

        owner_id = qp.get("prospection_owner")
        partenaire_id = qp.get("prospection_partenaire")
        if owner_id:
            qs = qs.filter(prospection__owner_id=owner_id)
        if partenaire_id:
            qs = qs.filter(prospection__partenaire_id=partenaire_id)

        return qs.order_by("-created_at", "-id").distinct()

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(qs, many=True)
        data = serializer.data
        resp = Response(data)
        resp["X-PC-Role"] = role_of(request.user)
        resp["X-PC-User"] = str(getattr(request.user, "id", "anon"))
        resp["X-PC-Count"] = str(len(data))
        return resp

    def perform_create(self, serializer):
        u = self.request.user
        prosp = serializer.validated_data["prospection"]

        if is_candidate(u):
            if prosp.owner_id != u.id:
                raise PermissionDenied("Vous ne pouvez commenter que vos propres prospections.")
            serializer.validated_data["is_internal"] = False
        elif is_staff_like(u) and not is_admin_like(u):
            cids = staff_centre_ids(u) or []
            form_centre_id = getattr(getattr(prosp, "formation", None), "centre_id", None)
            if form_centre_id and cids and form_centre_id not in cids:
                raise PermissionDenied("Prospection hors de votre périmètre (centres).")

        serializer.save(created_by=u)

    def perform_update(self, serializer):
        u = self.request.user
        obj: ProspectionComment = self.get_object()

        if is_candidate(u):
            if obj.prospection.owner_id != u.id:
                raise PermissionDenied("Accès refusé.")
            if obj.created_by_id != u.id:
                raise PermissionDenied("Vous ne pouvez modifier que vos propres commentaires.")
            if serializer.validated_data.get("is_internal", obj.is_internal):
                raise PermissionDenied("Un candidat ne peut pas rendre un commentaire interne.")
            new_prosp = serializer.validated_data.get("prospection")
            if new_prosp and new_prosp.id != obj.prospection_id:
                raise PermissionDenied("Vous ne pouvez pas changer la prospection d'un commentaire.")
            serializer.save()
            return

        if is_staff_like(u) and not is_admin_like(u):
            new_prosp = serializer.validated_data.get("prospection", obj.prospection)
            cids = staff_centre_ids(u) or []
            form_centre_id = getattr(getattr(new_prosp, "formation", None), "centre_id", None)
            if form_centre_id and cids and form_centre_id not in cids:
                raise PermissionDenied("Prospection hors de votre périmètre (centres).")

        serializer.save()

    def destroy(self, request, *args, **kwargs):
        u = request.user
        obj: ProspectionComment = self.get_object()

        if is_candidate(u):
            if obj.prospection.owner_id != u.id or obj.created_by_id != u.id or obj.is_internal:
                raise PermissionDenied("Vous ne pouvez pas supprimer ce commentaire.")
        return super().destroy(request, *args, **kwargs)


class HistoriqueProspectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HistoriqueProspection.objects.select_related(
        "prospection",
        "prospection__partenaire",
        "prospection__owner",
        "prospection__created_by",
        "prospection__formation",
        "prospection__formation__centre",
    )
    serializer_class = HistoriqueProspectionSerializer
    permission_classes = [IsOwnerOrStaffOrAbove]
    pagination_class = RapAppPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["prospection", "nouveau_statut", "type_prospection"]
    search_fields = ["commentaire", "resultat"]
    ordering_fields = ["date_modification", "prochain_contact"]
    ordering = ["-date_modification"]

    def get_queryset(self):
        qs = self.queryset
        user = self.request.user

        if not user.is_authenticated:
            return HistoriqueProspection.objects.none()
        if is_candidate(user):
            return qs.filter(prospection__owner=user)
        if is_admin_like(user):
            return qs
        if is_staff_like(user):
            cids = staff_centre_ids(user) or []
            if not cids:
                return qs.filter(Q(prospection__owner=user) | Q(prospection__created_by=user))
            return qs.filter(
                Q(prospection__formation__centre_id__in=cids)
                | Q(prospection__owner=user)
                | Q(prospection__created_by=user)
            ).distinct()
        return qs.filter(Q(prospection__owner=user) | Q(prospection__created_by=user))

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True)
        return Response(
            {
                "success": True,
                "message": "Liste paginée des historiques de prospection.",
                "data": {
                    "count": self.paginator.page.paginator.count,
                    "next": self.paginator.get_next_link(),
                    "previous": self.paginator.get_previous_link(),
                    "results": serializer.data,
                },
            }
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            {"success": True, "message": "Historique récupéré avec succès.", "data": serializer.data}
        )
