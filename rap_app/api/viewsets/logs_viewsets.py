from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from ...models.logs import LogUtilisateur
from ...api.serializers.logs_serializers import LogUtilisateurSerializer
from ...api.permissions import IsStaffOrAbove
from ...api.paginations import RapAppPagination


@extend_schema_view(
    list=extend_schema(
        summary="Liste des logs utilisateur",
        description="Affiche tous les logs enregistrés (lecture seule, paginée).",
        responses={200: OpenApiResponse(response=LogUtilisateurSerializer)},
    ),
    retrieve=extend_schema(
        summary="Détail d’un log",
        description="Affiche les détails d’un log utilisateur.",
        responses={200: OpenApiResponse(response=LogUtilisateurSerializer)},
    ),
)
class LogUtilisateurViewSet(viewsets.ReadOnlyModelViewSet):
    """
    📚 ViewSet en lecture seule pour consulter les logs utilisateur.
    Accès réservé aux membres du staff ou supérieur.
    """
    queryset = LogUtilisateur.objects.all()
    serializer_class = LogUtilisateurSerializer
    permission_classes = [IsAuthenticated, IsStaffOrAbove]
    pagination_class = RapAppPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["action", "details", "created_by__username"]
    ordering_fields = ["created_at", "action"]
    ordering = ["-created_at"]

    def list(self, request, *args, **kwargs):
        """
        📄 Liste paginée des logs utilisateur
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Liste des logs utilisateur.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """
        📄 Détail d’un log utilisateur
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "success": True,
            "message": "Log utilisateur récupéré avec succès.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
