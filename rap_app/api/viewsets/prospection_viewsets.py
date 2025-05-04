from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from ...models.prospection import Prospection, HistoriqueProspection
from ..serializers.prospection_serializers import ProspectionSerializer, HistoriqueProspectionSerializer
from ..permissions import IsOwnerOrStaffOrAbove


@extend_schema(
    tags=["📞 Prospection"],
    summary="Gérer les prospections",
    description="""
        - Un utilisateur voit ses propres prospections (où il est `responsable`)
        - Le staff/admin/superadmin voit tout
    """
)
class ProspectionViewSet(viewsets.ModelViewSet):
    serializer_class = ProspectionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaffOrAbove]

    def get_queryset(self):
        user = self.request.user
        role = getattr(user.profile, "role", "")
        if role in ["staff", "admin", "superadmin"]:
            return Prospection.objects.select_related('company', 'formation', 'responsable')
        return Prospection.objects.filter(responsable=user).select_related('company', 'formation', 'responsable')

    def perform_create(self, serializer):
        serializer.save(responsable=self.request.user)


@extend_schema(
    tags=["📞 Historique prospection"],
    summary="Historique des prospections",
    description="""
        - Un utilisateur voit l’historique de ses propres prospections (`modifie_par`)
        - Le staff/admin/superadmin voit tout
    """
)
class HistoriqueProspectionViewSet(viewsets.ModelViewSet):
    serializer_class = HistoriqueProspectionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaffOrAbove]

    def get_queryset(self):
        user = self.request.user
        role = getattr(user.profile, "role", "")
        if role in ["staff", "admin", "superadmin"]:
            return HistoriqueProspection.objects.select_related('prospection', 'modifie_par')
        return HistoriqueProspection.objects.filter(modifie_par=user).select_related('prospection', 'modifie_par')

    def perform_create(self, serializer):
        serializer.save(modifie_par=self.request.user)
