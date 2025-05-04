from rest_framework import viewsets, permissions, filters
from drf_spectacular.utils import extend_schema, OpenApiParameter
from ...models.partenaires import Partenaire
from ..serializers.partenaires_serializers import PartenaireSerializer

@extend_schema(
    tags=["Partenaires"],
    description="Endpoints pour gérer les partenaires (CRUD, filtres).",
    parameters=[
        OpenApiParameter(name="search", description="Recherche dans le nom, secteur ou contact", required=False, type=str),
    ]
)
class PartenaireViewSet(viewsets.ModelViewSet):
    """
    ViewSet complet pour le modèle Partenaire.
    - Authentification requise.
    - Permet de filtrer, rechercher, trier les partenaires.
    """
    queryset = Partenaire.objects.all()
    serializer_class = PartenaireSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nom', 'secteur_activite', 'contact_nom']
    ordering_fields = ['nom', 'secteur_activite', 'created_at']
    ordering = ['nom']
