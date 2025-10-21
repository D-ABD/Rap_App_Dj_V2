from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field
from drf_spectacular.types import OpenApiTypes

from ...models.appairage import Appairage, AppairageActivite, AppairageStatut
from ...models.formations import Formation
from ...models.candidat import Candidat
from ...models.partenaires import Partenaire
from ...models.custom_user import CustomUser
from ...models.centres import Centre
from ...models.commentaires_appairage import CommentaireAppairage


# ----------------- Commentaires -----------------
class CommentaireAppairageSerializer(serializers.ModelSerializer):
    auteur_nom = serializers.SerializerMethodField()
    
    @extend_schema_field(str)
    def get_auteur_nom(self, obj):
        u = getattr(obj, "created_by", None)
        if not u:
            return "Anonyme"
        return u.get_full_name() or getattr(u, "username", None) or getattr(u, "email", None)

    class Meta:
        model = CommentaireAppairage
        fields = ["id", "body", "auteur_nom", "created_at", "updated_at"]
        read_only_fields = fields


# ----------------- Base -----------------
class AppairageBaseSerializer(serializers.ModelSerializer):
    activite = serializers.ChoiceField(
        choices=AppairageActivite.choices,
        default=AppairageActivite.ACTIF,
    )
    activite_display = serializers.CharField(source="get_activite_display", read_only=True)

    candidat_nom = serializers.SerializerMethodField()
    partenaire_nom = serializers.CharField(source="partenaire.nom", read_only=True)
    partenaire_email = serializers.CharField(source="partenaire.contact_email", read_only=True)
    partenaire_telephone = serializers.CharField(source="partenaire.contact_telephone", read_only=True)

    candidat_cv_statut = serializers.CharField(source="candidat.cv_statut", read_only=True)
    candidat_cv_statut_display = serializers.CharField(source="candidat.get_cv_statut_display", read_only=True)

    # Formation
    formation_nom = serializers.SerializerMethodField()
    formation_detail = serializers.SerializerMethodField()
    formation_bref = serializers.SerializerMethodField()
    formation_type_offre = serializers.SerializerMethodField()
    formation_places_total = serializers.SerializerMethodField()
    formation_places_disponibles = serializers.SerializerMethodField()
    formation_statut = serializers.CharField(source="formation.statut", read_only=True)
    formation_date_debut = serializers.DateField(source="formation.start_date", read_only=True)
    formation_date_fin = serializers.DateField(source="formation.end_date", read_only=True)
    formation_numero_offre = serializers.CharField(source="formation.num_offre", read_only=True)
    formation_centre = serializers.CharField(source="formation.centre.nom", read_only=True)

    statut_display = serializers.CharField(source="get_statut_display", read_only=True)
    peut_modifier = serializers.SerializerMethodField()
    est_dernier_appairage = serializers.SerializerMethodField()
    
    @extend_schema_field(str)
    def get_est_dernier_appairage(self, obj):
        cand = getattr(obj, "candidat", None)
        if not cand:
            return False
        pid = getattr(cand, "placement_appairage_id", None)
        if pid is not None:
            return pid == obj.id
        last_id = (
            Appairage.objects.filter(candidat=cand)
            .order_by("-date_appairage", "-pk")
            .values_list("id", flat=True)
            .first()
        )
        return last_id == obj.id
   
    @extend_schema_field(str)
    def get_candidat_nom(self, obj):
        c = getattr(obj, "candidat", None)
        if not c:
            return None
        attr = getattr(c, "nom_complet", None)
        if callable(attr):
            try:
                v = (attr() or "").strip()
                if v:
                    return v
            except Exception:
                pass
        v = attr if isinstance(attr, str) else None
        return v or str(c)
    
    @extend_schema_field(str)
    def get_peut_modifier(self, instance):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return getattr(user, "role", None) in ["admin", "superadmin", "staff"]

    # ---------- helpers formation ----------
    @extend_schema_field(str)
    def _get_formation(self, obj):
        return obj.formation or getattr(obj.candidat, "formation", None)

    @extend_schema_field(str)
    def get_formation_nom(self, obj):
        f = self._get_formation(obj)
        return getattr(f, "nom", None) if f else None

    @extend_schema_field(str)
    def get_formation_detail(self, obj):
        f = self._get_formation(obj)
        return f.get_formation_identite_complete() if f else None
    
    @extend_schema_field(str)
    def get_formation_bref(self, obj):
        f = self._get_formation(obj)
        return f.get_formation_identite_bref() if f else None

    @extend_schema_field(OpenApiTypes.STR)
    def get_formation_type_offre(self, obj):
        f = self._get_formation(obj)
        if not f or not getattr(f, "type_offre", None):
            return None
        to = f.type_offre
        try:
            label = str(to).strip()
            if label:
                return label
        except Exception:
            pass
        return getattr(to, "nom", None)

    @extend_schema_field(str)
    def get_formation_places_total(self, obj):
        f = self._get_formation(obj)
        if not f:
            return None
        inscrits_total = (getattr(f, "inscrits_crif", 0) or 0) + (getattr(f, "inscrits_mp", 0) or 0)
        prevus_total = (getattr(f, "prevus_crif", 0) or 0) + (getattr(f, "prevus_mp", 0) or 0)
        cap = getattr(f, "cap", None)
        if cap is not None:
            return int(cap)
        if prevus_total:
            return int(prevus_total)
        if inscrits_total:
            return int(inscrits_total)
        return None

    @extend_schema_field(str)
    def get_formation_places_disponibles(self, obj):
        f = self._get_formation(obj)
        if not f:
            return None
        inscrits_total = (getattr(f, "inscrits_crif", 0) or 0) + (getattr(f, "inscrits_mp", 0) or 0)
        prevus_total = (getattr(f, "prevus_crif", 0) or 0) + (getattr(f, "prevus_mp", 0) or 0)
        cap = getattr(f, "cap", None)
        if cap is not None:
            return max(int(cap) - int(inscrits_total), 0)
        if prevus_total:
            return max(int(prevus_total) - int(inscrits_total), 0)
        return None


