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
    ProspectionChoiceListSerializer,
    ProspectionSerializer,
    ProspectionDetailSerializer,
    HistoriqueProspectionSerializer,
    ChangerStatutSerializer,
)
from ..permissions import IsOwnerOrStaffOrAbove
from ...models.logs import LogUtilisateur


@extend_schema_view(
    list=extend_schema(
        summary="📋 Liste des prospections",
        tags=["Prospections"],
        parameters=[
            OpenApiParameter(name="statut", type=str, description="Filtrer par statut"),
            OpenApiParameter(name="formation", type=int, description="Filtrer par formation"),
            OpenApiParameter(name="partenaire", type=int, description="Filtrer par partenaire"),
            OpenApiParameter(name="search", type=str, description="Recherche dans le commentaire ou le nom du partenaire")
        ],
        responses={200: OpenApiResponse(response=ProspectionSerializer)}
    ),
    retrieve=extend_schema(summary="🔍 Détail d’une prospection", tags=["Prospections"]),
    create=extend_schema(summary="➕ Créer une prospection", tags=["Prospections"]),
    update=extend_schema(summary="✏️ Modifier une prospection", tags=["Prospections"]),
    destroy=extend_schema(summary="🗑️ Annuler une prospection", tags=["Prospections"])
)
class ProspectionViewSet(viewsets.ModelViewSet):
    """
    API permettant de gérer les prospections (création, mise à jour, annulation, changement de statut...).
    """
    queryset = Prospection.objects.select_related("partenaire", "formation")
    serializer_class = ProspectionSerializer
    permission_classes = [IsOwnerOrStaffOrAbove]
    pagination_class = RapAppPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["statut", "formation", "partenaire"]
    search_fields = ["commentaire", "partenaire__nom"]
    ordering_fields = ["date_prospection", "created_at"]
    ordering = ["-date_prospection"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProspectionDetailSerializer
        return ProspectionSerializer

    def perform_create(self, serializer):
        """
        Lors de la création d’une prospection, l'utilisateur est défini comme `created_by`.
        """
        instance = serializer.save(created_by=self.request.user)
        LogUtilisateur.log_action(instance, LogUtilisateur.ACTION_CREATE, self.request.user, "Création d’une prospection")

    def perform_update(self, serializer):
        instance = serializer.save()
        LogUtilisateur.log_action(instance, LogUtilisateur.ACTION_UPDATE, self.request.user, "Mise à jour d’une prospection")

    def destroy(self, request, *args, **kwargs):
        """
        Suppression logique d’une prospection (statut = annulée + historique).
        """
        instance = self.get_object()
        ancien_statut = instance.statut
        instance.statut = ProspectionChoices.STATUT_ANNULEE
        instance.save(user=request.user)

        HistoriqueProspection.objects.create(
            prospection=instance,
            ancien_statut=ancien_statut,
            nouveau_statut=ProspectionChoices.STATUT_ANNULEE,
            type_prospection=instance.type_prospection,
            commentaire="Annulation de la prospection",
            resultat="Annulée par l'utilisateur",
            created_by=request.user
        )

        LogUtilisateur.log_action(instance, LogUtilisateur.ACTION_DELETE, request.user, "Suppression logique de la prospection")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="changer-statut")
    @extend_schema(
        summary="🔄 Changer le statut d’une prospection",
        tags=["Prospections"],
        request=ChangerStatutSerializer,
        responses={200: OpenApiResponse(response=ProspectionSerializer)}
    )
    def changer_statut(self, request, pk=None):
        """
        Permet de changer le statut d’une prospection (et enregistre un historique).
        """
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
            type_prospection=instance.type_prospection,
            commentaire="Changement de statut",
            resultat="Statut modifié manuellement",
            created_by=request.user
        )

        LogUtilisateur.log_action(
            instance,
            LogUtilisateur.ACTION_UPDATE,
            request.user,
            f"Changement de statut : {ancien_statut} → {nouveau_statut}"
        )

        return Response({
            "success": True,
            "message": "Statut mis à jour avec succès.",
            "data": self.get_serializer(instance).data
        })

    @action(detail=True, methods=["get"], url_path="historiques")
    @extend_schema(
        summary="📜 Voir l’historique d’une prospection",
        tags=["Prospections"],
        responses={200: OpenApiResponse(response=HistoriqueProspectionSerializer(many=True))}
    )
    def historiques(self, request, pk=None):
        """
        Retourne l’historique d’une prospection donnée.
        """
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
        summary="📜 Liste des historiques de prospection",
        tags=["HistoriquesProspection"],
        responses={200: OpenApiResponse(response=HistoriqueProspectionSerializer(many=True))}
    ),
    retrieve=extend_schema(
        summary="🔎 Détail d’un historique",
        tags=["HistoriquesProspection"],
        responses={200: OpenApiResponse(response=HistoriqueProspectionSerializer)}
    )
)
class HistoriqueProspectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet en lecture seule pour consulter les historiques de prospection.
    """
    serializer_class = HistoriqueProspectionSerializer
    permission_classes = [IsOwnerOrStaffOrAbove]
    pagination_class = RapAppPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = ["date_modification", "prochain_contact"]
    ordering = ["-date_modification"]
    search_fields = ["commentaire", "resultat"]
    filterset_fields = ["prospection", "nouveau_statut", "type_prospection"]

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

    @action(detail=False, methods=["get"], url_path="choices", url_name="choices")
    @extend_schema(
        summary="📚 Choix disponibles (statut, objectif, motif, type, moyen)",
        description="Retourne les listes de choix pour tous les champs sélectionnables.",
        tags=["Prospections"],
        responses={200: OpenApiResponse(response=ProspectionChoiceListSerializer)}
    )
    def get_choices(self, request):
        """
        Retourne les choix possibles pour tous les champs sélectionnables dans une prospection.
        """
        def format_choices(choices):
            return [{"value": key, "label": str(label)} for key, label in choices]

        data = {
            "statut": format_choices(ProspectionChoices.PROSPECTION_STATUS_CHOICES),
            "objectif": format_choices(ProspectionChoices.PROSPECTION_OBJECTIF_CHOICES),
            "motif": format_choices(ProspectionChoices.PROSPECTION_MOTIF_CHOICES),
            "type_prospection": format_choices(ProspectionChoices.TYPE_PROSPECTION_CHOICES),
            "moyen_contact": format_choices(ProspectionChoices.MOYEN_CONTACT_CHOICES),
        }

        return Response({
            "success": True,
            "message": "Choix disponibles pour les prospections",
            "data": data
        })
