# IsSuperAdminOnly / IsAdmin

from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema, OpenApiParameter

from ...models.rapports import Rapport
from ..serializers.rapports_serializers import RapportSerializer
from ..permissions import IsSuperAdminOnly, IsAdmin  # permissions personnalisées


@extend_schema(
    tags=["📊 Rapports"],
    summary="Gestion des rapports générés",
    description="""
        Ce ViewSet permet de :
        - visualiser la liste et les détails des rapports générés
        - créer ou supprimer des rapports (admin+ uniquement)

        🔒 Seuls les **admins** ou **superadmins** y ont accès.
    """,
    parameters=[
        OpenApiParameter(name='type_rapport', description="Filtrer par type de rapport", required=False, type=str),
        OpenApiParameter(name='periode', description="Filtrer par périodicité", required=False, type=str),
    ]
)
class RapportViewSet(viewsets.ModelViewSet):
    """
    API pour gérer les rapports générés dans le système (PDF, Excel, etc).

    Accès :
    - GET, POST, PUT, DELETE : réservés aux rôles admin et superadmin
    - Certaines actions critiques peuvent être réservées aux superadmins
    """

    queryset = Rapport.objects.all().select_related('centre', 'type_offre', 'statut', 'formation', 'utilisateur')
    serializer_class = RapportSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_permissions(self):
        """
        Autorise uniquement les superadmins à supprimer un rapport.
        """
        if self.action == "destroy":
            return [permissions.IsAuthenticated(), IsSuperAdminOnly()]
        return super().get_permissions()
