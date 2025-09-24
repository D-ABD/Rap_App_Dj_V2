# rap_app/api/viewsets/stats_viewsets/appairages_stats_viewsets.py
from __future__ import annotations
from typing import Dict, Optional, List, Literal
import logging

from django.db.models import Count, Q, QuerySet, Value
from django.db.models.functions import Substr, Coalesce
from django.utils.dateparse import parse_date

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from rap_app.models.appairage import Appairage, AppairageStatut

logger = logging.getLogger(__name__)

GroupKey = Literal["centre", "departement", "statut", "formation", "partenaire"]


def _safe_status_key(raw: str) -> str:
    """Normalise un code de statut en clé safe: espaces → '_'."""
    return (raw or "").replace(" ", "_").lower()


def _to_int_or_none(val) -> Optional[int]:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


class AppairageStatsViewSet(GenericViewSet):
    """
    Endpoints
    ---------
    GET /appairage-stats/                  → KPIs globaux (résumé)
    GET /appairage-stats/grouped/?by=...   → groupés par centre|departement|statut|formation|partenaire
    GET /appairage-stats/tops/             → tops partenaires / formations
    """
    permission_classes = [IsAuthenticated]

    # ────────────────────────────────────────────────────────────
    # Helpers périmètre staff/admin
    # ────────────────────────────────────────────────────────────
    def _is_admin_like(self, user) -> bool:
        return bool(
            getattr(user, "is_superuser", False)
            or (hasattr(user, "is_admin") and callable(user.is_admin) and user.is_admin())
        )

    def _staff_centre_ids(self, user) -> Optional[List[int]]:
        """None = admin-like → global ; [] = staff sans centres → aucun résultat."""
        if self._is_admin_like(user):
            return None
        if getattr(user, "is_staff", False) and hasattr(user, "centres"):
            return list(user.centres.values_list("id", flat=True))
        return []

    def _staff_departement_codes(self, user) -> List[str]:
        """
        Récupère les codes département ([:2]) depuis user / user.profile via
        attributs departements_codes|departements (liste/M2M/str).
        """
        def _norm_codes(val):
            if val is None:
                return []
            if hasattr(val, "all"):  # M2M
                return list({str(getattr(o, "code", o))[:2] for o in val.all() if o})
            if isinstance(val, (list, tuple, set)):
                return list({str(x)[:2] for x in val if x})
            s = str(val).strip()
            return [s[:2]] if s else []

        for owner in (self.request.user, getattr(self.request.user, "profile", None)):
            if not owner:
                continue
            for attr in ("departements_codes", "departements"):
                if hasattr(owner, attr):
                    codes = _norm_codes(getattr(owner, attr))
                    if codes:
                        return codes
        return []

    def _scope_appairages_for_user(self, qs: QuerySet) -> QuerySet:
        """
        Périmètre:
          - admin/superuser → global
          - staff → union (OR) des centres assignés **OU** des départements (via centre **ou** partenaire)
          - autres → pas de restriction spécifique ici
        """
        user = getattr(self.request, "user", None)
        if not (user and user.is_authenticated):
            return qs.none()

        if self._is_admin_like(user):
            return qs

        if getattr(user, "is_staff", False):
            centre_ids = self._staff_centre_ids(user)  # [] si pas d'attribut/valeur
            dep_codes = self._staff_departement_codes(user)

            if centre_ids is None:
                return qs
            if not centre_ids and not dep_codes:
                return qs.none()

            q = Q()
            if centre_ids:
                q |= Q(formation__centre_id__in=centre_ids)
            if dep_codes:
                q_dep = Q()
                for code in dep_codes:
                    # visibilité par département soit côté centre de la formation, soit côté partenaire
                    q_dep |= Q(formation__centre__code_postal__startswith=code) | Q(partenaire__zip_code__startswith=code)
                q |= q_dep
            return qs.filter(q).distinct()

        return qs

    # ────────────────────────────────────────────────────────────
    # Base QS + filtres
    # ────────────────────────────────────────────────────────────
    def get_queryset(self) -> QuerySet:
        qs = Appairage.objects.select_related("formation", "formation__centre", "partenaire", "candidat")
        return self._scope_appairages_for_user(qs)

    def _apply_common_filters(self, qs: QuerySet) -> QuerySet:
        p = self.request.query_params

        # Dates (YYYY-MM-DD)
        dfrom = parse_date(str(p.get("date_from"))) if p.get("date_from") else None
        dto = parse_date(str(p.get("date_to"))) if p.get("date_to") else None
        if dfrom:
            qs = qs.filter(date_appairage__date__gte=dfrom)
        if dto:
            qs = qs.filter(date_appairage__date__lte=dto)

        # Centre (via formation.centre)
        centre = _to_int_or_none(p.get("centre"))
        if centre is not None:
            qs = qs.filter(formation__centre_id=centre)

        # Département (via partenaire.zip_code -> 2 premiers chiffres)
        departement = p.get("departement")
        if departement:
            qs = qs.filter(partenaire__zip_code__startswith=str(departement)[:2])

        # Formation / Partenaire
        formation = _to_int_or_none(p.get("formation"))
        if formation is not None:
            qs = qs.filter(formation_id=formation)

        partenaire = _to_int_or_none(p.get("partenaire"))
        if partenaire is not None:
            qs = qs.filter(partenaire_id=partenaire)

        # Statut
        statut = p.get("statut")
        if statut:
            statut_key = _safe_status_key(statut)
            inv = { _safe_status_key(k): k for k, _ in AppairageStatut.choices }
            if statut_key in inv:
                qs = qs.filter(statut=inv[statut_key])
            else:
                # fallback historique: on tente la valeur brute en remplaçant _ par " "
                raw_guess = statut_key.replace("_", " ")
                logger.warning("AppairageStatsViewSet: statut inconnu '%s' (fallback='%s')", statut, raw_guess)
                qs = qs.filter(statut=raw_guess)

        return qs

    def _pct(self, num, den) -> float:
        try:
            n = int(num or 0)
            d = int(den or 0)
        except Exception:
            return 0.0
        return round((n * 100.0 / d), 2) if d > 0 else 0.0

    # ────────────────────────────────────────────────────────────
    # LIST (overview) — KPIs globaux + taux de transformation
    # ────────────────────────────────────────────────────────────
    def list(self, request, *args, **kwargs):
        qs = self._apply_common_filters(self.get_queryset())

        # KPIs distincts (1 requête)
        agg = qs.aggregate(
            appairages_total=Count("id", distinct=True),
            nb_candidats_distincts=Count("candidat", distinct=True),
            nb_partenaires_distincts=Count("partenaire", distinct=True),
            nb_formations_distinctes=Count("formation", distinct=True),
        )

        # Comptes par statut (sécurisé avec distinct)
        raw_counts = dict(
            qs.values("statut").annotate(c=Count("id", distinct=True)).values_list("statut", "c")
        )
        status_map: Dict[str, int] = {
            _safe_status_key(code): int(raw_counts.get(code, 0))
            for code, _ in AppairageStatut.choices
        }

        # Taux de transformation = appairage_ok / total
        total = int(agg.get("appairages_total") or 0)
        ok = int(status_map.get("appairage_ok") or 0)
        taux_transformation = self._pct(ok, total)

        # Répartition par statut (tableau code/label/count)
        statut_labels = dict(AppairageStatut.choices)
        by_statut = [
            {"code": code, "label": statut_labels.get(code, code), "count": raw_counts.get(code, 0)}
            for code, _ in AppairageStatut.choices
        ]

        payload = {
            "kpis": {**{k: int(v or 0) for k, v in agg.items()}, "statuts": status_map, "taux_transformation": taux_transformation},
            "repartition": {"par_statut": by_statut},
            "filters_echo": {k: v for k, v in request.query_params.items()},
        }
        return Response(payload)

    # ────────────────────────────────────────────────────────────
    # Grouped — KPIs par groupe + taux_transformation
    # ────────────────────────────────────────────────────────────
    @action(detail=False, methods=["GET"], url_path="grouped")
    def grouped(self, request):
        by: GroupKey = (request.query_params.get("by") or "centre").lower()  # défaut utile
        allowed = {"centre", "departement", "statut", "formation", "partenaire"}
        if by not in allowed:
            return Response({"detail": f"'by' doit être dans {sorted(allowed)}"}, status=400)

        qs = self._apply_common_filters(self.get_queryset())

        # pré-annotation departement (2 premiers chiffres du CP partenaire)
        qs = qs.annotate(departement=Coalesce(Substr("partenaire__zip_code", 1, 2), Value("—")))

        # Champs de groupage
        group_fields_map = {
            "centre": ["formation__centre_id", "formation__centre__nom"],
            "departement": ["departement"],
            "statut": ["statut"],
            "formation": ["formation_id", "formation__nom", "formation__centre__nom"],
            "partenaire": ["partenaire_id", "partenaire__nom"],
        }
        group_fields = group_fields_map[by]

        # Annotations par statut (sécurisé avec distinct)
        status_annots = {
            _safe_status_key(code): Count("id", filter=Q(statut=code), distinct=True)
            for code, _ in AppairageStatut.choices
        }

        rows = list(
            qs.values(*group_fields).annotate(
                appairages_total=Count("id", distinct=True),
                nb_candidats=Count("candidat", distinct=True),
                nb_partenaires=Count("partenaire", distinct=True),
                nb_formations=Count("formation", distinct=True),
                **status_annots,
            ).order_by(*group_fields)
        )

        # Post-traitement : group_key / group_label + taux_transformation
        results = []
        for r in rows:
            out = dict(r)

            if by == "centre":
                out["group_key"] = r.get("formation__centre_id")
                out["group_label"] = r.get("formation__centre__nom") or (
                    f"Centre #{r.get('formation__centre_id')}" if r.get("formation__centre_id") is not None else "—"
                )
            elif by == "departement":
                out["group_key"] = r.get("departement") or "—"
                out["group_label"] = out["group_key"]
            elif by == "statut":
                raw = r.get("statut") or ""
                out["group_key"] = _safe_status_key(raw)
                out["group_label"] = dict(AppairageStatut.choices).get(raw, raw) or "—"
            elif by == "formation":
                out["group_key"] = r.get("formation_id")
                out["group_label"] = r.get("formation__nom") or (
                    f"Formation #{r.get('formation_id')}" if r.get("formation_id") is not None else "—"
                )
            elif by == "partenaire":
                out["group_key"] = r.get("partenaire_id")
                out["group_label"] = r.get("partenaire__nom") or (
                    f"Partenaire #{r.get('partenaire_id')}" if r.get("partenaire_id") is not None else "—"
                )

            total = int(out.get("appairages_total") or 0)
            ok = int(out.get("appairage_ok") or 0)  # ← annotation safe ci-dessus
            out["taux_transformation"] = self._pct(ok, total)

            results.append(out)

        return Response({
            "group_by": by,
            "results": results,
            "filters_echo": {k: v for k, v in request.query_params.items()},
        })

    # ────────────────────────────────────────────────────────────
    # Tops — partenaires / formations
    # ────────────────────────────────────────────────────────────
    @action(detail=False, methods=["GET"], url_path="tops")
    def tops(self, request):
        qs = self._apply_common_filters(self.get_queryset())

        def _top(qs: QuerySet, id_field: str, label_field: str, label_fallback_prefix: str):
            rows = list(
                qs.values(id_field, label_field)
                .annotate(cnt=Count("id", distinct=True))
                .order_by("-cnt")[:10]
            )
            out = []
            for r in rows:
                _id = r.get(id_field)
                _nom = r.get(label_field) or f"{label_fallback_prefix} #{_id}"
                out.append({"id": _id, "nom": _nom, "count": r["cnt"]})
            return out

        top_partenaires = _top(qs, "partenaire_id", "partenaire__nom", "Partenaire")
        top_formations = _top(qs, "formation_id", "formation__nom", "Formation")

        return Response({
            "top_partenaires": top_partenaires,
            "top_formations": top_formations,
            "filters_echo": {k: v for k, v in request.query_params.items()},
        })
