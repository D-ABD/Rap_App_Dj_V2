from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from ...models.commentaires import Commentaire
from ...models.logs import LogUtilisateur
from ...api.serializers.commentaires_serializers import CommentaireMetaSerializer, CommentaireSerializer
from ...api.paginations import RapAppPagination
from ...api.permissions import IsOwnerOrStaffOrAbove


@extend_schema(tags=["Commentaires"])
@extend_schema(
    summary="",
    responses={200: CommentaireSerializer},
)
class CommentaireViewSet(viewsets.ModelViewSet):
    queryset = Commentaire.objects.select_related("formation", "created_by").all()
    serializer_class = CommentaireSerializer
    pagination_class = RapAppPagination
    permission_classes = [IsOwnerOrStaffOrAbove]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["contenu", "formation__nom", "created_by__username"]
    ordering = ["-created_at"]

    @extend_schema(summary="Lister les commentaires actifs")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Récupérer un commentaire")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Créer un commentaire")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        commentaire = serializer.save()

        LogUtilisateur.log_action(
            instance=commentaire,
            action=LogUtilisateur.ACTION_CREATE,
            user=request.user,
            details=f"Création d'un commentaire pour la formation #{commentaire.formation_id}"
        )

        return Response({
            "success": True,
            "message": "Commentaire créé avec succès.",
            "data": commentaire.to_serializable_dict(include_full_content=True)
        }, status=status.HTTP_201_CREATED)

    @extend_schema(summary="Mettre à jour un commentaire")
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        commentaire = serializer.save()

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_UPDATE,
            user=request.user,
            details=f"Mise à jour du commentaire #{instance.pk}"
        )

        return Response({
            "success": True,
            "message": "Commentaire mis à jour avec succès.",
            "data": commentaire.to_serializable_dict(include_full_content=True)
        }, status=status.HTTP_200_OK)

    @extend_schema(summary="Supprimer un commentaire")
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_DELETE,
            user=request.user,
            details=f"Suppression du commentaire #{instance.pk}"
        )

        return Response({
            "success": True,
            "message": "Commentaire supprimé avec succès.",
            "data": None
        }, status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Récupérer les statistiques de saturation des commentaires",
        responses={
            200: OpenApiResponse(
                description="Données de saturation pour une formation",
                response=None  # ou un serializer custom si tu veux
            )
        }
    )
    @action(detail=False, methods=["get"], url_path="saturation-stats")
    def saturation_stats(self, request):
        formation_id = request.query_params.get("formation_id")
        stats = Commentaire.get_saturation_stats(formation_id=formation_id)

        return Response({
            "success": True,
            "message": "Statistiques de saturation récupérées avec succès.",
            "data": stats
        })


class CommentaireMetaView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        serializer = CommentaireMetaSerializer()
        return Response(serializer.data)
