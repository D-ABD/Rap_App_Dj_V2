from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import csv

from ...models.appairage import Appairage, HistoriqueAppairage
from ..serializers.appairage_serializers import (
    AppairageSerializer,
    AppairageListSerializer,
    AppairageCreateUpdateSerializer,
    AppairageMetaSerializer,
    HistoriqueAppairageSerializer
)
from ..permissions import IsStaffOrAbove
from ..paginations import RapAppPagination


class AppairageViewSet(viewsets.ModelViewSet):
    queryset = Appairage.objects.all().select_related(
        "candidat", "partenaire", "formation", "created_by"
    ).prefetch_related("historiques")
    permission_classes = [IsStaffOrAbove]
    pagination_class = RapAppPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["statut", "formation", "candidat", "partenaire"]
    search_fields = ["candidat__nom", "candidat__prenom", "partenaire__nom"]
    ordering_fields = ["date_appairage", "statut"]

    def get_serializer_class(self):
        if self.action == "list":
            return AppairageListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return AppairageCreateUpdateSerializer
        return AppairageSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        instance.set_user(self.request.user)
        instance.save()

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.set_user(self.request.user)
        instance.save()

    @action(detail=False, methods=["get"], url_path="meta")
    def meta(self, request):
        return Response(AppairageMetaSerializer().data)

    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="appairages.csv"'

        writer = csv.writer(response)
        writer.writerow(["Candidat", "Partenaire", "Formation", "Statut", "Date"])

        for appairage in self.filter_queryset(self.get_queryset()):
            writer.writerow([
                appairage.candidat.nom_complet,
                appairage.partenaire.nom,
                appairage.formation.nom if appairage.formation else "",
                appairage.get_statut_display(),
                appairage.date_appairage.strftime("%d/%m/%Y %H:%M")
            ])

        return response

    @action(detail=False, methods=["get"], url_path="export-pdf")
    def export_pdf(self, request):
        appairages = self.filter_queryset(self.get_queryset())
        html_string = render_to_string("exports/appairages_pdf.html", {"appairages": appairages})
        html = HTML(string=html_string)
        pdf = html.write_pdf()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="appairages.pdf"'
        return response


class HistoriqueAppairageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HistoriqueAppairage.objects.all().select_related(
        "appairage", "auteur"
    )
    serializer_class = HistoriqueAppairageSerializer
    permission_classes = [IsStaffOrAbove]
    pagination_class = RapAppPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["appairage", "statut", "auteur"]
    search_fields = ["appairage__candidat__nom", "appairage__partenaire__nom", "auteur__first_name", "auteur__last_name"]
    ordering_fields = ["date"]
