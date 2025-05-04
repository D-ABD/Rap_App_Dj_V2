# IsSuperAdminOnly / IsAdmin

from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema, OpenApiParameter

from ..serializers.types_offre_serializers import TypeOffreSerializer
from ...models.types_offre import TypeOffre
from ..permissions import IsAdmin, IsSuperAdminOnly


@extend_schema(
    tags=["📦 Types d’offre"],
    summary="Gérer les types d’offres de formation",
    description="""
        Ce ViewSet permet de :
        - Lister, créer et modifier les types d'offres (CRIF, POEC, Alternance, etc.)
        - Supprimer des types d'offres (uniquement superadmin)

        🔐 Accès : admin ou superadmin uniquement
    """
)
class TypeOffreViewSet(viewsets.ModelViewSet):
    """
    API pour gérer les types d'offres de formation.

    Chaque offre peut inclure :
    - un nom (ex: CRIF, POEC, VAE…)
    - une couleur
    - un badge HTML pour l’affichage
    """

    queryset = TypeOffre.objects.all()
    serializer_class = TypeOffreSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_permissions(self):
        """
        Autorise uniquement les superadmins à supprimer un type d’offre.
        """
        if self.action == "destroy":
            return [permissions.IsAuthenticated(), IsSuperAdminOnly()]
        return super().get_permissions()

    @extend_schema(
        summary="📄 Lister les types d'offres",
        description="Retourne tous les types d'offres disponibles (standards ou personnalisés)."
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="➕ Créer un type d'offre",
        description="Permet de créer un nouveau type d'offre. Si `nom='autre'`, le champ `autre` est requis."
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="✏️ Modifier un type d'offre",
        description="Permet de modifier un type d'offre existant, avec contrôle sur la couleur, le type et les labels."
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="🗑️ Supprimer un type d'offre",
        description="Seul un superadmin peut supprimer un type d'offre."
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
