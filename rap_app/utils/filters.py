import django_filters

from ..models.formations import HistoriqueFormation

from ..models.candidat import Candidat
from ..models.atelier_tre import AtelierTRE

class AtelierTREFilter(django_filters.FilterSet):
    date_min = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_max = django_filters.DateFilter(field_name="date", lookup_expr="lte")
    type_atelier = django_filters.CharFilter(lookup_expr="exact")

    class Meta:
        model = AtelierTRE
        fields = ["date_min", "date_max", "type_atelier"]

class CandidatFilter(django_filters.FilterSet):
    date_inscription_min = django_filters.DateFilter(field_name="date_inscription", lookup_expr="gte")
    date_inscription_max = django_filters.DateFilter(field_name="date_inscription", lookup_expr="lte")
    formation = django_filters.NumberFilter()
    resultat_placement = django_filters.CharFilter(lookup_expr="exact")

    class Meta:
        model = Candidat
        fields = [
            "statut", "formation", "responsable_placement", "vu_par", "admissible",
            "entretien_done", "test_is_ok", "contrat_signe", "resultat_placement",
            "entreprise_placement", "entreprise_validee"
        ]




class HistoriqueFormationFilter(django_filters.FilterSet):
    centre_id = django_filters.NumberFilter(field_name="formation__centre_id")
    type_offre_id = django_filters.NumberFilter(field_name="formation__type_offre_id")
    statut_id = django_filters.NumberFilter(field_name="formation__statut_id")
    formation_id = django_filters.NumberFilter(field_name="formation_id")
    formation_etat = django_filters.CharFilter(method="filter_etat")

    class Meta:
        model = HistoriqueFormation
        fields = []

    def filter_etat(self, queryset, name, value):
        return queryset.filter(formation__etat=value)