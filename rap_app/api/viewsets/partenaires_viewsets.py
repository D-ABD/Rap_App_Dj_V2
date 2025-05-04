# IsOwnerOrStaffOrAbove

from rest_framework import viewsets, permissions, filters
from drf_spectacular.utils import extend_schema, OpenApiParameter
from ...models.partenaires import Partenaire
from ..serializers.partenaires_serializers import PartenaireSerializer
from ..permissions import IsOwnerOrStaffOrAbove


@extend_schema(
    tags=["Partenaires"],
    summary="Gérer les partenaires",
    description="""
        Ce ViewSet permet :
        - aux utilisateurs : de gérer uniquement les partenaires qu’ils ont créés (`created_by`)
        - aux rôles staff/admin/superadmin : de gérer tous les partenaires

        🔐 Authentification requise.
    """,
    parameters=[
        OpenApiParameter(name="search", description="Recherche dans le nom, secteur ou contact", required=False, type=str),
    ]
)
class PartenaireViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour le modèle Partenaire.

    Accès :
    - L’utilisateur peut gérer ses propres partenaires (`created_by`)
    - Le staff/admin/superadmin ont un accès complet
    """

    serializer_class = PartenaireSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaffOrAbove]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nom', 'secteur_activite', 'contact_nom']
    ordering_fields = ['nom', 'secteur_activite', 'created_at']
    ordering = ['nom']

    def get_queryset(self):
        user = self.request.user
        role = getattr(user.profile, "role", "")

        if role in ["staff", "admin", "superadmin"]:
            return Partenaire.objects.all()
        return Partenaire.objects.filter(created_by=user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
