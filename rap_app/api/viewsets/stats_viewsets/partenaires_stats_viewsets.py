# rap_app/api/viewsets/stats_viewsets/partenaires_stats_viewsets.py

from collections import OrderedDict
from typing import Dict, List, Tuple, Optional

from django.db.models import Q, Count, IntegerField, Value, F, QuerySet
from django.db.models.functions import Substr
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from ....models.appairage import AppairageStatut
from ....models.partenaires import Partenaire
from ....models.prospection_choices import ProspectionChoices


class PartenaireStatsViewSet(viewsets.ViewSet):
    """
    /api/partenaire-stats/            -> overview (GET list)
    /api/partenaire-stats/grouped/    -> grouped by 'by' (GET)
    /api/partenaire-stats/tops/       -> tops (GET)
    """

    permission_classes = [permissions.IsAuthenticated]

    # ------------------------------
    # Helpers scope staff/admin
    # ------------------------------
    def _is_admin_like(self, user) -> bool:
        return bool(
            getattr(user, "is_superuser", False)
            or (hasattr(user, "is_admin") and callable(user.is_admin) and user.is_admin())
        )

    def _staff_centre_ids(self, user) -> Optional[List[int]]:
        """None => admin/superadmin → accès global ; [] => staff sans centre."""
        if self._is_admin_like(user):
            return None
        if getattr(user, "is_staff", False) and hasattr(user, "centres"):
            return list(user.centres.values_list("id", flat=True))
        return []

    def _staff_departement_codes(self, user) -> List[str]:
        """
        Codes département [:2] depuis user / user.profile (departements_codes|departements),
        supporte str, list/tuple/set, ou M2M d'objets avec attribut .code.
        """
        def _norm(val):
            if val is None:
                return []
            if hasattr(val, "all"):  # M2M
                return list({str(getattr(o, "code", o))[:2] for o in val.all() if o})
            if isinstance(val, (list, tuple, set)):
                return list({str(x)[:2] for x in val if x})
            s = str(val).strip()
            return [s[:2]] if s else []

        for owner in (user, getattr(user, "profile", None)):
            if not owner:
                continue
            for attr in ("departements_codes", "departements"):
                if hasattr(owner, attr):
                    codes = _norm(getattr(owner, attr))
                    if codes:
                        return codes
        return []
    
    def _base_qs(self, request) -> QuerySet:
        """
        Construit le queryset de base déjà restreint en fonction du user.
        Ainsi, list/grouped/tops héritent tous du même périmètre.
        """
        qs = Partenaire.objects.all()
        qs = self._apply_base_filters(qs, request)
        qs = self._scope_partenaires_for_user(qs, getattr(request, "user", None))
        return qs


    def _scope_partenaires_for_user(self, qs: QuerySet, user):
        """
        Périmètre:
        - admin/superadmin → global
        - staff → union (OR) des centres assignés **OU** des départements,
                    en considérant: Partenaire.default_centre, Partenaire.zip_code,
                    Prospections.centre et Appairages.formation.centre.
        - candidats/stagiaires → uniquement les partenaires liés à leurs prospections
        - autres → aucun accès
        """
        if not (user and user.is_authenticated):
            return qs.none()

        # Accès complet pour admin/superadmin
        if self._is_admin_like(user):
            return qs

        # Restriction staff
        if getattr(user, "is_staff", False):
            centre_ids = self._staff_centre_ids(user)
            dep_codes = self._staff_departement_codes(user)

            if not centre_ids and not dep_codes:
                return qs.none()

            q = Q()
            if centre_ids:
                q |= Q(default_centre_id__in=centre_ids)
                q |= Q(prospections__centre_id__in=centre_ids)
                q |= Q(appairages__formation__centre_id__in=centre_ids)
            if dep_codes:
                q_dep = Q()
                for code in dep_codes:
                    q_dep |= Q(zip_code__startswith=code)
                    q_dep |= Q(prospections__centre__code_postal__startswith=code)
                    q_dep |= Q(appairages__formation__centre__code_postal__startswith=code)
                q |= q_dep
            return qs.filter(q).distinct()

        # ✅ Cas candidat / stagiaire : uniquement ses partenaires via prospections
        if hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire():
            return qs.filter(prospections__owner_id=user.id).distinct()

        # Tous les autres (ex: utilisateur inconnu ou rôle test) → aucun accès
        return qs.none()

    # ------------------------------
    # Helpers filtres
    # ------------------------------
    @staticmethod
    def _date_filters(request) -> Tuple[Optional[str], Optional[str]]:
        df = request.query_params.get("date_from") or None
        dt = request.query_params.get("date_to") or None
        return df, dt

    @staticmethod
    def _apply_base_filters(qs, request):
        """
        Ajoute des filtres "structurants" si besoin (centre_id, departement, search…).
        Laisse neutre pour ne pas surprendre le front.
        """
        return qs

    @staticmethod
    def _mk_pros_filters(date_from: Optional[str], date_to: Optional[str]) -> Q:
        q = Q()
        if date_from:
            q &= Q(prospections__date_prospection__date__gte=date_from)
        if date_to:
            q &= Q(prospections__date_prospection__date__lte=date_to)
        return q

    @staticmethod
    def _mk_app_filters(date_from: Optional[str], date_to: Optional[str]) -> Q:
        q = Q()
        if date_from:
            q &= Q(appairages__date_appairage__date__gte=date_from)
        if date_to:
            q &= Q(appairages__date_appairage__date__lte=date_to)
        return q



    # ------------------------------
    # GET /api/partenaire-stats/  (overview)
    # ------------------------------
    def list(self, request):
        date_from, date_to = self._date_filters(request)
        base_qs = self._base_qs(request)

        pros_q = self._mk_pros_filters(date_from, date_to)
        app_q = self._mk_app_filters(date_from, date_to)

        # KPIs globaux
        agg = base_qs.aggregate(
            nb_partenaires=Count("id", distinct=True),
            nb_avec_contact=Count(
                "id",
                distinct=True,
                filter=(
                    (Q(contact_nom__isnull=False) & ~Q(contact_nom="")) |
                    (Q(contact_email__isnull=False) & ~Q(contact_email="")) |
                    (Q(contact_telephone__isnull=False) & ~Q(contact_telephone=""))
                ),
            ),
            nb_avec_web=Count(
                "id",
                distinct=True,
                filter=Q(website__isnull=False) | Q(social_network_url__isnull=False),
            ),
            nb_avec_adresse=Count(
                "id",
                distinct=True,
                filter=Q(street_name__isnull=False) | Q(zip_code__isnull=False) | Q(city__isnull=False),
            ),
            prospections_total=Count("prospections", distinct=True, filter=pros_q),
            appairages_total=Count("appairages", distinct=True, filter=app_q),
            # formations liées via appairages + prospections
            nb_formations_app=Count(
                "appairages__formation",
                distinct=True,
                filter=app_q & Q(appairages__formation__isnull=False),
            ),
            nb_formations_pros=Count(
                "prospections__formation",
                distinct=True,
                filter=pros_q & Q(prospections__formation__isnull=False),
            ),
        )

        nb_formations_liees = (agg.get("nb_formations_app") or 0) + (agg.get("nb_formations_pros") or 0)

        # Détails par statut (prospections)
        pros_status_map = OrderedDict([
            ("a_faire", ProspectionChoices.STATUT_A_FAIRE),
            ("en_cours", ProspectionChoices.STATUT_EN_COURS),
            ("a_relancer", ProspectionChoices.STATUT_A_RELANCER),
            ("acceptee", ProspectionChoices.STATUT_ACCEPTEE),
            ("refusee", ProspectionChoices.STATUT_REFUSEE),
            ("annulee", ProspectionChoices.STATUT_ANNULEE),
            ("non_renseigne", ProspectionChoices.STATUT_NON_RENSEIGNE),
        ])
        pros_counts: Dict[str, int] = {}
        for key, val in pros_status_map.items():
            pros_counts[key] = base_qs.filter(pros_q & Q(prospections__statut=val)).values("prospections__id").distinct().count()

        # Détails par statut (appairages)
        app_status_map = OrderedDict([
            ("transmis", AppairageStatut.TRANSMIS),
            ("en_attente", AppairageStatut.EN_ATTENTE),
            ("accepte", AppairageStatut.ACCEPTE),
            ("refuse", AppairageStatut.REFUSE),
            ("annule", AppairageStatut.ANNULE),
            ("a_faire", AppairageStatut.A_FAIRE),
            ("contrat_a_signer", AppairageStatut.CONTRAT_A_SIGNER),
            ("contrat_en_attente", AppairageStatut.CONTRAT_EN_ATTENTE),
            ("appairage_ok", AppairageStatut.APPAIRAGE_OK),
        ])
        app_counts: Dict[str, int] = {}
        for key, val in app_status_map.items():
            app_counts[key] = base_qs.filter(app_q & Q(appairages__statut=val)).values("appairages__id").distinct().count()

        data = {
            "kpis": {
                "nb_partenaires": agg.get("nb_partenaires") or 0,
                "nb_avec_contact": agg.get("nb_avec_contact") or 0,
                "nb_avec_web": agg.get("nb_avec_web") or 0,
                "nb_avec_adresse": agg.get("nb_avec_adresse") or 0,
                "nb_formations_liees": nb_formations_liees,
                "prospections_total": agg.get("prospections_total") or 0,
                "appairages_total": agg.get("appairages_total") or 0,
                "prospections": pros_counts,
                "appairages": app_counts,
            }
        }
        return Response(data)

    # ------------------------------
    # GET /api/partenaire-stats/grouped/?by=...
    # ------------------------------
    @action(detail=False, methods=["get"])
    def grouped(self, request):
        by = (request.query_params.get("by") or "type").strip()

        allowed = {"type", "secteur", "centre", "departement", "actions"}
        if by not in allowed:
            by = "type"

        date_from, date_to = self._date_filters(request)
        pros_q = self._mk_pros_filters(date_from, date_to)
        app_q = self._mk_app_filters(date_from, date_to)

        qs = self._base_qs(request)

        # Group fields
        group_fields: List[str] = []
        if by == "type":
            group_fields = ["type"]
        elif by == "secteur":
            group_fields = ["secteur_activite"]
        elif by == "centre":
            group_fields = ["default_centre_id", "default_centre__nom"]
        elif by == "departement":
            qs = qs.annotate(departement=Substr("zip_code", 1, 2))
            group_fields = ["departement"]
        elif by == "actions":
            group_fields = ["actions"]

        # Prospection status annotations
        pros_status_pairs = [
            ("a_faire", ProspectionChoices.STATUT_A_FAIRE),
            ("en_cours", ProspectionChoices.STATUT_EN_COURS),
            ("a_relancer", ProspectionChoices.STATUT_A_RELANCER),
            ("acceptee", ProspectionChoices.STATUT_ACCEPTEE),
            ("refusee", ProspectionChoices.STATUT_REFUSEE),
            ("annulee", ProspectionChoices.STATUT_ANNULEE),
            ("non_renseigne", ProspectionChoices.STATUT_NON_RENSEIGNE),
        ]
        pros_status_counts = {
            key: Count("prospections", filter=pros_q & Q(prospections__statut=val), distinct=True)
            for key, val in pros_status_pairs
        }

        # Appairage status annotations
        app_status_pairs = [
            ("transmis", AppairageStatut.TRANSMIS),
            ("en_attente", AppairageStatut.EN_ATTENTE),
            ("accepte", AppairageStatut.ACCEPTE),
            ("refuse", AppairageStatut.REFUSE),
            ("annule", AppairageStatut.ANNULE),
            ("a_faire", AppairageStatut.A_FAIRE),
            ("contrat_a_signer", AppairageStatut.CONTRAT_A_SIGNER),
            ("contrat_en_attente", AppairageStatut.CONTRAT_EN_ATTENTE),
            ("appairage_ok", AppairageStatut.APPAIRAGE_OK),
        ]
        app_status_counts_raw = {
            key: Count("appairages", filter=app_q & Q(appairages__statut=val), distinct=True)
            for key, val in app_status_pairs
        }

        # Fusion en évitant les doublons (ex: 'a_faire' existe dans les 2 familles)
        annot_status = {**pros_status_counts}
        for k, v in app_status_counts_raw.items():
            key = k if k not in annot_status else f"app_{k}"
            annot_status[key] = v

        results = (
            qs.values(*group_fields)
            .annotate(
                nb_partenaires=Count("id", distinct=True),
                nb_avec_contact=Count(
                    "id",
                    distinct=True,
                    filter=(
                        (Q(contact_nom__isnull=False) & ~Q(contact_nom="")) |
                        (Q(contact_email__isnull=False) & ~Q(contact_email="")) |
                        (Q(contact_telephone__isnull=False) & ~Q(contact_telephone=""))
                    ),
                ),
                nb_avec_web=Count(
                    "id",
                    distinct=True,
                    filter=Q(website__isnull=False) | Q(social_network_url__isnull=False),
                ),
                nb_avec_adresse=Count(
                    "id",
                    distinct=True,
                    filter=Q(street_name__isnull=False) | Q(zip_code__isnull=False) | Q(city__isnull=False),
                ),
                prospections_total=Count("prospections", distinct=True, filter=pros_q),
                appairages_total=Count("appairages", distinct=True, filter=app_q),
                **annot_status,
            )
            .order_by(*group_fields)
        )

        return Response({
            "by": by,
            "results": list(results),
        })

    # ------------------------------
    # GET /api/partenaire-stats/tops/
    # ------------------------------
    @action(detail=False, methods=["get"])
    def tops(self, request):
        date_from, date_to = self._date_filters(request)
        pros_q = self._mk_pros_filters(date_from, date_to)
        app_q = self._mk_app_filters(date_from, date_to)

        base_qs = self._base_qs(request)

        # TOP par appairages
        top_appairages = (
            base_qs
            .annotate(appairages_count=Count("appairages", distinct=True, filter=app_q))
            .filter(appairages_count__gt=0)
            .values("id", "nom", "appairages_count")
            .order_by("-appairages_count", "nom")[:10]
        )
        top_appairages = [
            {"id": r["id"], "nom": r["nom"], "count": r["appairages_count"]} for r in top_appairages
        ]

        # TOP par prospections
        top_prospections = (
            base_qs
            .annotate(prospections_count=Count("prospections", distinct=True, filter=pros_q))
            .filter(prospections_count__gt=0)
            .values("id", "nom", "prospections_count")
            .order_by("-prospections_count", "nom")[:10]
        )
        top_prospections = [
            {"id": r["id"], "nom": r["nom"], "count": r["prospections_count"]} for r in top_prospections
        ]

        return Response({
            "top_appairages": top_appairages,
            "top_prospections": top_prospections,
        })
