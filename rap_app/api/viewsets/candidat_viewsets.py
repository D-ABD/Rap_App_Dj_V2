from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.renderers import JSONRenderer
from django.http import HttpResponse
from django.db import transaction
from django.db.models import Q, Count, OuterRef, Subquery, IntegerField, Value, Prefetch
from django.db.models.functions import Coalesce
from django.template.loader import render_to_string
from weasyprint import HTML
import csv
import logging
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from ...models import atelier_tre

# ✅ imports modèles
from ...models.candidat import (
    Candidat,
    HistoriquePlacement,
    ResultatPlacementChoices,
    NIVEAU_CHOICES,
)
from ...models.prospection import Prospection
from ...models.centres import Centre
from ...models.formations import Formation

# ✅ imports serializers
from ..serializers.candidat_serializers import (
    CandidatSerializer,
    CandidatListSerializer,
    CandidatCreateUpdateSerializer,
    HistoriquePlacementSerializer,
    HistoriquePlacementMetaSerializer,
    CandidatQueryParamsSerializer,  # pour valider/normaliser les query params
)

from ..permissions import IsStaffOrAbove
from ..paginations import RapAppPagination
from ...utils.filters import CandidatFilter

# ✅ logger dédié
logger = logging.getLogger("rap_app.candidats")

SENSITIVE_KEYS = {"password", "token", "secret", "api_key", "auth", "credential", "authorization"}


def _sanitize_dict(d: dict) -> dict:
    out = {}
    for k, v in d.items():
        if any(s in k.lower() for s in SENSITIVE_KEYS):
            out[k] = "***"
        else:
            out[k] = v
    return out


# ─────────────────────────────────────────────────────────────────────────────
# ✅ Construction robuste du payload /candidats/meta/ (scope staff inclus)
# ─────────────────────────────────────────────────────────────────────────────
def _build_candidat_meta(user=None) -> dict:
    # Scope centres/formations selon l'utilisateur
    is_admin_like = bool(getattr(user, "is_superuser", False) or (hasattr(user, "is_admin") and user.is_admin()))
    if is_admin_like:
        centres_qs = Centre.objects.order_by("nom").only("id", "nom")
        formations_qs = Formation.objects.select_related("centre").only("id", "nom", "num_offre", "centre__nom").order_by("nom")
    else:
        centre_ids = list(getattr(user, "centres", Centre.objects.none()).values_list("id", flat=True)) if getattr(user, "is_staff", False) else []
        centres_qs = Centre.objects.filter(id__in=centre_ids).order_by("nom").only("id", "nom") if centre_ids else Centre.objects.none()
        formations_qs = Formation.objects.select_related("centre").filter(centre_id__in=centre_ids).only("id", "nom", "num_offre", "centre__nom").order_by("nom") if centre_ids else Formation.objects.none()

    return {
        "statut_choices": [{"value": k, "label": v} for k, v in Candidat.StatutCandidat.choices],
        "cv_statut_choices": [{"value": k, "label": v} for k, v in Candidat.CVStatut.choices],
        "type_contrat_choices": [{"value": k, "label": v} for k, v in Candidat.TypeContrat.choices],
        "disponibilite_choices": [{"value": k, "label": v} for k, v in Candidat.Disponibilite.choices],
        "resultat_placement_choices": [{"value": k, "label": v} for k, v in ResultatPlacementChoices.choices],
        "contrat_signe_choices": [{"value": k, "label": v} for k, v in Candidat.ContratSigne.choices],
        "niveau_choices": [{"value": val, "label": f"{val} ★"} for val, _ in NIVEAU_CHOICES],
        "centre_choices": [{"value": c.id, "label": c.nom} for c in centres_qs],
        "formation_choices": [
            {
                "value": f.id,
                "label": f"{f.nom}" + (f" — {f.num_offre}" if f.num_offre else ""),
            }
            for f in formations_qs
        ],
    }


class CandidatViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrAbove]
    pagination_class = RapAppPagination

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CandidatFilter

    search_fields = [
        "nom",
        "prenom",
        "email",
        "telephone",
        "ville",
        "code_postal",
        "origine_sourcing",
        "numero_osia",
        "formation__nom",
        "formation__num_offre",
        "formation__centre__nom",
        "compte_utilisateur__email",
        "placement_appairage__partenaire__nom",
        "cv_statut",
    ]

    ordering_fields = [
        "date_inscription",
        "nom",
        "prenom",
        "statut",
        "cv_statut",
        "formation",
        "formation__nom",
        "formation__centre__nom",
        "nb_appairages_calc",
        "nb_prospections_calc",
        "date_placement",
        "resultat_placement",
        "contrat_signe",
        "entreprise_placement",
        "entreprise_validee",
        "vu_par",
        "placement_appairage__date_appairage",
        "placement_appairage__partenaire__nom",
    ]
    ordering = ["-date_inscription"]

    # ---------- UTILS LOGGING ----------
    def _qp_dict(self, request):
        qp = {}
        for k in request.query_params.keys():
            vals = request.query_params.getlist(k)
            qp[k] = vals if len(vals) > 1 else (vals[0] if vals else None)
        return _sanitize_dict(qp)

    def _log_filters(self, request, base_qs, filtered_qs):
        try:
            logger.debug("🔎 query_params=%s", self._qp_dict(request))
            before_count = base_qs.count()
            after_count = filtered_qs.count()
            logger.debug("📊 queryset counts: before=%s after=%s", before_count, after_count)
            try:
                logger.debug("🧠 SQL: %s", str(filtered_qs.query))
            except Exception:
                logger.debug("🧠 SQL: <unavailable>")

            backend = DjangoFilterBackend()
            fs = backend.get_filterset(request, base_qs, self)
            if fs is not None:
                valid = fs.is_valid()
                form = getattr(fs, "form", None)
                errors = getattr(form, "errors", {})
                cleaned = getattr(form, "cleaned_data", {})
                logger.debug("🧪 FilterSet valid=%s errors=%s cleaned=%s", valid, errors, cleaned)
        except Exception:
            logger.exception("Erreur pendant le logging des filtres.")

    # ---------- helpers scope/permission ----------

    def _is_admin_like(self, user) -> bool:
        return getattr(user, "is_superuser", False) or (hasattr(user, "is_admin") and user.is_admin())

    def _staff_centre_ids(self, user):
        if self._is_admin_like(user):
            return None  # accès global
        if getattr(user, "is_staff", False):
            return list(user.centres.values_list("id", flat=True))
        return []  # non-staff (ne devrait pas passer IsStaffOrAbove)

    def _scope_qs_to_user_centres(self, qs):
        """
        Staff : ne voit que les candidats dont formation.centre_id ∈ ses centres.
        Admin/superadmin : global.
        """
        user = self.request.user
        centre_ids = self._staff_centre_ids(user)
        if centre_ids is None:
            return qs  # admin-like
        if centre_ids:
            return qs.filter(formation__centre_id__in=centre_ids)
        return qs.none()

    def _assert_staff_can_use_formation(self, formation):
        """Empêche un staff d'assigner une formation hors de son périmètre."""
        if not formation:
            return
        user = self.request.user
        if self._is_admin_like(user):
            return
        if getattr(user, "is_staff", False):
            allowed = set(user.centres.values_list("id", flat=True))
            if getattr(formation, "centre_id", None) not in allowed:
                raise PermissionDenied("Formation hors de votre périmètre (centre).")

    # ---------- queryset de base + annotations ----------

    def base_queryset(self):
        qs = (
            Candidat.objects
            .select_related(
                "formation",
                "formation__centre",
                "formation__type_offre",
                "evenement",
                "compte_utilisateur",
                "responsable_placement",
                "vu_par",
                "entreprise_placement",
                "entreprise_validee",
                "placement_appairage",
                "placement_appairage__partenaire",
                "placement_appairage__created_by",
                "placement_appairage__updated_by",
            )
            .prefetch_related(
                "appairages",
                Prefetch(
                    "ateliers_tre",
                    queryset=atelier_tre.AtelierTRE.objects.only("id", "type_atelier"),
                ),
            )
        )

        # nb d'appairages par candidat (distinct)
        qs = qs.annotate(nb_appairages_calc=Count("appairages", distinct=True))

        # nb de prospections via subquery sur le propriétaire (compte_utilisateur)
        prospection_cnt = (
            Prospection.objects
            .filter(owner_id=OuterRef("compte_utilisateur_id"))
            .values("owner_id")
            .annotate(c=Count("id"))
            .values("c")[:1]
        )
        qs = qs.annotate(
            nb_prospections_calc=Coalesce(
                Subquery(prospection_cnt, output_field=IntegerField()),
                Value(0),
                output_field=IntegerField(),
            )
        )

        # (optionnel) ajoute les flags/compteurs par type d’atelier
        qs = atelier_tre.AtelierTRE.annotate_candidats_with_atelier_flags(qs)
        return qs

    def get_queryset(self):
        return self._scope_qs_to_user_centres(self.base_queryset())

    # ---------- list (log) ----------

    def list(self, request, *args, **kwargs):
        qp_ser = CandidatQueryParamsSerializer(data=request.query_params)
        qp_ser.is_valid(raise_exception=False)
        logger.debug(
            "🧭 qp valid=%s errors=%s cleaned=%s",
            qp_ser.is_valid(), qp_ser.errors, qp_ser.validated_data,
        )

        base_qs = self.get_queryset()
        filtered_qs = self.filter_queryset(base_qs)
        self._log_filters(request, base_qs, filtered_qs)

        return super().list(request, *args, **kwargs)

    # ---------- serializer + context ----------

    def get_serializer_class(self):
        if self.action == "list":
            return CandidatListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return CandidatCreateUpdateSerializer
        return CandidatSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = getattr(self, "request", None)
        return ctx

    # ---------- create/update : contrôle périmètre formation ----------

    def perform_create(self, serializer):
        instance = serializer.save()
        # Si formation fournie, vérifier périmètre du staff
        self._assert_staff_can_use_formation(getattr(instance, "formation", None))
        try:
            instance.save(user=self.request.user)  # si BaseModel.save(user=...)
        except TypeError:
            pass

    def _cascade_update_prospections_on_formation_change(self, candidat, old_form, new_form):
        """
        Recale toutes les prospections du candidat (owner = candidat.compte_utilisateur)
        - Si new_form est défini  : formation = new_form, centre_id = new_form.centre_id (bulk update)
        - Si new_form est None     : formation = None, centre_id = partenaire.default_centre_id (si dispo) sinon inchangé
                                     (fait en loop, car on dépend du partenaire)
        On ne met à jour QUE les prospections dont la formation était NULL ou == old_form,
        pour éviter d’écraser des choix manuels.
        """
        owner = getattr(candidat, "compte_utilisateur", None)
        if not owner:
            return

        base_qs = Prospection.objects.filter(owner=owner)
        if old_form is not None:
            qs = base_qs.filter(Q(formation__isnull=True) | Q(formation_id=old_form.id))
        else:
            qs = base_qs.filter(formation__isnull=True)

        if not qs.exists():
            return

        if new_form:
            # 🔄 Bulk update quand on peut (plus rapide)
            qs.update(formation=new_form, centre_id=new_form.centre_id)
        else:
            # 🔄 Pas de formation : pour chaque prospection, centre = partenaire.default_centre (si présent)
            for p in qs.select_related("partenaire"):
                p.formation = None
                fallback_centre_id = getattr(getattr(p, "partenaire", None), "default_centre_id", None)
                if fallback_centre_id is not None:
                    p.centre_id = fallback_centre_id
                # sinon on garde le centre existant
                if hasattr(p, "updated_by"):
                    p.updated_by = self.request.user
                    p.save(update_fields=["formation", "centre_id", "updated_by"])
                else:
                    p.save(update_fields=["formation", "centre_id"])

    def perform_update(self, serializer):
        # --- 1) contrôle périmètre ---
        new_formation = serializer.validated_data.get("formation", serializer.instance.formation)
        self._assert_staff_can_use_formation(new_formation)

        # --- 2) détecter changement de formation ---
        old_formation = serializer.instance.formation

        with transaction.atomic():
            instance = serializer.save()
            try:
                instance.save(user=self.request.user)
            except TypeError:
                pass

            # --- 3) cascade sur Prospection si la formation a changé ---
            old_id = getattr(old_formation, "id", None)
            new_id = getattr(instance.formation, "id", None)
            if old_id != new_id:
                self._cascade_update_prospections_on_formation_change(
                    candidat=instance,
                    old_form=old_formation,
                    new_form=instance.formation,
                )

    # ---------- META / EXPORT ----------

    @extend_schema(responses=None)
    @action(
        detail=False,
        methods=["get"],
        url_path="meta",
        url_name="meta",
        renderer_classes=[JSONRenderer],
        permission_classes=[IsAuthenticated],
    )
    def meta(self, request):
        logger.debug("ℹ️ /candidats/meta called")
        data = _build_candidat_meta(request.user)  # ✅ scope staff
        logger.debug("ℹ️ /candidats/meta keys=%s", list(data.keys()))
        return Response(data)

    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request):
        qs = self.filter_queryset(self.get_queryset())
        logger.debug("📤 export CSV candidats params=%s rows=%d", self._qp_dict(request), qs.count())

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="candidats.csv"'
        writer = csv.writer(response)

        writer.writerow(
            [
                "Nom",
                "Prénom",
                "Email",
                "Téléphone",
                "Formation",
                "Statut CV",
                "Statut",
                "OSIA",
                "Nb appairages",
                "Nb prospections",
            ]
        )
        for c in qs:
            writer.writerow(
                [
                    c.nom,
                    c.prenom,
                    c.email,
                    c.telephone,
                    c.formation.nom if c.formation else "",
                    getattr(c, "get_cv_statut_display", lambda: None)() or (c.cv_statut or ""),
                    c.get_statut_display() if hasattr(c, "get_statut_display") else (c.statut or ""),
                    c.numero_osia or "",
                    getattr(c, "nb_appairages_calc", 0),
                    getattr(c, "nb_prospections_calc", 0),
                ]
            )
        return response

    @action(detail=False, methods=["get"], url_path="export-pdf")
    def export_pdf(self, request):
        qs = self.filter_queryset(self.get_queryset())
        logger.debug("📄 export PDF candidats params=%s rows=%d", self._qp_dict(request), qs.count())
        html_string = render_to_string("exports/candidats_pdf.html", {"candidats": qs})
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="candidats.pdf"'
        return response


