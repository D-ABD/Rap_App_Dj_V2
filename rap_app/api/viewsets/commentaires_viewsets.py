import io
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.http import Http404
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from io import BytesIO
import datetime

from ...models.commentaires import Commentaire
from ...models.logs import LogUtilisateur
from ...api.serializers.commentaires_serializers import CommentaireMetaSerializer, CommentaireSerializer
from ...api.paginations import RapAppPagination
from ...api.permissions import IsStaffOrAbove  # <-- réservé au staff/admin/superadmin
from ...utils.exporter import Exporter
from django.utils import timezone as dj_timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from weasyprint import HTML

from ...models.appairage import Appairage
from ...models.partenaires import Partenaire
from ...models.formations import Formation
from ...models.candidat import Candidat
from ...models.commentaires_appairage import CommentaireAppairage
from ...models.commentaires import Commentaire
from ..permissions import IsStaffOrAbove

@extend_schema(tags=["Commentaires"])
class CommentaireViewSet(viewsets.ModelViewSet):
    """
    API CRUD pour les commentaires liés aux formations.
    Permet la création, l’édition, la suppression, la recherche et l’export.
    Accès réservé aux utilisateurs staff/admin/superadmin.

    ⚠️ Scope centres :
      - Admin/Superadmin : accès global
      - Staff : limité aux commentaires dont la formation appartient à leurs centres
    """
    queryset = Commentaire.objects.select_related(
        "formation", "formation__type_offre", "formation__statut", "formation__centre", "created_by"
    ).all()
    serializer_class = CommentaireSerializer
    pagination_class = RapAppPagination
    permission_classes = [IsStaffOrAbove]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["contenu", "formation__nom", "formation__num_offre", "created_by__username"]
    ordering = ["-created_at"]

    # --------------------- helpers scope/permissions ---------------------

    def _is_admin_like(self, user) -> bool:
        # Utilise tes helpers de CustomUser si présents (is_admin()); sinon flags Django
        return getattr(user, "is_superuser", False) or (hasattr(user, "is_admin") and user.is_admin())

    def _staff_centre_ids(self, user):
        """Liste des centres du staff (None si admin-like = accès global)."""
        if self._is_admin_like(user):
            return None
        if is_staff_or_staffread(user):
            # nécessite le M2M user.centres déjà mis en place
            return list(user.centres.values_list("id", flat=True))
        return []

    def _scope_qs_to_user_centres(self, qs):
        user = self.request.user
        centre_ids = self._staff_centre_ids(user)
        if centre_ids is None:
            return qs  # admin/superadmin
        if centre_ids:
            return qs.filter(formation__centre_id__in=centre_ids)
        return qs.none()

    def _assert_staff_can_use_formation(self, formation):
        """Empêche un staff d'écrire hors de son périmètre (centre de la formation)."""
        if not formation:
            return
        user = self.request.user
        if self._is_admin_like(user):
            return
        if is_staff_or_staffread(user):
            allowed = set(user.centres.values_list("id", flat=True))
            if getattr(formation, "centre_id", None) not in allowed:
                raise PermissionDenied("Formation hors de votre périmètre (centre).")

    # ------------------------------ context ------------------------------

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["include_full_content"] = True
        return context


    # ------------------------------ filtres UI ----------------------------

    @extend_schema(
        summary="Récupérer les filtres disponibles pour les commentaires",
        responses={200: OpenApiResponse(description="Filtres disponibles")}
    )
    @action(detail=False, methods=["get"], url_path="filtres", permission_classes=[IsStaffOrAbove])
    def get_filtres(self, request):
        """
        Renvoie les options de filtres disponibles pour les commentaires.
        (Sur la base du queryset **déjà scopé**)
        """
        scoped = self.get_queryset()

        centres = scoped.filter(formation__centre__isnull=False) \
            .values_list("formation__centre_id", "formation__centre__nom").distinct()

        statuts = scoped.filter(formation__statut__isnull=False) \
            .values_list("formation__statut_id", "formation__statut__nom").distinct()

        type_offres = scoped.filter(formation__type_offre__isnull=False) \
            .values_list("formation__type_offre_id", "formation__type_offre__nom").distinct()

        formation_etats = [
            {"value": "actives", "label": "Formations actives"},
            {"value": "a_venir", "label": "À venir"},
            {"value": "terminees", "label": "Formations terminées"},
            {"value": "a_recruter", "label": "À recruter"},
        ]

        return Response({
            "success": True,
            "message": "Filtres récupérés avec succès",
            "data": {
                "centres": [{"id": c[0], "nom": c[1]} for c in centres],
                "statuts": [{"id": s[0], "nom": s[1]} for s in statuts],
                "type_offres": [{"id": t[0], "nom": t[1]} for t in type_offres],
                "formation_etats": formation_etats,
            }
        })

    # --------------------------- CRUD standard ----------------------------

    @extend_schema(summary="Lister les commentaires actifs")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Récupérer un commentaire")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Créer un commentaire")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 🔐 Contrôle périmètre formation avant save
        formation = serializer.validated_data.get("formation", None)
        self._assert_staff_can_use_formation(formation)

        commentaire = serializer.save()

        LogUtilisateur.log_action(
            instance=commentaire,
            action=LogUtilisateur.ACTION_CREATE,
            user=request.user,
            details=f"Création d'un commentaire pour la formation #{commentaire.formation_id}"
        )

        return Response({
            "success": True,
            "message": "Commentaire créé avec succès.",
            "data": commentaire.to_serializable_dict(include_full_content=True)
        }, status=status.HTTP_201_CREATED)

    @extend_schema(summary="Mettre à jour un commentaire")
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # 🔐 Contrôle périmètre (nouvelle formation si fournie, sinon formation existante)
        new_formation = serializer.validated_data.get("formation", instance.formation)
        self._assert_staff_can_use_formation(new_formation)

        commentaire = serializer.save()

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_UPDATE,
            user=request.user,
            details=f"Mise à jour du commentaire #{instance.pk}"
        )

        return Response({
            "success": True,
            "message": "Commentaire mis à jour avec succès.",
            "data": commentaire.to_serializable_dict(include_full_content=True)
        }, status=status.HTTP_200_OK)

    @extend_schema(summary="Supprimer un commentaire")
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # 🔐 Optionnel : verrouille la suppression à son centre
        self._assert_staff_can_use_formation(getattr(instance, "formation", None))

        instance.delete()

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_DELETE,
            user=request.user,
            details=f"Suppression du commentaire #{instance.pk}"
        )

        return Response({
            "success": True,
            "message": "Commentaire supprimé avec succès.",
            "data": None
        }, status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Récupérer les statistiques de saturation des commentaires",
        responses={200: OpenApiResponse(description="Données de saturation pour une formation", response=None)}
    )
    @action(detail=False, methods=["get"], url_path="saturation-stats", permission_classes=[IsStaffOrAbove])
    def saturation_stats(self, request):
        """
        Renvoie les statistiques de saturation pour une formation donnée.
        """
        formation_id = request.query_params.get("formation_id")
        stats = Commentaire.get_saturation_stats(formation_id=formation_id)

        return Response({
            "success": True,
            "message": "Statistiques de saturation récupérées avec succès.",
            "data": stats
        })




