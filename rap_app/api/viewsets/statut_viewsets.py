# viewsets/statut_viewset.py
import logging
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from ...models.statut import Statut
from ..serializers.statut_serializers import StatutSerializer

logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Statuts"],
    description="Endpoints pour la gestion des statuts de formation (recrutement, annulée, pleine...)."
)
class StatutViewSet(viewsets.ModelViewSet):
    """
    API CRUD complète pour les statuts d'une formation.

    - `GET /api/statuts/` : liste paginée des statuts
    - `POST /api/statuts/` : créer un nouveau statut
    - `GET /api/statuts/{id}/` : détail d’un statut
    - `PUT /api/statuts/{id}/` : mise à jour complète
    - `PATCH /api/statuts/{id}/` : mise à jour partielle
    - `DELETE /api/statuts/{id}/` : suppression
    """
    queryset = Statut.objects.all()
    serializer_class = StatutSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        instance = serializer.save()
        logger.info(f"🟢 Statut créé via API : {instance.nom}")

    def perform_destroy(self, instance):
        logger.warning(f"❌ Statut supprimé via API : {instance.nom}")
        return super().perform_destroy(instance)
