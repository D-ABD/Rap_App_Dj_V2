# Imports Django & DRF
from rest_framework import viewsets, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from ...models.centres import Centre
from ...models.jury import SuiviJury

# Permissions, pagination, log
from ..permissions import IsStaffOrAbove
from ..paginations import RapAppPagination
from ...models.logs import LogUtilisateur

# Serializers
from ..serializers.jury_serializers import SuiviJurySerializer


@extend_schema(tags=["Suivi Jury"])
class SuiviJuryViewSet(viewsets.ModelViewSet):
    queryset = SuiviJury.objects.filter(is_active=True)
    serializer_class = SuiviJurySerializer
    permission_classes = [IsStaffOrAbove]
    pagination_class = RapAppPagination

    @extend_schema(summary="Créer un suivi jury")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_CREATE,
            user=request.user,
            details="Création d’un suivi de jury",
        )
        return Response(
            {
                "success": True,
                "message": "Suivi jury créé avec succès.",
                "data": instance.to_serializable_dict(),
            },
            status=status.HTTP_201_CREATED,
        )

    def perform_create(self, serializer):
        centre = Centre.objects.get(pk=self.request.data.get("centre_id"))
        serializer.save(created_by=self.request.user, centre=centre)

    @extend_schema(summary="Mettre à jour un suivi jury")
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        instance = serializer.instance

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_UPDATE,
            user=request.user,
            details="Mise à jour d’un suivi de jury",
        )
        return Response(
            {
                "success": True,
                "message": "Suivi jury mis à jour avec succès.",
                "data": instance.to_serializable_dict(),
            }
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @extend_schema(summary="Supprimer logiquement un suivi jury")
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_DELETE,
            user=request.user,
            details="Suppression logique d’un suivi de jury",
        )
        return Response(
            {
                "success": True,
                "message": "Suivi jury supprimé avec succès.",
                "data": None,
            },
            status=status.HTTP_204_NO_CONTENT,
        )

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.updated_by = self.request.user
        instance.save()
 