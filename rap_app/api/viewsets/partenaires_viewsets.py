# viewsets/partenaire_viewsets.py

from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from ...api.permissions import IsOwnerOrStaffOrAbove

from ...models.partenaires import Partenaire
from ..serializers.partenaires_serializers import PartenaireSerializer
from ...models.logs import LogUtilisateur


@extend_schema_view(
    list=extend_schema(summary="Lister les partenaires", responses={200: OpenApiResponse(response=PartenaireSerializer)}),
    retrieve=extend_schema(summary="Détail d’un partenaire", responses={200: OpenApiResponse(response=PartenaireSerializer)}),
    create=extend_schema(summary="Créer un partenaire", responses={201: OpenApiResponse(description="Création réussie")}),
    update=extend_schema(summary="Modifier un partenaire", responses={200: OpenApiResponse(description="Mise à jour réussie")}),
    destroy=extend_schema(summary="Supprimer un partenaire", responses={204: OpenApiResponse(description="Suppression réussie")}),
)
class PartenaireViewSet(viewsets.ModelViewSet):
    """
    🔁 ViewSet CRUD complet pour les partenaires
    """
    queryset = Partenaire.objects.filter(is_active=True).order_by("nom")
    serializer_class = PartenaireSerializer
    permission_classes = [IsOwnerOrStaffOrAbove]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nom", "secteur_activite", "city", "contact_nom"]
    ordering_fields = ["nom", "created_at"]
    ordering = ["nom"]

    def perform_create(self, serializer):
        instance = serializer.save()
        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_CREATE,
            user=self.request.user,
            details="Création d'un partenaire"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_CREATE,
            user=request.user,
            details="Création d'un partenaire"
        )

        return Response({
            "success": True,
            "message": "Partenaire créé avec succès.",
            "data": instance.to_serializable_dict()
        }, status=status.HTTP_201_CREATED)


    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        result = serializer.update(instance, serializer.validated_data)

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_UPDATE,
            user=request.user,
            details="Modification d'un partenaire"
        )

        return Response(result, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_DELETE,
            user=request.user,
            details="Suppression logique d'un partenaire"
        )

        return Response({
            "success": True,
            "message": "Partenaire supprimé avec succès.",
            "data": None
        }, status=status.HTTP_204_NO_CONTENT)
