import django_filters
from django.db.models import Q

from ..models.prospection_comments import ProspectionComment
from ..models.appairage import Appairage
from ..models.prospection import Prospection
from ..models.custom_user import CustomUser
from ..models.formations import HistoriqueFormation
from ..models.candidat import Candidat, ResultatPlacementChoices
from ..models.atelier_tre import AtelierTRE


# ─────────────────────────────────────────────────────────────────────────────
# Atelier TRE
# ─────────────────────────────────────────────────────────────────────────────
class AtelierTREFilter(django_filters.FilterSet):
    # ✅ Compat front : filtre par JOUR sur le champ DateTime "debut"
    date_min = django_filters.DateFilter(field_name="debut", lookup_expr="date__gte")
    date_max = django_filters.DateFilter(field_name="debut", lookup_expr="date__lte")

    # ✅ Bornes précises si on veut tenir compte de l’heure
    debut_min = django_filters.IsoDateTimeFilter(field_name="debut", lookup_expr="gte")
    debut_max = django_filters.IsoDateTimeFilter(field_name="debut", lookup_expr="lte")

    # ✅ type d’atelier (value des choices)
    type_atelier = django_filters.ChoiceFilter(
        field_name="type_atelier",
        choices=AtelierTRE.TypeAtelier.choices,
        lookup_expr="exact",
    )

    class Meta:
        model = AtelierTRE
        fields = ["type_atelier", "date_min", "date_max", "debut_min", "debut_max"]


# ─────────────────────────────────────────────────────────────────────────────
# IN filters “safe” (ignorent les valeurs vides)
# ─────────────────────────────────────────────────────────────────────────────
class _SafeBaseInFilter(django_filters.filters.BaseInFilter):
    def filter(self, qs, value):
        if not value:
            return qs
        cleaned = [v for v in value if v not in (None, "", [])]
        if not cleaned:
            return qs
        return super().filter(qs, cleaned)

class SafeNumberInFilter(_SafeBaseInFilter, django_filters.NumberFilter):
    pass

class SafeCharInFilter(_SafeBaseInFilter, django_filters.CharFilter):
    pass

# (Compat éventuelle avec ancien code)
class CharInFilter(_SafeBaseInFilter, django_filters.CharFilter):
    """Alias rétro-compatible : ?field__in=a,b,c"""
    pass

class NumberInFilter(_SafeBaseInFilter, django_filters.NumberFilter):
    """Alias rétro-compatible : ?field__in=1,2,3"""
    pass


