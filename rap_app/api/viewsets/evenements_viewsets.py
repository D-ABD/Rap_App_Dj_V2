from rest_framework import viewsets, permissions
from ...models.evenements import Evenement
from ..serializers.evenements_serializers import EvenementSerializer

class EvenementViewSet(viewsets.ModelViewSet):
    """
    ViewSet permettant de lister, créer, mettre à jour et supprimer des événements.
    
    Ce ViewSet fournit toutes les opérations CRUD standard et expose
    des informations enrichies pour le frontend (statut, taux de participation...).
    """
    queryset = Evenement.objects.select_related('formation').all().order_by('-event_date')
    serializer_class = EvenementSerializer
    permission_classes = [permissions.IsAuthenticated]
