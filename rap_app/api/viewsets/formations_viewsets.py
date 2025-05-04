# IsStaffOrAbove

from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from ...models.formations import Formation
from ..serializers.formations_serializers import FormationSerializer
from ..permissions import IsStaffOrAbove


@extend_schema(
    tags=["Formations"],
    summary="Gestion des formations",
    description="""
        Ce ViewSet est réservé aux rôles **staff, admin et superadmin**.

        Il permet de :
        - Lister, rechercher et trier les formations
        - Créer, modifier ou supprimer des formations

        ⚠️ Les utilisateurs `stagiaire`, `test` ou non connectés n’ont aucun accès.
    """
)
class FormationViewSet(viewsets.ModelViewSet):
    """
    API ViewSet pour gérer les formations.

    Endpoints :
    - GET /formations/
    - GET /formations/{id}/
    - POST /formations/
    - PUT/PATCH /formations/{id}/
    - DELETE /formations/{id}/

    Permissions :
    - Accès réservé au staff, admin et superadmin.
    """

    serializer_class = FormationSerializer
    permission_classes = [IsAuthenticated, IsStaffOrAbove]

    queryset = Formation.objects.select_related('centre', 'statut', 'type_offre').all()

    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['start_date', 'end_date', 'nom']
    search_fields = ['nom', 'num_kairos', 'num_offre', 'num_produit']
