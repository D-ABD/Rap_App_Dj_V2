# rap_app_project/rap_app/api/viewsets/rapports_viewset.py

from rest_framework import viewsets, permissions
from ...models.rapports import Rapport
from ..serializers.rapports_serializers import RapportSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter

class RapportViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des rapports.

    Fournit les opérations standard :
    - list : Liste tous les rapports générés
    - retrieve : Affiche les détails d’un rapport spécifique
    - create : Génère un nouveau rapport
    - update / partial_update : Modifie un rapport existant
    - destroy : Supprime un rapport

    Accessible uniquement aux utilisateurs authentifiés.
    """
    queryset = Rapport.objects.all().select_related('centre', 'type_offre', 'statut', 'formation', 'utilisateur')
    serializer_class = RapportSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Liste des rapports",
        parameters=[
            OpenApiParameter(name='type_rapport', description="Filtrer par type de rapport", required=False, type=str),
            OpenApiParameter(name='periode', description="Filtrer par périodicité", required=False, type=str),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
