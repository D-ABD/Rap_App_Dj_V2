from __future__ import annotations

from typing import Literal, Optional

from django.db.models import Count, Q, Value
from django.db.models.functions import Coalesce, Substr
from django.utils.dateparse import parse_date
from django.utils import timezone

from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ....models.commentaires_appairage import CommentaireAppairage


try:
    from ..permissions import IsOwnerOrStaffOrAbove  # type: ignore
except Exception:  # pragma: no cover
    IsOwnerOrStaffOrAbove = IsAuthenticated

try:
    from ..mixins import RestrictToUserOwnedQueryset  # type: ignore
except Exception:  # pragma: no cover
    class RestrictToUserOwnedQueryset:
        def restrict_queryset_to_user(self, qs): return qs


GroupKey = Literal[
    "centre",
    "departement",
    "formation",
    "partenaire",
    "statut_snapshot",
    "appairage",
]


class AppairageCommentaireStatsViewSet(RestrictToUserOwnedQueryset, GenericViewSet):
    """KPIs & agrégats sur **Commentaires d’appairage**."""

    permission_classes = [IsOwnerOrStaffOrAbove]

    # ───────────────────────────────
    # Helpers périmètre
    # ───────────────────────────────
    def _is_admin_like(self, user) -> bool:
        return getattr(user, "is_superuser", False) or (
            hasattr(user, "is_admin") and callable(user.is_admin) and user.is_admin()
        )

    def _staff_centre_ids(self, user) -> Optional[list[int]]:
        if self._is_admin_like(user):
            return None
        if getattr(user, "is_staff", False) and hasattr(user, "centres"):
            return list(user.centres.values_list("id", flat=True))
        return []

    def _staff_departement_codes(self, user) -> list[str]:
        def _norm(val):
            if not val:
                return []
            if hasattr(val, "all"):
                return list({str(getattr(x, "code", x))[:2] for x in val.all()})
            if isinstance(val, (list, tuple, set)):
                return list({str(x)[:2] for x in val if x})
            return [str(val)[:2]]
        for owner in (user, getattr(user, "profile", None)):
            if not owner:
                continue
            for attr in ("departements_codes", "departements"):
                if hasattr(owner, attr):
                    codes = _norm(getattr(owner, attr))
                    if codes:
                        return codes
        return []

    def _scope_queryset_for_user(self, qs, user):
        if not (user and user.is_authenticated):
            return qs.none()
        if self._is_admin_like(user):
            return qs
        if getattr(user, "is_staff", False):
            centre_ids = self._staff_centre_ids(user)
            dep_codes = self._staff_departement_codes(user)
            if centre_ids is None:
                return qs
            if not centre_ids and not dep_codes:
                return qs.none()
            q = Q()
            if centre_ids:
                q |= Q(appairage__formation__centre_id__in=centre_ids)
            if dep_codes:
                q_dep = Q()
                for code in dep_codes:
                    q_dep |= Q(appairage__formation__centre__code_postal__startswith=code)
                q |= q_dep
            return qs.filter(q).distinct()
        return qs

    # ───────────────────────────────
    # Base queryset + filtres
    # ───────────────────────────────
    def get_queryset(self):
        qs = CommentaireAppairage.objects.select_related(
            "appairage",
            "appairage__formation",
            "appairage__formation__centre",
            "appairage__partenaire",
            "created_by",
        )
        if hasattr(self, "restrict_queryset_to_user"):
            qs = self.restrict_queryset_to_user(qs)
        qs = self._scope_queryset_for_user(qs, getattr(self.request, "user", None))
        return qs

    def _apply_common_filters(self, qs):
        p = self.request.query_params
        dfrom = parse_date(p.get("date_from") or "") if p.get("date_from") else None
        dto = parse_date(p.get("date_to") or "") if p.get("date_to") else None
        if dfrom:
            qs = qs.filter(created_at__date__gte=dfrom)
        if dto:
            qs = qs.filter(created_at__date__lte=dto)

        if p.get("centre"):
            qs = qs.filter(appairage__formation__centre_id=p["centre"])
        if p.get("departement"):
            qs = qs.filter(appairage__formation__centre__code_postal__startswith=str(p["departement"])[:2])
        if p.get("formation"):
            qs = qs.filter(appairage__formation_id=p["formation"])
        if p.get("partenaire"):
            qs = qs.filter(appairage__partenaire_id=p["partenaire"])
        if p.get("statut"):
            qs = qs.filter(appairage__statut=p["statut"])
        return qs

    # ───────────────────────────────
    # LIST = KPIs globaux
    # ───────────────────────────────
    def list(self, request, *args, **kwargs):
        qs = self._apply_common_filters(self.get_queryset())

        agg = qs.aggregate(
            total=Count("id"),
            distinct_appairages=Count("appairage", distinct=True),
            distinct_auteurs=Count("created_by", distinct=True),
        )

        by_statut = list(qs.values("statut_snapshot").annotate(count=Count("id")).order_by("statut_snapshot"))
        by_auteur = list(qs.values("created_by").annotate(count=Count("id")).order_by("-count"))

        payload = {
            "kpis": {k: int(v or 0) for k, v in agg.items()},
            "repartition": {
                "par_statut_snapshot": by_statut,
                "par_auteur": by_auteur,
            },
            "filters_echo": dict(request.query_params),
        }
        return Response(payload)

    # ───────────────────────────────
    # LATEST = derniers commentaires
    # ───────────────────────────────
    @action(detail=False, methods=["GET"], url_path="latest")
    def latest(self, request):
        qs = self._apply_common_filters(self.get_queryset()).order_by("-created_at")

        try:
            limit = int(request.query_params.get("limit") or 20)
        except ValueError:
            limit = 20
        qs = qs[:limit]

        now = timezone.now()
        results = []
        for c in qs:
            results.append({
                "id": c.id,
                "appairage_id": c.appairage_id,
                "centre_nom": getattr(c.appairage.formation.centre, "nom", None),
                "formation_nom": getattr(c.appairage.formation, "nom", None),
                "partenaire_nom": getattr(c.appairage.partenaire, "nom", None),
                "statut_snapshot": c.statut_snapshot,
                "body": c.body[:280],
                "auteur": c.auteur_nom(),
                "date": c.created_at.strftime("%d/%m/%Y") if c.created_at else None,
                "heure": c.created_at.strftime("%H:%M") if c.created_at else None,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                "is_recent": c.created_at and c.created_at.date() == now.date(),
                "is_edited": bool(c.updated_at and c.updated_at > c.created_at),
            })

        payload = {
            "count": self.get_queryset().count(),
            "results": results,
            "filters_echo": dict(request.query_params),
        }
        return Response(payload)

    # ───────────────────────────────
    # GROUPED = regroupements dynamiques
    # ───────────────────────────────
    @action(detail=False, methods=["GET"], url_path="grouped")
    def grouped(self, request):
        by: GroupKey = (request.query_params.get("by") or "departement").lower()
        allowed = {"centre", "departement", "formation", "partenaire", "statut_snapshot", "appairage"}
        if by not in allowed:
            return Response({"detail": "Paramètre 'by' invalide."}, status=400)

        qs = self._apply_common_filters(self.get_queryset())
        qs = qs.annotate(
            departement=Coalesce(Substr("appairage__formation__centre__code_postal", 1, 2), Value("NA"))
        )

        group_fields_map = {
            "centre": ["appairage__formation__centre_id", "appairage__formation__centre__nom"],
            "departement": ["departement"],
            "formation": ["appairage__formation_id", "appairage__formation__nom", "appairage__formation__num_offre"],
            "partenaire": ["appairage__partenaire_id", "appairage__partenaire__nom"],
            "statut_snapshot": ["statut_snapshot"],
            "appairage": ["appairage_id"],
        }

        rows = list(
            qs.values(*group_fields_map[by]).annotate(
                total=Count("id"),
                distinct_appairages=Count("appairage", distinct=True),
                distinct_auteurs=Count("created_by", distinct=True),
            ).order_by(*group_fields_map[by])
        )

        for r in rows:
            if by == "centre":
                r["group_key"] = r.get("appairage__formation__centre_id")
                r["group_label"] = r.get("appairage__formation__centre__nom") or "—"
            elif by == "departement":
                r["group_key"] = r.get("departement")
                r["group_label"] = r.get("departement") or "—"
            elif by == "formation":
                r["group_key"] = r.get("appairage__formation_id")
                r["group_label"] = r.get("appairage__formation__nom") or "—"
            elif by == "partenaire":
                r["group_key"] = r.get("appairage__partenaire_id")
                r["group_label"] = r.get("appairage__partenaire__nom") or "—"
            elif by == "statut_snapshot":
                r["group_key"] = r.get("statut_snapshot")
                r["group_label"] = r.get("statut_snapshot") or "—"
            elif by == "appairage":
                r["group_key"] = r.get("appairage_id")
                r["group_label"] = f"Appairage #{r.get('appairage_id')}"
        return Response({"group_by": by, "results": rows})
