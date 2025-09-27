from django.utils import timezone as dj_timezone
from django.db.models import Q, OuterRef, Subquery
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import csv
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from ...utils.filters import AppairageFilterSet
from ...models.appairage import Appairage, HistoriqueAppairage
from ...models.commentaires_appairage import CommentaireAppairage
from ..serializers.appairage_serializers import (
    AppairageSerializer,
    AppairageListSerializer,
    AppairageCreateUpdateSerializer,
    AppairageMetaSerializer,
    HistoriqueAppairageSerializer,
    CommentaireAppairageSerializer,
)
from ..permissions import IsStaffOrAbove
from ..paginations import RapAppPagination


class AppairageViewSet(viewsets.ModelViewSet):
    base_queryset = (
        Appairage.objects.all()
        .select_related(
            "candidat",
            "candidat__formation",
            "candidat__formation__centre",
            "candidat__formation__type_offre",
            "candidat__formation__statut",
            "partenaire",
            "formation",
            "formation__centre",
            "formation__type_offre",
            "formation__statut",
            "created_by",
            "updated_by",
        )
        .prefetch_related("historiques", "commentaires")
    )

    permission_classes = [IsStaffOrAbove]
    pagination_class = RapAppPagination
    filterset_class = AppairageFilterSet
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["statut", "formation", "candidat", "partenaire", "created_by"]

    search_fields = [
        "candidat__nom",
        "candidat__prenom",
        "partenaire__nom",
        "formation__nom",
        "candidat__formation__nom",
        "formation__centre__nom",
        "candidat__formation__centre__nom",
        "commentaires__body",
        "retour_partenaire",
        "created_by__first_name",
        "created_by__last_name",
        "created_by__username",
        "created_by__email",
    ]

    ordering_fields = [
        "date_appairage",
        "statut",
        "formation__nom",
        "formation__centre__nom",
        "updated_at",
        "created_at",
    ]

    # ------------------------- helpers scope/permission -------------------------

    def _is_admin_like(self, user) -> bool:
        return getattr(user, "is_superuser", False) or (hasattr(user, "is_admin") and user.is_admin())

    def _staff_centre_ids(self, user):
        if self._is_admin_like(user):
            return None
        if getattr(user, "is_staff", False):
            return list(user.centres.values_list("id", flat=True))
        return []

    def _scope_qs_to_user_centres(self, qs):
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()

        if hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire():
            formation = getattr(getattr(user, "candidat_associe", None), "formation", None)
            if formation:
                return qs.filter(Q(formation=formation) | Q(candidat__formation=formation))
            return qs.none()

        centre_ids = self._staff_centre_ids(user)
        if centre_ids is None:
            return qs

        if centre_ids:
            return qs.filter(
                Q(formation__centre_id__in=centre_ids)
                | Q(candidat__formation__centre_id__in=centre_ids)
            ).distinct()

        return qs.none()

    def _assert_staff_can_use_formation(self, formation):
        if not formation:
            return
        user = self.request.user
        if self._is_admin_like(user):
            return
        if getattr(user, "is_staff", False):
            allowed = set(user.centres.values_list("id", flat=True))
            if getattr(formation, "centre_id", None) not in allowed:
                raise PermissionDenied("Formation hors de votre périmètre (centre).")

    # ------------------------------- DRF hooks ---------------------------------

    def get_serializer_class(self):
        if self.action == "list":
            return AppairageListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return AppairageCreateUpdateSerializer
        return AppairageSerializer

    def get_queryset(self):
        qs = self.base_queryset

        # 🔹 Annoter le dernier commentaire via Subquery
        last_comment_qs = (
            CommentaireAppairage.objects.filter(appairage=OuterRef("pk"))
            .order_by("-created_at")
            .values("body")[:1]
        )
        qs = qs.annotate(last_commentaire=Subquery(last_comment_qs))

        return self._scope_qs_to_user_centres(qs)

    def perform_create(self, serializer):
        user = self.request.user

        if hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire():
            formation = getattr(getattr(user, "candidat_associe", None), "formation", None)
            if not formation:
                raise PermissionDenied("Votre compte n'est associé à aucune formation.")
            self._assert_staff_can_use_formation(formation)

            candidat_payload = serializer.validated_data.get("candidat")
            partenaire_payload = serializer.validated_data.get("partenaire")

            if Appairage.objects.filter(
                candidat=candidat_payload, partenaire=partenaire_payload, formation=formation
            ).exists():
                raise ValidationError(
                    {
                        "detail": "Un appairage existe déjà pour ce candidat, ce partenaire et cette formation."
                    }
                )

            instance = serializer.save(created_by=user, formation=formation)

        else:
            formation_payload = serializer.validated_data.get("formation")
            candidat_payload = serializer.validated_data.get("candidat")
            formation = (
                formation_payload
                or (getattr(getattr(candidat_payload, "formation", None), "pk", None) and candidat_payload.formation)
                or None
            )

            if formation:
                self._assert_staff_can_use_formation(formation)

            partenaire_payload = serializer.validated_data.get("partenaire")

            if Appairage.objects.filter(
                candidat=candidat_payload, partenaire=partenaire_payload, formation=formation
            ).exists():
                raise ValidationError(
                    {
                        "detail": "Un appairage existe déjà pour ce candidat, ce partenaire et cette formation."
                    }
                )

            instance = serializer.save(
                created_by=user, formation=formation or serializer.validated_data.get("formation")
            )

        if hasattr(instance, "set_user"):
            instance.set_user(user)

        try:
            instance.save(user=user)
        except TypeError:
            instance.save()

    def perform_update(self, serializer):
        user = self.request.user
        instance = serializer.instance

        data_formation = serializer.validated_data.get("formation", instance.formation)

        if hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire():
            user_formation = getattr(getattr(user, "candidat_associe", None), "formation", None)
            if data_formation != user_formation:
                raise PermissionDenied("Vous ne pouvez pas modifier la formation associée.")
            formation = user_formation
        else:
            formation = data_formation
            if formation:
                self._assert_staff_can_use_formation(formation)

        instance = serializer.save(formation=formation)
        if hasattr(instance, "set_user"):
            instance.set_user(user)
        try:
            instance.save(user=user)
        except TypeError:
            instance.save()

    @action(detail=False, methods=["get"], url_path="meta")
    def meta(self, request):
        serializer = AppairageMetaSerializer(instance={}, context={"request": request})
        return Response(serializer.data)

    # ---------------------------- Helpers export ----------------------------

    def _parse_selected_ids(self, request):
        ids = set()

        qp_list = request.query_params.getlist("ids")
        for v in qp_list:
            for p in str(v).split(","):
                p = p.strip()
                if p.isdigit():
                    ids.add(int(p))

        qp = request.query_params.get("ids")
        if qp:
            for p in str(qp).split(","):
                p = p.strip()
                if p.isdigit():
                    ids.add(int(p))

        if request.method in ("POST", "PUT", "PATCH"):
            data = getattr(request, "data", {}) or {}
            for key in ("ids", "selected"):
                val = data.get(key)
                if isinstance(val, (list, tuple)):
                    for x in val:
                        try:
                            ids.add(int(x))
                        except (TypeError, ValueError):
                            pass

        return list(ids)

    def _get_export_queryset(self, request):
        qs = self.filter_queryset(self.get_queryset())
        selected_ids = self._parse_selected_ids(request)
        if selected_ids:
            qs = qs.filter(pk__in=selected_ids)
        return qs

    def _formation_id(self, appairage):
        if getattr(appairage, "formation_id", None):
            return appairage.formation_id
        cand_form = getattr(getattr(appairage, "candidat", None), "formation", None)
        return getattr(cand_form, "id", "") or ""

    def _formation_label(self, appairage):
        if appairage.formation:
            return appairage.formation.nom or ""
        cand_form = getattr(getattr(appairage, "candidat", None), "formation", None)
        return getattr(cand_form, "nom", "") or ""

    def _formation_type_offre(self, appairage):
        f = appairage.formation or getattr(getattr(appairage, "candidat", None), "formation", None)
        if not f or not getattr(f, "type_offre", None):
            return ""
        to = f.type_offre
        return getattr(to, "libelle", None) or getattr(to, "nom", None) or str(to) or ""

    def _formation_num_offre(self, appairage):
        f = appairage.formation or getattr(getattr(appairage, "candidat", None), "formation", None)
        return getattr(f, "num_offre", "") or ""

    def _partenaire_email(self, appairage):
        p = getattr(appairage, "partenaire", None)
        return getattr(p, "contact_email", "") if p else ""

    def _partenaire_telephone(self, appairage):
        p = getattr(appairage, "partenaire", None)
        return getattr(p, "contact_telephone", "") if p else ""

    def _user_display(self, u):
        if not u:
            return ""
        return u.get_full_name() or getattr(u, "username", "") or getattr(u, "email", "") or ""

    # ---------------------------- Commentaires ----------------------------

    @action(detail=True, methods=["get", "post"], url_path="commentaires")
    def commentaires(self, request, pk=None):
        """📌 Liste ou ajout de commentaires liés à un appairage"""
        appairage = self.get_object()

        if request.method == "GET":
            qs = appairage.commentaires.order_by("-created_at")
            serializer = CommentaireAppairageSerializer(qs, many=True)
            return Response(serializer.data)

        if request.method == "POST":
            serializer = CommentaireAppairageSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(created_by=request.user, appairage=appairage)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    # ---------------------------- Actions export ----------------------------
    @action(detail=False, methods=["get", "post"], url_path="export-xlsx")
    def export_xlsx(self, request):
        qs = self._get_export_queryset(request)

        wb = Workbook()
        ws = wb.active
        ws.title = "Appairages"

        headers = [
            "id",
            "candidat_id",
            "candidat_nom",
            "partenaire_id",
            "partenaire_nom",
            "partenaire_email",
            "partenaire_telephone",
            "formation_id",
            "formation_nom",
            "formation_type_offre",
            "formation_num_offre",
            "statut",
            "statut_display",
            "date_appairage",
            "commentaire",
            "retour_partenaire",
            "date_retour",
            "created_by",
            "created_by_nom",
            "updated_by",
            "updated_by_nom",
            "created_at",
            "updated_at",
        ]

        # écrire en-têtes
        ws.append(headers)

        for a in qs:
            ws.append([
                a.id,
                getattr(a.candidat, "id", "") or "",
                getattr(a.candidat, "nom_complet", "") or "",
                getattr(a.partenaire, "id", "") or "",
                getattr(a.partenaire, "nom", "") or "",
                self._partenaire_email(a),
                self._partenaire_telephone(a),
                self._formation_id(a),
                self._formation_label(a),
                self._formation_type_offre(a),
                self._formation_num_offre(a),
                a.statut,
                a.get_statut_display(),
                a.date_appairage.isoformat() if a.date_appairage else "",
                a.last_commentaire or "",
                a.retour_partenaire or "",
                a.date_retour.isoformat() if a.date_retour else "",
                getattr(a.created_by, "id", "") if a.created_by else "",
                self._user_display(a.created_by),
                getattr(a.updated_by, "id", "") if a.updated_by else "",
                self._user_display(a.updated_by),
                a.created_at.isoformat() if getattr(a, "created_at", None) else "",
                a.updated_at.isoformat() if getattr(a, "updated_at", None) else "",
            ])

        # ajuster la largeur des colonnes automatiquement
        for col in ws.columns:
            max_length = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            ws.column_dimensions[col_letter].width = min(max_length + 2, 50)

        # créer la réponse HTTP
        from io import BytesIO
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = HttpResponse(
            buffer,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = f'appairages_{dj_timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class HistoriqueAppairageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HistoriqueAppairage.objects.all().select_related(
        "appairage", "auteur", "appairage__formation", "appairage__candidat__formation"
    )
    serializer_class = HistoriqueAppairageSerializer
    permission_classes = [IsStaffOrAbove]
    pagination_class = RapAppPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["appairage", "statut", "auteur"]
    search_fields = [
        "appairage__candidat__nom",
        "appairage__partenaire__nom",
        "auteur__first_name",
        "auteur__last_name",
    ]
    ordering_fields = ["date"]

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if not u.is_authenticated:
            return qs.none()

        if hasattr(u, "is_candidat_or_stagiaire") and u.is_candidat_or_stagiaire():
            formation = getattr(getattr(u, "candidat_associe", None), "formation", None)
            if formation:
                return qs.filter(
                    Q(appairage__formation=formation) | Q(appairage__candidat__formation=formation)
                )
            return qs.none()

        if getattr(u, "is_superuser", False) or (hasattr(u, "is_admin") and u.is_admin()):
            return qs

        if getattr(u, "is_staff", False):
            centre_ids = list(u.centres.values_list("id", flat=True))
            if not centre_ids:
                return qs.none()
            return qs.filter(
                Q(appairage__formation__centre_id__in=centre_ids)
                | Q(appairage__candidat__formation__centre_id__in=centre_ids)
            ).distinct()

        return qs.none()
