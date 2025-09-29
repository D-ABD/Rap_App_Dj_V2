from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import csv

from ...models.atelier_tre import (
    AtelierTRE,
    PresenceStatut,
)
from ...models.candidat import Candidat
from ..serializers.atelier_tre_serializers import (
    AtelierTRESerializer,
    AtelierTREMetaSerializer,
)
from ..permissions import IsStaffOrAbove, is_staff_or_staffread
from ..paginations import RapAppPagination


class AtelierTREViewSet(viewsets.ModelViewSet):
    """
    CRUD minimal des ateliers TRE (M2M direct pour les candidats).
    Accès réservé au staff (lecture/écriture).

    - Filtres: type_atelier, centre, date_atelier (exact/gte/lte)
    - Tri: date_atelier, type_atelier, id
    - Endpoints utilitaires: /meta, /add-candidats, /remove-candidats
    - Présences: /set-presences, /mark-present, /mark-absent

    ⚠️ Scope centres :
      - Admin/Superadmin : accès global
      - Staff : limité aux ateliers dont centre ∈ user.centres
    """
    permission_classes = [IsStaffOrAbove]  # ✅ staff-only partout
    pagination_class = RapAppPagination
    serializer_class = AtelierTRESerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {
        "type_atelier": ["exact", "in"],
        "centre": ["exact", "isnull"],
        "date_atelier": ["exact", "date", "gte", "lte"],
    }
    ordering_fields = ["date_atelier", "type_atelier", "id"]
    ordering = ["-date_atelier", "-id"]

    # --------------------- helpers scope/permissions ---------------------

    def _is_admin_like(self, user) -> bool:
        """True si admin ou superadmin."""
        return getattr(user, "is_superuser", False) or (
            hasattr(user, "is_admin") and user.is_admin()
        )

    def _staff_centre_ids(self, user):
        """Liste des centres visibles par staff/staff_read (None si admin-like = accès global)."""
        if self._is_admin_like(user):
            return None
        if is_staff_or_staffread(user):  # ✅ inclut staff_read
            return list(user.centres.values_list("id", flat=True))
        return []

    def _scope_qs_to_user_centres(self, qs):
        """Filtre le queryset selon les centres accessibles."""
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()

        # Candidats/stagiaires → pas d'accès
        if hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire():
            return qs.none()

        centre_ids = self._staff_centre_ids(user)

        # admin/superadmin → pas de restriction
        if centre_ids is None:
            return qs

        # staff/staff_read avec centres
        if centre_ids:
            return qs.filter(centre_id__in=centre_ids).distinct()

        # staff/staff_read sans centre → aucun résultat
        return qs.none()

    def _assert_staff_can_use_centre(self, centre):
        """Empêche un staff/staff_read d'écrire hors de son périmètre de centres."""
        if not centre:
            return
        user = self.request.user
        if self._is_admin_like(user):
            return
        if is_staff_or_staffread(user):  # ✅ inclut staff_read
            allowed = set(user.centres.values_list("id", flat=True))
            if getattr(centre, "id", None) not in allowed:
                raise PermissionDenied("Centre hors de votre périmètre.")

    # ------------------------------ queryset ------------------------------

    def get_queryset(self):
        base = (
            AtelierTRE.objects
            # ⬇️ NE PAS annoter "nb_inscrits" (conflit avec @property du modèle)
            .annotate(nb_inscrits_calc=Count("candidats", distinct=True))
            .select_related("centre", "created_by", "updated_by")
            .prefetch_related("candidats")
        )
        return self._scope_qs_to_user_centres(base)

    # --- création / mise à jour (propager l'utilisateur si supporté par BaseModel.save) ---

    def perform_create(self, serializer):
        instance = serializer.save()
        # Vérifie le centre (si fourni par le payload)
        self._assert_staff_can_use_centre(getattr(instance, "centre", None))
        try:
            instance.save(user=self.request.user)
        except TypeError:
            instance.save()

    def perform_update(self, serializer):
        # On récupère le centre proposé (ou existant)
        current = serializer.instance
        new_centre = serializer.validated_data.get("centre", getattr(current, "centre", None))
        self._assert_staff_can_use_centre(new_centre)

        instance = serializer.save()
        try:
            instance.save(user=self.request.user)
        except TypeError:
            instance.save()

    # --- Meta (petit durcissement) ---
    @extend_schema(responses=AtelierTREMetaSerializer)
    @action(detail=False, methods=["get"], url_path="meta", url_name="meta", permission_classes=[IsStaffOrAbove])
    def meta(self, request):
        # instancier avec un "instance={}" pour forcer la représentation complète
        ser = AtelierTREMetaSerializer(instance={}, context={"request": request})
        return Response(ser.data)

    # --- Actions candidats (ajout/retrait sans remplacer toute la liste) ------

    @extend_schema(
        request={"application/json": {"type": "object", "properties": {
            "candidats": {"type": "array", "items": {"type": "integer"}}
        }}},
        responses=AtelierTRESerializer,
        summary="Ajouter des candidats",
        description=(
            "Ajoute des candidats (IDs) à l'atelier sans écraser les existants. "
            "Les candidats doivent appartenir au même centre que l’atelier (via candidat.formation.centre)."
        ),
    )
    @action(detail=True, methods=["post"], url_path="add-candidats", permission_classes=[IsStaffOrAbove])
    def add_candidats(self, request, pk=None):
        atelier = self.get_object()  # ✅ déjà scopé par get_queryset()
        ids = request.data.get("candidats", [])
        if not isinstance(ids, list) or any(not isinstance(i, int) for i in ids):
            return Response(
                {"detail": "'candidats' doit être une liste d'entiers."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not ids:
            return Response(self.get_serializer(atelier).data)

        qs = Candidat.objects.filter(id__in=ids)

        if not qs.exists():
            return Response(
                {"detail": "Aucun candidat trouvé pour les IDs fournis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ Vérifier appartenance au même centre (via la formation du candidat)
        atelier_centre_id = getattr(atelier.centre, "id", None)
        mismatched = [
            c.id for c in qs
            if getattr(getattr(c, "formation", None), "centre_id", None) != atelier_centre_id
        ]
        if mismatched:
            return Response(
                {"detail": f"Candidats hors centre de l'atelier: {sorted(mismatched)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        atelier.candidats.add(*qs)
        return Response(self.get_serializer(atelier).data)

    @extend_schema(
        request={"application/json": {"type": "object", "properties": {
            "candidats": {"type": "array", "items": {"type": "integer"}}
        }}},
        responses=AtelierTRESerializer,
        summary="Retirer des candidats",
        description="Retire des candidats (IDs) de l'atelier.",
    )
    @action(detail=True, methods=["post"], url_path="remove-candidats", permission_classes=[IsStaffOrAbove])
    def remove_candidats(self, request, pk=None):
        atelier = self.get_object()
        ids = request.data.get("candidats", [])
        if not isinstance(ids, list) or any(not isinstance(i, int) for i in ids):
            return Response(
                {"detail": "'candidats' doit être une liste d'entiers."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not ids:
            return Response(self.get_serializer(atelier).data)

        qs = Candidat.objects.filter(id__in=ids)
        if not qs.exists():
            return Response(
                {"detail": "Aucun candidat trouvé pour les IDs fournis."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        atelier.candidats.remove(*qs)
        return Response(self.get_serializer(atelier).data)

    # --- Présences ------------------------------------------------------------

    @extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "candidat": {"type": "integer"},
                                "statut": {"type": "string"},
                                "commentaire": {"type": "string"},
                            },
                            "required": ["candidat", "statut"],
                        },
                    }
                },
                "required": ["items"],
            }
        },
        responses=AtelierTRESerializer,
        summary="Définir des présences (upsert par candidat)",
        description="Met à jour (ou crée) la présence pour chaque (candidat, atelier).",
    )
    @action(detail=True, methods=["post"], url_path="set-presences", permission_classes=[IsStaffOrAbove])
    def set_presences(self, request, pk=None):
        atelier = self.get_object()
        items = request.data.get("items", [])
        if not isinstance(items, list):
            return Response(
                {"detail": "'items' doit être une liste d'objets {candidat, statut, commentaire?}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed = {code for code, _ in PresenceStatut.choices}
        pairs = {}
        for it in items:
            if not isinstance(it, dict):
                return Response({"detail": "Chaque item doit être un objet."}, status=status.HTTP_400_BAD_REQUEST)
            cid = it.get("candidat")
            st = it.get("statut")
            com = it.get("commentaire", None)
            if not isinstance(cid, int) or st not in allowed:
                return Response({"detail": f"Item invalide: {it!r}"}, status=status.HTTP_400_BAD_REQUEST)
            pairs[cid] = {"statut": st, "commentaire": com}

        if not pairs:
            return Response(self.get_serializer(atelier).data)

        # Vérifie que les candidats existent
        wanted_ids = set(pairs.keys())
        existing_ids = set(Candidat.objects.filter(id__in=wanted_ids).values_list("id", flat=True))
        unknown = wanted_ids - existing_ids
        if unknown:
            return Response({"detail": f"Candidats introuvables: {sorted(unknown)}"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Vérifie appartenance au même centre que l'atelier
        atelier_centre_id = getattr(atelier.centre, "id", None)
        mismatch = [
            cid for cid in wanted_ids
            if getattr(getattr(Candidat.objects.get(id=cid), "formation", None), "centre_id", None) != atelier_centre_id
        ]
        if mismatch:
            return Response(
                {"detail": f"Candidats hors centre de l'atelier: {sorted(mismatch)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Vérifie inscription préalable à l'atelier
        inscrits_ids = set(atelier.candidats.values_list("id", flat=True))
        not_enrolled = wanted_ids - inscrits_ids
        if not_enrolled:
            return Response(
                {"detail": f"Candidats non inscrits à l'atelier: {sorted(not_enrolled)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Upsert
        for cid in wanted_ids:
            data = pairs[cid]
            c = Candidat.objects.get(id=cid)
            atelier.set_presence(candidat=c, statut=data["statut"], commentaire=data.get("commentaire"), user=request.user)

        return Response(self.get_serializer(atelier).data)

    @extend_schema(
        request={"application/json": {"type": "object", "properties": {"candidats": {"type": "array", "items": {"type": "integer"}}}}},
        responses=AtelierTRESerializer,
        summary="Marquer présents",
    )
    @action(detail=True, methods=["post"], url_path="mark-present", permission_classes=[IsStaffOrAbove])
    def mark_present(self, request, pk=None):
        atelier = self.get_object()
        ids = request.data.get("candidats", [])
        if not isinstance(ids, list) or any(not isinstance(i, int) for i in ids):
            return Response({"detail": "'candidats' doit être une liste d'entiers."},
                            status=status.HTTP_400_BAD_REQUEST)

        # ✅ ne garde que les candidats déjà inscrits
        qs = atelier.candidats.filter(id__in=ids)
        for c in qs:
            # (optionnel) vérifier centre cohérent ici aussi — l'inscription l'a déjà garanti
            atelier.set_presence(c, PresenceStatut.PRESENT, user=request.user)
        return Response(self.get_serializer(atelier).data)

    @extend_schema(
        request={"application/json": {"type": "object", "properties": {"candidats": {"type": "array", "items": {"type": "integer"}}}}},
        responses=AtelierTRESerializer,
        summary="Marquer absents",
    )
    @action(detail=True, methods=["post"], url_path="mark-absent", permission_classes=[IsStaffOrAbove])
    def mark_absent(self, request, pk=None):
        atelier = self.get_object()
        ids = request.data.get("candidats", [])
        if not isinstance(ids, list) or any(not isinstance(i, int) for i in ids):
            return Response({"detail": "'candidats' doit être une liste d'entiers."},
                            status=status.HTTP_400_BAD_REQUEST)

        # ✅ idem ici
        qs = atelier.candidats.filter(id__in=ids)
        for c in qs:
            atelier.set_presence(c, PresenceStatut.ABSENT, user=request.user)
        return Response(self.get_serializer(atelier).data)