# ----------------- Détail -----------------
@extend_schema_serializer()
class AppairageSerializer(AppairageBaseSerializer):
    created_by_nom = serializers.SerializerMethodField()
    updated_by_nom = serializers.SerializerMethodField()
    last_commentaire = serializers.SerializerMethodField()
    commentaires = CommentaireAppairageSerializer(many=True, read_only=True)

    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)
    partenaire_contact_nom = serializers.CharField(source="partenaire.contact_nom", read_only=True)

    @extend_schema_field(str)
    def validate_activite(self, value):
        if value not in dict(AppairageActivite.choices):
            raise serializers.ValidationError("Valeur d'activité invalide.")
        return value

    @extend_schema_field(str)
    def _user_label(self, u):
        if not u:
            return None
        full = getattr(u, "get_full_name", None)
        if callable(full):
            val = (full() or "").strip()
            if val:
                return val
        for cand in ("username", "email"):
            v = getattr(u, cand, None)
            if v:
                return v
        return str(u)

    @extend_schema_field(str)
    def get_created_by_nom(self, obj):
        return self._user_label(getattr(obj, "created_by", None))

    @extend_schema_field(str)
    def get_updated_by_nom(self, obj):
        return self._user_label(getattr(obj, "updated_by", None))

    @extend_schema_field(str)
    def get_last_commentaire(self, obj):
        last = obj.commentaires.order_by("-created_at").first()
        return last.body if last else None

    class Meta:
        model = Appairage
        fields = [
            "id",
            "est_dernier_appairage",
            "candidat",
            "candidat_nom",
            "candidat_cv_statut",
            "candidat_cv_statut_display",
            "partenaire",
            "partenaire_nom",
            "partenaire_contact_nom",
            "partenaire_email",
            "partenaire_telephone",
            "formation",
            "formation_nom",
            "formation_bref",
            "formation_detail",
            "formation_type_offre",
            "formation_places_total",
            "formation_places_disponibles",
            "formation_statut",
            "formation_date_debut",
            "formation_date_fin",
            "formation_numero_offre",
            "formation_centre",
            "date_appairage",
            "statut",
            "statut_display",
            "activite",
            "activite_display",
            "retour_partenaire",
            "date_retour",
            "created_by",
            "created_by_nom",
            "created_at",
            "updated_by",
            "updated_by_nom",
            "updated_at",
            "peut_modifier",
            "historiques",
            "last_commentaire",
            "commentaires",
        ]
        read_only_fields = fields


# ----------------- Liste -----------------
@extend_schema_serializer()
class AppairageListSerializer(AppairageBaseSerializer):
    created_by_nom = serializers.SerializerMethodField()
    updated_by_nom = serializers.SerializerMethodField()
    last_commentaire = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)
    partenaire_contact_nom = serializers.CharField(source="partenaire.contact_nom", read_only=True)

    class Meta:
        model = Appairage
        fields = [
            "id",
            "candidat_nom",
            "candidat_cv_statut",
            "candidat_cv_statut_display",
            "partenaire_nom",
            "partenaire_contact_nom",
            "partenaire_email",
            "partenaire_telephone",
            "formation",
            "formation_nom",
            "formation_bref",
            "formation_detail",
            "formation_type_offre",
            "formation_date_debut",
            "formation_date_fin",
            "formation_numero_offre",
            "formation_places_total",
            "formation_places_disponibles",
            "statut",
            "statut_display",
            "activite",
            "activite_display",
            "date_appairage",
            "created_by_nom",
            "updated_by",
            "updated_by_nom",
            "updated_at",
            "created_at",
            "last_commentaire",
        ]
        read_only_fields = fields

    @extend_schema_field(str)
    def _user_label(self, u):
        if not u:
            return None
        full = getattr(u, "get_full_name", None)
        if callable(full):
            val = (full() or "").strip()
            if val:
                return val
        for cand in ("username", "email"):
            v = getattr(u, cand, None)
            if v:
                return v
        return str(u)

    @extend_schema_field(str)
    def get_created_by_nom(self, obj):
        return self._user_label(getattr(obj, "created_by", None))

    @extend_schema_field(str)
    def get_updated_by_nom(self, obj):
        return self._user_label(getattr(obj, "updated_by", None))

    @extend_schema_field(str)
    def get_last_commentaire(self, obj):
        last = obj.commentaires.order_by("-created_at").first()
        return last.body if last else None


