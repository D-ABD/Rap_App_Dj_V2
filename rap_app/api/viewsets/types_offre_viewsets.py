from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema, OpenApiParameter

from ..serializers.types_offre_serializers import TypeOffreSerializer
from ...models.types_offre import TypeOffre


class TypeOffreViewSet(viewsets.ModelViewSet):
    """
    API permettant de lister, créer, modifier et supprimer les types d'offres de formation.

    Chaque type d'offre peut être standard (CRIF, POEC, etc.) ou personnalisé.
    Le champ `badge_html` permet un affichage visuel dans l'interface utilisateur.
    """

    queryset = TypeOffre.objects.all()
    serializer_class = TypeOffreSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Lister les types d'offres",
        description="Retourne tous les types d'offres disponibles (standards ou personnalisés)."
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Créer un type d'offre",
        description="Permet de créer un nouveau type d'offre. Si `nom='autre'`, le champ `autre` est requis."
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Mettre à jour un type d'offre",
        description="Permet de modifier un type d'offre existant, avec contrôle sur la couleur, le type et les labels."
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
