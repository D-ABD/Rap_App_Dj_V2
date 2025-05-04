# IsOwnerOrStaffOrAbove

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from ...models.evenements import Evenement
from ..serializers.evenements_serializers import EvenementSerializer
from ..permissions import IsOwnerOrStaffOrAbove


@extend_schema(
    tags=["Événements"],
    summary="Gérer les événements de formation",
    description="""
        - Les utilisateurs voient uniquement les événements qu’ils ont créés (`created_by`).
        - Les membres du staff, admin, superadmin ont accès à tous les événements.
    """
)
class EvenementViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les événements.

    - GET /evenements/ : liste
    - GET /evenements/{id}/ : détail
    - POST : création
    - PUT/PATCH : mise à jour
    - DELETE : suppression
    """

    serializer_class = EvenementSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaffOrAbove]

    def get_queryset(self):
        user = self.request.user
        role = getattr(user.profile, "role", "")

        if role in ["staff", "admin", "superadmin"]:
            return Evenement.objects.select_related('formation').all().order_by('-event_date')
        return Evenement.objects.filter(created_by=user).select_related('formation').order_by('-event_date')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
