"""
ViewSet DRF — Statistiques Prospection (scope staff centres + départements)
---------------------------------------------------------------------------

Brancher dans `urls.py` (router) :

    from rest_framework.routers import SimpleRouter
    from .prospection_stats import ProspectionStatsViewSet
    router = SimpleRouter()
    router.register(r"prospection-stats", ProspectionStatsViewSet, basename="prospection-stats")

Endpoints :
    GET /prospection-stats/                    → KPIs globaux (résumé)
    GET /prospection-stats/grouped/?by=...     → groupés par centre|departement|owner|formation|partenaire|statut|objectif|motif|type

Filtres (query params, tous optionnels) :
    - date_from=YYYY-MM-DD       (date_prospection >= …)
    - date_to=YYYY-MM-DD         (date_prospection <= …)
    - centre=<id>
    - departement=<DD>           (sur Centre.code_postal commence par DD)
    - formation=<id>
    - partenaire=<id>
    - owner=<user_id>
    - statut=<code>              (ProspectionChoices)
    - objectif=<code>            (ProspectionChoices)
    - motif=<code>               (ProspectionChoices)
    - type=<code>                (ProspectionChoices.TYPE_*)
    - relance_due=true|false     (uniquement celles à relancer aujourd’hui ou avant)

Notes :
    • Périmètre staff : centres affectés + départements (préfixe CP) ; admin = global.
    • KPIs : total, actives, à relancer, acceptées, refusées, annulées, par statut/motif/objectif/moyen,
             + taux_acceptation (% acceptées / total).
    • `group_label` renvoyé pour tous les regroupements.
    • Quand `by=formation`, les champs suivants sont aussi renvoyés :
        - formation__num_offre
        - formation__centre__nom
"""
from __future__ import annotations

from typing import Literal, Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count, Q, Value, F
from django.db.models.functions import Coalesce, Substr
from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

try:
    # Si dispo, on réutilise vos permissions/mixins
    from ..permissions import IsOwnerOrStaffOrAbove  # type: ignore
except Exception:  # pragma: no cover
    IsOwnerOrStaffOrAbove = IsAuthenticated  # fallback

try:
    from ..mixins import RestrictToUserOwnedQueryset  # type: ignore
except Exception:  # pragma: no cover
    class RestrictToUserOwnedQueryset:  # stub minimal
        def restrict_queryset_to_user(self, qs):
            return qs

# ⚠️ Ajustez les imports selon votre arborescence
from ....models.prospection import Prospection, ProspectionChoices

GroupKey = Literal[
    "centre",
    "departement",
    "owner",
    "formation",
    "partenaire",
    "statut",
    "objectif",
    "motif",
    "type",
]


