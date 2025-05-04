# IsAdmin

import logging
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from ...models.statut import Statut
from ..serializers.statut_serializers import StatutSerializer
from ..permissions import IsAdmin  # Permission personnalisée : staff+ ou admin+

logger = logging.getLogger(__name__)


@extend_schema(
    tags=["📌 Statuts"],
    summary="Gérer les statuts de formation",
    description="""
        API complète pour créer, mettre à jour ou supprimer les statuts d'une formation
        (Exemples : "Recrutement", "Annulée", "Pleine", etc.).

        🔒 Accès réservé aux **admins ou superadmins**.
    """
)
class StatutViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD pour les statuts des formations.

    Routes :
    - GET /api/statuts/ : liste des statuts
    - POST /api/statuts/ : création
    - GET /api/statuts/{id}/ : détail
    - PUT/PATCH : modification
    - DELETE : suppression

    ✅ Journalise les créations et suppressions.
    """

    queryset = Statut.objects.all()
    serializer_class = StatutSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def perform_create(self, serializer):
        instance = serializer.save()
        logger.info(f"🟢 Statut créé via API : {instance.nom}")

    def perform_destroy(self, instance):
        logger.warning(f"❌ Statut supprimé via API : {instance.nom}")
        super().perform_destroy(instance)
