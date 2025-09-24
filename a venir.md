










# rap_app/api/viewsets/stats_viewsets/appairages_stats_viewsets.py
from datetime import datetime
from typing import Dict

from django.db.models import Count, Q, QuerySet
from django.db.models.functions import Substr
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rap_app.models.appairage import Appairage, AppairageStatut


def _safe_status_key(raw: str) -> str:
    """Normalise un code de statut en clé safe: espaces → '_'."""
    return raw.replace(" ", "_").lower()


class AppairageStatsViewSet(viewsets.ViewSet):
    """
    /api/appairage-stats/           -> overview
    /api/appairage-stats/grouped/   -> groupé par centre|departement|statut|formation|partenaire
    /api/appairage-stats/tops/      -> tops partenaires / formations
    """
    permission_classes = [permissions.IsAuthenticated]

    # ────────────────────────────────────────────────────────────
    # Base QS + filtres
    # ────────────────────────────────────────────────────────────
    def _base_qs(self, request) -> QuerySet:
        return (
            Appairage.objects
            .select_related("formation", "formation__centre", "partenaire", "candidat")
        )

    def _apply_filters(self, qs: QuerySet, request) -> QuerySet:
        p = request.query_params

        # Dates (YYYY-MM-DD)
        date_from = p.get("date_from")
        date_to = p.get("date_to")
        if date_from:
            qs = qs.filter(date_appairage__date__gte=date_from)
        if date_to:
            qs = qs.filter(date_appairage__date__lte=date_to)

        # Centre (via formation.centre)
        centre = p.get("centre")
        if centre:
            try:
                qs = qs.filter(formation__centre_id=int(centre))
            except ValueError:
                pass

        # Département (via partenaire.zip_code -> 2 premiers chiffres)
        departement = p.get("departement")
        if departement:
            qs = qs.filter(partenaire__zip_code__startswith=str(departement)[:2])

        # Formation / Partenaire / Statut
        formation = p.get("formation")
        if formation:
            try:
                qs = qs.filter(formation_id=int(formation))
            except ValueError:
                pass

        partenaire = p.get("partenaire")
        if partenaire:
            try:
                qs = qs.filter(partenaire_id=int(partenaire))
            except ValueError:
                pass

        statut = p.get("statut")
        if statut:
            # accepte, en_attente, etc. (normaliser les espaces potentiels)
            statut = statut.replace(" ", "_")
            # remappe vers la valeur réelle de l'enum si besoin
            # mapping simple inverse
            inv = { _safe_status_key(k): k for k, _ in AppairageStatut.choices }
            if statut in inv:
                qs = qs.filter(statut=inv[statut])
            else:
                qs = qs.filter(statut=statut.replace("_", " "))  # au cas où on reçoit la valeur brute
        return qs

    # ────────────────────────────────────────────────────────────
    # Overview
    # ────────────────────────────────────────────────────────────
    def list(self, request):
        qs = self._apply_filters(self._base_qs(request), request)

        # Statuts → counts
        raw_counts = dict(
            qs.values("statut").annotate(c=Count("id")).values_list("statut", "c")
        )
        status_map: Dict[str, int] = {
            _safe_status_key(code): int(raw_counts.get(code, 0))
            for code, _ in AppairageStatut.choices
        }

        kpis = {
            "appairages_total": qs.count(),
            "nb_candidats_distincts": qs.values("candidat").distinct().count(),
            "nb_partenaires_distincts": qs.values("partenaire").distinct().count(),
            "nb_formations_distinctes": qs.values("formation").distinct().count(),
            "statuts": status_map,
        }

        return Response({
            "kpis": kpis,
            "filters_echo": {k: v for k, v in request.query_params.items()},
        })

    # ────────────────────────────────────────────────────────────
    # Grouped
    # ────────────────────────────────────────────────────────────
    @action(detail=False, methods=["get"])
    def grouped(self, request):
        by = request.query_params.get("by", "centre").lower()
        allowed = {"centre", "departement", "statut", "formation", "partenaire"}
        if by not in allowed:
            return Response({"detail": f"'by' doit être dans {sorted(allowed)}"}, status=400)

        base = self._apply_filters(self._base_qs(request), request)

        # Champ(s) de groupage
        group_fields = []
        qs = base
        if by == "centre":
            group_fields = ["formation__centre_id", "formation__centre__nom"]
        elif by == "departement":
            qs = qs.annotate(departement=Substr("partenaire__zip_code", 1, 2))
            group_fields = ["departement"]
        elif by == "statut":
            group_fields = ["statut"]
        elif by == "formation":
            group_fields = ["formation_id", "formation__nom"]
        elif by == "partenaire":
            group_fields = ["partenaire_id", "partenaire__nom"]

        # Annotations — éviter toute collision de clés
        status_annots = {
            _safe_status_key(code): Count("id", filter=Q(statut=code))
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

        # Post-process : ajouter group_key / group_label
        results = []
        for r in rows:
            out = dict(r)
            if by == "centre":
                out["group_key"] = r.get("formation__centre_id")
                out["group_label"] = r.get("formation__centre__nom") or "—"
            elif by == "departement":
                out["group_key"] = r.get("departement") or "—"
                out["group_label"] = out["group_key"]
            elif by == "statut":
                raw = r.get("statut") or ""
                out["group_key"] = _safe_status_key(raw)
                out["group_label"] = dict(AppairageStatut.choices).get(raw, raw) or "—"
            elif by == "formation":
                out["group_key"] = r.get("formation_id")
                out["group_label"] = r.get("formation__nom") or f"Formation #{out['group_key'] or '—'}"
            elif by == "partenaire":
                out["group_key"] = r.get("partenaire_id")
                out["group_label"] = r.get("partenaire__nom") or f"Partenaire #{out['group_key'] or '—'}"
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

        # Top Partenaires (évite d'annoter 'nb_appairages' qui pourrait
        # entrer en collision avec d'éventuelles @property)
        top_partenaires = list(
            qs.values("partenaire_id", "partenaire__nom")
            .annotate(cnt=Count("id"))
            .order_by("-cnt")[:10]
        )
        top_partenaires = [
            {"id": r["partenaire_id"], "nom": r["partenaire__nom"] or f"Partenaire #{r['partenaire_id']}", "count": r["cnt"]}
            for r in top_partenaires
        ]

        # Top Formations
        top_formations = list(
            qs.values("formation_id", "formation__nom")
            .annotate(cnt=Count("id"))
            .order_by("-cnt")[:10]
        )
        top_formations = [
            {"id": r["formation_id"], "nom": r["formation__nom"] or f"Formation #{r['formation_id']}", "count": r["cnt"]}
            for r in top_formations
        ]

        return Response({
            "top_partenaires": top_partenaires,
            "top_formations": top_formations,
            "filters_echo": {k: v for k, v in request.query_params.items()},
        })



# backend/api/candidat_stats.py
# ViewSet DRF — Statistiques des candidats (scope centre + département + appairages)

from __future__ import annotations

import logging
from typing import Iterable, Literal, Optional

from django.conf import settings
from django.db import models
from django.db.models import Count, Q, F, Value
from django.db.models.functions import Coalesce, Substr
from django.utils.dateparse import parse_date

from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

logger = logging.getLogger("application.candidat_stats")

try:
    from ..permissions import IsOwnerOrStaffOrAbove  # type: ignore
except Exception:  # pragma: no cover
    IsOwnerOrStaffOrAbove = IsAuthenticated

try:
    from ..mixins import RestrictToUserOwnedQueryset  # type: ignore
except Exception:  # pragma: no cover
    class RestrictToUserOwnedQueryset:  # stub minimal
        def restrict_queryset_to_user(self, qs):
            return qs

# ⚠️ adaptez l'import à votre arborescence
from ....models.candidat import Candidat


GroupKey = Literal[
    "centre",
    "departement",
    "formation",
    "statut",
    "type_contrat",
    "cv_statut",
    "resultat_placement",
    "contrat_signe",
    "responsable",
    "entreprise",
]


class CandidatStatsViewSet(RestrictToUserOwnedQueryset, GenericViewSet):
    """
    KPIs & agrégats sur Candidat.
    Endpoints :
      GET /candidat-stats/                 → résumé global
      GET /candidat-stats/grouped/?by=... → groupés par centre|departement|formation|statut|type_contrat|cv_statut|resultat_placement|contrat_signe|responsable|entreprise

    Filtres (query params, tous optionnels) :
      - date_from=YYYY-MM-DD   (date_inscription >= …)
      - date_to=YYYY-MM-DD     (date_inscription <= …)
      - centre=<id>            (via formation.centre)
      - departement=<DD>       (via formation.centre.code_postal ^ DD ; fallback candidat.code_postal)
      - formation=<id>
      - statut=<code Candidat.StatutCandidat>
      - type_contrat=<code>
      - cv_statut=<code>
      - resultat_placement=<code>
      - contrat_signe=<code>
      - responsable=<user id>
      - entreprise=<partenaire id>
      - entretien_ok=true|false
      - test_ok=true|false
      - gespers=true|false
      - admissible=true|false
      - rqth=true|false
    """

    permission_classes = [IsOwnerOrStaffOrAbove]

    # ───────────────────────────────
    # Helpers périmètre staff
    # ───────────────────────────────
    def _is_admin_like(self, user) -> bool:
        return bool(
            getattr(user, "is_superuser", False)
            or (hasattr(user, "is_admin") and callable(user.is_admin) and user.is_admin())
        )

    def _staff_centre_ids(self, user) -> Optional[list[int]]:
        """
        - None => admin/superadmin → accès global
        - []   => staff sans centre → aucun résultat
        """
        if self._is_admin_like(user):
            return None
        if getattr(user, "is_staff", False) and hasattr(user, "centres"):
            return list(user.centres.values_list("id", flat=True))
        return []

    def _staff_departement_codes(self, user) -> list[str]:
        """
        Collecte des codes ([:2]) depuis user / user.profile (attributs departements_codes|departements).
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

        for owner in (user, getattr(user, "profile", None)):
            if not owner:
                continue
            for attr in ("departements_codes", "departements"):
                if hasattr(owner, attr):
                    codes = _norm_codes(getattr(owner, attr))
                    if codes:
                        return codes
        return []

    def _scope_candidats_for_user(self, qs, user):
        """
        Périmètre :
          - admin/superadmin → global
          - staff → via formation.centre IN centres utilisateur OU formation.centre.code_postal ^ dep
                    (fallback: candidat.code_postal ^ dep pour ceux sans formation)
          - non staff → pas de restriction (ou gérée par RestrictToUserOwnedQueryset)
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
                q |= Q(formation__centre_id__in=centre_ids)
            if dep_codes:
                q_dep = Q()
                for code in dep_codes:
                    q_dep |= Q(formation__centre__code_postal__startswith=code) | Q(code_postal__startswith=code)
                q |= q_dep

            return qs.filter(q).distinct()

        return qs

    # ───────────────────────────────
    # Data
    # ───────────────────────────────
    def get_queryset(self):
        qs = (
            Candidat.objects
            .select_related(
                "formation",
                "formation__centre",
                "entreprise_placement",
                "responsable_placement",
            )
        )
        if hasattr(self, "restrict_queryset_to_user"):
            qs = self.restrict_queryset_to_user(qs)
        qs = self._scope_candidats_for_user(qs, getattr(self.request, "user", None))
        return qs

    # Bool parsing
    @staticmethod
    def _as_bool(v: str | None) -> Optional[bool]:
        if v is None:
            return None
        return str(v).lower() in {"1", "true", "t", "yes", "on"}

    def _apply_common_filters(self, qs):
        p = self.request.query_params

        dfrom = parse_date(p.get("date_from") or "") if p.get("date_from") else None
        dto = parse_date(p.get("date_to") or "") if p.get("date_to") else None
        if dfrom:
            qs = qs.filter(date_inscription__date__gte=dfrom)
        if dto:
            qs = qs.filter(date_inscription__date__lte=dto)

        if p.get("formation"):
            qs = qs.filter(formation_id=p.get("formation"))
        if p.get("centre"):
            qs = qs.filter(formation__centre_id=p.get("centre"))
        if p.get("departement"):
            dep = str(p.get("departement"))[:2]
            qs = qs.filter(
                Q(formation__centre__code_postal__startswith=dep) | Q(code_postal__startswith=dep)
            )

        if p.get("statut"):
            qs = qs.filter(statut=p.get("statut"))
        if p.get("type_contrat"):
            qs = qs.filter(type_contrat=p.get("type_contrat"))
        if p.get("cv_statut"):
            qs = qs.filter(cv_statut=p.get("cv_statut"))
        if p.get("resultat_placement"):
            qs = qs.filter(resultat_placement=p.get("resultat_placement"))
        if p.get("contrat_signe"):
            qs = qs.filter(contrat_signe=p.get("contrat_signe"))
        if p.get("responsable"):
            qs = qs.filter(responsable_placement_id=p.get("responsable"))
        if p.get("enterprise") or p.get("entreprise"):  # tolère une typo
            qs = qs.filter(entreprise_placement_id=p.get("enterprise") or p.get("entreprise"))

        b = self._as_bool
        if (v := b(p.get("entretien_ok"))) is not None:
            qs = qs.filter(entretien_done=v)
        if (v := b(p.get("test_ok"))) is not None:
            qs = qs.filter(test_is_ok=v)
        if (v := b(p.get("gespers"))) is not None:
            qs = qs.filter(inscrit_gespers=v)
        if (v := b(p.get("admissible"))) is not None:
            qs = qs.filter(admissible=v)
        if (v := b(p.get("rqth"))) is not None:
            qs = qs.filter(rqth=v)

        return qs

    # ---------- résolution de libellés pour FK ----------
    @staticmethod
    def _guess_label_field(model: type[models.Model]) -> Optional[str]:
        """
        Tente de trouver un champ 'label' pertinent.
        """
        preferred = {"nom", "name", "label", "libelle", "libellé", "titre", "username", "email", "first_name", "last_name"}
        name_map = {f.name: f for f in model._meta.get_fields() if isinstance(f, models.Field)}
        for cand in preferred:
            f = name_map.get(cand)
            if f and isinstance(f, models.CharField):
                return cand
        for f in model._meta.get_fields():
            if isinstance(f, models.CharField):
                return f.name
        return None

    def _fk_label_map(self, model: type[models.Model], ids: Iterable[int | str]) -> dict[int | str, str]:
        ids_list = [i for i in ids if i is not None]
        if not ids_list:
            return {}

        # cas particulier: utilisateur → full_name || email || username
        try:
            UserModel = settings.AUTH_USER_MODEL and __import__(settings.AUTH_USER_MODEL.split(".")[0]).__dict__
        except Exception:
            UserModel = None

        if getattr(model, "__name__", "") in {"User", "CustomUser"}:
            # on récupère plusieurs champs pour composer un label propre
            rows = model.objects.filter(pk__in=ids_list).values("pk", "first_name", "last_name", "email", "username")
            out: dict[int | str, str] = {}
            for r in rows:
                full = f"{(r.get('first_name') or '').strip()} {(r.get('last_name') or '').strip()}".strip()
                out[r["pk"]] = full or r.get("email") or r.get("username") or f"User #{r['pk']}"
            return out

        label_field = self._guess_label_field(model)
        if label_field:
            rows = model.objects.filter(pk__in=ids_list).values_list("pk", label_field)
            return {pk: (label or f"{model.__name__} #{pk}") for pk, label in rows}
        objs = model.objects.filter(pk__in=ids_list)
        return {obj.pk: str(obj) for obj in objs}

    # ───────────────────────────────
    # LIST — KPIs globaux
    # ───────────────────────────────
    def list(self, request, *args, **kwargs):
        qs = self._apply_common_filters(self.get_queryset())

        # KPI candidats
        kpis = qs.aggregate(
            total=Count("id"),
            entretien_ok=Count("id", filter=Q(entretien_done=True)),
            test_ok=Count("id", filter=Q(test_is_ok=True)),
            gespers=Count("id", filter=Q(inscrit_gespers=True)),
            admissibles=Count("id", filter=Q(admissible=True)),
            en_formation=Count("id", filter=Q(statut=Candidat.StatutCandidat.EN_FORMATION)),
            en_appairage=Count("id", filter=Q(statut=Candidat.StatutCandidat.EN_APPAIRAGE)),
            en_accompagnement=Count("id", filter=Q(statut=Candidat.StatutCandidat.EN_ACCOMPAGNEMENT)),
            # contrats
            contrat_apprentissage=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.APPRENTISSAGE)),
            contrat_professionnalisation=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.PROFESSIONNALISATION)),
            contrat_poei=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.POEI)),
            contrat_poec=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.POEC)),
            contrat_sans=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.SANS_CONTRAT)),
            contrat_autre=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.AUTRE)),
        )

        # KPI appairages (via relation inverse)
        app = qs.aggregate(
            appairages_total=Count("appairages", distinct=True),
            app_transmis=Count("appairages", filter=Q(appairages__statut="transmis"), distinct=True),
            app_en_attente=Count("appairages", filter=Q(appairages__statut="en_attente"), distinct=True),
            app_accepte=Count("appairages", filter=Q(appairages__statut="accepte"), distinct=True),
            app_refuse=Count("appairages", filter=Q(appairages__statut="refuse"), distinct=True),
            app_annule=Count("appairages", filter=Q(appairages__statut="annule"), distinct=True),
            app_a_faire=Count("appairages", filter=Q(appairages__statut="a_faire"), distinct=True),
            app_contrat_a_signer=Count("appairages", filter=Q(appairages__statut="contrat a signer"), distinct=True),
            app_contrat_en_attente=Count("appairages", filter=Q(appairages__statut="contrat en attente"), distinct=True),
            app_appairage_ok=Count("appairages", filter=Q(appairages__statut="appairage ok"), distinct=True),
        )

        # Répartitions principales
        rep_statut = list(qs.values("statut").annotate(count=Count("id")).order_by("statut"))
        rep_type_contrat = list(qs.values("type_contrat").annotate(count=Count("id")).order_by("type_contrat"))
        rep_cv = list(qs.values("cv_statut").annotate(count=Count("id")).order_by("cv_statut"))
        rep_resultat = list(qs.values("resultat_placement").annotate(count=Count("id")).order_by("resultat_placement"))

        payload = {
            "kpis": {k: int(v or 0) for k, v in kpis.items()},
            "appairages": {k: int(v or 0) for k, v in app.items()},
            "repartition": {
                "par_statut": rep_statut,
                "par_type_contrat": rep_type_contrat,
                "par_cv": rep_cv,
                "par_resultat": rep_resultat,
            },
            "filters_echo": {k: v for k, v in request.query_params.items()},
        }
        logger.debug("CandidatStats overview computed (total=%s)", payload["kpis"]["total"])
        return Response(payload)

    # ───────────────────────────────
    # GROUPED — par centre / département / …
    # ───────────────────────────────
    @action(detail=False, methods=["GET"], url_path="grouped")
    def grouped(self, request):
        by: GroupKey = (request.query_params.get("by") or "centre").lower()  # type: ignore[assignment]
        if by not in {
            "centre",
            "departement",
            "formation",
            "statut",
            "type_contrat",
            "cv_statut",
            "resultat_placement",
            "contrat_signe",
            "responsable",
            "entreprise",
        }:
            return Response({"detail": "Paramètre 'by' invalide."}, status=400)

        qs = self._apply_common_filters(self.get_queryset()).annotate(
            departement=Coalesce(Substr("formation__centre__code_postal", 1, 2), Value("NA"))
        )

        group_fields_map = {
            "centre": ["formation__centre_id", "formation__centre__nom"],
            "departement": ["departement"],
            "formation": ["formation_id", "formation__nom"],
            "statut": ["statut"],
            "type_contrat": ["type_contrat"],
            "cv_statut": ["cv_statut"],
            "resultat_placement": ["resultat_placement"],
            "contrat_signe": ["contrat_signe"],
            "responsable": ["responsable_placement_id"],  # label résolu plus bas
            "entreprise": ["entreprise_placement_id", "entreprise_placement__nom"],
        }
        fields = group_fields_map[by]

        rows = list(
            qs.values(*fields).annotate(
                total=Count("id"),
                entretien_ok=Count("id", filter=Q(entretien_done=True)),
                test_ok=Count("id", filter=Q(test_is_ok=True)),
                gespers=Count("id", filter=Q(inscrit_gespers=True)),
                admissibles=Count("id", filter=Q(admissible=True)),
                en_formation=Count("id", filter=Q(statut=Candidat.StatutCandidat.EN_FORMATION)),
                en_appairage=Count("id", filter=Q(statut=Candidat.StatutCandidat.EN_APPAIRAGE)),
                # contrats
                contrat_apprentissage=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.APPRENTISSAGE)),
                contrat_professionnalisation=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.PROFESSIONNALISATION)),
                contrat_poei=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.POEI)),
                contrat_poec=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.POEC)),
                contrat_sans=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.SANS_CONTRAT)),
                contrat_autre=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.AUTRE)),
                # appairages (distinct pour éviter les doublons)
                appairages_total=Count("appairages", distinct=True),
                app_transmis=Count("appairages", filter=Q(appairages__statut="transmis"), distinct=True),
                app_en_attente=Count("appairages", filter=Q(appairages__statut="en_attente"), distinct=True),
                app_accepte=Count("appairages", filter=Q(appairages__statut="accepte"), distinct=True),
                app_refuse=Count("appairages", filter=Q(appairages__statut="refuse"), distinct=True),
                app_annule=Count("appairages", filter=Q(appairages__statut="annule"), distinct=True),
                app_a_faire=Count("appairages", filter=Q(appairages__statut="a_faire"), distinct=True),
                app_contrat_a_signer=Count("appairages", filter=Q(appairages__statut="contrat a signer"), distinct=True),
                app_contrat_en_attente=Count("appairages", filter=Q(appairages__statut="contrat en attente"), distinct=True),
                app_appairage_ok=Count("appairages", filter=Q(appairages__statut="appairage ok"), distinct=True),
            ).order_by(*fields)
        )

        # group_key / group_label
        if by == "centre":
            for r in rows:
                r["group_key"] = r.get("formation__centre_id")
                r["group_label"] = r.get("formation__centre__nom") or (
                    f"Centre #{r.get('formation__centre_id')}" if r.get("formation__centre_id") is not None else "—"
                )
        elif by == "departement":
            for r in rows:
                r["group_key"] = r.get("departement")
                r["group_label"] = r.get("departement") or "—"
        elif by == "formation":
            for r in rows:
                r["group_key"] = r.get("formation_id")
                r["group_label"] = r.get("formation__nom") or (
                    f"Formation #{r.get('formation_id')}" if r.get("formation_id") is not None else "—"
                )
        elif by in {"statut", "type_contrat", "cv_statut", "resultat_placement", "contrat_signe"}:
            key = fields[0]
            for r in rows:
                gid = r.get(key)
                r["group_key"] = gid
                r["group_label"] = gid or "—"
        elif by == "responsable":
            # User label map
            from django.contrib.auth import get_user_model
            ids = [r.get("responsable_placement_id") for r in rows if r.get("responsable_placement_id") is not None]
            if ids:
                User = get_user_model()
                raw = User.objects.filter(pk__in=ids).values("pk", "first_name", "last_name", "email", "username")
                label = {}
                for u in raw:
                    full = f"{(u.get('first_name') or '').strip()} {(u.get('last_name') or '').strip()}".strip()
                    label[u["pk"]] = full or u.get("email") or u.get("username") or f"User #{u['pk']}"
            else:
                label = {}
            for r in rows:
                gid = r.get("responsable_placement_id")
                r["group_key"] = gid
                r["group_label"] = label.get(gid, f"User #{gid}" if gid is not None else "—")
        elif by == "entreprise":
            for r in rows:
                r["group_key"] = r.get("entreprise_placement_id")
                r["group_label"] = r.get("entreprise_placement__nom") or (
                    f"Entreprise #{r.get('entreprise_placement_id')}" if r.get("entreprise_placement_id") is not None else "—"
                )

        logger.debug("CandidatStats grouped by %s → %d lignes", by, len(rows))
        return Response({"group_by": by, "results": rows})



