from __future__ import annotations

from datetime import timedelta
from typing import Dict, List, Optional

from django.db import models
from django.db.models import Q, Count, Avg, Value, F
from django.db.models.functions import Substr, Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

try:
    from ..permissions import IsOwnerOrStaffOrAbove  # type: ignore
except Exception:  # pragma: no cover
    IsOwnerOrStaffOrAbove = permissions.IsAuthenticated

# ⚠️ adapte l'import à ton arborescence
from ....models.commentaires import Commentaire


class CommentaireStatsViewSet(viewsets.ViewSet):
    """
    /api/commentaire-stats/             -> overview
    /api/commentaire-stats/grouped/     -> groupé par centre|departement|formation|auteur
    /api/commentaire-stats/tops/        -> tops formations / auteurs
    """
    permission_classes = [IsOwnerOrStaffOrAbove]

    # ────────────────────────────────────────────────────────────
    # Helpers — scope staff (centres + départements)
    # ────────────────────────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="latest")
    def latest(self, request):
        """
        GET /api/commentaire-stats/latest/?limit=5&full=false
        Respecte le scope staff (centres + départements) et les filtres communs:
        date_from, date_to, centre, departement, formation, auteur, search, saturation_min, saturation_max.
        """
        qs = self._apply_filters(self._base_qs(request), request)

        # Limite & contenu complet ?
        try:
            limit = int(request.query_params.get("limit", 5))
        except ValueError:
            limit = 5
        limit = max(1, min(limit, 50))

        include_full = str(request.query_params.get("full", "false")).lower() in {"1", "true", "yes", "on"}

        # Sélection des N derniers
        rows = (
            qs.order_by("-created_at")
              .all()[:limit]
        )

        results = [obj.to_serializable_dict(include_full_content=include_full) for obj in rows]

        return Response({
            "results": results,
            "count": len(results),
            "limit": limit,
            "filters_echo": {k: v for k, v in request.query_params.items()},
        })
    
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
                    codes = _norm_codes(getattr(owner, attr))
                    if codes:
                        return codes
        return []

    def _base_qs(self, request):
        qs = Commentaire.objects.select_related(
            "formation",
            "formation__centre",
            "formation__type_offre",
            "formation__statut",
            "created_by",
        )
        user = getattr(request, "user", None)
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
                q |= Q(formation__centre_id__in=centre_ids)
            if dep_codes:
                q_dep = Q()
                for code in dep_codes:
                    q_dep |= Q(formation__centre__code_postal__startswith=code)
                q |= q_dep
            return qs.filter(q).distinct()

        # non-staff
        return qs

    # ────────────────────────────────────────────────────────────
    # Filtres
    # ────────────────────────────────────────────────────────────
    def _apply_filters(self, qs, request):
        p = request.query_params

        dfrom = parse_date(p.get("date_from") or "") if p.get("date_from") else None
        dto = parse_date(p.get("date_to") or "") if p.get("date_to") else None
        if dfrom:
            qs = qs.filter(created_at__date__gte=dfrom)
        if dto:
            qs = qs.filter(created_at__date__lte=dto)

        if p.get("formation"):
            qs = qs.filter(formation_id=p.get("formation"))
        if p.get("centre"):
            qs = qs.filter(formation__centre_id=p.get("centre"))
        if p.get("departement"):
            dep = str(p.get("departement"))[:2]
            qs = qs.filter(formation__centre__code_postal__startswith=dep)

        if p.get("auteur"):
            qs = qs.filter(created_by_id=p.get("auteur"))

        if p.get("search"):
            s = p.get("search")
            qs = qs.filter(
                Q(contenu__icontains=s)
                | Q(created_by__username__icontains=s)
                | Q(formation__nom__icontains=s)
            )

        def _as_int(v):
            try:
                return int(v) if v is not None else None
            except ValueError:
                return None

        smin = _as_int(p.get("saturation_min"))
        smax = _as_int(p.get("saturation_max"))
        if smin is not None:
            qs = qs.filter(saturation__gte=max(0, smin))
        if smax is not None:
            qs = qs.filter(saturation__lte=min(100, smax))

        return qs

    # ────────────────────────────────────────────────────────────
    # Overview
    # ────────────────────────────────────────────────────────────
    def list(self, request):
        qs = self._apply_filters(self._base_qs(request), request)

        seven_days_ago = timezone.now() - timedelta(days=7)

        agg = qs.aggregate(
            total=Count("id"),
            avec_saturation=Count("id", filter=Q(saturation__isnull=False)),
            avg_saturation=Avg("saturation"),
            min_saturation=models.Min("saturation"),
            max_saturation=models.Max("saturation"),
            nb_formations=Count("formation", distinct=True),
            nb_auteurs=Count("created_by", distinct=True),
            recent_7d=Count("id", filter=Q(created_at__gte=seven_days_ago)),
            edited=Count("id", filter=Q(updated_at__gt=F("created_at"))),
        )

        data = {
            "kpis": {
                "total": int(agg.get("total") or 0),
                "avec_saturation": int(agg.get("avec_saturation") or 0),
                "avg_saturation": round(float(agg["avg_saturation"]), 2) if agg.get("avg_saturation") is not None else None,
                "min_saturation": int(agg["min_saturation"]) if agg.get("min_saturation") is not None else None,
                "max_saturation": int(agg["max_saturation"]) if agg.get("max_saturation") is not None else None,
                "nb_formations": int(agg.get("nb_formations") or 0),
                "nb_auteurs": int(agg.get("nb_auteurs") or 0),
                "recent_7d": int(agg.get("recent_7d") or 0),
                "edited": int(agg.get("edited") or 0),
            },
            "filters_echo": {k: v for k, v in request.query_params.items()},
        }
        return Response(data)

    # ────────────────────────────────────────────────────────────
    # Grouped
    # ────────────────────────────────────────────────────────────
    @action(detail=False, methods=["get"])
    def grouped(self, request):
        by = (request.query_params.get("by") or "departement").lower()
        allowed = {"centre", "departement", "formation", "auteur"}
        if by not in allowed:
            return Response({"detail": f"'by' doit être dans {sorted(allowed)}"}, status=400)

        base = self._apply_filters(self._base_qs(request), request)

        seven_days_ago = timezone.now() - timedelta(days=7)

        # departement annotate
        qs = base.annotate(
            departement=Coalesce(Substr("formation__centre__code_postal", 1, 2), Value("NA"))
        )

        group_fields: List[str] = []
        if by == "centre":
            group_fields = ["formation__centre_id", "formation__centre__nom"]
        elif by == "departement":
            group_fields = ["departement"]
        elif by == "formation":
            group_fields = [
                "formation_id",
                "formation__nom",
                "formation__num_offre",
                "formation__type_offre",
                "formation__type_offre__nom",
            ]
        elif by == "auteur":
            group_fields = [
                "created_by_id",
                "created_by__first_name",
                "created_by__last_name",
                "created_by__email",
                "created_by__username",
            ]

        rows = list(
            qs.values(*group_fields).annotate(
                total=Count("id"),
                avec_saturation=Count("id", filter=Q(saturation__isnull=False)),
                avg_saturation=Avg("saturation"),
                min_saturation=models.Min("saturation"),
                max_saturation=models.Max("saturation"),
                recent_7d=Count("id", filter=Q(created_at__gte=seven_days_ago)),
            ).order_by(*group_fields)
        )

        # group_key / group_label
        results: List[Dict] = []
        for r in rows:
            out = dict(r)
            if by == "centre":
                out["group_key"] = r.get("formation__centre_id")
                out["group_label"] = r.get("formation__centre__nom") or (
                    f"Centre #{r.get('formation__centre_id')}" if r.get("formation__centre_id") is not None else "—"
                )
            elif by == "departement":
                out["group_key"] = r.get("departement")
                out["group_label"] = r.get("departement") or "—"
            elif by == "formation":
                out["group_key"] = r.get("formation_id")
                out["formation_nom"] = r.get("formation__nom")
                out["group_label"] = r.get("formation__nom") or (
                    f"Formation #{r.get('formation_id')}" if r.get("formation_id") is not None else "—"
                )
                # ✅ Infos complémentaires
                out["num_offre"] = r.get("formation__num_offre")
                out["type_offre_id"] = r.get("formation__type_offre")       # ID brut
                out["type_offre_nom"] = r.get("formation__type_offre__nom") # Nom lisible
            elif by == "auteur":
                rid = r.get("created_by_id")
                fn = (r.get("created_by__first_name") or "").strip()
                ln = (r.get("created_by__last_name") or "").strip()
                full = f"{fn} {ln}".strip()
                fallback = r.get("created_by__email") or r.get("created_by__username")
                out["group_key"] = rid
                out["group_label"] = full or fallback or (f"Utilisateur #{rid}" if rid is not None else "—")

            # normalise numériques
            for k in ("total", "avec_saturation", "recent_7d"):
                out[k] = int(out.get(k) or 0)
            for k in ("avg_saturation", "min_saturation", "max_saturation"):
                v = out.get(k)
                out[k] = round(float(v), 2) if v is not None else None

            results.append(out)

        return Response({
            "group_by": by,
            "results": results,
            "filters_echo": {k: v for k, v in request.query_params.items()},
        })


    # ────────────────────────────────────────────────────────────
    # Tops
    # ────────────────────────────────────────────────────────────
    @action(detail=False, methods=["get"])
    def tops(self, request):
        qs = self._apply_filters(self._base_qs(request), request)

        # Formations les plus commentées
        top_formations = list(
            qs.values("formation_id", "formation__nom")
            .annotate(cnt=Count("id"))
            .order_by("-cnt", "formation__nom")[:10]
        )
        top_formations = [
            {
                "id": r["formation_id"],
                "nom": r["formation__nom"] or (f"Formation #{r['formation_id']}" if r["formation_id"] is not None else "—"),
                "count": r["cnt"],
            }
            for r in top_formations
        ]

        # Auteurs les plus actifs
        top_auteurs = list(
            qs.values("created_by_id", "created_by__first_name", "created_by__last_name", "created_by__email", "created_by__username")
            .annotate(cnt=Count("id"))
            .order_by("-cnt")[:10]
        )
        def _label(u):
            full = f"{(u.get('created_by__first_name') or '').strip()} {(u.get('created_by__last_name') or '').strip()}".strip()
            return full or u.get("created_by__email") or u.get("created_by__username") or (f"User #{u['created_by_id']}" if u["created_by_id"] is not None else "—")

        top_auteurs = [
            {"id": r["created_by_id"], "nom": _label(r), "count": r["cnt"]}
            for r in top_auteurs
        ]

        return Response({
            "top_formations": top_formations,
            "top_auteurs": top_auteurs,
            "filters_echo": {k: v for k, v in request.query_params.items()},
        })
