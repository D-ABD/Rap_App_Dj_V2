from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiResponse, extend_schema_view, OpenApiParameter

from ..permissions import IsStaffOrAbove
from ..paginations import RapAppPagination
from ..serializers.prepacomp_serializers import SemaineSerializer, PrepaCompGlobalSerializer
from ...models.prepacomp import Semaine, PrepaCompGlobal
from ...models.logs import LogUtilisateur


@extend_schema_view(
    list=extend_schema(summary="Lister les semaines", description="Retourne toutes les semaines avec pagination."),
    retrieve=extend_schema(summary="Détail d'une semaine"),
    create=extend_schema(summary="Créer une semaine"),
    update=extend_schema(summary="Mettre à jour une semaine"),
    destroy=extend_schema(summary="Supprimer une semaine"),
)
class SemaineViewSet(viewsets.ModelViewSet):
    queryset = Semaine.objects.filter(is_active=True).select_related("centre")
    serializer_class = SemaineSerializer
    permission_classes = [IsStaffOrAbove]
    pagination_class = RapAppPagination

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(created_by=request.user)

        LogUtilisateur.log_action(
            instance=instance,
            user=request.user,
            action=LogUtilisateur.ACTION_CREATE,
            details="Création d'une semaine"
        )

        return Response({
            "success": True,
            "message": "Semaine créée avec succès.",
            "data": instance.to_serializable_dict()
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)

        LogUtilisateur.log_action(
            instance=instance,
            user=request.user,
            action=LogUtilisateur.ACTION_UPDATE,
            details="Modification d'une semaine"
        )

        return Response({
            "success": True,
            "message": "Semaine mise à jour avec succès.",
            "data": instance.to_serializable_dict()
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=["is_active"])

        LogUtilisateur.log_action(
            instance=instance,
            user=request.user,
            action=LogUtilisateur.ACTION_DELETE,
            details="Suppression logique d'une semaine"
        )

        return Response({
            "success": True,
            "message": "Semaine supprimée avec succès.",
            "data": None
        }, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="courante")
    @extend_schema(
        summary="Semaine courante",
        description="Retourne la semaine en cours pour un centre donné.",
        parameters=[
            OpenApiParameter(name="centre_id", required=True, type=int, location=OpenApiParameter.QUERY,
                             description="ID du centre concerné")
        ],
        responses={200: OpenApiResponse(description="Semaine courante trouvée")}
    )
    def courante(self, request):
        centre_id = request.query_params.get("centre_id")
        if not centre_id:
            return Response({
                "success": False,
                "message": "Paramètre 'centre_id' requis.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        semaine = Semaine.custom.semaine_courante(centre_id)
        if semaine:
            return Response({
                "success": True,
                "message": "Semaine courante trouvée.",
                "data": semaine.to_serializable_dict()
            })
        return Response({
            "success": False,
            "message": "Aucune semaine courante trouvée.",
            "data": None
        }, status=status.HTTP_404_NOT_FOUND)


@extend_schema_view(
    list=extend_schema(summary="Lister les bilans globaux"),
    retrieve=extend_schema(summary="Détail d’un bilan global"),
    create=extend_schema(summary="Créer un bilan global"),
    update=extend_schema(summary="Modifier un bilan global"),
    destroy=extend_schema(summary="Supprimer un bilan global")
)
class PrepaCompGlobalViewSet(viewsets.ModelViewSet):
    queryset = PrepaCompGlobal.objects.filter(is_active=True).select_related("centre")
    serializer_class = PrepaCompGlobalSerializer
    permission_classes = [IsStaffOrAbove]
    pagination_class = RapAppPagination

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(created_by=request.user)

        LogUtilisateur.log_action(
            instance=instance,
            user=request.user,
            action=LogUtilisateur.ACTION_CREATE,
            details="Création d'un bilan PrepaCompGlobal"
        )

        return Response({
            "success": True,
            "message": "Bilan PrepaCompGlobal créé avec succès.",
            "data": instance.to_serializable_dict()
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)

        LogUtilisateur.log_action(
            instance=instance,
            user=request.user,
            action=LogUtilisateur.ACTION_UPDATE,
            details="Modification d'un bilan PrepaCompGlobal"
        )

        return Response({
            "success": True,
            "message": "Bilan PrepaCompGlobal mis à jour avec succès.",
            "data": instance.to_serializable_dict()
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=["is_active"])

        LogUtilisateur.log_action(
            instance=instance,
            user=request.user,
            action=LogUtilisateur.ACTION_DELETE,
            details="Suppression logique d'un bilan PrepaCompGlobal"
        )

        return Response({
            "success": True,
            "message": "Bilan supprimé avec succès.",
            "data": None
        }, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="par-centre")
    @extend_schema(
        summary="Filtrer les bilans par centre et année",
        parameters=[
            OpenApiParameter(name="centre_id", required=True, type=int, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="annee", required=False, type=int, location=OpenApiParameter.QUERY),
        ],
        responses={200: OpenApiResponse(description="Liste des bilans filtrés")}
    )
    def par_centre(self, request):
        centre_id = request.query_params.get("centre_id")
        annee = request.query_params.get("annee")

        if not centre_id:
            return Response({
                "success": False,
                "message": "Le paramètre 'centre_id' est requis.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.queryset.filter(centre_id=centre_id)
        if annee:
            queryset = queryset.filter(annee=annee)

        page = self.paginate_queryset(queryset)
        data = [obj.to_serializable_dict() for obj in page] if page else [obj.to_serializable_dict() for obj in queryset]
        return self.get_paginated_response(data)
