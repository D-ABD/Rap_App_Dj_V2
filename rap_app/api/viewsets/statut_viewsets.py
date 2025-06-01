import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from rest_framework.decorators import action
from ...models.statut import get_default_color

from ...api.permissions import ReadOnlyOrAdmin
from ...models.statut import Statut
from ..serializers.statut_serializers import StatutChoiceSerializer, StatutSerializer

logger = logging.getLogger("application.statut")


@extend_schema_view(
    list=extend_schema(
        summary="Liste des statuts",
        description="Récupère tous les statuts actifs avec libellés, couleurs et badges HTML.",
        tags=["Statuts"],
        responses={200: OpenApiResponse(response=StatutSerializer)}
    ),
    retrieve=extend_schema(
        summary="Détail d’un statut",
        description="Retourne les détails d’un statut par ID.",
        tags=["Statuts"],
        responses={200: OpenApiResponse(response=StatutSerializer)}
    ),
    create=extend_schema(
        summary="Créer un statut",
        description="Crée un nouveau statut avec validation stricte des couleurs et du champ 'autre'.",
        tags=["Statuts"],
        request=StatutSerializer,
        responses={201: OpenApiResponse(response=StatutSerializer)}
    ),
    update=extend_schema(
        summary="Mettre à jour un statut",
        description="Met à jour un statut existant (partiellement ou complètement).",
        tags=["Statuts"],
        request=StatutSerializer,
        responses={200: OpenApiResponse(response=StatutSerializer)}
    ),
    destroy=extend_schema(
        summary="Supprimer un statut",
        description="Supprime logiquement un statut en le désactivant (is_active = False).",
        tags=["Statuts"],
        responses={204: OpenApiResponse(description="Suppression réussie")}
    ),
)
class StatutViewSet(viewsets.ModelViewSet):
    """
    🎯 API REST pour la gestion des statuts de formation.
    Permet la création, consultation, mise à jour et désactivation logique.
    """
    queryset = Statut.objects.all()
    serializer_class = StatutSerializer
    permission_classes = [ReadOnlyOrAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        logger.info(f"🟢 Statut créé : {instance}")
        return Response({
            "success": True,
            "message": "Statut créé avec succès.",
            "data": instance.to_serializable_dict()
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        logger.info(f"📝 Statut mis à jour : {instance}")
        return Response({
            "success": True,
            "message": "Statut mis à jour avec succès.",
            "data": instance.to_serializable_dict()
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()  # ❌ Supprime définitivement
        logger.warning(f"🗑️ Statut supprimé définitivement : {instance}")
        return Response({
            "success": True,
            "message": "Statut supprimé avec succès.",
            "data": None
        }, status=status.HTTP_204_NO_CONTENT)


    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response({
            "success": True,
            "message": "Détail du statut chargé avec succès.",
            "data": instance.to_serializable_dict()
        })

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        results = [obj.to_serializable_dict() for obj in page] if page is not None else [obj.to_serializable_dict() for obj in queryset]
        response = {
            "success": True,
            "message": "Liste des statuts récupérée avec succès.",
            "data": results
        }
        return self.get_paginated_response(results) if page is not None else Response(response)




    @extend_schema(
        summary="Liste des choix possibles de statuts",
        description="Retourne la liste des valeurs `nom` possibles pour un statut, avec libellé et couleur par défaut.",
        tags=["Statuts"],
        responses={200: OpenApiResponse(
            response=StatutChoiceSerializer(many=True),
            description="Liste des choix disponibles"
        )}
    )
    @action(detail=False, methods=["get"], url_path="choices", url_name="choices")
    def get_choices(self, request):
        """
        ✅ Retourne les choix disponibles pour `nom`, avec label et couleur par défaut.
        """
        data = [
            {
                "value": key,
                "label": label,
                "default_color": get_default_color(key)
            }
            for key, label in Statut.STATUT_CHOICES
        ]
        logger.debug("📋 Statut choices envoyés.")
        return Response({
            "success": True,
            "message": "Liste des choix de statuts.",
            "data": data
        })
