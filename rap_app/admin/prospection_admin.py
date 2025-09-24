# rap_app/admin/prospection_admin.py
from datetime import timedelta

from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html

from ..models.prospection import Prospection, HistoriqueProspection
from ..models.prospection_choices import ProspectionChoices


# ───────────────────────── Inlines ─────────────────────────

class HistoriqueProspectionInline(admin.TabularInline):
    model = HistoriqueProspection
    extra = 0
    can_delete = False
    ordering = ("-date_modification", "-id")
    show_change_link = False

    readonly_fields = (
        "date_modification",
        "champ_modifie",
        "ancienne_valeur",
        "nouvelle_valeur",
        "ancien_statut",
        "nouveau_statut",
        "type_prospection",
        "commentaire",
        "resultat",
        "prochain_contact",
        "moyen_contact",
        "created_by",
        "created_at",
        "updated_at",
    )
    fields = readonly_fields
    verbose_name = "Historique"
    verbose_name_plural = "Historiques (lecture seule)"


# ─────────────────────── Filtres custom ─────────────────────

class RelanceEtatFilter(admin.SimpleListFilter):
    """Filtre pratique pour l’état de relance."""
    title = "Relance"
    parameter_name = "relance_etat"

    def lookups(self, request, model_admin):
        return (
            ("a_relancer", "À relancer (échu)"),
            ("planifiee", "Relance planifiée"),
            ("sans", "Sans relance"),
        )

    def queryset(self, request, queryset):
        today = timezone.now().date()
        v = self.value()
        if v == "a_relancer":
            return queryset.filter(relance_prevue__isnull=False, relance_prevue__lte=today) \
                           .exclude(statut__in=[ProspectionChoices.STATUT_REFUSEE, ProspectionChoices.STATUT_ANNULEE])
        if v == "planifiee":
            return queryset.filter(relance_prevue__gt=today)
        if v == "sans":
            return queryset.filter(relance_prevue__isnull=True)
        return queryset


# ─────────────────────── Admin principal ────────────────────