# ─────────────────────────────────────────────────────────────────────────────
# Candidat
# ─────────────────────────────────────────────────────────────────────────────
class CandidatFilter(django_filters.FilterSet):
    id__in = SafeNumberInFilter(field_name='id', lookup_expr='in')

    # 📅 bornes date d'inscription + alias
    date_inscription_min = django_filters.DateFilter(field_name="date_inscription", lookup_expr="gte")
    date_inscription_max = django_filters.DateFilter(field_name="date_inscription", lookup_expr="lte")
    date_min = django_filters.DateFilter(field_name="date_inscription", lookup_expr="gte")
    date_max = django_filters.DateFilter(field_name="date_inscription", lookup_expr="lte")

    # 📅 date de naissance
    date_naissance_min = django_filters.DateFilter(field_name="date_naissance", lookup_expr="gte")
    date_naissance_max = django_filters.DateFilter(field_name="date_naissance", lookup_expr="lte")

    # 🔗 FK
    formation = django_filters.NumberFilter(field_name="formation_id")
    centre = django_filters.NumberFilter(field_name="formation__centre_id")

    # 🔤 choix + variantes IN
    statut = django_filters.ChoiceFilter(field_name="statut", choices=Candidat.StatutCandidat.choices)
    statut__in = SafeCharInFilter(field_name="statut", lookup_expr="in")
    statut_i = django_filters.CharFilter(field_name="statut", lookup_expr="iexact")

    type_contrat = django_filters.ChoiceFilter(field_name="type_contrat", choices=Candidat.TypeContrat.choices)
    type_contrat__in = SafeCharInFilter(field_name="type_contrat", lookup_expr="in")
    type_contrat_i = django_filters.CharFilter(field_name="type_contrat", lookup_expr="iexact")
    type_contrat_isnull = django_filters.BooleanFilter(field_name="type_contrat", lookup_expr="isnull")

    disponibilite = django_filters.ChoiceFilter(field_name="disponibilite", choices=Candidat.Disponibilite.choices)
    contrat_signe = django_filters.ChoiceFilter(field_name="contrat_signe", choices=Candidat.ContratSigne.choices)
    resultat_placement = django_filters.ChoiceFilter(
        field_name="resultat_placement", choices=ResultatPlacementChoices.choices
    )

    # ✅ statut de CV
    cv_statut = django_filters.ChoiceFilter(field_name="cv_statut", choices=Candidat.CVStatut.choices)
    cv_statut__in = SafeCharInFilter(field_name="cv_statut", lookup_expr="in")

    ville = django_filters.CharFilter(field_name="ville", lookup_expr="icontains")
    code_postal = django_filters.CharFilter(field_name="code_postal", lookup_expr="istartswith")

    # ✅ booléens
    rqth = django_filters.BooleanFilter(field_name="rqth")
    permis_b = django_filters.BooleanFilter(field_name="permis_b")
    admissible = django_filters.BooleanFilter(field_name="admissible")
    entretien_done = django_filters.BooleanFilter(field_name="entretien_done")
    test_is_ok = django_filters.BooleanFilter(field_name="test_is_ok")

    # 🆕 a-t-il un OSIA ?
    has_osia = django_filters.BooleanFilter(method="filter_has_osia")
    def filter_has_osia(self, qs, name, value):
        if value is None:
            return qs
        if value:
            return qs.exclude(numero_osia__isnull=True).exclude(numero_osia__exact="")
        return qs.filter(Q(numero_osia__isnull=True) | Q(numero_osia__exact=""))

    class Meta:
        model = Candidat
        fields = [
            "statut", "type_contrat", "disponibilite",
            "formation", "centre",
            "responsable_placement", "vu_par",
            "admissible", "entretien_done", "test_is_ok",
            "contrat_signe", "resultat_placement",
            "entreprise_placement", "entreprise_validee",
            "ville", "code_postal", "id__in",
            "rqth", "permis_b",
            "date_inscription_min", "date_inscription_max",
            "date_min", "date_max",
            "date_naissance_min", "date_naissance_max",
            "has_osia",
            "statut__in", "type_contrat__in", "type_contrat_isnull", "statut_i", "type_contrat_i",
            "cv_statut", "cv_statut__in",
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Historique formation
# ─────────────────────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────────────────────────────────────
class UserFilterSet(django_filters.FilterSet):
    role = django_filters.CharFilter(field_name="role", lookup_expr="exact")
    is_active = django_filters.BooleanFilter(field_name="is_active")
    date_joined_min = django_filters.DateFilter(field_name="date_joined", lookup_expr="gte")
    date_joined_max = django_filters.DateFilter(field_name="date_joined", lookup_expr="lte")

    formation = django_filters.NumberFilter(field_name="candidat_associe__formation__id", lookup_expr="exact")
    centre = django_filters.NumberFilter(field_name="candidat_associe__formation__centre__id", lookup_expr="exact")
    type_offre = django_filters.NumberFilter(field_name="candidat_associe__formation__type_offre__id", lookup_expr="exact")

    class Meta:
        model = CustomUser
        fields = [
            "role", "is_active",
            "formation", "centre", "type_offre",
            "date_joined_min", "date_joined_max"
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Prospection & Appairage
# ─────────────────────────────────────────────────────────────────────────────
class ProspectionFilterSet(django_filters.FilterSet):
    # 🆕 pratiques
    id__in = SafeNumberInFilter(field_name="id", lookup_expr="in")
    date_min = django_filters.DateFilter(field_name="date_prospection", lookup_expr="date__gte")
    date_max = django_filters.DateFilter(field_name="date_prospection", lookup_expr="date__lte")
    relance_min = django_filters.DateFilter(field_name="relance_prevue", lookup_expr="gte")
    relance_max = django_filters.DateFilter(field_name="relance_prevue", lookup_expr="lte")

    # 🔗 FK directs
    centre = django_filters.NumberFilter(field_name="centre_id", lookup_expr="exact")
    formation = django_filters.NumberFilter(field_name="formation_id", lookup_expr="exact")
    formation__in = SafeNumberInFilter(field_name="formation_id", lookup_expr="in")
    partenaire = django_filters.NumberFilter(field_name="partenaire_id", lookup_expr="exact")
    partenaire__in = SafeNumberInFilter(field_name="partenaire_id", lookup_expr="in")
    owner = django_filters.NumberFilter(field_name="owner_id", lookup_expr="exact")
    owner__in = SafeNumberInFilter(field_name="owner_id", lookup_expr="in")

    # 🔤 choices (avec variantes __in)
    statut = django_filters.CharFilter(field_name="statut", lookup_expr="exact")
    statut__in = SafeCharInFilter(field_name="statut", lookup_expr="in")
    objectif = django_filters.CharFilter(field_name="objectif", lookup_expr="exact")
    objectif__in = SafeCharInFilter(field_name="objectif", lookup_expr="in")
    motif = django_filters.CharFilter(field_name="motif", lookup_expr="exact")
    motif__in = SafeCharInFilter(field_name="motif", lookup_expr="in")
    type_prospection = django_filters.CharFilter(field_name="type_prospection", lookup_expr="exact")
    type_prospection__in = SafeCharInFilter(field_name="type_prospection", lookup_expr="in")

    # 🆕 filtre direct sur le champ du modèle (et option historique si besoin)
    moyen_contact = django_filters.CharFilter(field_name="moyen_contact", lookup_expr="exact")
    historique_moyen_contact = django_filters.CharFilter(method="filter_historique_moyen_contact")

    # 🆕 filtres liés à la formation
    formation_type_offre = django_filters.NumberFilter(field_name="formation__type_offre_id", lookup_expr="exact")
    formation_type_offre__in = SafeNumberInFilter(field_name="formation__type_offre_id", lookup_expr="in")
    formation_statut = django_filters.NumberFilter(field_name="formation__statut_id", lookup_expr="exact")
    formation_statut__in = SafeNumberInFilter(field_name="formation__statut_id", lookup_expr="in")

    class Meta:
        model = Prospection
        fields = [
            # FK
            "centre", "formation", "partenaire", "owner",
            # choices
            "statut", "objectif", "motif", "type_prospection",
            # moyens/relance/dates
            "moyen_contact", "relance_min", "relance_max", "date_min", "date_max",
            # formation liés
            "formation_type_offre", "formation_statut",
            # utilitaires
            "id__in",
        ]

    def filter_historique_moyen_contact(self, qs, name, value):
        """
        Optionnel : permet ?historique_moyen_contact=email pour retrouver
        les prospections où un historique a été saisi avec ce moyen.
        """
        if not value:
            return qs
        return qs.filter(historiques__moyen_contact=value).distinct()


class AppairageFilterSet(django_filters.FilterSet):
    statut = django_filters.CharFilter(lookup_expr="exact")
    formation = django_filters.NumberFilter(field_name="formation_id")
    centre = django_filters.NumberFilter(method="filter_centre")

    class Meta:
        model = Appairage
        fields = ["statut", "formation", "candidat", "partenaire", "created_by", "centre"]

    def filter_centre(self, qs, name, value):
        return qs.filter(
            Q(formation__centre_id=value) |
            Q(candidat__formation__centre_id=value)
        )


# ─────────────────────────────────────────────────────────────────────────────
# Prospection comments
# ─────────────────────────────────────────────────────────────────────────────
class ProspectionCommentFilter(django_filters.FilterSet):
    formation_nom = django_filters.CharFilter(field_name="prospection__formation__nom", lookup_expr="icontains")
    partenaire_nom = django_filters.CharFilter(field_name="prospection__partenaire__nom", lookup_expr="icontains")
    created_by_username = django_filters.CharFilter(field_name="created_by__username", lookup_expr="icontains")

    prospection = django_filters.NumberFilter(field_name="prospection_id")
    created_by = django_filters.NumberFilter(field_name="created_by_id")
    is_internal = django_filters.BooleanFilter()

    # 🆕 utilitaires pour le front (cohérents avec tes usages ailleurs)
    prospection_owner = django_filters.NumberFilter(field_name="prospection__owner_id")
    prospection_partenaire = django_filters.NumberFilter(field_name="prospection__partenaire_id")

    class Meta:
        model = ProspectionComment
        fields = [
            "prospection",
            "is_internal",
            "created_by",
            "formation_nom",
            "partenaire_nom",
            "created_by_username",
            "prospection_owner",
            "prospection_partenaire",
        ]
