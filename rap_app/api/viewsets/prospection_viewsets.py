# views/prospection.py

from django.db import transaction
from rest_framework import viewsets, status, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, OuterRef, Subquery
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiExample,
)
import datetime

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from io import BytesIO
from django.http import HttpResponse
from django.utils import timezone as dj_timezone

from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied

from ...models.prospection_comments import ProspectionComment
from ...models.formations import Formation
from ...utils.filters import ProspectionFilterSet
from ...models.partenaires import Partenaire
from ...models.custom_user import CustomUser
from ...api.paginations import RapAppPagination
from ...models.prospection import Prospection, HistoriqueProspection, ProspectionChoices
from ..serializers.prospection_serializers import (
    ProspectionChoiceListSerializer,
    ProspectionListSerializer,
    ProspectionSerializer,
    ProspectionDetailSerializer,
    HistoriqueProspectionSerializer,
)
from ...models.logs import LogUtilisateur
from ...models.candidat import Candidat
from ..permissions import IsOwnerOrStaffOrAbove  # ✅ protection R/W


# ─────────────────────────────────────────────────────────────────────────────
# Helpers formation
# ─────────────────────────────────────────────────────────────────────────────
def get_candidate_formation(user):
    cand = getattr(user, "candidat_associe", None) or getattr(user, "candidat", None)
    return getattr(cand, "formation", None)


def get_owner_formation(owner):
    if not owner:
        return None
    cand = getattr(owner, "candidat_associe", None) or getattr(owner, "candidat", None)
    return getattr(cand, "formation", None)


