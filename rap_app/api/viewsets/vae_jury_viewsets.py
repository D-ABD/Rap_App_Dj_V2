# Imports Django & DRF
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from ...models.centres import Centre

# Permissions, pagination, log
from ...api.permissions import IsStaffOrAbove
from ...api.paginations import RapAppPagination
from ...models.logs import LogUtilisateur

# Modèles
from ...models.vae_jury import VAE, SuiviJury, HistoriqueStatutVAE

# Serializers
from ...api.serializers.vae_jury_serializers import (
    VAESerializer, SuiviJurySerializer,
    HistoriqueStatutVAESerializer, ChangerStatutVAESerializer
)
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
            details="Création d’un suivi de jury"
        )
        return Response({
            "success": True,
            "message": "Suivi jury créé avec succès.",
            "data": instance.to_serializable_dict()
        }, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        centre = Centre.objects.get(pk=self.request.data.get("centre_id"))
        serializer.save(created_by=self.request.user, centre=centre)

    @extend_schema(summary="Mettre à jour un suivi jury")
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        instance = serializer.instance

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_UPDATE,
            user=request.user,
            details="Mise à jour d’un suivi de jury"
        )
        return Response({
            "success": True,
            "message": "Suivi jury mis à jour avec succès.",
            "data": instance.to_serializable_dict()
        })
    
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
            details="Suppression logique d’un suivi de jury"
        )
        return Response({
            "success": True,
            "message": "Suivi jury supprimé avec succès.",
            "data": None
        }, status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.updated_by = self.request.user
        instance.save()


@extend_schema(tags=["VAE"])
class VAEViewSet(viewsets.ModelViewSet):
    """
    📝 ViewSet principal pour la gestion des VAE individuelles.
    """
    queryset = VAE.objects.filter(is_active=True)
    serializer_class = VAESerializer
    permission_classes = [IsStaffOrAbove]
    pagination_class = RapAppPagination

    @extend_schema(summary="Créer une VAE")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_CREATE,
            user=request.user,
            details="Création d’une VAE"
        )
        return Response({
            "success": True,
            "message": "VAE créée avec succès.",
            "data": instance.to_serializable_dict()
        }, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer):
        centre = Centre.objects.get(pk=self.request.data.get("centre_id"))
        serializer.save(created_by=self.request.user, centre=centre)


    @extend_schema(summary="Mettre à jour une VAE")
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        instance = serializer.instance

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_UPDATE,
            user=request.user,
            details="Mise à jour d’une VAE"
        )
        return Response({
            "success": True,
            "message": "VAE mise à jour avec succès.",
            "data": instance.to_serializable_dict()
        })

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


    @extend_schema(summary="Supprimer logiquement une VAE")
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_DELETE,
            user=request.user,
            details="Suppression logique d’une VAE"
        )

        return Response({
            "success": True,
            "message": "VAE supprimée avec succès.",
            "data": None
        }, status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.updated_by = self.request.user
        instance.save()


    @action(detail=True, methods=["post"], url_path="changer-statut")
    @extend_schema(
        summary="Changer le statut d’une VAE",
        tags=["VAE"],
        request=ChangerStatutVAESerializer,
        responses={200: OpenApiResponse(description="Statut changé avec succès.")}
    )
    def changer_statut(self, request, pk=None):
        """
        🔁 Change le statut d’une VAE avec historique.
        """
        instance = self.get_object()
        serializer = ChangerStatutVAESerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            instance.changer_statut(
                nouveau_statut=serializer.validated_data["statut"],
                date_effet=serializer.validated_data.get("date_changement_effectif"),
                commentaire=serializer.validated_data.get("commentaire", ""),
                user=request.user
            )
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e),
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "success": True,
            "message": "Statut changé avec succès.",
            "data": instance.to_serializable_dict()
        })

    @action(detail=True, methods=["get"], url_path="historiques")
    @extend_schema(
        summary="Récupérer l’historique des statuts d’une VAE",
        tags=["VAE"],
        responses={200: HistoriqueStatutVAESerializer(many=True)}
    )
    def historiques(self, request, pk=None):
        """
        📜 Liste des changements de statut pour une VAE donnée.
        """
        instance = self.get_object()
        historiques = instance.historique_statuts.all()
        serializer = HistoriqueStatutVAESerializer(historiques, many=True)
        return Response({
            "success": True,
            "message": "Historique des statuts récupéré avec succès.",
            "data": serializer.data
        })
    
@extend_schema(tags=["VAE - Historique Statut"])
class HistoriqueStatutVAEViewSet(viewsets.ReadOnlyModelViewSet):
    """
    📘 ViewSet en lecture seule pour l’historique des statuts de VAE.
    """
    queryset = HistoriqueStatutVAE.objects.all()
    serializer_class = HistoriqueStatutVAESerializer
    permission_classes = [IsStaffOrAbove]
    pagination_class = RapAppPagination