"""
ViewSet DRF — Statistiques des formations (v2 + scope staff + candidats + appairages + fix aggregates + group_label)
---------------------------------------------------------------------
[… en-tête identique …]
"""
from __future__ import annotations

from typing import Literal, Iterable, Optional

from django.db import models
from django.db.models import Count, Sum, F, Q, Value
from django.db.models.functions import Coalesce, Substr, Greatest, NullIf
from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

try:
    from ..permissions import IsOwnerOrStaffOrAbove  # type: ignore
except Exception:  # pragma: no cover
    IsOwnerOrStaffOrAbove = IsAuthenticated  # fallback sécurisé

try:
    from ..mixins import RestrictToUserOwnedQueryset  # type: ignore
except Exception:  # pragma: no cover
    class RestrictToUserOwnedQueryset:  # stub minimal
        def restrict_queryset_to_user(self, qs):
            return qs

# ⚠️ Ajustez les imports selon votre arborescence réelle
from ....models.formations import Formation
from ....models.candidat import Candidat
from ....models.appairage import Appairage, AppairageStatut  # ← NEW

GroupKey = Literal["formation", "centre", "departement", "type_offre", "statut"]


class FormationStatsViewSet(RestrictToUserOwnedQueryset, GenericViewSet):
    """Vue d’agrégats/KPI sur **Formation** (JSON only)."""

    permission_classes = [IsOwnerOrStaffOrAbove]

    # ────────────────────────────────────────────────────────────
    # Helpers « périmètre user » (mêmes principes que Prospection)
    # ────────────────────────────────────────────────────────────
    def _is_admin_like(self, user) -> bool:
        return bool(
            getattr(user, "is_superuser", False)
            or (hasattr(user, "is_admin") and callable(user.is_admin) and user.is_admin())
        )

    def _staff_centre_ids(self, user) -> Optional[list[int]]:
        if self._is_admin_like(user):
            return None
        if getattr(user, "is_staff", False):
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

    def _scope_formations_for_user(self, qs, user):
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
    # Helpers « data »
    # ────────────────────────────────────────────────────────────
    def get_queryset(self):
        qs = Formation.objects.select_related("centre", "type_offre", "statut")
        if hasattr(self, "restrict_queryset_to_user"):
            qs = self.restrict_queryset_to_user(qs)
        qs = self._scope_formations_for_user(qs, getattr(self.request, "user", None))
        return qs

    def _apply_common_filters(self, qs):
        p = self.request.query_params
        raw_from = p.get("date_from")
        raw_to = p.get("date_to")
        dfrom = parse_date(str(raw_from)) if raw_from is not None and raw_from != "" else None
        dto = parse_date(str(raw_to)) if raw_to is not None and raw_to != "" else None

        centre_id = p.get("centre")
        dep = p.get("departement")
        type_offre_id = p.get("type_offre")
        statut_id = p.get("statut")

        if dfrom:
            qs = qs.filter(start_date__gte=dfrom)
        if dto:
            qs = qs.filter(end_date__lte=dto)
        if centre_id:
            qs = qs.filter(centre_id=centre_id)
        if dep:
            qs = qs.filter(centre__code_postal__startswith=str(dep)[:2])
        if type_offre_id:
            qs = qs.filter(type_offre_id=type_offre_id)
        if statut_id:
            qs = qs.filter(statut_id=statut_id)
        return qs

    @staticmethod
    def _pct(num: int | float | None, den: int | float | None) -> float:
        if not num or not den or float(den) == 0.0:
            return 0.0
        return round(float(num) * 100.0 / float(den), 2)

    def _base_metrics(self, qs):
        today = timezone.now().date()
        agg = qs.aggregate(
            nb_formations=Count("id"),
            nb_actives=Count("id", filter=Q(start_date__lte=today, end_date__gte=today)),
            nb_a_venir=Count("id", filter=Q(start_date__gt=today)),
            nb_terminees=Count("id", filter=Q(end_date__lt=today)),

            total_places_crif=Coalesce(Sum("prevus_crif"), Value(0)),
            total_places_mp=Coalesce(Sum("prevus_mp"), Value(0)),
            total_inscrits_crif=Coalesce(Sum("inscrits_crif"), Value(0)),
            total_inscrits_mp=Coalesce(Sum("inscrits_mp"), Value(0)),

            total_places=Coalesce(Sum(F("prevus_crif") + F("prevus_mp")), Value(0)),
            total_inscrits=Coalesce(Sum(F("inscrits_crif") + F("inscrits_mp")), Value(0)),

            total_dispo_crif=Coalesce(Sum(Greatest(F("prevus_crif") - F("inscrits_crif"), Value(0))), Value(0)),
            total_dispo_mp=Coalesce(Sum(Greatest(F("prevus_mp") - F("inscrits_mp"), Value(0))), Value(0)),
        )
        agg["total_disponibles"] = int(agg["total_dispo_crif"]) + int(agg["total_dispo_mp"])
        agg["taux_saturation"] = self._pct(agg["total_inscrits"], agg["total_places"])
        agg["repartition_financeur"] = {
            "crif": int(agg["total_inscrits_crif"]),
            "mp": int(agg["total_inscrits_mp"]),
            "crif_pct": self._pct(agg["total_inscrits_crif"], agg["total_inscrits"]),
            "mp_pct": self._pct(agg["total_inscrits_mp"], agg["total_inscrits"]),
        }
        return agg

    @staticmethod
    def _guess_label_field(model: type[models.Model]) -> Optional[str]:
        preferred = {"nom", "name", "label", "libelle", "libellé", "titre"}
        name_map = {f.name: f for f in model._meta.get_fields() if isinstance(f, models.Field)}
        for cand in preferred:
            field = name_map.get(cand)
            if field and isinstance(field, models.CharField):
                return cand
        for f in model._meta.get_fields():
            if isinstance(f, models.CharField):
                return f.name
        return None

    def _fk_label_map(self, model: type[models.Model], ids: Iterable[int | str]) -> dict[int | str, str]:
        ids_list = [i for i in ids if i is not None]
        if not ids_list:
            return {}
        label_field = self._guess_label_field(model)
        if label_field:
            rows = model.objects.filter(pk__in=ids_list).values_list("pk", label_field)
            return {pk: (label or f"{model.__name__} #{pk}") for pk, label in rows}
        objs = model.objects.filter(pk__in=ids_list)
        return {obj.pk: str(obj) for obj in objs}

    # ────────────────────────────────────────────────────────────
    # LIST (overview)
    # ────────────────────────────────────────────────────────────
    def list(self, request, *args, **kwargs):
        qs = self._apply_common_filters(self.get_queryset())
        base = self._base_metrics(qs)

        # Entrées formation (champ Formation)
        entree_total = qs.aggregate(x=Coalesce(Sum("entree_formation"), Value(0)))["x"]

        # ----- Candidats (scopés aux formations du qs)
        cand_qs = Candidat.objects.filter(formation__in=qs)
        cand_agg = cand_qs.aggregate(
            nb_candidats=Count("id", distinct=True),
            nb_entretien_ok=Count("id", filter=Q(entretien_done=True), distinct=True),
            nb_test_ok=Count("id", filter=Q(test_is_ok=True), distinct=True),
            nb_inscrits_gespers=Count("id", filter=Q(inscrit_gespers=True), distinct=True),
            nb_entrees_formation=Count(
                "id",
                filter=Q(statut=Candidat.StatutCandidat.EN_FORMATION) | Q(date_rentree__isnull=False),
                distinct=True,
            ),
            nb_contrats_apprentissage=Count(
                "id",
                filter=Q(type_contrat=Candidat.TypeContrat.APPRENTISSAGE),
                distinct=True,
            ),
            nb_admissibles=Count("id", filter=Q(admissible=True), distinct=True),
        )
        cand = {k: int(v or 0) for k, v in cand_agg.items()}

        # ----- Appairages (scopés aux formations du qs) ← NEW
        app_qs = Appairage.objects.filter(formation__in=qs)
        app_agg = app_qs.aggregate(
            total=Count("id", distinct=True),
            transmis=Count("id", filter=Q(statut=AppairageStatut.TRANSMIS), distinct=True),
            en_attente=Count("id", filter=Q(statut=AppairageStatut.EN_ATTENTE), distinct=True),
            accepte=Count("id", filter=Q(statut=AppairageStatut.ACCEPTE), distinct=True),
            refuse=Count("id", filter=Q(statut=AppairageStatut.REFUSE), distinct=True),
            annule=Count("id", filter=Q(statut=AppairageStatut.ANNULE), distinct=True),
            a_faire=Count("id", filter=Q(statut=AppairageStatut.A_FAIRE), distinct=True),
            contrat_a_signer=Count("id", filter=Q(statut=AppairageStatut.CONTRAT_A_SIGNER), distinct=True),
            contrat_en_attente=Count("id", filter=Q(statut=AppairageStatut.CONTRAT_EN_ATTENTE), distinct=True),
            appairage_ok=Count("id", filter=Q(statut=AppairageStatut.APPAIRAGE_OK), distinct=True),
        )
        appairages = {
            "total": int(app_agg["total"] or 0),
            "par_statut": {k: int(app_agg.get(k) or 0) for k in [
                "transmis", "en_attente", "accepte", "refuse", "annule",
                "a_faire", "contrat_a_signer", "contrat_en_attente", "appairage_ok"
            ]},
        }

        payload = {
            "kpis": {
                **{
                    k: int(v) if isinstance(v, int) else v
                    for k, v in base.items()
                    if k not in {"repartition_financeur", "taux_saturation"}
                },
                "taux_saturation": base["taux_saturation"],
                "repartition_financeur": base["repartition_financeur"],
                "entrees_formation": int(entree_total or 0),
                "candidats": cand,
                "appairages": appairages,  # ← NEW
            },
            "filters_echo": {k: v for k, v in request.query_params.items()},
        }
        return Response(payload)

    # ────────────────────────────────────────────────────────────
    # Grouped
    # ────────────────────────────────────────────────────────────
    @action(detail=False, methods=["GET"], url_path="grouped")
    def grouped(self, request):
        by: GroupKey = (request.query_params.get("by") or "departement").lower()
        if by not in {"formation", "centre", "departement", "type_offre", "statut"}:
            return Response({"detail": "Paramètre 'by' invalide."}, status=400)

        qs = self._apply_common_filters(self.get_queryset())
        today = timezone.now().date()

        qs = qs.annotate(
            departement=Coalesce(Substr("centre__code_postal", 1, 2), Value("NA")),
        )

        group_fields = {
            "formation": ["id", "nom"],
            "centre": ["centre_id", "centre__nom"],
            "departement": ["departement"],
            "type_offre": ["type_offre_id"],
            "statut": ["statut_id"],
        }[by]

        rows = list(
            qs.values(*group_fields).annotate(
                nb_formations=Count("id"),
                nb_actives=Count("id", filter=Q(start_date__lte=today, end_date__gte=today)),
                nb_a_venir=Count("id", filter=Q(start_date__gt=today)),
                nb_terminees=Count("id", filter=Q(end_date__lt=today)),

                total_places=Coalesce(Sum(F("prevus_crif") + F("prevus_mp")), Value(0)),
                total_places_crif=Coalesce(Sum("prevus_crif"), Value(0)),
                total_places_mp=Coalesce(Sum("prevus_mp"), Value(0)),

                total_inscrits=Coalesce(Sum(F("inscrits_crif") + F("inscrits_mp")), Value(0)),
                total_inscrits_crif=Coalesce(Sum("inscrits_crif"), Value(0)),
                total_inscrits_mp=Coalesce(Sum("inscrits_mp"), Value(0)),

                total_dispo_crif=Coalesce(Sum(Greatest(F("prevus_crif") - F("inscrits_crif"), Value(0))), Value(0)),
                total_dispo_mp=Coalesce(Sum(Greatest(F("prevus_mp") - F("inscrits_mp"), Value(0))), Value(0)),

                entrees_formation=Coalesce(Sum("entree_formation"), Value(0)),

                # ----- Candidats
                nb_candidats=Count("candidats", distinct=True),
                nb_entretien_ok=Count("candidats", filter=Q(candidats__entretien_done=True), distinct=True),
                nb_test_ok=Count("candidats", filter=Q(candidats__test_is_ok=True), distinct=True),
                nb_inscrits_gespers=Count("candidats", filter=Q(candidats__inscrit_gespers=True), distinct=True),
                nb_entrees_formation=Count(
                    "candidats",
                    filter=Q(candidats__statut=Candidat.StatutCandidat.EN_FORMATION) | Q(candidats__date_rentree__isnull=False),
                    distinct=True,
                ),
                nb_contrats_apprentissage=Count(
                    "candidats",
                    filter=Q(candidats__type_contrat=Candidat.TypeContrat.APPRENTISSAGE),
                    distinct=True,
                ),
                nb_admissibles=Count("candidats", filter=Q(candidats__admissible=True), distinct=True),

                # ----- Appairages par statut ← NEW
                app_total=Count("appairages", distinct=True),
                app_transmis=Count("appairages", filter=Q(appairages__statut=AppairageStatut.TRANSMIS), distinct=True),
                app_en_attente=Count("appairages", filter=Q(appairages__statut=AppairageStatut.EN_ATTENTE), distinct=True),
                app_accepte=Count("appairages", filter=Q(appairages__statut=AppairageStatut.ACCEPTE), distinct=True),
                app_refuse=Count("appairages", filter=Q(appairages__statut=AppairageStatut.REFUSE), distinct=True),
                app_annule=Count("appairages", filter=Q(appairages__statut=AppairageStatut.ANNULE), distinct=True),
                app_a_faire=Count("appairages", filter=Q(appairages__statut=AppairageStatut.A_FAIRE), distinct=True),
                app_contrat_a_signer=Count("appairages", filter=Q(appairages__statut=AppairageStatut.CONTRAT_A_SIGNER), distinct=True),
                app_contrat_en_attente=Count("appairages", filter=Q(appairages__statut=AppairageStatut.CONTRAT_EN_ATTENTE), distinct=True),
                app_appairage_ok=Count("appairages", filter=Q(appairages__statut=AppairageStatut.APPAIRAGE_OK), distinct=True),
            ).order_by(*group_fields)
        )

        for r in rows:
            r["total_disponibles"] = int(r["total_dispo_crif"]) + int(r["total_dispo_mp"])
            r["taux_saturation"] = self._pct(r["total_inscrits"], r["total_places"])
            r["repartition_financeur"] = {
                "crif": int(r["total_inscrits_crif"]),
                "mp": int(r["total_inscrits_mp"]),
                "crif_pct": self._pct(r["total_inscrits_crif"], r["total_inscrits"]),
                "mp_pct": self._pct(r["total_inscrits_mp"], r["total_inscrits"]),
            }

        # Labels
        if by == "formation":
            for r in rows:
                r["group_key"] = r.get("id")
                r["group_label"] = r.get("nom") or (f"Formation #{r.get('id')}" if r.get("id") is not None else "—")
        elif by == "centre":
            for r in rows:
                r["group_key"] = r.get("centre_id")
                r["group_label"] = r.get("centre__nom") or (f"Centre #{r.get('centre_id')}" if r.get("centre_id") is not None else "—")
        elif by == "departement":
            for r in rows:
                r["group_key"] = r.get("departement")
                r["group_label"] = r.get("departement") or "—"
        elif by in {"type_offre", "statut"}:
            fk_field = Formation._meta.get_field(by)
            model = fk_field.remote_field.model  # type: ignore[attr-defined]
            ids = [r.get(f"{by}_id") for r in rows if r.get(f"{by}_id") is not None]
            label_map = self._fk_label_map(model, ids)
            for r in rows:
                gid = r.get(f"{by}_id")
                r["group_key"] = gid
                r["group_label"] = label_map.get(gid, f"{by.replace('_', ' ').title()} #{gid}" if gid is not None else "—")

        return Response({"group_by": by, "results": rows})

    # ────────────────────────────────────────────────────────────
    # Tops (identique)
    # ────────────────────────────────────────────────────────────
    @action(detail=False, methods=["GET"], url_path="tops")
    def tops(self, request):
        qs = self._apply_common_filters(self.get_queryset()).annotate(
            total_places=F("prevus_crif") + F("prevus_mp"),
            total_inscrits=F("inscrits_crif") + F("inscrits_mp"),
            places_disponibles=Greatest(
                (F("prevus_crif") + F("prevus_mp")) - (F("inscrits_crif") + F("inscrits_mp")),
                Value(0),
            ),
        )
        limit = int(request.query_params.get("limit", 10))
        a_recruter = list(
            qs.filter(places_disponibles__gt=0)
            .values("id", "nom", "places_disponibles")
            .order_by("-places_disponibles")[:limit]
        )
        qs_taux = qs.annotate(taux=Coalesce(100.0 * F("total_inscrits") / NullIf(F("total_places"), 0), Value(0.0)))
        top_saturees = list(qs_taux.values("id", "nom", "taux").order_by("-taux")[:limit])
        en_tension = list(
            qs_taux.filter(taux__gte=80.0, places_disponibles__gt=0)
            .values("id", "nom", "taux", "places_disponibles")
            .order_by("places_disponibles", "-taux")[:limit]
        )
        return Response({"a_recruter": a_recruter, "top_saturees": top_saturees, "en_tension": en_tension})




