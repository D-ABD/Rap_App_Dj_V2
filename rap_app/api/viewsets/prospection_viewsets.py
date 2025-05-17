# Nettoyage complet des ViewSets avec pagination enrichie et tests compatibles

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiParameter
)

from ...api.paginations import RapAppPagination
from ...models.prospection import Prospection, HistoriqueProspection, ProspectionChoices
from ..serializers.prospection_serializers import (
    ProspectionSerializer,
    HistoriqueProspectionSerializer,
    ChangerStatutSerializer,
)
from ..permissions import IsOwnerOrStaffOrAbove
from ...models.logs import LogUtilisateur


@extend_schema_view(
    list=extend_schema(
        summary="Liste des prospections",
        tags=["Prospections"],
        parameters=[
            OpenApiParameter(name="statut", type=str, description="Filtrer par statut"),
            OpenApiParameter(name="formation", type=int, description="ID de la formation"),
            OpenApiParameter(name="partenaire", type=int, description="ID du partenaire"),
            OpenApiParameter(name="search", type=str, description="Recherche dans les commentaires ou le nom du partenaire")
        ],
        responses={200: OpenApiResponse(response=ProspectionSerializer)}
    ),
    retrieve=extend_schema(summary="Détail d'une prospection", tags=["Prospections"]),
    create=extend_schema(summary="Créer une prospection", tags=["Prospections"]),
    update=extend_schema(summary="Mettre à jour une prospection", tags=["Prospections"]),
    destroy=extend_schema(summary="Annuler une prospection", tags=["Prospections"])
)

class ProspectionViewSet(viewsets.ModelViewSet):
    queryset = Prospection.objects.select_related("partenaire", "formation")
    serializer_class = ProspectionSerializer
    permission_classes = [IsOwnerOrStaffOrAbove]
    pagination_class = RapAppPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["statut", "formation", "partenaire"]
    search_fields = ["commentaire", "partenaire__nom"]
    ordering_fields = ["date_prospection", "created_at"]
    ordering = ["-date_prospection"]

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_CREATE,
            user=self.request.user,
            details="Création d’une prospection"
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_UPDATE,
            user=self.request.user,
            details="Mise à jour d’une prospection"
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        ancien_statut = instance.statut
        instance.statut = ProspectionChoices.STATUT_ANNULEE
        instance.save(user=request.user)

        HistoriqueProspection.objects.create(
            prospection=instance,
            ancien_statut=ancien_statut,
            nouveau_statut=ProspectionChoices.STATUT_ANNULEE,
            type_contact=instance.type_contact,
            commentaire="Annulation de la prospection",
            resultat="Annulée par l'utilisateur",
            created_by=request.user
        )

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_DELETE,
            user=request.user,
            details="Suppression logique de la prospection"
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "success": True,
            "message": "Prospection récupérée avec succès.",
            "data": serializer.data
        })

    @action(detail=True, methods=["post"], url_path="changer-statut")
    @extend_schema(
        summary="Changer le statut d’une prospection",
        tags=["Prospections"],
        request=ChangerStatutSerializer,
        responses={200: OpenApiResponse(response=ProspectionSerializer)}
    )
    def changer_statut(self, request, pk=None):
        serializer = ChangerStatutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        nouveau_statut = serializer.validated_data["statut"]

        instance = self.get_object()
        ancien_statut = instance.statut
        instance.statut = nouveau_statut
        instance.save(user=request.user)

        HistoriqueProspection.objects.create(
            prospection=instance,
            ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut,
            type_contact=instance.type_contact,
            commentaire="Changement de statut",
            resultat="Statut modifié manuellement",
            created_by=request.user
        )

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_UPDATE,
            user=request.user,
            details=f"Changement de statut : {ancien_statut} → {nouveau_statut}"
        )

        return Response({
            "success": True,
            "message": "Statut mis à jour avec succès.",
            "data": self.get_serializer(instance).data
        })

    @action(detail=True, methods=["get"], url_path="historiques")
    @extend_schema(
        summary="Lister l’historique d’une prospection",
        tags=["Prospections"],
        responses={200: OpenApiResponse(response=HistoriqueProspectionSerializer(many=True))}
    )
    def historiques(self, request, pk=None):
        instance = self.get_object()
        historiques = instance.historiques.order_by("-date_modification")
        serializer = HistoriqueProspectionSerializer(historiques, many=True)
        return Response({
            "success": True,
            "message": "Historique chargé avec succès.",
            "data": serializer.data
        })


@extend_schema_view(
    list=extend_schema(
        summary="Lister les historiques de prospection",
        tags=["HistoriquesProspection"],
        responses={200: OpenApiResponse(response=HistoriqueProspectionSerializer(many=True))}
    ),
    retrieve=extend_schema(
        summary="Détail d’un historique de prospection",
        tags=["HistoriquesProspection"],
        responses={200: OpenApiResponse(response=HistoriqueProspectionSerializer)}
    )
)
class HistoriqueProspectionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = HistoriqueProspectionSerializer
    permission_classes = [IsOwnerOrStaffOrAbove]
    pagination_class = RapAppPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = ["date_modification", "prochain_contact"]
    ordering = ["-date_modification"]
    search_fields = ["commentaire", "resultat"]
    filterset_fields = ["prospection", "nouveau_statut", "type_contact"]

    def get_queryset(self):
        return HistoriqueProspection.objects.select_related("prospection", "created_by")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "success": True,
            "message": "Historique récupéré avec succès.",
            "data": serializer.data
        })