class HistoriquePlacementViewSet(viewsets.ReadOnlyModelViewSet):
    """ 📘 Historique des placements des candidats. """

    queryset = HistoriquePlacement.objects.all().select_related("candidat", "entreprise", "responsable", "candidat__formation", "candidat__formation__centre")
    serializer_class = HistoriquePlacementSerializer
    permission_classes = [IsStaffOrAbove]
    pagination_class = RapAppPagination

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["candidat", "entreprise", "responsable", "resultat"]

    search_fields = [
        "candidat__nom",
        "candidat__prenom",
        "candidat__ville",
        "candidat__code_postal",
        "entreprise__nom",
    ]

    ordering_fields = ["date_placement", "created_at"]

    # ✅ scope staff par centres (via candidat.formation.centre)
    def _is_admin_like(self, user) -> bool:
        return getattr(user, "is_superuser", False) or (hasattr(user, "is_admin") and user.is_admin())

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if self._is_admin_like(u):
            return qs
        if getattr(u, "is_staff", False):
            centre_ids = list(u.centres.values_list("id", flat=True))
            if not centre_ids:
                return qs.none()
            return qs.filter(candidat__formation__centre_id__in=centre_ids)
        return qs.none()

    def list(self, request, *args, **kwargs):
        base_qs = self.get_queryset()
        filtered_qs = self.filter_queryset(base_qs)
        try:
            logger.debug(
                "📚 HP list params=%s before=%d after=%d SQL=%s",
                {k: request.query_params.getlist(k) for k in request.query_params.keys()},
                base_qs.count(),
                filtered_qs.count(),
                str(filtered_qs.query),
            )
        except Exception:
            logger.debug("📚 HP list (logging limited)")
        return super().list(request, *args, **kwargs)

    @extend_schema(responses=HistoriquePlacementMetaSerializer)
    @action(
        detail=False, methods=["get"], url_path="meta", url_name="meta", renderer_classes=[JSONRenderer],
    )
    def meta(self, request):
        logger.debug("ℹ️ /historique-placements/meta called")
        return Response(HistoriquePlacementMetaSerializer().data)
