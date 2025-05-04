# IsStaffOrAbove

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from ..serializers.vae_jury_serializers import (
    VAESerializer,
    SuiviJurySerializer,
    HistoriqueStatutVAESerializer
)
from ...models.vae_jury import VAE, SuiviJury, HistoriqueStatutVAE
from ..permissions import IsStaffOrAbove


@extend_schema(
    tags=["📅 Suivi Jury"],
    summary="Suivi mensuel des jurys par centre",
    description="Consultation et mise à jour du suivi des jurys par mois, centre et année."
)
class SuiviJuryViewSet(viewsets.ModelViewSet):
    queryset = SuiviJury.objects.all()
    serializer_class = SuiviJurySerializer
    permission_classes = [IsAuthenticated, IsStaffOrAbove]


@extend_schema(
    tags=["📘 VAE"],
    summary="Gérer les dossiers VAE",
    description="CRUD complet pour les parcours VAE : création, lecture, mise à jour et suppression."
)
class VAEViewSet(viewsets.ModelViewSet):
    queryset = VAE.objects.all().select_related('centre')
    serializer_class = VAESerializer
    permission_classes = [IsAuthenticated, IsStaffOrAbove]


@extend_schema(
    tags=["🕘 Historique VAE"],
    summary="Historique des changements de statut VAE",
    description="Chaque changement de statut d’un dossier VAE est enregistré avec date et commentaire."
)
class HistoriqueStatutVAEViewSet(viewsets.ModelViewSet):
    queryset = HistoriqueStatutVAE.objects.all().select_related('vae')
    serializer_class = HistoriqueStatutVAESerializer
    permission_classes = [IsAuthenticated, IsStaffOrAbove]