@admin.register(Prospection)
class ProspectionAdmin(admin.ModelAdmin):
    date_hierarchy = "date_prospection"

    list_display = (
        "id",
        "partenaire",
        "formation",
        "centre",            # ✅ nouveau : afficher le centre
        "owner",
        "statut_badge",
        "type_prospection",
        "objectif",
        "motif",
        "moyen_contact",
        "date_prospection",
        "relance_prevue",
        "relance_etat",
        "created_by",
        "created_at",
    )

    list_filter = (
        "statut",
        RelanceEtatFilter,
        "type_prospection",
        "objectif",
        "motif",
        "moyen_contact",
        "owner",
        "partenaire",
        "formation",
        "centre",            # ✅ nouveau : filtre par centre
        ("date_prospection", admin.DateFieldListFilter),
        ("relance_prevue", admin.DateFieldListFilter),
    )

    search_fields = (
        "id",
        "commentaire",
        "partenaire__nom",
        "formation__nom",
        "centre__nom",       # ✅ nouveau : recherche par nom de centre
        "created_by__username",
        "owner__username",
    )

    ordering = ("-date_prospection", "-id")

    raw_id_fields = ("partenaire", "formation", "centre", "owner", "created_by", "updated_by")  # ✅ centre ajouté
    readonly_fields = ("created_by", "created_at", "updated_at")

    fieldsets = (
        ("Ciblage", {
            "fields": ("partenaire", "formation", "centre", "owner"),  # ✅ centre visible/éditable
        }),
        ("Détails prospection", {
            "fields": (
                "date_prospection",
                "type_prospection",
                "motif",
                "objectif",
                "statut",
                "moyen_contact",
                "commentaire",
            )
        }),
        ("Relance", {
            "fields": ("relance_prevue",),
        }),
        ("Métadonnées", {
            "fields": ("created_by", "created_at", "updated_at"),
        }),
    )

    inlines = [HistoriqueProspectionInline]

    # Perf
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "partenaire", "formation", "centre", "owner", "created_by", "updated_by"  # ✅ centre préchargé
        )

    # Badge coloré de statut
    def statut_badge(self, obj: Prospection):
        colors = {
            ProspectionChoices.STATUT_A_FAIRE: "#6b7280",      # gris
            ProspectionChoices.STATUT_EN_COURS: "#2563eb",     # bleu
            ProspectionChoices.STATUT_A_RELANCER: "#d97706",   # orange
            ProspectionChoices.STATUT_ACCEPTEE: "#16a34a",     # vert
            ProspectionChoices.STATUT_REFUSEE: "#b91c1c",      # rouge
            ProspectionChoices.STATUT_ANNULEE: "#374151",      # gris foncé
            ProspectionChoices.STATUT_NON_RENSEIGNE: "#9ca3af",
        }
        color = colors.get(obj.statut, "#9ca3af")
        label = obj.get_statut_display()
        return format_html(
            '<span style="display:inline-block;padding:.15rem .5rem;border-radius:9999px;'
            'background:{bg};color:#fff;font-size:12px">{label}</span>',
            bg=color, label=label
        )
    statut_badge.short_description = "Statut"

    # État de relance (affichage)
    def relance_etat(self, obj: Prospection):
        today = timezone.now().date()
        if not obj.relance_prevue:
            return "—"
        delta = (obj.relance_prevue - today).days
        if delta < 0:
            return f"⚠️ Échue (J{delta})"
        if delta == 0:
            return "⏰ Aujourd’hui"
        return f"📆 J+{delta}"
    relance_etat.short_description = "Relance"

    # Propager l’utilisateur à la sauvegarde
    def save_model(self, request, obj: Prospection, form, change):
        # Transmet à la fois user (BaseModel) et updated_by (logique Prospection.save)
        # NB: Prospection.save() resynchronise centre à partir de formation/default_centre si nécessaire.
        obj.save(user=request.user, updated_by=request.user)

    def save_formset(self, request, form, formset, change):
        # Inline RO, mais on garde le pattern
        instances = formset.save(commit=False)
        for inst in instances:
            try:
                inst.save(user=request.user)
            except TypeError:
                inst.save()
        formset.save_m2m()

    # ───────────── Actions de masse (créent l’historique) ─────────────

    def _bulk_apply(self, request, queryset, **changes):
        n = 0
        for obj in queryset:
            for k, v in changes.items():
                setattr(obj, k, v)
            obj.save(user=request.user, updated_by=request.user)  # garde l’historique
            n += 1
        self.message_user(request, f"{n} prospection(s) mises à jour.", level=messages.SUCCESS)

    @admin.action(description="Statut → À faire")
    def act_statut_a_faire(self, request, queryset):
        self._bulk_apply(request, queryset, statut=ProspectionChoices.STATUT_A_FAIRE)

    @admin.action(description="Statut → En cours")
    def act_statut_en_cours(self, request, queryset):
        self._bulk_apply(request, queryset, statut=ProspectionChoices.STATUT_EN_COURS)

    @admin.action(description="Statut → À relancer (J+7)")
    def act_statut_a_relancer_7(self, request, queryset):
        d = timezone.now().date() + timedelta(days=7)
        # la logique save() basculera statut → A_RELANCER si relance_prevue est posée
        self._bulk_apply(request, queryset, relance_prevue=d)

    @admin.action(description="Statut → Acceptée")
    def act_statut_acceptee(self, request, queryset):
        self._bulk_apply(request, queryset, statut=ProspectionChoices.STATUT_ACCEPTEE)

    @admin.action(description="Statut → Refusée")
    def act_statut_refusee(self, request, queryset):
        self._bulk_apply(request, queryset, statut=ProspectionChoices.STATUT_REFUSEE)

    @admin.action(description="Statut → Annulée")
    def act_statut_annulee(self, request, queryset):
        self._bulk_apply(request, queryset, statut=ProspectionChoices.STATUT_ANNULEE)

    @admin.action(description="Planifier relance J+3")
    def act_relance_j3(self, request, queryset):
        d = timezone.now().date() + timedelta(days=3)
        self._bulk_apply(request, queryset, relance_prevue=d)

    @admin.action(description="Planifier relance J+14")
    def act_relance_j14(self, request, queryset):
        d = timezone.now().date() + timedelta(days=14)
        self._bulk_apply(request, queryset, relance_prevue=d)

    @admin.action(description="Annuler la relance (retour à En cours)")
    def act_annuler_relance(self, request, queryset):
        # save() remettra le statut à EN_COURS si relance_prevue est null
        self._bulk_apply(request, queryset, relance_prevue=None)

    actions = (
        "act_statut_a_faire",
        "act_statut_en_cours",
        "act_statut_a_relancer_7",
        "act_statut_acceptee",
        "act_statut_refusee",
        "act_statut_annulee",
        "act_relance_j3",
        "act_relance_j14",
        "act_annuler_relance",
    )


# ───────────────────── Historique (admin direct) ─────────────────────

@admin.register(HistoriqueProspection)
class HistoriqueProspectionAdmin(admin.ModelAdmin):
    date_hierarchy = "date_modification"
    list_display = (
        "id",
        "prospection",
        "date_modification",
        "champ_modifie",
        "ancien_statut",
        "nouveau_statut",
        "type_prospection",
        "prochain_contact",
        "moyen_contact",
        "created_by",
        "created_at",
    )
    list_filter = (
        "nouveau_statut",
        "type_prospection",
        ("date_modification", admin.DateFieldListFilter),
        ("prochain_contact", admin.DateFieldListFilter),
    )
    search_fields = ("id", "prospection__partenaire__nom", "prospection__formation__nom", "champ_modifie", "commentaire")
    ordering = ("-date_modification", "-id")
    raw_id_fields = ("prospection", "created_by", "updated_by")
    readonly_fields = ("created_by", "created_at", "updated_at")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("prospection", "prospection__partenaire", "prospection__formation", "created_by", "updated_by")

    def save_model(self, request, obj, form, change):
        # Historique est normalement RO, mais si besoin…
        obj.save(user=request.user)
