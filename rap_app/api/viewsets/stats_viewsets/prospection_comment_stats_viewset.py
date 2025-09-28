# rap_app/api/viewsets/stats_viewsets/prospection_comment_stats_viewset.py
from __future__ import annotations

from typing import Optional

from django.db.models import Q, Value, Count
from django.db.models.functions import Coalesce, Substr
from django.utils.dateparse import parse_date
from django.utils import timezone

from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ....models.prospection_comments import ProspectionComment

try:
    from ...permissions import IsOwnerOrStaffOrAbove  # type: ignore
except Exception:  # pragma: no cover
    IsOwnerOrStaffOrAbove = IsAuthenticated  # fallback

try:
    from ...mixins import RestrictToUserOwnedQueryset  # type: ignore
except Exception:  # pragma: no cover
    class RestrictToUserOwnedQueryset:  # stub minimal
        def restrict_queryset_to_user(self, qs):
            return qs


class ProspectionCommentStatsViewSet(RestrictToUserOwnedQueryset, GenericViewSet):
    """
    Endpoints:
      GET /prospection-comment-stats/latest/   → derniers commentaires (limit=5 par défaut)
      GET /prospection-comment-stats/grouped/?by=centre|departement → options pour selects

    Filtres (query params, tous optionnels) :
      - date_from=YYYY-MM-DD (sur created_at)
      - date_to=YYYY-MM-DD
      - centre=<id>            (via prospection.centre)
      - departement=<DD>       (via prospection.centre.code_postal ^ DD)
      - formation=<id>         (via prospection.formation)
      - partenaire=<id>        (via prospection.partenaire)
      - owner=<user id>        (via prospection.owner)
      - is_internal=true|false
      - search="..."
      - limit=<n>              (défaut 5)
    """
    permission_classes = [IsOwnerOrStaffOrAbove]

    # ────────────────────────────────────────────────────────────
    # Helpers périmètre (aligné sur ProspectionStats)
    # ────────────────────────────────────────────────────────────
    def _is_admin_like(self, user) -> bool:
        return bool(
            getattr(user, "is_superuser", False)
            or (hasattr(user, "is_admin") and callable(user.is_admin) and user.is_admin())
        )

    def _staff_centre_ids(self, user) -> Optional[list[int]]:
        if self._is_admin_like(user):
            return None
        if getattr(user, "is_staff", False) and hasattr(user, "centres"):
            return list(user.centres.values_list("id", flat=True))
        return []

    def _staff_departement_codes(self, user) -> list[str]:
        def _norm_codes(val):
            if val is None:
                return []
            if hasattr(val, "all"):
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

    def _scope_for_user(self, qs, user):
        if not (user and user.is_authenticated):
            return qs.none()

        # Admin = accès global
        if self._is_admin_like(user):
            return qs

        # Staff = périmètre centres/départements
        if getattr(user, "is_staff", False):
            centre_ids = self._staff_centre_ids(user)
            if centre_ids is None:
                return qs
            dep_codes = self._staff_departement_codes(user)

            if not centre_ids and not dep_codes:
                return qs.none()

            q = Q()
            if centre_ids:
                q |= Q(prospection__centre_id__in=centre_ids)
            if dep_codes:
                q_dep = Q()
                for code in dep_codes:
                    q_dep |= Q(prospection__centre__code_postal__startswith=code)
                q |= q_dep
            return qs.filter(q).distinct()

        # ✅ Cas candidat / stagiaire : uniquement ses propres commentaires visibles
        if hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire():
            return qs.filter(is_internal=False, prospection__owner_id=user.id)

        # Tous les autres → aucun accès
        return qs.none()


    # ────────────────────────────────────────────────────────────
    # Data
    # ────────────────────────────────────────────────────────────
    def get_queryset(self):
        qs = ProspectionComment.objects.select_related(
            "prospection",
            "prospection__centre",
            "prospection__formation",
            "prospection__partenaire",
            "created_by",
        )
        if hasattr(self, "restrict_queryset_to_user"):
            qs = self.restrict_queryset_to_user(qs)
        qs = self._scope_for_user(qs, getattr(self.request, "user", None))
        return qs

    @staticmethod
    def _as_bool(v: str | None):
        if v is None:
            return None
        return str(v).lower() in {"1", "true", "t", "yes", "on", "oui"}

    def _apply_filters(self, qs, params=None):
        """
        Applique les filtres. Si `params` est fourni (dict-like), on l’utilise
        à la place de `self.request.query_params` (utile pour /grouped).
        """
        p = params or self.request.query_params

        dfrom = parse_date(p.get("date_from") or "") if p.get("date_from") else None
        dto = parse_date(p.get("date_to") or "") if p.get("date_to") else None
        if dfrom:
            qs = qs.filter(created_at__date__gte=dfrom)
        if dto:
            qs = qs.filter(created_at__date__lte=dto)

        if p.get("centre"):
            qs = qs.filter(prospection__centre_id=p.get("centre"))
        if p.get("departement"):
            qs = qs.filter(prospection__centre__code_postal__startswith=str(p.get("departement"))[:2])
        if p.get("formation"):
            qs = qs.filter(prospection__formation_id=p.get("formation"))
        if p.get("partenaire"):
            qs = qs.filter(prospection__partenaire_id=p.get("partenaire"))
        if p.get("owner"):
            qs = qs.filter(prospection__owner_id=p.get("owner"))

        b = self._as_bool(p.get("is_internal"))
        if b is True:
            qs = qs.filter(is_internal=True)
        elif b is False:
            qs = qs.filter(is_internal=False)

        search = (p.get("search") or "").strip()
        if search:
            qs = qs.filter(
                Q(body__icontains=search)
                | Q(created_by__username__icontains=search)
                | Q(prospection__formation__nom__icontains=search)
                | Q(prospection__partenaire__nom__icontains=search)
            )
        return qs

    # ────────────────────────────────────────────────────────────
    # Latest (limit, tri desc)
    # ────────────────────────────────────────────────────────────
    @action(detail=False, methods=["GET"], url_path="latest")
    def latest(self, request):
        qs = self._apply_filters(self.get_queryset())

        try:
            limit = int(request.query_params.get("limit", 5))
        except Exception:
            limit = 5
        limit = max(1, min(200, limit))

        qs = qs.order_by("-created_at")[:limit]
        now = timezone.now()

        def _full_name(u):
            if not u:
                return "Anonyme"
            full = f"{(getattr(u, 'first_name', '') or '').strip()} {(getattr(u, 'last_name', '') or '').strip()}".strip()
            return full or getattr(u, "email", None) or getattr(u, "username", None) or "Anonyme"

        results = []
        for c in qs:
            p = c.prospection
            centre_nom = getattr(getattr(p, "centre", None), "nom", None)
            formation_nom = getattr(getattr(p, "formation", None), "nom", None)
            partenaire_nom = getattr(getattr(p, "partenaire", None), "nom", None)
            statut = getattr(p, "statut", None)
            type_prospection = getattr(p, "type_prospection", None)
            objectif = getattr(p, "objectif", None)

            body = c.body or ""
            preview_len = 180
            body_preview = body if len(body) <= preview_len else f"{body[:preview_len]}…"

            is_edited = bool(c.updated_at and (c.updated_at - c.created_at).total_seconds() > 60)
            is_recent = (now - c.created_at).days <= 7

            results.append({
                "id": c.pk,
                "prospection_id": p.id if p else None,
                "prospection_text": getattr(c, "prospection_text", f"#{getattr(p, 'id', None)}"),
                "centre_nom": centre_nom,
                "formation_nom": formation_nom,
                "partenaire_nom": partenaire_nom,
                "statut": statut,
                "type_prospection": type_prospection,
                "objectif": objectif,
                "body": body_preview,
                "is_internal": bool(c.is_internal),
                "auteur": _full_name(c.created_by),
                "date": c.created_at.strftime("%d/%m/%Y"),
                "heure": c.created_at.strftime("%H:%M"),
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                "is_recent": is_recent,
                "is_edited": is_edited,
            })

        return Response({
            "count": len(results),
            "results": results,
            "filters_echo": {k: v for k, v in request.query_params.items()},
        })

    # ────────────────────────────────────────────────────────────
    # Grouped (centre / departement) — pour alimenter les selects
    # ────────────────────────────────────────────────────────────
    @action(detail=False, methods=["GET"], url_path="grouped")
    def grouped(self, request):
        """
        GET /prospection-comment-stats/grouped/?by=centre|departement
        Renvoie les options (clé + label + total) pour les <select>.
        """
        by = (request.query_params.get("by") or "centre").lower()
        allowed = {"centre", "departement"}
        if by not in allowed:
            return Response({"detail": f"'by' doit être dans {sorted(allowed)}"}, status=400)

        # On applique tous les filtres SAUF celui du group_by pour lister les options complètes.
        params = request.query_params.copy()
        if by == "centre":
            params.pop("centre", None)
        if by == "departement":
            params.pop("departement", None)

        qs = self._apply_filters(self.get_queryset(), params)

        # departement dérivé du code postal centre
        qs = qs.annotate(
            departement=Coalesce(Substr("prospection__centre__code_postal", 1, 2), Value("NA"))
        )

        if by == "centre":
            group_fields = ["prospection__centre_id", "prospection__centre__nom"]
        else:  # departement
            group_fields = ["departement"]

        rows = list(
            qs.values(*group_fields)
              .annotate(total=Count("id"))
              .order_by(*group_fields)
        )

        results = []
        for r in rows:
            if by == "centre":
                group_key = r.get("prospection__centre_id")
                group_label = r.get("prospection__centre__nom") or (
                    f"Centre #{group_key}" if group_key is not None else "—"
                )
            else:
                group_key = r.get("departement")
                group_label = group_key or "—"

            results.append({
                **r,
                "group_key": group_key,
                "group_label": group_label,
                "total": int(r.get("total") or 0),
            })

        return Response({
            "group_by": by,
            "results": results,
            "filters_echo": {k: v for k, v in request.query_params.items()},
        })
