from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from ...models.formations import Formation
from ..serializers.formations_serializers import FormationSerializer

class FormationViewSet(viewsets.ModelViewSet):
    """
    API permettant de gérer les formations.

    Endpoints disponibles :
    - GET /formations/ → Liste paginée des formations
    - GET /formations/{id}/ → Détail d'une formation
    - POST /formations/ → Créer une nouvelle formation
    - PUT /formations/{id}/ → Modifier complètement une formation
    - PATCH /formations/{id}/ → Modifier partiellement une formation
    - DELETE /formations/{id}/ → Supprimer une formation

    Options de filtre disponibles :
    - ?centre=ID
    - ?type_offre=ID
    - ?statut=ID
    - ?ordering=start_date
    """

    queryset = Formation.objects.select_related('centre', 'statut', 'type_offre').all()
    serializer_class = FormationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['start_date', 'end_date', 'nom']
    search_fields = ['nom', 'num_kairos', 'num_offre', 'num_produit']
