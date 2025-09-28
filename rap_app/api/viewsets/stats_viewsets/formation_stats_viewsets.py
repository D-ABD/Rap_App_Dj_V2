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

from ...permissions import IsStaffOrAbove

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

    permission_classes = [IsStaffOrAbove]

    # ────────────────────────────────────────────────────────────
    # Helpers périmètre user
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

    def _scope_formations_for_user(self, qs, user):
        if not (user and user.is_authenticated):
            return qs.none()

        if self._is_admin_like(user):
            return qs

        if getattr(user, "is_staff", False):
            centre_ids = self._staff_centre_ids(user)  # [] si pas d'attribut/valeur
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
        qs = Formation.objects.select_related("centre", "type_offre", "statut")
        qs = self._scope_formations_for_user(qs, getattr(self.request, "user", None))

        user = getattr(self.request, "user", None)
        is_staff_like = bool(
            user and (
                getattr(user, "is_superuser", False)
                or getattr(user, "is_staff", False)
                or (hasattr(user, "is_admin") and callable(user.is_admin) and user.is_admin())
            )
        )
        if not is_staff_like and hasattr(self, "restrict_queryset_to_user"):
            qs = self.restrict_queryset_to_user(qs)

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
            # ── Contrats par type
            nb_contrats_apprentissage=Count(
                "id",
                filter=Q(type_contrat=Candidat.TypeContrat.APPRENTISSAGE),
                distinct=True,
            ),
            nb_contrats_professionnalisation=Count(
                "id",
                filter=Q(type_contrat=Candidat.TypeContrat.PROFESSIONNALISATION),
                distinct=True,
            ),
            nb_contrats_poei_poec=Count(
                "id",
                filter=Q(type_contrat=Candidat.TypeContrat.POEI_POEC),
                distinct=True,
            ),
            nb_contrats_autres=Count(
                "id",
                filter=Q(type_contrat__in=[Candidat.TypeContrat.AUTRE, Candidat.TypeContrat.SANS_CONTRAT]),
                distinct=True,
            ),
            nb_admissibles=Count("id", filter=Q(admissible=True), distinct=True),
        )
        cand = {k: int(v or 0) for k, v in cand_agg.items()}

        # ----- Appairages (scopés aux formations du qs)
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
                "appairages": appairages,
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

        # ✅ Ajout de centre__nom et num_offre quand by="formation"
        group_fields = {
            "formation": ["id", "nom", "centre__nom", "num_offre"],
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
                # ── Contrats par type (groupés)
                nb_contrats_apprentissage=Count(
                    "candidats",
                    filter=Q(candidats__type_contrat=Candidat.TypeContrat.APPRENTISSAGE),
                    distinct=True,
                ),
                nb_contrats_professionnalisation=Count(
                    "candidats",
                    filter=Q(candidats__type_contrat=Candidat.TypeContrat.PROFESSIONNALISATION),
                    distinct=True,
                ),
                nb_contrats_poei_poec=Count(
                    "candidats",
                    filter=Q(candidats__type_contrat=Candidat.TypeContrat.POEI_POEC),
                    distinct=True,
                ),
                nb_contrats_autres=Count(
                    "candidats",
                    filter=Q(candidats__type_contrat__in=[Candidat.TypeContrat.AUTRE, Candidat.TypeContrat.SANS_CONTRAT]),
                    distinct=True,
                ),
                nb_admissibles=Count("candidats", filter=Q(candidats__admissible=True), distinct=True),

                # ----- Appairages par statut
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
    # Tops (règles: saturées ≥ 80%, tension < 50% & places > 0)
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

        # Taux = 100 * inscrits / places (0 si places = 0)
        qs_taux = qs.annotate(
            taux=Coalesce(100.0 * F("total_inscrits") / NullIf(F("total_places"), 0), Value(0.0))
        )

        # 1) À recruter : plus de places restantes d'abord
        a_recruter = list(
            qs.filter(places_disponibles__gt=0)
              .values("id", "nom", "places_disponibles", "centre__nom", "num_offre")
              .order_by("-places_disponibles")[:limit]
        )

        # 2) Top saturées : ≥ 80%
        top_saturees = list(
            qs_taux.filter(total_places__gt=0, taux__gte=80.0)
                  .values("id", "nom", "taux", "places_disponibles", "centre__nom", "num_offre")
                  .order_by("-taux")[:limit]
        )

        # 3) En tension : < 50% et encore des places
        en_tension = list(
            qs_taux.filter(total_places__gt=0, places_disponibles__gt=0, taux__lt=50.0)
                  .values("id", "nom", "taux", "places_disponibles", "centre__nom", "num_offre")
                  .order_by("taux", "-places_disponibles")[:limit]
        )

        return Response({
            "a_recruter": a_recruter,
            "top_saturees": top_saturees,
            "en_tension": en_tension,
        })