def annotate_last_visible_comment(queryset, user):
    base = ProspectionComment.objects.filter(prospection=OuterRef('pk'))

    is_staff_like = bool(
        user.is_authenticated and (user.is_staff or getattr(user, "is_admin", False) or getattr(user, "is_superuser", False))
    )
    is_candidat = bool(
        user.is_authenticated and hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire()
    )

    if is_staff_like:
        visible_sub = base
    elif is_candidat:
        visible_sub = base.filter(Q(is_internal=False) | Q(created_by=user))
    else:
        visible_sub = base.filter(is_internal=False)

    if is_staff_like:
        comments_filter = Q()
    elif is_candidat:
        comments_filter = Q(comments__is_internal=False) | Q(comments__created_by=user)
    else:
        comments_filter = Q(comments__is_internal=False)

    return queryset.annotate(
        last_comment=Subquery(visible_sub.order_by('-created_at').values('body')[:1]),
        last_comment_at=Subquery(visible_sub.order_by('-created_at').values('created_at')[:1]),
        last_comment_id=Subquery(visible_sub.order_by('-created_at').values('id')[:1]),
        comments_count=Count('comments', filter=comments_filter, distinct=True),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Utils parsing ids CSV (pour ?centre=1,2,3 etc.)
# ─────────────────────────────────────────────────────────────────────────────
def _parse_id_list(raw):
    """
    Accepte '12' ou '12,13,14' → renvoie liste d'int valides.
    """
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        items = raw
    else:
        items = str(raw).split(",")
    out = []
    for it in items:
        it = str(it).strip()
        if not it:
            continue
        try:
            out.append(int(it))
        except ValueError:
            continue
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Serializers « créer depuis prospection » (autonomes dans ce fichier)
# ─────────────────────────────────────────────────────────────────────────────
class PartenaireCreateFromProspectionSerializer(serializers.ModelSerializer):
    """Payload minimal pour créer un partenaire depuis une prospection."""
    class Meta:
        model = Partenaire
        fields = [
            "nom", "type", "secteur_activite",
            "street_name", "zip_code", "city", "country",
            "contact_nom", "contact_poste", "contact_telephone", "contact_email",
            "website", "social_network_url",
            "actions", "action_description", "description",
        ]


class PartenaireReadMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partenaire
        fields = [
            "id", "nom", "type", "secteur_activite",
            "city", "zip_code",
            "contact_nom", "contact_email", "contact_telephone",
            "website", "is_active", "created_at", "updated_at",
        ]


class CandidatCreateFromProspectionSerializer(serializers.ModelSerializer):
    """Création rapide d'un candidat depuis une prospection.
       - Remplit la formation à partir de la prospection si non fournie.
       - Défauts sûrs : statut='accompagnement', cv_statut='en_cours' si absents.
    """
    formation = serializers.PrimaryKeyRelatedField(
        queryset=Formation.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Candidat
        fields = [
            "nom", "prenom", "email", "telephone",
            "ville", "code_postal",
            "formation",
            "statut", "cv_statut",
        ]

    def validate_formation(self, value):
        # Même règle usuelle côté CandidatCreateUpdate : staff requis si on fixe la formation
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if value is not None and (not user or getattr(user, "role", None) not in ["admin", "superadmin", "staff"]):
            raise serializers.ValidationError("Seul le staff peut fixer la formation.")
        return value

    def validate(self, attrs):
        attrs.setdefault("statut", getattr(Candidat.StatutCandidat, "ACCOMPAGNEMENT", "accompagnement"))
        attrs.setdefault("cv_statut", getattr(Candidat.CVStatut, "EN_COURS", "en_cours"))
        return attrs


class CandidatReadMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidat
        fields = [
            "id", "nom", "prenom", "email", "telephone",
            "ville", "code_postal", "formation",
            "statut", "cv_statut", "created_at", "updated_at",
        ]


@extend_schema_view(
    list=extend_schema(
        summary="📋 Liste des prospections",
        tags=["Prospections"],
        parameters=[
            OpenApiParameter("statut", str, description="Filtrer par statut (prospection)"),
            OpenApiParameter("formation", int, description="Filtrer par formation (id)"),
            OpenApiParameter("partenaire", int, description="Filtrer par partenaire (id)"),
            OpenApiParameter("owner", int, description="Filtrer par responsable (id)"),
            OpenApiParameter("search", str, description="Recherche texte (commentaire, partenaire, etc.)"),

            # ✅ Nouveaux filtres formation
            OpenApiParameter("formation_type_offre", str, description="ID ou liste d’IDs type d’offre (ex: 1 ou 1,2,3)"),
            OpenApiParameter("formation_statut", str, description="ID ou liste d’IDs statut de formation"),
            OpenApiParameter("centre", str, description="ID ou liste d’IDs centre de formation"),

            # (facultatif) autres filtres déjà supportés par DjangoFilterBackend via ProspectionFilterSet
            OpenApiParameter("moyen_contact", str, description="Moyen de contact (email, telephone, visite, reseaux)"),
            OpenApiParameter("type_prospection", str, description="Type de prospection"),
            OpenApiParameter("motif", str, description="Motif de prospection"),
            OpenApiParameter("objectif", str, description="Objectif de prospection"),
        ],
        responses={200: OpenApiResponse(response=ProspectionListSerializer)},
    ),
    retrieve=extend_schema(
        summary="🔍 Détail d’une prospection",
        tags=["Prospections"],
        responses={200: OpenApiResponse(response=ProspectionDetailSerializer)},
    ),
    create=extend_schema(summary="➕ Créer une prospection", tags=["Prospections"]),
    update=extend_schema(summary="✏️ Modifier une prospection", tags=["Prospections"]),
    destroy=extend_schema(summary="🗑️ Annuler une prospection", tags=["Prospections"]),
)
class ProspectionViewSet(viewsets.ModelViewSet):
    queryset = Prospection.objects.select_related(
        "partenaire",
        "formation",
        "formation__type_offre",
        "formation__statut",
        "formation__centre",
    )
    permission_classes = [IsOwnerOrStaffOrAbove]  # ✅ protège les opérations objet
    pagination_class = RapAppPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProspectionFilterSet
    ordering_fields = ["date_prospection", "created_at", "owner__username", "last_comment_at", "comments_count"]
    ordering = ["created_at"]

    search_fields = [
        "commentaire",
        "statut", "objectif", "motif", "type_prospection",
        "owner__username", "created_by__username",
        "partenaire__nom", "partenaire__city", "partenaire__zip_code",
        "partenaire__secteur_activite", "partenaire__contact_nom",
        "partenaire__contact_email", "partenaire__contact_telephone",
        "formation__nom", "formation__num_offre",
    ]

    # ---------- helpers scope/permissions ----------
    def _is_admin_like(self, user) -> bool:
        # ✅ micro-fix: ne pas appeler is_admin comme un callable
        return bool(getattr(user, "is_superuser", False) or getattr(user, "is_admin", False))

    def _staff_centre_ids(self, user):
        if self._is_admin_like(user):
            return None
        if getattr(user, "is_staff", False):
            return list(user.centres.values_list("id", flat=True))
        return []

    def _scoped_for_user(self, qs, user):
        """Applique le périmètre de visibilité par rôle."""
        if not user.is_authenticated:
            return Prospection.objects.none()

        # candidats / stagiaires → seulement leurs prospections
        if hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire():
            return qs.filter(owner=user)

        # admin/superadmin → tout
        if self._is_admin_like(user):
            return qs

        # staff → prospections dont la formation est dans ses centres
        # + fallback: celles qu'il possède (owner) ou a créées (created_by) si formation absente
        if getattr(user, "is_staff", False):
            centre_ids = self._staff_centre_ids(user) or []
            if not centre_ids:
                return qs.filter(Q(owner=user) | Q(created_by=user))
            return qs.filter(
                Q(formation__centre_id__in=centre_ids) |
                Q(owner=user) |
                Q(created_by=user)
            ).distinct()

        # autres rôles non staff → possède ou a créé
        return qs.filter(Q(owner=user) | Q(created_by=user))

    def _ensure_staff_can_use_formation(self, user, formation: Formation | None):
        """Empêche un staff (non admin) d'utiliser une formation hors de ses centres."""
        if not formation:
            return
        if self._is_admin_like(user):
            return
        if getattr(user, "is_staff", False):
            allowed = set(user.centres.values_list("id", flat=True))
            if formation.centre_id not in allowed:
                raise PermissionDenied("Formation hors de votre périmètre (centres).")

    # ---------- Queryset & visibilité ----------
    def get_queryset(self):
        """
        Annote chaque prospection avec:
          - last_comment, last_comment_at, last_comment_id
          - comments_count (filtré selon la visibilité)
        Et limite la visibilité selon le rôle + centres.
        """
        base = super().get_queryset()
        user = getattr(self.request, "user", None)
        qs = annotate_last_visible_comment(base, user)
        qs = self._scoped_for_user(qs, user)
        return qs

    @action(detail=False, methods=["get"], url_path="filtres")
    def get_filters(self, request):
        """
        Renvoie des listes d'options pour construire l’UI de filtres,
        basées sur le queryset **déjà scopé** (centres/roles).
        """
        def to_choice(queryset, label_attr="nom"):
            return [{"value": obj.id, "label": getattr(obj, label_attr)} for obj in queryset]

        qs = self._scoped_for_user(Prospection.objects.all(), request.user)

        formation_ids = qs.values_list("formation_id", flat=True).distinct()
        partenaire_ids = qs.values_list("partenaire_id", flat=True).distinct()
        owner_ids = qs.values_list("owner_id", flat=True).distinct()

        formations_qs = Formation.objects.filter(id__in=formation_ids).only("id", "nom", "num_offre", "centre_id")
        partenaires = Partenaire.objects.filter(id__in=partenaire_ids)
        owners = CustomUser.objects.filter(id__in=owner_ids)

        formations = [
            {
                "value": f.id,
                "label": f"{f.nom} — {f.num_offre}" if getattr(f, "num_offre", None) else f.nom,
            }
            for f in formations_qs
        ]

        type_offres = (
            formations_qs
            .values("type_offre_id", "type_offre__nom")
            .exclude(type_offre_id__isnull=True)
            .distinct()
        )
        statuts = (
            formations_qs
            .values("statut_id", "statut__nom")
            .exclude(statut_id__isnull=True)
            .distinct()
        )
        centres = (
            formations_qs
            .values("centre_id", "centre__nom")
            .exclude(centre_id__isnull=True)
            .distinct()
        )

        return Response(
            {
                "data": {
                    "formations": formations,
                    "partenaires": to_choice(partenaires),
                    "owners": to_choice(owners, label_attr="username"),
                    "statut": ProspectionChoices.get_statut_choices() if hasattr(ProspectionChoices, "get_statut_choices") else [{"value": k, "label": str(v)} for k, v in getattr(ProspectionChoices, "PROSPECTION_STATUS_CHOICES", [])],
                    "objectif": ProspectionChoices.get_objectif_choices() if hasattr(ProspectionChoices, "get_objectif_choices") else [{"value": k, "label": str(v)} for k, v in getattr(ProspectionChoices, "PROSPECTION_OBJECTIF_CHOICES", [])],
                    "motif": ProspectionChoices.get_motif_choices() if hasattr(ProspectionChoices, "get_motif_choices") else [{"value": k, "label": str(v)} for k, v in getattr(ProspectionChoices, "PROSPECTION_MOTIF_CHOICES", [])],
                    "type_prospection": ProspectionChoices.get_type_choices() if hasattr(ProspectionChoices, "get_type_choices") else [{"value": k, "label": str(v)} for k, v in getattr(ProspectionChoices, "TYPE_PROSPECTION_CHOICES", [])],
                    "moyen_contact": ProspectionChoices.get_moyen_contact_choices() if hasattr(ProspectionChoices, "get_moyen_contact_choices") else [{"value": k, "label": str(v)} for k, v in getattr(ProspectionChoices, "MOYEN_CONTACT_CHOICES", [])],
                    "formation_type_offre": [
                        {"value": row["type_offre_id"], "label": row["type_offre__nom"]}
                        for row in type_offres
                    ],
                    "formation_statut": [
                        {"value": row["statut_id"], "label": row["statut__nom"]}
                        for row in statuts
                    ],
                    "centres": [
                        {"value": row["centre_id"], "label": row["centre__nom"]}
                        for row in centres
                    ],
                    "user_role": getattr(request.user, "role", None),
                }
            }
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ProspectionListSerializer
        elif self.action == "retrieve":
            return ProspectionDetailSerializer
        elif self.action == "creer_partenaire":
            return PartenaireCreateFromProspectionSerializer
        elif self.action == "creer_candidat":
            return CandidatCreateFromProspectionSerializer
        return ProspectionSerializer

    # ---------- CREATE / UPDATE ----------
    def perform_create(self, serializer):
        user = self.request.user

        if hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire():
            instance = serializer.save(
                created_by=user,
                owner=user,
                formation=get_candidate_formation(user),
            )
        else:
            owner = serializer.validated_data.get("owner") or user
            owner_form = get_owner_formation(owner)
            formation_payload = serializer.validated_data.get("formation")
            partenaire = serializer.validated_data.get("partenaire")

            chosen_formation = owner_form or formation_payload

            # ✅ staff non admin : contrôle périmètre formation
            self._ensure_staff_can_use_formation(user, chosen_formation)

            # ✅ centre résolu : formation.centre > partenaire.default_centre > (rien)
            centre_id = None
            if chosen_formation:
                centre_id = chosen_formation.centre_id
            elif partenaire:
                centre_id = getattr(partenaire, "default_centre_id", None)

            instance = serializer.save(
                created_by=user,
                owner=owner,
                formation=chosen_formation,
                centre_id=centre_id,
            )

        LogUtilisateur.log_action(instance, LogUtilisateur.ACTION_CREATE, user, "Création d’une prospection")

    def perform_update(self, serializer):
        user = self.request.user
        instance = serializer.instance

        if hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire():
            new_form = serializer.validated_data.get("formation")
            if new_form and new_form != instance.formation:
                raise PermissionDenied("Vous n’avez pas le droit de modifier la formation associée.")
            data_owner = instance.owner
            data_formation = instance.formation
        else:
            new_owner = serializer.validated_data.get("owner", instance.owner)
            owner_changed = (new_owner is not None and new_owner.pk != instance.owner_id)

            if owner_changed:
                owner_form = get_owner_formation(new_owner)
                if owner_form:
                    data_formation = owner_form
                elif "formation" in serializer.validated_data:
                    data_formation = serializer.validated_data["formation"]
                else:
                    data_formation = instance.formation
            else:
                data_formation = serializer.validated_data.get("formation", instance.formation)

            # ✅ staff non admin : contrôle périmètre formation
            self._ensure_staff_can_use_formation(user, data_formation)

            data_owner = new_owner

        # ✅ recalcul centre : formation.centre > partenaire.default_centre > centre existant
        partenaire = serializer.validated_data.get("partenaire", instance.partenaire)
        if data_formation:
            centre_id = data_formation.centre_id
        elif partenaire:
            centre_id = getattr(partenaire, "default_centre_id", None) or instance.centre_id
        else:
            centre_id = instance.centre_id

        instance = serializer.save(updated_by=user, owner=data_owner, formation=data_formation, centre_id=centre_id)
        LogUtilisateur.log_action(instance, LogUtilisateur.ACTION_UPDATE, user, "Mise à jour d’une prospection")

    # ---------- DRF actions ----------
    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            paginated_response.data["success"] = True
            paginated_response.data["message"] = "Liste paginée des prospections."
            return paginated_response

        serializer = self.get_serializer(qs, many=True)
        return Response(
            {"success": True, "message": "Liste des prospections.", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"success": True, "message": "Détail de la prospection", "data": serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        output_serializer = self.get_serializer(serializer.instance, context={"request": request})
        return Response(
            {"success": True, "message": "Prospection créée avec succès.", "data": output_serializer.data},
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={"request": request})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        output_serializer = self.get_serializer(serializer.instance, context={"request": request})
        return Response({"success": True, "message": "Prospection mise à jour avec succès.", "data": output_serializer.data})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        LogUtilisateur.log_action(instance, LogUtilisateur.ACTION_DELETE, request.user, "Suppression définitive de la prospection")
        instance.delete()
        return Response(
            {"success": True, "message": f"Prospection #{instance_id} supprimée définitivement."},
            status=status.HTTP_200_OK,
        )

    # ---------- Actions custom ----------
    @action(detail=True, methods=["post"], url_path="changer-statut")
    @extend_schema(
        summary="🔄 Mettre à jour le statut (et autres champs) d’une prospection",
        description=(
            "Permet de modifier le statut ET tout autre champ éditable de la prospection en une seule requête. "
            "Supporte l’alias `prochain_contact` (équivalent à `relance_prevue`). "
            "Si `relance_prevue` est renseigné et que le statut n’est pas terminal, "
            "la cohérence statut ↔ relance sera appliquée lors de l’enregistrement."
        ),
        tags=["Prospections"],
        request=ProspectionSerializer,
        responses={200: OpenApiResponse(response=ProspectionSerializer)},
    )
    def changer_statut(self, request, pk=None):
        instance = self.get_object()

        ancien_statut = instance.statut

        allowed_keys = {
            "partenaire",
            "formation",
            "owner",
            "date_prospection",
            "type_prospection",
            "motif",
            "statut",
            "objectif",
            "commentaire",
            "relance_prevue",
            "moyen_contact",
        }

        incoming = {k: v for k, v in request.data.items() if k in allowed_keys or k == "prochain_contact"}

        if "relance_prevue" not in incoming and "prochain_contact" in incoming:
            incoming["relance_prevue"] = incoming.pop("prochain_contact")

        moyen_contact_provided = "moyen_contact" in incoming
        moyen_contact_value = incoming.pop("moyen_contact", None) if moyen_contact_provided else None
        commentaire_payload = incoming.get("commentaire") or request.data.get("commentaire") or ""

        serializer = self.get_serializer(instance, data=incoming, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # ⚠️ si la formation change, re-vérifier le périmètre staff
        new_form = serializer.validated_data.get("formation", instance.formation)
        self._ensure_staff_can_use_formation(request.user, new_form)

        self.perform_update(serializer)

        if moyen_contact_provided and hasattr(instance, "moyen_contact"):
            instance.refresh_from_db()
            if instance.moyen_contact != moyen_contact_value:
                instance.moyen_contact = moyen_contact_value
                if hasattr(instance, "updated_by"):
                    instance.updated_by = request.user
                    instance.save(update_fields=["moyen_contact", "updated_by"])
                else:
                    instance.save(update_fields=["moyen_contact"])

        instance.refresh_from_db()
        nouveau_statut = instance.statut
        relance_prevue_finale = getattr(instance, "relance_prevue", None)

        if commentaire_payload:
            ProspectionComment.objects.create(
                prospection=instance,
                body=commentaire_payload,
                is_internal=False,
                created_by=request.user,
            )

        if hasattr(instance, "creer_historique"):
            instance.creer_historique(
                ancien_statut=ancien_statut,
                nouveau_statut=nouveau_statut,
                type_prospection=instance.type_prospection,
                commentaire=commentaire_payload,
                resultat="Mise à jour via changer-statut",
                moyen_contact=moyen_contact_value if moyen_contact_provided else None,
                user=request.user,
                prochain_contact=relance_prevue_finale,
            )

        LogUtilisateur.log_action(
            instance,
            LogUtilisateur.ACTION_UPDATE,
            request.user,
            f"Mise à jour via changer-statut : {ancien_statut} → {nouveau_statut}"
        )

        return Response(
            {
                "success": True,
                "message": "Prospection mise à jour avec succès.",
                "data": ProspectionSerializer(instance, context={"request": request}).data,
            }
        )

    @action(detail=True, methods=["get"], url_path="historiques")
    @extend_schema(
        summary="📜 Voir l’historique d’une prospection",
        tags=["Prospections"],
        responses={200: OpenApiResponse(response=HistoriqueProspectionSerializer(many=True))},
    )
    def historiques(self, request, pk=None):
        instance = self.get_object()
        qs = instance.historiques.order_by("-date_modification")
        serializer = HistoriqueProspectionSerializer(qs, many=True, context={"request": request})
        return Response({"success": True, "message": "Historique chargé avec succès.", "data": serializer.data})

    @action(detail=False, methods=["get"], url_path="choices")
    @extend_schema(
        summary="📚 Choix disponibles (statut, objectif, motif, type_prospection, moyen_contact, responsables, partenaires)",
        tags=["Prospections"],
        responses={200: OpenApiResponse(response=ProspectionChoiceListSerializer)},
    )
    def get_choices(self, request):
        def fmt(choices):
            return [{"value": k, "label": str(l)} for k, l in choices]

        User = get_user_model()
        user_role = getattr(request.user, "role", None)

        # ✅ restreint aux owners visibles dans le périmètre de l'utilisateur
        scoped_qs = self._scoped_for_user(Prospection.objects.all(), request.user)
        owner_ids = scoped_qs.values_list("owner_id", flat=True).distinct()
        users = User.objects.filter(id__in=owner_ids)
        sorted_users = sorted(users, key=lambda u: (u.get_full_name() or u.username).lower())
        owners = [{"value": u.id, "label": u.get_full_name() or u.username} for u in sorted_users]

        partenaire_ids = scoped_qs.values_list("partenaire_id", flat=True).distinct()
        partenaires = [
            {"value": p.id, "label": p.nom}
            for p in Partenaire.objects.filter(id__in=partenaire_ids,).order_by("nom")
        ]

        return Response(
            {
                "success": True,
                "message": "Choix disponibles pour les prospections",
                "data": {
                    "statut": fmt(getattr(ProspectionChoices, "PROSPECTION_STATUS_CHOICES", [])),
                    "objectif": fmt(getattr(ProspectionChoices, "PROSPECTION_OBJECTIF_CHOICES", [])),
                    "motif": fmt(getattr(ProspectionChoices, "PROSPECTION_MOTIF_CHOICES", [])),
                    "type_prospection": fmt(getattr(ProspectionChoices, "TYPE_PROSPECTION_CHOICES", [])),
                    "moyen_contact": fmt(getattr(ProspectionChoices, "MOYEN_CONTACT_CHOICES", [])),
                    "owners": owners,
                    "partenaires": partenaires,
                    "user_role": user_role,
                },
            }
        )

    # ---------- Actions exports ----------
    @action(detail=False, methods=["get", "post"], url_path="export-xlsx")
    def export_xlsx(self, request):
        user = request.user
        qs = self.filter_queryset(
            self.get_queryset().select_related(
                "formation",
                "formation__centre",
                "formation__type_offre",
                "formation__statut",
                "partenaire",
                "owner",
                "created_by",
            )
        )

        ids = request.data.get("ids") if request.method == "POST" else None
        if ids:
            ids = _parse_id_list(ids)
            qs = qs.filter(id__in=ids)

        wb = Workbook()
        ws = wb.active
        ws.title = "Prospections"

        # Prospection toujours
        prospection_fields = [
            "id", "date_prospection", "statut", "objectif",
            "motif", "type_prospection", "commentaire", "relance_prevue",
        ]

        # Rôle candidat/stagiaire → Formation limitée
        if hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire():
            formation_fields = ["nom", "centre_nom"]
        else:
            formation_fields = [
                "id", "nom", "centre_nom", "type_offre_nom", "statut_nom",
                "start_date", "end_date", "num_offre", "places_disponibles",
                "taux_saturation", "total_places", "total_inscrits",
            ]

        # Partenaire : toujours toutes les infos demandées
        partenaire_fields = [
            "nom", "zip_code", "contact_nom", "contact_email", "contact_telephone",
        ]

        # Ajout staff-only : owner / created_by
        extra_fields = []
        if not (hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire()):
            extra_fields = ["owner_username", "created_by_username"]

        headers = prospection_fields + [f"formation__{f}" for f in formation_fields] + [f"partenaire__{f}" for f in partenaire_fields] + extra_fields
        ws.append(headers)

        def _fmt(val):
            if val is None:
                return ""
            if isinstance(val, datetime.datetime):
                return val.strftime("%d/%m/%Y %H:%M")
            if isinstance(val, datetime.date):
                return val.strftime("%d/%m/%Y")
            if isinstance(val, float):
                return round(val, 2)
            return str(val)

        for p in qs:
            row = []
            # Prospection
            for field in prospection_fields:
                row.append(_fmt(getattr(p, field, "")))

            # Formation
            f = p.formation
            if f:
                if hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire():
                    row += [
                        f.nom,
                        getattr(f.centre, "nom", ""),
                    ]
                else:
                    row += [
                        f.id,
                        f.nom,
                        getattr(f.centre, "nom", ""),
                        getattr(f.type_offre, "nom", ""),
                        getattr(f.statut, "nom", ""),
                        _fmt(f.start_date),
                        _fmt(f.end_date),
                        f.num_offre or "",
                        f.places_disponibles,
                        f.taux_saturation,
                        f.total_places,
                        f.total_inscrits,
                    ]
            else:
                row += [""] * len(formation_fields)

            # Partenaire
            part = p.partenaire
            row += [
                getattr(part, "nom", ""),
                getattr(part, "zip_code", ""),
                getattr(part, "contact_nom", ""),
                getattr(part, "contact_email", ""),
                getattr(part, "contact_telephone", ""),
            ]

            # Staff-only extras
            if not (hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire()):
                row += [
                    getattr(p.owner, "username", ""),
                    getattr(p.created_by, "username", ""),
                ]

            ws.append(row)

        # Ajustement colonnes
        for col in ws.columns:
            max_length = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = min(max_length + 2, 50)

        buffer = BytesIO()
        wb.save(buffer)
        binary_content = buffer.getvalue()

        filename = f'prospections_{dj_timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response = HttpResponse(
            binary_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Content-Length"] = len(binary_content)
        return response

class HistoriqueProspectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HistoriqueProspection.objects.select_related(
        "prospection",
        "prospection__partenaire",
        "prospection__formation",
        "prospection__formation__centre",
    )
    serializer_class = HistoriqueProspectionSerializer
    permission_classes = [IsOwnerOrStaffOrAbove]  # ✅ protection lecture objet
    pagination_class = RapAppPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["prospection", "nouveau_statut", "type_prospection"]
    search_fields = ["commentaire", "resultat"]
    ordering_fields = ["date_modification", "prochain_contact"]
    ordering = ["-date_modification"]

    def _is_admin_like(self, user) -> bool:
        # ✅ micro-fix ici aussi
        return bool(getattr(user, "is_superuser", False) or getattr(user, "is_admin", False))

    def get_queryset(self):
        qs = self.queryset
        user = self.request.user
        if not user.is_authenticated:
            return HistoriqueProspection.objects.none()

        # candidats → historiques de leurs prospections
        if hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire():
            return qs.filter(prospection__owner=user)

        # admin/superadmin → tout
        if self._is_admin_like(user):
            return qs

        # staff → restreint à ses centres + fallback owner/creator
        if getattr(user, "is_staff", False):
            centre_ids = list(user.centres.values_list("id", flat=True))
            if not centre_ids:
                return qs.filter(Q(prospection__owner=user) | Q(prospection__created_by=user))
            return qs.filter(
                Q(prospection__formation__centre_id__in=centre_ids) |
                Q(prospection__owner=user) |
                Q(prospection__created_by=user)
            ).distinct()

        # autres rôles → owner/creator uniquement
        return qs.filter(Q(prospection__owner=user) | Q(prospection__created_by=user))

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True)
        return Response(
            {
                "success": True,
                "message": "Liste paginée des historiques de prospection.",
                "data": {
                    "count": self.paginator.page.paginator.count,
                    "next": self.paginator.get_next_link(),
                    "previous": self.paginator.get_previous_link(),
                    "results": serializer.data,
                },
            }
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"success": True, "message": "Historique récupéré avec succès.", "data": serializer.data})
