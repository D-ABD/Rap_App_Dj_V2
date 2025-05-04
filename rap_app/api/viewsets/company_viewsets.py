
# views/company_viewset.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from ..serializers.company_serializers import CompanySerializer
from ...models.company import Company

class CompanyViewSet(viewsets.ModelViewSet):
    """
    API ViewSet pour le modèle Company.

    Ce viewset permet aux utilisateurs authentifiés de :
    - lister toutes les entreprises (GET /api/companies/)
    - consulter une entreprise spécifique (GET /api/companies/{id}/)
    - créer une nouvelle entreprise (POST)
    - modifier une entreprise (PUT / PATCH)
    - supprimer une entreprise (DELETE)

    Utilise : CompanySerializer
    """
    queryset = Company.objects.all().order_by('name')
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]
