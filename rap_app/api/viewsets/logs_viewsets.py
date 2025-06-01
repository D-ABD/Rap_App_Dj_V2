from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from rest_framework.views import APIView

from ...models.logs import LogUtilisateur
from ...api.serializers.logs_serializers import LogChoicesSerializer, LogUtilisateurSerializer
from ...api.permissions import IsStaffOrAbove
from ...api.paginations import RapAppPagination


@extend_schema_view(
    list=extend_schema(
        summary="Liste des logs utilisateur",
        description="Affiche tous les logs enregistrés (lecture seule, paginée).",
        tags=["Logs"],
        responses={200: OpenApiResponse(response=LogUtilisateurSerializer)},
    ),
    retrieve=extend_schema(
        summary="Détail d’un log",
        description="Affiche les détails d’un log utilisateur.",
        tags=["Logs"],
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



@extend_schema(
    methods=["GET"],
    responses={200: LogChoicesSerializer},
    description="Retourne la liste des actions possibles enregistrées dans les logs utilisateur."
)
class LogChoicesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        label_map = {
            LogUtilisateur.ACTION_CREATE: "Création",
            LogUtilisateur.ACTION_UPDATE: "Modification",
            LogUtilisateur.ACTION_DELETE: "Suppression",
            LogUtilisateur.ACTION_VIEW: "Consultation",
            LogUtilisateur.ACTION_LOGIN: "Connexion",
            LogUtilisateur.ACTION_LOGOUT: "Déconnexion",
            LogUtilisateur.ACTION_EXPORT: "Export",
            LogUtilisateur.ACTION_IMPORT: "Import",
        }

        data = {
            "actions": [
                {"value": k, "label": v}
                for k, v in label_map.items()
            ]
        }
        return Response(data)
