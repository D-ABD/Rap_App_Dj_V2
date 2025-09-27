from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from ..serializers.commentaires_appairage_serializers import (
    CommentaireAppairageSerializer,
    CommentaireAppairageWriteSerializer,
)
from ...models.commentaires_appairage import CommentaireAppairage
from ...models.logs import LogUtilisateur
from ..paginations import RapAppPagination
from ..permissions import IsStaffOrAbove
from rest_framework.decorators import action
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from django.utils import timezone as dj_timezone
from io import BytesIO
@extend_schema(tags=["Commentaires Appairages"])
class CommentaireAppairageViewSet(viewsets.ModelViewSet):
    """
    API CRUD pour les commentaires liés aux appairages.
    Accès réservé aux utilisateurs staff/admin/superadmin.
    """

    queryset = CommentaireAppairage.objects.select_related(
        "appairage",
        "appairage__candidat",
        "appairage__partenaire",
        "appairage__formation",
        "created_by",
    ).all()
    pagination_class = RapAppPagination
    permission_classes = [IsStaffOrAbove]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "body",
        "created_by__username",
        "created_by__email",
        "appairage__candidat__nom",
        "appairage__candidat__prenom",
        "appairage__partenaire__nom",
    ]
    ordering = ["-created_at"]

    # ---------------- Queryset dynamique ----------------
    def get_queryset(self):
        qs = super().get_queryset()
        appairage_id = self.request.query_params.get("appairage")
        if appairage_id:
            qs = qs.filter(appairage_id=appairage_id)
        return qs

    # ---------------- Serializer dynamique ----------------
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CommentaireAppairageWriteSerializer
        return CommentaireAppairageSerializer
    
    # ---------------- CRUD ----------------
    @extend_schema(summary="Lister les commentaires d’appairage")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Récupérer un commentaire d’appairage")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Créer un commentaire d’appairage")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        commentaire = serializer.save(created_by=request.user)

        LogUtilisateur.log_action(
            instance=commentaire,
            action=LogUtilisateur.ACTION_CREATE,
            user=request.user,
            details=f"Création d’un commentaire pour l’appairage #{commentaire.appairage_id}",
        )

        # réponse enrichie via serializer de lecture
        read_data = CommentaireAppairageSerializer(commentaire, context={"request": request}).data
        return Response(
            {"success": True, "message": "Commentaire d’appairage créé avec succès.", "data": read_data},
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(summary="Mettre à jour un commentaire d’appairage")
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        commentaire = serializer.save(updated_by=request.user)

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_UPDATE,
            user=request.user,
            details=f"Mise à jour du commentaire d’appairage #{instance.pk}",
        )

        read_data = CommentaireAppairageSerializer(commentaire, context={"request": request}).data
        return Response(
            {"success": True, "message": "Commentaire d’appairage mis à jour avec succès.", "data": read_data},
            status=status.HTTP_200_OK,
        )

    @extend_schema(summary="Supprimer un commentaire d’appairage")
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        pk = instance.pk
        instance.delete()

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_DELETE,
            user=request.user,
            details=f"Suppression du commentaire d’appairage #{pk}",
        )

        return Response(
            {"success": True, "message": "Commentaire d’appairage supprimé avec succès.", "data": None},
            status=status.HTTP_204_NO_CONTENT,
        )


    
# ---------------------------- Actions export ----------------------------

    # ---------------------------- Actions export ----------------------------

    @action(detail=False, methods=["get", "post"], url_path="export-pdf")
    def export_pdf(self, request):
        qs = self.filter_queryset(
            self.get_queryset().select_related(
                "appairage__partenaire",
                "appairage__candidat",
                "appairage__formation",
                "appairage__formation__type_offre",
            )
        )

        # Si des IDs sont envoyés (POST), on filtre dessus
        ids = request.data.get("ids") if request.method == "POST" else None
        if ids:
            qs = qs.filter(id__in=ids)

        html_string = render_to_string(
            "exports/appairage_commentaires_pdf.html",
            {"commentaires": qs},
        )
        pdf = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf, content_type="application/pdf")
        filename = f'commentaires_appairage_{dj_timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


    @action(detail=False, methods=["get", "post"], url_path="export-xlsx")
    def export_xlsx(self, request):
        qs = self.filter_queryset(
            self.get_queryset().select_related(
                "appairage__partenaire",
                "appairage__candidat",
                "appairage__formation",
                "appairage__formation__type_offre",
            )
        )

        # Si des IDs sont envoyés (POST), on filtre dessus
        ids = request.data.get("ids") if request.method == "POST" else None
        if ids:
            qs = qs.filter(id__in=ids)

        wb = Workbook()
        ws = wb.active
        ws.title = "Commentaires Appairage"

        headers = [
            "Commentaire ID",
            "Appairage ID",
            "Statut appairage",
            "Candidat",
            "Entreprise",
            "Formation",
            "Numéro offre",
            "Type de formation",
            "Début",
            "Fin",
            "Auteur commentaire",
            "Date commentaire",
            "Texte commentaire",
        ]
        ws.append(headers)

        for c in qs:
            a = c.appairage
            f = a.formation if a else None
            ws.append([
                c.id,
                getattr(a, "id", ""),
                getattr(a, "statut", ""),
                getattr(a.candidat, "nom_complet", "") if a and a.candidat else "",
                getattr(a.partenaire, "nom", "") if a and a.partenaire else "",
                getattr(f, "nom", "") if f else "",
                getattr(f, "num_offre", "") if f else "",
                getattr(f.type_offre, "nom", "") if f and f.type_offre else "",
                f.start_date.strftime("%d/%m/%Y") if f and f.start_date else "",
                f.end_date.strftime("%d/%m/%Y") if f and f.end_date else "",
                getattr(c.created_by, "username", "") if c.created_by else "",
                c.created_at.strftime("%d/%m/%Y %H:%M") if c.created_at else "",
                c.body or "",
            ])

        # Ajuster automatiquement la largeur des colonnes
        for col in ws.columns:
            max_length = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = min(max_length + 2, 50)

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = HttpResponse(
            buffer,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        filename = f'commentaires_appairage_{dj_timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
