# viewsets/typeoffre_viewsets.py

from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from ...api.serializers.types_offre_serializers import TypeOffreSerializer
from ...models.types_offre import TypeOffre

from ...models.logs import LogUtilisateur
from ..permissions import ReadWriteAdminReadStaff
from ..paginations import RapAppPagination


@extend_schema_view(
    list=extend_schema(
        summary="📄 Liste des types d'offres",
        description="Retourne la liste paginée des types d'offres disponibles.",
        responses={200: OpenApiResponse(response=TypeOffreSerializer)},
    ),
    retrieve=extend_schema(
        summary="🔍 Détail d’un type d’offre",
        description="Retourne les informations détaillées pour un type d'offre.",
        responses={200: OpenApiResponse(response=TypeOffreSerializer)},
    ),
    create=extend_schema(
        summary="➕ Créer un type d’offre",
        description="Ajoute un nouveau type d’offre, standard ou personnalisé.",
        responses={201: OpenApiResponse(description="Création réussie.")},
    ),
    update=extend_schema(
        summary="✏️ Modifier un type d’offre",
        description="Met à jour les données d’un type d’offre existant.",
        responses={200: OpenApiResponse(description="Mise à jour réussie.")},
    ),
    destroy=extend_schema(
        summary="🗑️ Supprimer un type d’offre",
        description="Suppression logique d’un type d’offre (désactivation).",
        responses={204: OpenApiResponse(description="Suppression réussie.")},
    ),
)
class TypeOffreViewSet(viewsets.ModelViewSet):
    """
    🎯 ViewSet complet pour les types d'offres.
    CRUD + journalisation + pagination + permissions + Swagger.
    """
    queryset = TypeOffre.objects.filter(is_active=True).order_by("nom")
    serializer_class = TypeOffreSerializer
    permission_classes = [ReadWriteAdminReadStaff]
    pagination_class = RapAppPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ["nom", "created_at"]
    search_fields = ["nom", "autre"]

    def perform_create(self, serializer):
        instance = serializer.save()
        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_CREATE,
            user=self.request.user,
            details=f"Création du type d'offre : {instance}"
        )

    def perform_update(self, serializer):
        instance = self.get_object()
        updated_instance = serializer.update(instance, serializer.validated_data)
        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_UPDATE,
            user=self.request.user,
            details=f"Mise à jour du type d'offre : {instance}"
        )
        return updated_instance

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_DELETE,
            user=request.user,
            details=f"Suppression logique du type d'offre : {instance}"
        )
        return Response({
            "success": True,
            "message": "Type d'offre supprimé avec succès.",
            "data": None
        }, status=status.HTTP_204_NO_CONTENT)