# -------------------------------------------------------------------
# Export commentaires (PDF / XLSX)
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# Export commentaires (PDF / XLSX)
# -------------------------------------------------------------------
    @action(detail=False, methods=["get", "post"], url_path="export", permission_classes=[IsStaffOrAbove])
    def export(self, request):
        """
        Export des commentaires en PDF ou XLSX
        (Scope centres appliqué via get_queryset() + filter_queryset())
        """
        # 🔑 lit d'abord le body si POST, sinon query_params
        fmt = request.data.get("format") or request.query_params.get("format", "pdf")

        if request.method == "POST":
            ids = request.data.get("ids", [])
            export_all = request.data.get("all", False)
        else:
            ids = request.query_params.get("ids", "")
            export_all = request.query_params.get("all", "false").lower() == "true"

        qs = self.filter_queryset(
            self.get_queryset().select_related(
                "formation",
                "formation__centre",
                "formation__type_offre",
                "formation__statut",
                "created_by",
            )
        )

        if ids:
            if isinstance(ids, str):
                id_list = [int(i) for i in ids.split(",") if i.isdigit()]
            else:
                id_list = [int(i) for i in ids if str(i).isdigit()]
            qs = qs.filter(id__in=id_list)

        if not export_all and not ids:
            return Response({"detail": "Aucun commentaire sélectionné"}, status=400)

        if fmt == "pdf":
            return self._export_pdf(qs)
        elif fmt == "xlsx":
            return self._export_xlsx(qs)
        else:
            return Response({"detail": "Format non supporté (seuls pdf, xlsx)"}, status=400)

    def _export_pdf(self, qs):
        data = []
        for c in qs:
            f = getattr(c, "formation", None)
            data.append({
                "id": c.id,
                "contenu": c.contenu or "",
                "auteur": getattr(c.created_by, "username", ""),
                "created_at": c.created_at.strftime("%d/%m/%Y %H:%M") if c.created_at else "",
                "formation": {
                    "nom": getattr(f, "nom", "") if f else "",
                    "num_offre": getattr(f, "num_offre", "") if f else "",
                    "centre_nom": getattr(f.centre, "nom", "") if f and f.centre else "",
                    "type_offre_nom": getattr(f.type_offre, "nom", "") if f and f.type_offre else "",
                    "statut_nom": getattr(f.statut, "nom", "") if f and f.statut else "",
                    # 🔽 Nouveaux champs saturation / remplissage
                    "places_prevues": f.total_places if f else "",
                    "inscrits": f.total_inscrits if f else "",
                    "places_disponibles": f.places_disponibles if f else "",
                    "taux_saturation": f.taux_saturation if f else "",
                    "saturation_commentaires": f.get_saturation_moyenne_commentaires() if f else "",
                },
            })

        html_string = render_to_string(
            "exports/commentaires_pdf.html",
            {"items": data, "user": self.request.user},
        )
        pdf = HTML(string=html_string).write_pdf()

        filename = f'commentaires_{dj_timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Content-Length"] = len(pdf)
        return response


    def _export_xlsx(self, qs):
        wb = Workbook()
        ws = wb.active
        ws.title = "Commentaires Formation"

        headers = [
            "ID", "Contenu", "Auteur", "Créé le",
            "Formation", "N° Offre", "Centre", "Type d’offre", "Statut",
            "Places prévues", "Inscrits", "Places dispo", "Taux saturation (%)", "Sat. moy. commentaires",
        ]
        ws.append(headers)

        def _fmt(val):
            if val is None:
                return ""
            if isinstance(val, datetime.datetime):
                return val.strftime("%d/%m/%Y %H:%M")
            return str(val)

        for c in qs:
            f = getattr(c, "formation", None)
            ws.append([
                c.id,
                c.contenu or "",   # ✅ contenu du commentaire
                getattr(c.created_by, "username", ""),
                _fmt(c.created_at),
                getattr(f, "nom", "") if f else "",
                getattr(f, "num_offre", "") if f else "",
                getattr(f.centre, "nom", "") if f and f.centre else "",
                getattr(f.type_offre, "nom", "") if f and f.type_offre else "",
                getattr(f.statut, "nom", "") if f and f.statut else "",
                getattr(f, "total_places", ""),
                getattr(f, "total_inscrits", ""),
                getattr(f, "places_disponibles", ""),
                getattr(f, "taux_saturation", ""),
                f.get_saturation_moyenne_commentaires() if f else "",
            ])

        # Ajustement colonnes
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            if col_letter == "B":  # colonne "Contenu"
                ws.column_dimensions[col_letter].width = 80   # largeur fixe
                for cell in col:
                    cell.alignment = cell.alignment.copy(wrapText=True)  # ✅ retour à la ligne
            else:
                max_length = max((len(str(cell.value)) for cell in col if cell.value), default=0)
                ws.column_dimensions[col_letter].width = min(max_length + 2, 40)

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        binary_content = buffer.getvalue()

        filename = f'commentaires_{dj_timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response = HttpResponse(
            binary_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Content-Length"] = len(binary_content)
        return response

