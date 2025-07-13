from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import csv

from ...models.candidat import Candidat, HistoriquePlacement
from ..serializers.candidat_serializers import (
    CandidatSerializer,
    CandidatListSerializer,
    CandidatCreateUpdateSerializer,
    CandidatMetaSerializer,
    HistoriquePlacementSerializer,
    HistoriquePlacementMetaSerializer,
)
from ..permissions import IsStaffOrAbove
from ..paginations import RapAppPagination
from ...utils.filters import CandidatFilter


class CandidatViewSet(viewsets.ModelViewSet):
    """
    🔹 ViewSet complet pour la ressource Candidat :
    - CRUD complet
    - Filtres, recherche, tri
    - Permissions personnalisées
    - Export CSV/PDF
    - Endpoint `meta/`
    """
    queryset = Candidat.objects.all().select_related(
        "formation", "evenement", "compte_utilisateur",
        "responsable_placement", "vu_par", "entreprise_placement", "entreprise_validee"
    ).prefetch_related("appairages", "ateliers_tre_collectifs")
    permission_classes = [IsStaffOrAbove]
    pagination_class = RapAppPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CandidatFilter
    search_fields = ["nom", "prenom", "email", "telephone", "ville"]
    ordering_fields = ["date_inscription", "nom", "prenom", "statut", "formation"]

    def get_serializer_class(self):
        if self.action == "list":
            return CandidatListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return CandidatCreateUpdateSerializer
        return CandidatSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @extend_schema(responses=CandidatMetaSerializer)
    @action(detail=False, methods=["get"], url_path="meta", url_name="meta")
    def meta(self, request):
        return Response(CandidatMetaSerializer().data)

    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request):
        """
        📤 Export CSV des candidats (filtrés).
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="candidats.csv"'

        writer = csv.writer(response)
        writer.writerow(["Nom", "Prénom", "Email", "Téléphone", "Formation", "Statut"])

        for candidat in self.filter_queryset(self.get_queryset()):
            writer.writerow([
                candidat.nom,
                candidat.prenom,
                candidat.email,
                candidat.telephone,
                candidat.formation.nom if candidat.formation else "",
                candidat.get_statut_display()
            ])

        return response

    @action(detail=False, methods=["get"], url_path="export-pdf")
    def export_pdf(self, request):
        """
        📄 Export PDF des candidats (filtrés).
        """
        candidats = self.filter_queryset(self.get_queryset())
        html_string = render_to_string("exports/candidats_pdf.html", {"candidats": candidats})
        html = HTML(string=html_string)
        pdf = html.write_pdf()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="candidats.pdf"'
        return response


class HistoriquePlacementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    📘 Historique des placements des candidats.
    - Lecture seule
    - Filtres par candidat, entreprise, résultat, responsable
    - Endpoint `meta/`
    """
    queryset = HistoriquePlacement.objects.all().select_related(
        "candidat", "entreprise", "responsable"
    )
    serializer_class = HistoriquePlacementSerializer
    permission_classes = [IsStaffOrAbove]
    pagination_class = RapAppPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["candidat", "entreprise", "responsable", "resultat"]
    search_fields = ["candidat__nom", "candidat__prenom", "entreprise__nom"]
    ordering_fields = ["date_placement", "created_at"]

    @extend_schema(responses=HistoriquePlacementMetaSerializer)
    @action(detail=False, methods=["get"], url_path="meta", url_name="meta")
    def meta(self, request):
        """
        🎛️ Métadonnées pour les filtres (résultats, etc.)
        """
        return Response(HistoriquePlacementMetaSerializer().data)
