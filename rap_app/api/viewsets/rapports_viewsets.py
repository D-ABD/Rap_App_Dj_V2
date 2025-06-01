from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from ...models.rapports import Rapport
from ...api.serializers.rapports_serializers import RapportChoiceGroupSerializer, RapportSerializer
from ...api.permissions import IsStaffOrAbove
from ...api.paginations import RapAppPagination
from ...models.logs import LogUtilisateur


@extend_schema_view(
    list=extend_schema(
        summary="📊 Liste des rapports",
        description="Affiche la liste paginée des rapports générés.",
        tags=["Rapports"],
        responses={200: OpenApiResponse(response=RapportSerializer)},
    ),
    retrieve=extend_schema(
        summary="📄 Détail d’un rapport",
        description="Récupère les détails complets d’un rapport.",
        tags=["Rapports"],
        responses={200: OpenApiResponse(response=RapportSerializer)},
    ),
    create=extend_schema(
        summary="➕ Créer un rapport",
        description="Crée un nouveau rapport système ou manuel.",
        tags=["Rapports"],
        responses={201: OpenApiResponse(description="Rapport créé avec succès.")},
    ),
    update=extend_schema(
        summary="✏️ Modifier un rapport",
        description="Met à jour les champs d’un rapport existant.",
        tags=["Rapports"],
        responses={200: OpenApiResponse(description="Rapport mis à jour avec succès.")},
    ),
    destroy=extend_schema(
        summary="🗑️ Supprimer un rapport",
        description="Supprime logiquement un rapport (désactivation).",
        tags=["Rapports"],
        responses={204: OpenApiResponse(description="Rapport supprimé avec succès.")},
    ),
)
class RapportViewSet(viewsets.ModelViewSet):
    """
    📊 ViewSet complet pour les rapports.
    CRUD + pagination + journalisation + sécurité
    """
    queryset = Rapport.objects.filter(is_active=True)
    serializer_class = RapportSerializer
    permission_classes = [IsStaffOrAbove]
    pagination_class = RapAppPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nom", "type_rapport", "periode"]
    ordering_fields = ["created_at", "date_debut", "date_fin"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_CREATE,
            user=self.request.user,
            details="Création d’un rapport"
        )

    def perform_update(self, serializer):
        instance = serializer.save(updated_by=self.request.user)
        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_UPDATE,
            user=self.request.user,
            details="Modification d’un rapport"
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=["is_active"])
        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_DELETE,
            user=request.user,
            details="Suppression logique du rapport"
        )
        return Response({
            "success": True,
            "message": "Rapport supprimé avec succès.",
            "data": None
        }, status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "success": True,
            "message": "Rapport créé avec succès.",
            "data": serializer.instance.to_serializable_dict()
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "success": True,
            "message": "Rapport mis à jour avec succès.",
            "data": serializer.instance.to_serializable_dict()
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "success": True,
            "message": "Rapport récupéré avec succès.",
            "data": serializer.instance.to_serializable_dict()
        })

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Liste des rapports récupérée avec succès.",
            "data": serializer.data
        })
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse


class RapportChoicesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Liste des choix possibles pour les rapports",
        description="Retourne les choix disponibles pour les types de rapports, périodicité et formats.",
        responses={200: OpenApiResponse(response=RapportChoiceGroupSerializer)},
        tags=["Rapports"]
    )
    def get(self, request):
        def serialize_choices(choices):
            return [{"value": k, "label": v} for k, v in choices]

        return Response({
            "type_rapport": serialize_choices(Rapport.TYPE_CHOICES),
            "periode": serialize_choices(Rapport.PERIODE_CHOICES),
            "format": serialize_choices(Rapport.FORMAT_CHOICES),
        })
