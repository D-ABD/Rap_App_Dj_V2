from __future__ import annotations
# rap_app/api/viewsets/stats_viewsets/candidats_stats_viewsets.py
# ViewSet DRF — Statistiques des candidats (scope centre + département + appairages)
from ...serializers.base_serializers import EmptySerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter


import logging
from typing import Iterable, Literal, Optional

from django.db import models
from django.db.models import Count, Q, Value
from django.db.models.functions import Coalesce, Substr
from django.utils.dateparse import parse_date

from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from ...permissions import IsStaffOrAbove, is_staff_or_staffread

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


def _poei_poec_values() -> list[str]:
    """
    Support des valeurs historiques et de la nouvelle valeur unique.
    """
    return [
        "poei", "poe_i",
        "poec", "poe_c",
        getattr(Candidat.TypeContrat, "POEI_POEC", "poei_poec"),
    ]


class CandidatStatsViewSet(RestrictToUserOwnedQueryset, GenericViewSet):
    serializer_class = EmptySerializer
    """
    KPIs & agrégats sur Candidat.
    Endpoints :
      GET /candidat-stats/                 → résumé global
      GET /candidat-stats/grouped/?by=... → groupés par centre|departement|formation|statut|type_contrat|cv_statut|resultat_placement|contrat_signe|responsable|entreprise
    """

    permission_classes = [IsStaffOrAbove]

    # ───────────────────────────────
    # Helpers périmètre staff
    # ───────────────────────────────
    def _is_admin_like(self, user) -> bool:
        return bool(
            getattr(user, "is_superuser", False)
            or (hasattr(user, "is_admin") and callable(user.is_admin) and user.is_admin())
        )

    def _staff_centre_ids(self, user) -> Optional[list[int]]:
        if self._is_admin_like(user):
            return None
        if is_staff_or_staffread(user) and hasattr(user, "centres"):
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

        if is_staff_or_staffread(user):
            centre_ids = self._staff_centre_ids(user)
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
    @extend_schema(
    parameters=[
        OpenApiParameter(
            name="avec_archivees",
            type=bool,
            required=False,
            description="Inclure les candidats liés à des formations archivées (true/false)"
        ),
    ],
)
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
        # 1️⃣ Périmètre user
        qs = self._scope_candidats_for_user(qs, getattr(self.request, "user", None))

        # 2️⃣ Gestion des formations archivées
        inclure_archivees = str(self.request.query_params.get("avec_archivees", "false")).lower() in ["1", "true", "yes", "on"]
        if not inclure_archivees:
            qs = qs.exclude(formation__activite="archivee")

        # 3️⃣ Restriction "owned" pour non-staff
        user = getattr(self.request, "user", None)
        is_staff_like = bool(
            user and (
                getattr(user, "is_superuser", False)
                or is_staff_or_staffread(user)
                or (hasattr(user, "is_admin") and callable(user.is_admin) and user.is_admin())
            )
        )
        if not is_staff_like and hasattr(self, "restrict_queryset_to_user"):
            qs = self.restrict_queryset_to_user(qs)

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

        # Département — couvre CP du centre **ou** du candidat (cohérent avec le scope staff)
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
        if getattr(model, "__name__", "") in {"User", "CustomUser"}:
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
            total=Count("id", distinct=True),
            entretien_ok=Count("id", filter=Q(entretien_done=True), distinct=True),
            test_ok=Count("id", filter=Q(test_is_ok=True), distinct=True),
            gespers=Count("id", filter=Q(inscrit_gespers=True), distinct=True),
            admissibles=Count("id", filter=Q(admissible=True), distinct=True),
            en_formation=Count("id", filter=Q(statut=Candidat.StatutCandidat.EN_FORMATION), distinct=True),
            en_appairage=Count("id", filter=Q(statut=Candidat.StatutCandidat.EN_APPAIRAGE), distinct=True),
            en_accompagnement=Count("id", filter=Q(statut=Candidat.StatutCandidat.EN_ACCOMPAGNEMENT), distinct=True),

            # ⭐️ nouveaux compteurs
            osia_count=Count("id", filter=Q(numero_osia__isnull=False) & ~Q(numero_osia=""), distinct=True),
            cv_renseigne=Count("id", filter=Q(cv_statut__isnull=False) & ~Q(cv_statut=""), distinct=True),
            courrier_rentree_count=Count("id", filter=Q(courrier_rentree=True), distinct=True),

            # 🆕 Ateliers TRE — nombre d'ateliers distincts impliquant ≥1 candidat du périmètre
            ateliers_tre_total=Count("ateliers_tre", distinct=True),

            # contrats (POEI/POEC fusionnés)
            contrat_apprentissage=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.APPRENTISSAGE), distinct=True),
            contrat_professionnalisation=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.PROFESSIONNALISATION), distinct=True),
            contrat_poei_poec=Count("id", filter=Q(type_contrat__in=_poei_poec_values()), distinct=True),
            contrat_sans=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.SANS_CONTRAT), distinct=True),
            contrat_crif=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.CRIF), distinct=True),
            contrat_autre=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.AUTRE), distinct=True),
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
        rep_statut = list(qs.values("statut").annotate(count=Count("id", distinct=True)).order_by("statut"))
        rep_type_contrat = list(qs.values("type_contrat").annotate(count=Count("id", distinct=True)).order_by("type_contrat"))
        rep_cv = list(qs.values("cv_statut").annotate(count=Count("id", distinct=True)).order_by("cv_statut"))
        rep_resultat = list(qs.values("resultat_placement").annotate(count=Count("id", distinct=True)).order_by("resultat_placement"))

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
        "centre": ["formation__centre_id", "formation__centre__nom", "formation__num_offre"],
        "departement": ["departement"],
        "formation": ["formation_id", "formation__nom", "formation__num_offre"],
        "statut": ["statut"],
        "type_contrat": ["type_contrat"],
        "cv_statut": ["cv_statut"],
        "resultat_placement": ["resultat_placement"],
        "contrat_signe": ["contrat_signe"],
        "responsable": ["responsable_placement_id"],
        "entreprise": ["entreprise_placement_id", "entreprise_placement__nom"],
    }

        fields = group_fields_map[by]

        rows = list(
            qs.values(*fields).annotate(
                total=Count("id", distinct=True),
                entretien_ok=Count("id", filter=Q(entretien_done=True), distinct=True),
                test_ok=Count("id", filter=Q(test_is_ok=True), distinct=True),
                gespers=Count("id", filter=Q(inscrit_gespers=True), distinct=True),
                admissibles=Count("id", filter=Q(admissible=True), distinct=True),
                en_formation=Count("id", filter=Q(statut=Candidat.StatutCandidat.EN_FORMATION), distinct=True),
                en_appairage=Count("id", filter=Q(statut=Candidat.StatutCandidat.EN_APPAIRAGE), distinct=True),

                # ⭐️ nouveaux compteurs (groupés)
                rqth_count=Count("id", filter=Q(rqth=True), distinct=True),
                osia_count=Count("id", filter=Q(numero_osia__isnull=False) & ~Q(numero_osia=""), distinct=True),
                cv_renseigne=Count("id", filter=Q(cv_statut__isnull=False) & ~Q(cv_statut=""), distinct=True),
                courrier_rentree_count=Count("id", filter=Q(courrier_rentree=True), distinct=True),

                # 🆕 Ateliers TRE — nombre d'ateliers distincts impliquant ≥1 candidat du groupe
                ateliers_tre_total=Count("ateliers_tre", distinct=True),

                # contrats (POEI/POEC fusionnés)
                contrat_apprentissage=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.APPRENTISSAGE), distinct=True),
                contrat_professionnalisation=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.PROFESSIONNALISATION), distinct=True),
                contrat_poei_poec=Count("id", filter=Q(type_contrat__in=_poei_poec_values()), distinct=True),
                contrat_sans=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.SANS_CONTRAT), distinct=True),
                contrat_autre=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.AUTRE), distinct=True),
                contrat_crif=Count("id", filter=Q(type_contrat=Candidat.TypeContrat.CRIF), distinct=True),


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
                    f"Centre #{r.get('formation__centre_id')}" if r.get('formation__centre_id') is not None else "—"
                )
        elif by == "departement":
            for r in rows:
                r["group_key"] = r.get("departement")
                r["group_label"] = r.get("departement") or "—"
        elif by == "formation":
            for r in rows:
                r["group_key"] = r.get("formation_id")
                num = r.get("formation__num_offre")
                nom = r.get("formation__nom")
                if nom and num:
                    r["group_label"] = f"{nom} ({num})"
                else:
                    r["group_label"] = nom or (
                        f"Formation #{r.get('formation_id')}" if r.get("formation_id") is not None else "—"
                    )

        elif by in {"statut", "type_contrat", "cv_statut", "resultat_placement", "contrat_signe"}:
            key = fields[0]
            for r in rows:
                gid = r.get(key)
                r["group_key"] = gid
                r["group_label"] = gid or "—"
        elif by == "responsable":
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