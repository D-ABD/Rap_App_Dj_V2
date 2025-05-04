from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, DateTimeFilter
from ..serializers.logs_serializers import LogUtilisateurSerializer
from ...models.logs import LogUtilisateur
from rest_framework.permissions import IsAuthenticated


class LogUtilisateurFilter(FilterSet):
    """
    Filtres personnalisés pour les logs :
    - date_min : logs après cette date
    - date_max : logs avant cette date
    """

    date_min = DateTimeFilter(field_name="date", lookup_expr="gte")
    date_max = DateTimeFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = LogUtilisateur
        fields = ['utilisateur', 'modele', 'action']


class LogUtilisateurViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ReadOnly pour consulter les logs utilisateurs.

    ✅ Recherche plein texte : action, modèle, utilisateur
    ✅ Filtres :
      - utilisateur
      - modèle
      - action
      - date_min (>=)
      - date_max (<=)
    """

    queryset = LogUtilisateur.objects.select_related('utilisateur').all()
    serializer_class = LogUtilisateurSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LogUtilisateurFilter
    search_fields = ['utilisateur__username', 'utilisateur__email', 'action', 'modele']
    ordering_fields = ['date', 'modele']
    ordering = ['-date']
