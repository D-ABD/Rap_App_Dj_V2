# viewsets/typeoffre_viewsets.py

from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from ...api.serializers.types_offre_serializers import TypeOffreChoiceSerializer, TypeOffreSerializer
from ...models.types_offre import TypeOffre

from ...models.logs import LogUtilisateur
from ..permissions import ReadWriteAdminReadStaff
from ..paginations import RapAppPagination


@extend_schema_view(
    list=extend_schema(
        summary="📄 Liste des types d'offres",
        description="Retourne la liste paginée des types d'offres disponibles.",
        tags=["TypesOffre"],
        responses={200: OpenApiResponse(response=TypeOffreSerializer)},
    ),
    retrieve=extend_schema(
        summary="🔍 Détail d’un type d’offre",
        description="Retourne les informations détaillées pour un type d'offre.",
        tags=["TypesOffre"],
        responses={200: OpenApiResponse(response=TypeOffreSerializer)},
    ),
    create=extend_schema(
        summary="➕ Créer un type d’offre",
        description="Ajoute un nouveau type d’offre, standard ou personnalisé.",
        tags=["TypesOffre"],
        responses={201: OpenApiResponse(description="Création réussie.")},
    ),
    update=extend_schema(
        summary="✏️ Modifier un type d’offre",
        description="Met à jour les données d’un type d’offre existant.",
        tags=["TypesOffre"],
        responses={200: OpenApiResponse(description="Mise à jour réussie.")},
    ),
    destroy=extend_schema(
        summary="🗑️ Supprimer un type d’offre",
        description="Suppression logique d’un type d’offre (désactivation).",
        tags=["TypesOffre"],
        responses={204: OpenApiResponse(description="Suppression réussie.")},
    ),
)
class TypeOffreViewSet(viewsets.ModelViewSet):
    """
    🎯 ViewSet complet pour les types d'offres.
    CRUD + journalisation + pagination + permissions + Swagger.
    """
    queryset = TypeOffre.objects.all().order_by("nom")
    serializer_class = TypeOffreSerializer
    permission_classes = [ReadWriteAdminReadStaff]
    pagination_class = RapAppPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ["nom", "created_at"]
    search_fields = ["nom", "autre"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_CREATE,
            user=request.user,
            details=f"Création du type d'offre : {instance}"
        )

        return Response({
            "success": True,
            "message": "Type d'offre créé avec succès.",
            "data": self.get_serializer(instance).data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        LogUtilisateur.log_action(
            instance=updated_instance,
            action=LogUtilisateur.ACTION_UPDATE,
            user=request.user,
            details=f"Mise à jour du type d'offre : {updated_instance}"
        )

        return Response({
            "success": True,
            "message": "Type d'offre mis à jour avec succès.",
            "data": self.get_serializer(updated_instance).data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()  # ✅ Suppression réelle
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

# views/typeoffre_viewsets.py


    @extend_schema(
        summary="📋 Liste des choix possibles de types d'offres",
        description="Retourne les valeurs possibles pour `nom`, avec libellé et couleur par défaut.",
        tags=["TypesOffre"],
        responses={200: OpenApiResponse(
            response=TypeOffreChoiceSerializer(many=True),
            description="Liste des types d'offres disponibles"
        )}
    )
    @action(detail=False, methods=["get"], url_path="choices", url_name="choices")
    def get_choices(self, request):
        """
        Retourne tous les types d'offres standards (hors base de données),
        avec leur libellé et couleur par défaut.
        """
        data = [
            {
                "value": key,
                "label": label,
                "default_color": TypeOffre.COULEURS_PAR_DEFAUT.get(key, "#6c757d")
            }
            for key, label in TypeOffre.TYPE_OFFRE_CHOICES
        ]
        return Response({
            "success": True,
            "message": "Liste des types d'offres prédéfinis.",
            "data": data
        })
