# ReadWriteAdminReadStaff

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from ..serializers.centres_serializers import CentreSerializer
from ...models.centres import Centre
from ..permissions import ReadWriteAdminReadStaff


@extend_schema(
    tags=["Centres"],
    summary="Gérer les centres de formation",
    description="""
        Ce ViewSet permet de consulter, créer, modifier ou supprimer des centres de formation.

        - **Lecture (GET)** : accessible aux rôles `staff`, `admin`, `superadmin`
        - **Écriture (POST/PUT/PATCH/DELETE)** : réservée aux rôles `admin` et `superadmin`

        Nécessite une authentification.
    """
)
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
    - Lecture : staff, admin, superadmin
    - Écriture : admin, superadmin uniquement
    """

    queryset = Centre.objects.all().order_by("nom")
    serializer_class = CentreSerializer
    permission_classes = [IsAuthenticated, ReadWriteAdminReadStaff]
