from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from ...models.prospection import Prospection, HistoriqueProspection
from ..serializers.prospection_serializers import ProspectionSerializer, HistoriqueProspectionSerializer

class ProspectionViewSet(viewsets.ModelViewSet):
    """
    API endpoint permettant de créer, modifier et consulter les prospections.

    🔹 GET /api/prospections/ → Liste toutes les prospections
    🔹 POST /api/prospections/ → Crée une nouvelle prospection
    🔹 GET /api/prospections/{id}/ → Détail d'une prospection
    🔹 PUT /api/prospections/{id}/ → Modifier une prospection
    🔹 DELETE /api/prospections/{id}/ → Supprimer une prospection
    """
    queryset = Prospection.objects.all().select_related('company', 'formation', 'responsable')
    serializer_class = ProspectionSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Lister les prospections", tags=["📞 Prospection"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class HistoriqueProspectionViewSet(viewsets.ModelViewSet):
    """
    API endpoint permettant de consulter l'historique des prospections.

    🔹 GET /api/historique-prospections/ → Liste des modifications
    🔹 POST /api/historique-prospections/ → Ajout manuel (rare)
    """
    queryset = HistoriqueProspection.objects.all().select_related('prospection', 'modifie_par')
    serializer_class = HistoriqueProspectionSerializer
    permission_classes = [IsAuthenticated]