# rap_app/api/viewsets/stats_viewsets/partenaires_stats_viewsets.py

from collections import OrderedDict
from typing import Dict, List, Tuple, Optional

from django.db.models import (
    Q,
    Count,
    IntegerField,
    Value,
    F,
)
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
    # Helpers
    # ------------------------------
    @staticmethod
    def _date_filters(request) -> Tuple[Optional[str], Optional[str]]:
        df = request.query_params.get("date_from") or None
        dt = request.query_params.get("date_to") or None
        return df, dt

    @staticmethod
    def _apply_base_filters(qs, request):
        """
        Ajoute des filtres "structurants" si tu en as besoin (centre_id, departement, search, etc.).
        Ici on laisse neutre pour ne pas surprendre.
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
        base_qs = self._apply_base_filters(Partenaire.objects.all(), request)

        pros_q = self._mk_pros_filters(date_from, date_to)
        app_q = self._mk_app_filters(date_from, date_to)

        # KPIs globaux
        agg = base_qs.aggregate(
            nb_partenaires=Count("id", distinct=True),
            nb_avec_contact=Count(
                "id",
                distinct=True,
                filter=Q(
                    Q(contact_nom__isnull=False) | Q(contact_email__isnull=False) | Q(contact_telephone__isnull=False)
                )
                & ~Q(contact_nom="")
                | ~Q(contact_email="")
                | ~Q(contact_telephone="")
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
            nb_formations_app=Count("appairages__formation", distinct=True, filter=app_q & Q(appairages__formation__isnull=False)),
            nb_formations_pros=Count("prospections__formation", distinct=True, filter=pros_q & Q(prospections__formation__isnull=False)),
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

        qs = self._apply_base_filters(Partenaire.objects.all(), request)

        # Group fields
        group_fields: List[str] = []
        # Additional annotate needed (departement)
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

        # 🔧 Fusion en évitant les doublons (ex: 'a_faire' existe dans les 2 familles)
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
                    filter=Q(
                        Q(contact_nom__isnull=False)
                        | Q(contact_email__isnull=False)
                        | Q(contact_telephone__isnull=False)
                    )
                    & (~Q(contact_nom="") | ~Q(contact_email="") | ~Q(contact_telephone="")),
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

        base_qs = self._apply_base_filters(Partenaire.objects.all(), request)

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
    • KPIs : total, actives, à relancer, acceptées, refusées, annulées, par statut/motif/objectif/moyen.
    • `group_label` renvoyé pour tous les regroupements.
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
        qs = Prospection.objects.select_related("centre", "formation", "partenaire", "owner")
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
            "kpis": {k: int(v or 0) for k, v in agg.items()},
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
            "formation": ["formation_id", "formation__nom"],
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

        # Labels clairs pour chaque regroupement
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

        return Response({"group_by": by, "results": rows})

# rap_app/api/viewsets/stats_viewsets/atelier_tre_stats_viewset.py
from datetime import datetime
from typing import Any, Dict, List, Tuple

from django.db.models import Count, Q, Sum, Case, When, IntegerField
from django.utils.dateparse import parse_date
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rap_app.models.atelier_tre import AtelierTRE, AtelierTREPresence, PresenceStatut


def _parse_date(value: str | None):
    if not value:
        return None
    try:
        # accepte YYYY-MM-DD
        return parse_date(value)
    except Exception:
        return None


class AtelierTREStatsViewSet(viewsets.ViewSet):
    """
    /api/ateliertre-stats/           -> overview
    /api/ateliertre-stats/grouped/   -> groupé par centre|departement|type_atelier
    /api/ateliertre-stats/tops/      -> tops (types & centres)
    """
    permission_classes = [permissions.IsAuthenticated]

    # ─────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────
    def _apply_filters(self, qs, request):
        """
        Filtres supportés:
          - date_from, date_to         (YYYY-MM-DD) sur date_atelier (date)
          - centre (id)
          - departement (centre__departement)
          - type_atelier
        """
        date_from = _parse_date(request.query_params.get("date_from"))
        date_to = _parse_date(request.query_params.get("date_to"))
        centre = request.query_params.get("centre")
        departement = request.query_params.get("departement")
        type_atelier = request.query_params.get("type_atelier") or request.query_params.get("type")

        if date_from:
            qs = qs.filter(date_atelier__date__gte=date_from)
        if date_to:
            qs = qs.filter(date_atelier__date__lte=date_to)
        if centre:
            qs = qs.filter(centre_id=centre)
        if departement:
            # ⚠️ adapte le champ si ton modèle Centre utilise un autre nom (ex: code_departement)
            qs = qs.filter(centre__departement=departement)
        if type_atelier:
            qs = qs.filter(type_atelier=type_atelier)

        return qs

    def _presence_counts_for_qs(self, qs):
        pres_qs = AtelierTREPresence.objects.filter(atelier__in=qs)
        total = pres_qs.count()
        by_status = dict(
            pres_qs.values_list("statut").annotate(c=Count("id"))
        )
        # normalise clés manquantes à 0
        norm = {
            PresenceStatut.INCONNU: by_status.get(PresenceStatut.INCONNU, 0),
            PresenceStatut.PRESENT: by_status.get(PresenceStatut.PRESENT, 0),
            PresenceStatut.ABSENT: by_status.get(PresenceStatut.ABSENT, 0),
            PresenceStatut.EXCUSE: by_status.get(PresenceStatut.EXCUSE, 0),
        }
        return total, norm

    # ─────────────────────────────────────────────────────────────
    # Overview
    # ─────────────────────────────────────────────────────────────
    def list(self, request, *args, **kwargs):
        qs = self._apply_filters(AtelierTRE.objects.all(), request)

        nb_ateliers = qs.count()

        # nombre de candidats uniques liés aux ateliers (via M2M)
        from rap_app.models.candidat import Candidat  # import local pour éviter cycles
        nb_candidats_uniques = (
            Candidat.objects.filter(ateliers_tre__in=qs).distinct().count()
        )

        # total d'inscriptions (M2M rows) → Count("candidats") agrège toutes les lignes
        inscrits_total = qs.aggregate(total=Count("candidats"))["total"] or 0

        # répartition par type d’atelier (un seul GROUP BY)
        type_map = dict(qs.values_list("type_atelier").annotate(c=Count("id")))

        # présences
        pres_total, pres_map = self._presence_counts_for_qs(qs)

        data = {
            "kpis": {
                "nb_ateliers": nb_ateliers,
                "nb_candidats_uniques": nb_candidats_uniques,
                "inscrits_total": inscrits_total,
                "ateliers": type_map,               # { "atelier_1": 3, "atelier_2": 1, ...}
                "presences_total": pres_total,
                "presences": pres_map,              # { "present": X, "absent": Y, ...}
            },
            "filters_echo": {k: v for k, v in request.query_params.items()},
        }
        return Response(data)

    # ─────────────────────────────────────────────────────────────
    # Grouped
    # ─────────────────────────────────────────────────────────────
    @action(detail=False, methods=["GET"], url_path="grouped")
    def grouped(self, request, *args, **kwargs):
        by = request.query_params.get("by") or "centre"
        if by not in ("centre", "departement", "type_atelier"):
            return Response({"detail": "Paramètre 'by' invalide."}, status=400)

        qs = self._apply_filters(AtelierTRE.objects.all(), request)

        if by == "centre":
            group_fields: Tuple[str, ...] = ("centre_id", "centre__nom")
        elif by == "departement":
            # ⚠️ adapte si ton modèle Centre utilise un autre nom
            group_fields = ("centre__departement",)
        else:  # type_atelier
            group_fields = ("type_atelier",)

        # agrégations de présence
        present = Sum(
            Case(When(presences__statut=PresenceStatut.PRESENT, then=1), default=0, output_field=IntegerField())
        )
        absent = Sum(
            Case(When(presences__statut=PresenceStatut.ABSENT, then=1), default=0, output_field=IntegerField())
        )
        excuse = Sum(
            Case(When(presences__statut=PresenceStatut.EXCUSE, then=1), default=0, output_field=IntegerField())
        )
        inconnu = Sum(
            Case(When(presences__statut=PresenceStatut.INCONNU, then=1), default=0, output_field=IntegerField())
        )

        base = (
            qs.values(*group_fields)
              .annotate(
                  nb_ateliers=Count("id", distinct=True),
                  candidats_uniques=Count("candidats", distinct=True),
                  presences_total=Count("presences"),
                  present=present,
                  absent=absent,
                  excuse=excuse,
                  inconnu=inconnu,
              )
              .order_by(*group_fields)
        )

        results: List[Dict[str, Any]] = []
        for row in base:
            if by == "centre":
                group_key = row.get("centre_id")
                group_label = row.get("centre__nom") or (f"Centre #{group_key}" if group_key else "—")
            elif by == "departement":
                group_key = row.get("centre__departement")
                group_label = group_key or "—"
            else:  # type_atelier
                group_key = row.get("type_atelier")
                # petit mapping lisible ; côté front on n’a pas besoin de recoder
                group_label = dict(AtelierTRE.TypeAtelier.choices).get(group_key, group_key or "—")

            results.append(
                {
                    "group_key": group_key,
                    "group_label": group_label,
                    **row,
                }
            )

        return Response(
            {
                "by": by,
                "results": results,
                "filters_echo": {k: v for k, v in request.query_params.items()},
            }
        )

    # ─────────────────────────────────────────────────────────────
    # Tops
    # ─────────────────────────────────────────────────────────────
    @action(detail=False, methods=["GET"], url_path="tops")
    def tops(self, request, *args, **kwargs):
        qs = self._apply_filters(AtelierTRE.objects.all(), request)

        # Top types par nb d’ateliers
        top_types_qs = qs.values("type_atelier").annotate(count=Count("id")).order_by("-count")[:10]
        top_types = [
            {
                "type_atelier": r["type_atelier"],
                "label": dict(AtelierTRE.TypeAtelier.choices).get(r["type_atelier"], r["type_atelier"]),
                "count": r["count"],
            }
            for r in top_types_qs
        ]

        # Top centres par nb d’ateliers
        top_centres_qs = qs.values("centre_id", "centre__nom").annotate(count=Count("id")).order_by("-count")[:10]
        top_centres = [
            {"id": r["centre_id"], "nom": r["centre__nom"] or f"Centre #{r['centre_id']}", "count": r["count"]}
            for r in top_centres_qs
        ]

        return Response(
            {
                "top_types": top_types,
                "top_centres": top_centres,
                "filters_echo": {k: v for k, v in request.query_params.items()},
            }
        )
