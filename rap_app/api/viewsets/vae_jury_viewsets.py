# viewsets/vae_viewsets.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from ..serializers.vae_jury_serializers import HistoriqueStatutVAESerializer, SuiviJurySerializer, VAESerializer
from ...models.vae_jury import VAE, HistoriqueStatutVAE, SuiviJury

@extend_schema(tags=["Suivi Jury"])
class SuiviJuryViewSet(viewsets.ModelViewSet):
    """
    API permettant de consulter et mettre à jour le suivi des jurys
    par centre, mois et année.
    """
    queryset = SuiviJury.objects.all()
    serializer_class = SuiviJurySerializer
    permission_classes = [IsAuthenticated]


@extend_schema(tags=["VAE"])
class VAEViewSet(viewsets.ModelViewSet):
    """
    API CRUD pour les VAE individuelles.

    Permet de créer, lire, modifier et supprimer les dossiers de VAE
    ainsi que de suivre leur statut dans le temps.
    """
    queryset = VAE.objects.all().select_related('centre')
    serializer_class = VAESerializer
    permission_classes = [IsAuthenticated]


@extend_schema(tags=["Historique VAE"])
class HistoriqueStatutVAEViewSet(viewsets.ModelViewSet):
    """
    API pour consulter l'historique des statuts des VAE.

    Chaque changement de statut d'une VAE est enregistré avec une date
    et un commentaire pour suivi.
    """
    queryset = HistoriqueStatutVAE.objects.all().select_related('vae')
    serializer_class = HistoriqueStatutVAESerializer
    permission_classes = [IsAuthenticated]
