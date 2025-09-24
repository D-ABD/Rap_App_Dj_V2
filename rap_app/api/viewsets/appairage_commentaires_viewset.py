from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from ..serializers.commentaires_appairage_serializers import (
    CommentaireAppairageSerializer,
    CommentaireAppairageWriteSerializer,
)
from ...models.commentaires_appairage import CommentaireAppairage
from ...models.logs import LogUtilisateur
from ..paginations import RapAppPagination
from ..permissions import IsStaffOrAbove


@extend_schema(tags=["Commentaires Appairages"])
class CommentaireAppairageViewSet(viewsets.ModelViewSet):
    """
    API CRUD pour les commentaires liés aux appairages.
    Accès réservé aux utilisateurs staff/admin/superadmin.
    """

    queryset = CommentaireAppairage.objects.select_related(
        "appairage",
        "appairage__candidat",
        "appairage__partenaire",
        "appairage__formation",
        "created_by",
    ).all()
    pagination_class = RapAppPagination
    permission_classes = [IsStaffOrAbove]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "body",
        "created_by__username",
        "created_by__email",
        "appairage__candidat__nom",
        "appairage__candidat__prenom",
        "appairage__partenaire__nom",
    ]
    ordering = ["-created_at"]

    # ---------------- Queryset dynamique ----------------
    def get_queryset(self):
        qs = super().get_queryset()
        appairage_id = self.request.query_params.get("appairage")
        if appairage_id:
            qs = qs.filter(appairage_id=appairage_id)
        return qs

    # ---------------- Serializer dynamique ----------------
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CommentaireAppairageWriteSerializer
        return CommentaireAppairageSerializer
    
    # ---------------- CRUD ----------------
    @extend_schema(summary="Lister les commentaires d’appairage")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Récupérer un commentaire d’appairage")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Créer un commentaire d’appairage")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        commentaire = serializer.save(created_by=request.user)

        LogUtilisateur.log_action(
            instance=commentaire,
            action=LogUtilisateur.ACTION_CREATE,
            user=request.user,
            details=f"Création d’un commentaire pour l’appairage #{commentaire.appairage_id}",
        )

        # réponse enrichie via serializer de lecture
        read_data = CommentaireAppairageSerializer(commentaire, context={"request": request}).data
        return Response(
            {"success": True, "message": "Commentaire d’appairage créé avec succès.", "data": read_data},
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(summary="Mettre à jour un commentaire d’appairage")
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        commentaire = serializer.save(updated_by=request.user)

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_UPDATE,
            user=request.user,
            details=f"Mise à jour du commentaire d’appairage #{instance.pk}",
        )

        read_data = CommentaireAppairageSerializer(commentaire, context={"request": request}).data
        return Response(
            {"success": True, "message": "Commentaire d’appairage mis à jour avec succès.", "data": read_data},
            status=status.HTTP_200_OK,
        )

    @extend_schema(summary="Supprimer un commentaire d’appairage")
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        pk = instance.pk
        instance.delete()

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_DELETE,
            user=request.user,
            details=f"Suppression du commentaire d’appairage #{pk}",
        )

        return Response(
            {"success": True, "message": "Commentaire d’appairage supprimé avec succès.", "data": None},
            status=status.HTTP_204_NO_CONTENT,
        )
 