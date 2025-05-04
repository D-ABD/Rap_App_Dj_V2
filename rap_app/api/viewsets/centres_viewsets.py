from rest_framework import viewsets, permissions

from ..serializers.centres_serializers import CentreSerializer
from ...models.centres import Centre
class CentreViewSet(viewsets.ModelViewSet):
    """
    API ViewSet pour les centres de formation.

    Fournit les actions suivantes :
    - GET /centres/        : liste paginée des centres
    - GET /centres/{id}/   : détails d’un centre
    - POST /centres/       : création d’un nouveau centre
    - PUT /centres/{id}/   : mise à jour complète
    - PATCH /centres/{id}/ : mise à jour partielle
    - DELETE /centres/{id}/: suppression

    Permissions :
    - Accessible aux utilisateurs authentifiés par défaut
    """

    queryset = Centre.objects.all().order_by("nom")
    serializer_class = CentreSerializer
    permission_classes = [permissions.IsAuthenticated]