# ----------------- Create/Update -----------------
class AppairageCreateUpdateSerializer(serializers.ModelSerializer):
    formation = serializers.PrimaryKeyRelatedField(
        queryset=Formation.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Appairage
        exclude = ["created_by", "updated_by", "updated_at"]

    @extend_schema_field(str)
    def validate_statut(self, value):
        user = self.context.get("request").user
        allowed_roles = {"admin", "superadmin", "staff"}
        if not user or getattr(user, "role", None) not in allowed_roles:
            if self.instance is None and value != AppairageStatut.TRANSMIS:
                raise serializers.ValidationError("Seul le statut 'Transmis' est autorisé à la création.")
            if self.instance is not None:
                raise serializers.ValidationError("Vous n’êtes pas autorisé à modifier le statut.")
        elif value not in dict(AppairageStatut.choices):
            raise serializers.ValidationError(f"Statut '{value}' non reconnu.")
        return value

    @extend_schema_field(str)
    def validate_formation(self, value):
        request = self.context.get("request")
        user = request.user if request else None
        if user and hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire():
            if self.instance is None:
                return getattr(getattr(user, "candidat_associe", None), "formation_id", None)
            return getattr(self.instance, "formation_id", None)
        return value


# ----------------- Meta -----------------
@extend_schema_serializer()
class AppairageMetaSerializer(serializers.Serializer):
    statut_choices = serializers.SerializerMethodField()
    formation_choices = serializers.SerializerMethodField()
    candidat_choices = serializers.SerializerMethodField()
    partenaire_choices = serializers.SerializerMethodField()
    user_choices = serializers.SerializerMethodField()
    centre_choices = serializers.SerializerMethodField()
    candidat_cv_statut_choices = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_statut_choices(self, _):
        return [{"value": k, "label": v} for k, v in AppairageStatut.choices]

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_candidat_cv_statut_choices(self, _):
        return [{"value": k, "label": v} for k, v in Candidat.CVStatut.choices]

    @extend_schema_field(str)
    def _resolve_label(self, obj, label_field="__str__"):
        if callable(label_field):
            try:
                val = label_field(obj)
            except Exception:
                val = None
        else:
            if label_field == "__str__":
                val = str(obj)
            else:
                attr = getattr(obj, label_field, None)
                val = attr() if callable(attr) else attr
        if isinstance(val, str):
            val = val.strip()
        if not val:
            for cand in ("get_full_name", "full_name", "username", "email"):
                a = getattr(obj, cand, None)
                v = a() if callable(a) else a
                if v:
                    val = v
                    break
        return str(val) if val is not None else str(obj)

    @extend_schema_field(str)
    def _serialize_queryset(self, queryset, value_field="id", label_field="__str__"):
        return [
            {"value": getattr(obj, value_field), "label": self._resolve_label(obj, label_field)}
            for obj in queryset
        ]

    @extend_schema_field(str)
    def get_formation_choices(self, _):
        qs = Formation.objects.all().order_by("nom")
        return self._serialize_queryset(qs, "id", "nom")

    @extend_schema_field(OpenApiTypes.STR)
    def get_candidat_choices(self, _):
        ids = Appairage.objects.values_list("candidat", flat=True).distinct()
        qs = Candidat.objects.filter(id__in=ids)
        return self._serialize_queryset(qs, "id", "nom_complet")

    @extend_schema_field(OpenApiTypes.STR)
    def get_partenaire_choices(self, _):
        ids = Appairage.objects.values_list("partenaire", flat=True).distinct()
        qs = Partenaire.objects.filter(id__in=ids)
        return self._serialize_queryset(qs, "id", "nom")

    @extend_schema_field(OpenApiTypes.STR)
    def get_user_choices(self, _):
        ids = (
            Appairage.objects.exclude(created_by__isnull=True)
            .values_list("created_by", flat=True)
            .distinct()
        )
        qs = CustomUser.objects.filter(id__in=ids).order_by("last_name", "first_name")
        return self._serialize_queryset(qs, "id", "get_full_name")

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_centre_choices(self, _):
        centre_ids = (
            Appairage.objects.exclude(formation__centre__isnull=True)
            .values_list("formation__centre_id", flat=True)
            .distinct()
        )
        qs = Centre.objects.filter(id__in=centre_ids).order_by("nom")
        return [{"value": c.id, "label": c.nom} for c in qs]
