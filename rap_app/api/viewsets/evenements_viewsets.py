import csv
import logging
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from ...services.evenements_export import csv_export_evenements

from ...models.evenements import Evenement
from ...api.serializers.evenements_serializers import EvenementSerializer
from ...api.paginations import RapAppPagination
from ...api.permissions import IsOwnerOrStaffOrAbove

logger = logging.getLogger("application.api")


@extend_schema(tags=["Événements"])
class EvenementViewSet(viewsets.ModelViewSet):
    """
    📆 ViewSet pour gérer les événements liés aux formations.
    - CRUD complet
    - Actions personnalisées : stats, export CSV
    - Permissions : IsOwnerOrStaffOrAbove
    - Pagination personnalisée : RapAppPagination
    """
    queryset = Evenement.objects.all().select_related("formation")
    serializer_class = EvenementSerializer
    permission_classes = [IsAuthenticated & IsOwnerOrStaffOrAbove]
    pagination_class = RapAppPagination

    @extend_schema(
        summary="📚 Lister les événements",
        tags=["Événements"],
        parameters=[
            OpenApiParameter("formation", int, description="ID de la formation"),
            OpenApiParameter("type_evenement", str, description="Type d'événement"),
            OpenApiParameter("date_min", str, description="Date minimale (YYYY-MM-DD)"),
            OpenApiParameter("date_max", str, description="Date maximale (YYYY-MM-DD)"),
        ],
        responses={200: OpenApiResponse(response=EvenementSerializer(many=True))}
    )
    def list(self, request, *args, **kwargs):
        formation = request.query_params.get("formation")
        type_evenement = request.query_params.get("type_evenement")
        date_min = request.query_params.get("date_min")
        date_max = request.query_params.get("date_max")

        queryset = self.queryset
        if formation:
            queryset = queryset.filter(formation_id=formation)
        if type_evenement:
            queryset = queryset.filter(type_evenement=type_evenement)
        if date_min:
            queryset = queryset.filter(event_date__gte=date_min)
        if date_max:
            queryset = queryset.filter(event_date__lte=date_max)

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page or queryset, many=True)
        return self.get_paginated_response(serializer.data) if page else Response(serializer.data)

    @extend_schema(
        summary="🧾 Exporter les événements au format CSV",
        tags=["Événements"],
        responses={
            200: OpenApiResponse(
                description="Fichier CSV contenant les événements",
                response="application/csv"
            )
        }
    )
    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request):
        response = csv_export_evenements(self.queryset)
        return response

    @extend_schema(
        summary="📊 Statistiques par type d'événement",
        tags=["Événements"],
        parameters=[
            OpenApiParameter("start", str, required=False, description="Date de début (YYYY-MM-DD)"),
            OpenApiParameter("end", str, required=False, description="Date de fin (YYYY-MM-DD)"),
        ],
        responses={
            200: OpenApiResponse(
                description="Dictionnaire des types d'événements avec leurs occurrences",
                response=None  # ou un serializer spécifique si tu veux
            )
        }
    )
    @action(detail=False, methods=["get"], url_path="stats-par-type")
    def stats_par_type(self, request):
        start_date = request.query_params.get("start")
        end_date = request.query_params.get("end")
        stats = Evenement.get_stats_by_type(start_date=start_date, end_date=end_date)
        return Response({"success": True, "data": stats})