class ProspectionStatsViewSet(RestrictToUserOwnedQueryset, GenericViewSet):
    """Vue d’agrégats/KPI sur **Prospection** (JSON only)."""

    permission_classes = [IsOwnerOrStaffOrAbove]

    # ────────────────────────────────────────────────────────────
    # Helpers périmètre user (mêmes principes que formations)
    # ────────────────────────────────────────────────────────────
    def _is_admin_like(self, user) -> bool:
        return bool(
            getattr(user, "is_superuser", False)
            or (hasattr(user, "is_admin") and callable(user.is_admin) and user.is_admin())
        )

    def _staff_centre_ids(self, user) -> Optional[list[int]]:
        """
        Retourne la liste des IDs de centres du staff.
        - None => admin/superadmin → accès global
        - []   => staff sans centre → aucun résultat (pour ce ViewSet)
        """
        if self._is_admin_like(user):
            return None
        if getattr(user, "is_staff", False) and hasattr(user, "centres"):
            return list(user.centres.values_list("id", flat=True))
        return []

    def _staff_departement_codes(self, user) -> list[str]:
        """
        Codes département (ex: ["92","75"]) via :
          - user.departements_codes (str/list/tuple/set)
          - user.departements (M2M d'objets avec attribut .code)
          - user.profile.departements_codes / user.profile.departements
        """
        def _norm_codes(val):
            if val is None:
                return []
            if hasattr(val, "all"):  # M2M
                out = []
                for obj in val.all():
                    code = getattr(obj, "code", None) or str(obj)
                    if code:
                        out.append(str(code)[:2])
                return list(set(out))
            if isinstance(val, (list, tuple, set)):
                return list({str(x)[:2] for x in val if x is not None and str(x).strip()})
            s = str(val).strip()
            return [s[:2]] if s else []

        for owner in (user, getattr(user, "profile", None)):
            if not owner:
                continue
            for attr in ("departements_codes", "departements"):
                if hasattr(owner, attr):
                    codes = _norm_codes(getattr(owner, attr))
                    if codes:
                        return codes
        return []

    def _scope_prospections_for_user(self, qs, user):
        """
        Applique le périmètre de visibilité:
          - admin/superadmin → global
          - staff → prospections du périmètre centres + départements
          - autres → pas de filtre spécifique ici (peut être géré par RestrictToUserOwnedQueryset)
        """
        if not (user and user.is_authenticated):
            return qs.none()

        if self._is_admin_like(user):
            return qs

        if getattr(user, "is_staff", False):
            centre_ids = self._staff_centre_ids(user)
            if centre_ids is None:
                return qs
            dep_codes = self._staff_departement_codes(user)

            if not centre_ids and not dep_codes:
                return qs.none()

            q = Q()
            if centre_ids:
                q |= Q(centre_id__in=centre_ids)
            if dep_codes:
                q_dep = Q()
                for code in dep_codes:
                    q_dep |= Q(centre__code_postal__startswith=code)
                q |= q_dep

            return qs.filter(q).distinct()

        return qs

    # ────────────────────────────────────────────────────────────
    # Helpers data
    # ────────────────────────────────────────────────────────────
    def get_queryset(self):
        qs = Prospection.objects.select_related("centre", "formation", "formation__centre", "partenaire", "owner")
        # éventuel scope "owned" générique
        if hasattr(self, "restrict_queryset_to_user"):
            qs = self.restrict_queryset_to_user(qs)
        # périmètre staff (centres + départements)
        qs = self._scope_prospections_for_user(qs, getattr(self.request, "user", None))
        return qs

    def _apply_common_filters(self, qs):
        p = self.request.query_params

        raw_from = p.get("date_from")
        raw_to = p.get("date_to")
        dfrom = parse_date(str(raw_from)) if raw_from not in (None, "") else None
        dto = parse_date(str(raw_to)) if raw_to not in (None, "") else None

        if dfrom:
            qs = qs.filter(date_prospection__date__gte=dfrom)
        if dto:
            qs = qs.filter(date_prospection__date__lte=dto)

        if p.get("centre"):
            qs = qs.filter(centre_id=p.get("centre"))
        if p.get("departement"):
            qs = qs.filter(centre__code_postal__startswith=str(p.get("departement"))[:2])
        if p.get("formation"):
            qs = qs.filter(formation_id=p.get("formation"))
        if p.get("partenaire"):
            qs = qs.filter(partenaire_id=p.get("partenaire"))
        if p.get("owner"):
            qs = qs.filter(owner_id=p.get("owner"))

        if p.get("statut"):
            qs = qs.filter(statut=p.get("statut"))
        if p.get("objectif"):
            qs = qs.filter(objectif=p.get("objectif"))
        if p.get("motif"):
            qs = qs.filter(motif=p.get("motif"))
        if p.get("type"):
            qs = qs.filter(type_prospection=p.get("type"))

        # relance_due=true → relance prévue <= aujourd’hui & non terminal
        relance_due = p.get("relance_due")
        if str(relance_due).lower() in {"true", "1", "yes", "oui"}:
            today = timezone.now().date()
            qs = qs.filter(
                relance_prevue__isnull=False,
                relance_prevue__lte=today
            ).exclude(
                statut__in=[
                    ProspectionChoices.STATUT_REFUSEE,
                    ProspectionChoices.STATUT_ANNULEE,
                ]
            )
        return qs

    # Petit helper pour les pourcentages
    def _pct(self, num, den) -> float:
        try:
            n = int(num or 0)
            d = int(den or 0)
        except Exception:
            return 0.0
        return round((n * 100.0 / d), 2) if d > 0 else 0.0

    # ────────────────────────────────────────────────────────────
    # LIST (overview) — KPIs globaux
    # ────────────────────────────────────────────────────────────
    def list(self, request, *args, **kwargs):
        qs = self._apply_common_filters(self.get_queryset())
        today = timezone.now().date()

        TERMINAUX = [
            ProspectionChoices.STATUT_REFUSEE,
            ProspectionChoices.STATUT_ANNULEE,
        ]

        agg = qs.aggregate(
            total=Count("id"),
            actives=Count("id", filter=~Q(statut__in=TERMINAUX)),
            a_relancer=Count(
                "id",
                filter=Q(relance_prevue__isnull=False, relance_prevue__lte=today) & ~Q(statut__in=TERMINAUX),
            ),
            acceptees=Count("id", filter=Q(statut=ProspectionChoices.STATUT_ACCEPTEE)),
            refusees=Count("id", filter=Q(statut=ProspectionChoices.STATUT_REFUSEE)),
            annulees=Count("id", filter=Q(statut=ProspectionChoices.STATUT_ANNULEE)),
            en_cours=Count("id", filter=Q(statut=ProspectionChoices.STATUT_EN_COURS)),
            a_faire=Count("id", filter=Q(statut=ProspectionChoices.STATUT_A_FAIRE)),
            a_relancer_statut=Count("id", filter=Q(statut=ProspectionChoices.STATUT_A_RELANCER)),
            non_renseigne=Count("id", filter=Q(statut=ProspectionChoices.STATUT_NON_RENSEIGNE)),
        )

        taux_acceptation = self._pct(agg.get("acceptees"), agg.get("total"))

        # Répartition par statut (clé = code, label = texte)
        by_statut_qs = qs.values("statut").annotate(count=Count("id")).order_by("statut")
        statut_labels = ProspectionChoices.get_statut_labels()
        by_statut = [
            {
                "code": r["statut"],
                "label": statut_labels.get(r["statut"], r["statut"]),
                "count": r["count"],
            }
            for r in by_statut_qs
        ]

        # Répartitions additionnelles
        by_objectif = list(qs.values("objectif").annotate(count=Count("id")).order_by("objectif"))
        by_motif = list(qs.values("motif").annotate(count=Count("id")).order_by("motif"))
        by_type = list(qs.values("type_prospection").annotate(count=Count("id")).order_by("type_prospection"))
        by_moyen = list(qs.values("moyen_contact").annotate(count=Count("id")).order_by("moyen_contact"))

        payload = {
            "kpis": {**{k: int(v or 0) for k, v in agg.items()}, "taux_acceptation": taux_acceptation},
            "repartition": {
                "par_statut": by_statut,
                "par_objectif": by_objectif,
                "par_motif": by_motif,
                "par_type": by_type,
                "par_moyen_contact": by_moyen,
            },
            "filters_echo": {k: v for k, v in request.query_params.items()},
        }
        return Response(payload)

    # ────────────────────────────────────────────────────────────
    # Grouped KPIs — centre/departement/owner/formation/partenaire/statut/objectif/motif/type
    # ────────────────────────────────────────────────────────────
    @action(detail=False, methods=["GET"], url_path="grouped")
    def grouped(self, request):
        by: GroupKey = (request.query_params.get("by") or "departement").lower()  # default utile
        allowed = {"centre", "departement", "owner", "formation", "partenaire", "statut", "objectif", "motif", "type"}
        if by not in allowed:
            return Response({"detail": "Paramètre 'by' invalide."}, status=400)

        qs = self._apply_common_filters(self.get_queryset())
        today = timezone.now().date()
        TERMINAUX = [ProspectionChoices.STATUT_REFUSEE, ProspectionChoices.STATUT_ANNULEE]

        # Pré-annot departement
        qs = qs.annotate(departement=Coalesce(Substr("centre__code_postal", 1, 2), Value("NA")))

        group_fields_map = {
            "centre": ["centre_id", "centre__nom"],
            "departement": ["departement"],
            "owner": ["owner_id", "owner__first_name", "owner__last_name", "owner__email", "owner__username"],
            # ↓↓↓ Ajout des champs formation__num_offre & formation__centre__nom
            "formation": ["formation_id", "formation__nom", "formation__num_offre", "formation__centre__nom"],
            "partenaire": ["partenaire_id", "partenaire__nom"],
            "statut": ["statut"],
            "objectif": ["objectif"],
            "motif": ["motif"],
            "type": ["type_prospection"],
        }
        group_fields = group_fields_map[by]

        rows = list(
            qs.values(*group_fields).annotate(
                total=Count("id"),
                actives=Count("id", filter=~Q(statut__in=TERMINAUX)),
                a_relancer=Count(
                    "id",
                    filter=Q(relance_prevue__isnull=False, relance_prevue__lte=today) & ~Q(statut__in=TERMINAUX),
                ),
                acceptees=Count("id", filter=Q(statut=ProspectionChoices.STATUT_ACCEPTEE)),
                refusees=Count("id", filter=Q(statut=ProspectionChoices.STATUT_REFUSEE)),
                annulees=Count("id", filter=Q(statut=ProspectionChoices.STATUT_ANNULEE)),
                en_cours=Count("id", filter=Q(statut=ProspectionChoices.STATUT_EN_COURS)),
                a_faire=Count("id", filter=Q(statut=ProspectionChoices.STATUT_A_FAIRE)),
                a_relancer_statut=Count("id", filter=Q(statut=ProspectionChoices.STATUT_A_RELANCER)),
                non_renseigne=Count("id", filter=Q(statut=ProspectionChoices.STATUT_NON_RENSEIGNE)),
            ).order_by(*group_fields)
        )

        # Labels clairs + taux_acceptation par ligne
        for r in rows:
            if by == "centre":
                r["group_key"] = r.get("centre_id")
                r["group_label"] = (
                    r.get("centre__nom")
                    or (f"Centre #{r.get('centre_id')}" if r.get("centre_id") is not None else "—")
                )
            elif by == "departement":
                r["group_key"] = r.get("departement")
                r["group_label"] = r.get("departement") or "—"
            elif by == "owner":
                rid = r.get("owner_id")
                fname = (r.get("owner__first_name") or "").strip()
                lname = (r.get("owner__last_name") or "").strip()
                fullname = f"{fname} {lname}".strip()
                fallback = r.get("owner__email") or r.get("owner__username")
                r["group_key"] = rid
                r["group_label"] = fullname or fallback or (f"Utilisateur #{rid}" if rid is not None else "—")
            elif by == "formation":
                r["group_key"] = r.get("formation_id")
                r["group_label"] = (
                    r.get("formation__nom")
                    or (f"Formation #{r.get('formation_id')}" if r.get("formation_id") is not None else "—")
                )
                # rien à faire de plus : `formation__num_offre` et `formation__centre__nom`
                # sont déjà présents dans le payload via .values(...)
            elif by == "partenaire":
                r["group_key"] = r.get("partenaire_id")
                r["group_label"] = (
                    r.get("partenaire__nom")
                    or (f"Partenaire #{r.get('partenaire_id')}" if r.get("partenaire_id") is not None else "—")
                )
            elif by == "statut":
                code = r.get("statut")
                label = ProspectionChoices.get_statut_labels().get(code, code)
                r["group_key"] = code
                r["group_label"] = label or (code or "—")
            elif by == "objectif":
                code = r.get("objectif")
                r["group_key"] = code
                r["group_label"] = code or "—"
            elif by == "motif":
                code = r.get("motif")
                r["group_key"] = code
                r["group_label"] = code or "—"
            elif by == "type":
                code = r.get("type_prospection")
                r["group_key"] = code
                r["group_label"] = code or "—"

            # Taux de transformation par ligne
            r["taux_acceptation"] = self._pct(r.get("acceptees"), r.get("total"))

        return Response({"group_by": by, "results": rows})
