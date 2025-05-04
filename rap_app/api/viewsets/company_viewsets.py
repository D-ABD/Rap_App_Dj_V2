# IsOwnerOrStaffOrAbove

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from ..serializers.company_serializers import CompanySerializer
from ...models.company import Company
from ..permissions import IsOwnerOrStaffOrAbove


@extend_schema(
    tags=["Entreprises"],
    summary="Gérer les entreprises",
    description="""
        Ce ViewSet permet aux utilisateurs :
        - de gérer uniquement les entreprises qu’ils ont créées (`created_by`),
        - et aux membres `staff`, `admin`, `superadmin` de gérer toutes les entreprises.

        L’utilisateur connecté est automatiquement associé à l’entreprise créée.
    """
)
class CompanyViewSet(viewsets.ModelViewSet):
    """
    API ViewSet pour les entreprises.

    Accès :
    - Créateur (`created_by`) : accès total à ses propres entreprises.
    - Staff, admin, superadmin : accès complet à toutes les entreprises.
    """

    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaffOrAbove]

    def get_queryset(self):
        user = self.request.user
        role = getattr(user.profile, "role", "")

        if role in ["staff", "admin", "superadmin"]:
            return Company.objects.all().order_by('name')
        return Company.objects.filter(created_by=user).order_by('name')

    def perform_create(self, serializer):
        """
        Associe automatiquement l’utilisateur connecté comme créateur (`created_by`).
        """
        serializer.save(created_by=self.request.user)
