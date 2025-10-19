import logging
from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q

from ..models.atelier_tre import AtelierTRE, AtelierTREPresence, PresenceStatut

logger = logging.getLogger("application.ateliers_tre")


# ───────────────────────────────────────────────
# Inline : Présences à l’atelier
# ───────────────────────────────────────────────
class AtelierTREPresenceInline(admin.TabularInline):
    model = AtelierTREPresence
    extra = 0
    verbose_name = _("Présence")
    verbose_name_plural = _("Présences")
    fields = ("candidat", "statut", "commentaire", "created_by", "updated_by", "updated_at")
    readonly_fields = ("created_by", "updated_by", "updated_at")
    ordering = ("candidat__nom",)

    raw_id_fields = ("candidat",)

    def has_add_permission(self, request, obj=None):
        """Empêche l’ajout direct dans le inline si atelier non sauvegardé."""
        return bool(obj)

    def save_model(self, request, obj, form, change):
        """Trace l’utilisateur."""
        obj.save(user=request.user)


# ───────────────────────────────────────────────
# Admin principal : AtelierTRE
# ───────────────────────────────────────────────
@admin.register(AtelierTRE)
class AtelierTREAdmin(admin.ModelAdmin):
    """Interface d’administration des ateliers TRE."""

    date_hierarchy = "date_atelier"
    ordering = ("-date_atelier", "-id")
    list_per_page = 50

    list_display = (
        "id",
        "get_label",
        "centre",
        "date_atelier",
        "nb_inscrits_display",
        "nb_presents",
        "created_by",
        "created_at",
    )

    list_filter = (
        "type_atelier",
        "centre",
        ("date_atelier", admin.DateFieldListFilter),
    )

    search_fields = (
        "id",
        "centre__nom",
        "candidats__nom",
        "candidats__prenom",
    )

    readonly_fields = ("created_by", "created_at", "updated_by", "updated_at", "nb_inscrits")
    raw_id_fields = ("centre", "candidats")
    autocomplete_fields = ("centre", "candidats")

    fieldsets = (
        (
            _("Informations principales"),
            {"fields": ("type_atelier", "date_atelier", "centre")},
        ),
        (
            _("Candidats liés"),
            {"fields": ("candidats", "nb_inscrits")},
        ),
        (
            _("Métadonnées"),
            {"fields": ("created_by", "created_at", "updated_by", "updated_at")},
        ),
    )

    inlines = [AtelierTREPresenceInline]

    # ───────────────────────────────
    # Helpers d’affichage
    # ───────────────────────────────
    def get_label(self, obj):
        label = obj.get_type_atelier_display()
        return label if not obj.date_atelier else f"{label} – {obj.date_atelier:%d/%m/%Y %H:%M}"
    get_label.short_description = _("Atelier")

    def nb_inscrits_display(self, obj):
        return obj.nb_inscrits
    nb_inscrits_display.short_description = _("Nb inscrits")

    def nb_presents(self, obj):
        return obj.presences.filter(statut=PresenceStatut.PRESENT).count()
    nb_presents.short_description = _("Nb présents")

    # ───────────────────────────────
    # Optimisation du queryset
    # ───────────────────────────────
    def get_queryset(self, request):
        qs = (
            super()
            .get_queryset(request)
            .select_related("centre", "created_by")
            .prefetch_related("candidats")
            .annotate(
                nb_inscrits_annot=Count("candidats", distinct=True),
                nb_presents_annot=Count(
                    "presences",
                    filter=Q(presences__statut=PresenceStatut.PRESENT),
                    distinct=True,
                ),
            )
        )
        return qs

    # ───────────────────────────────
    # Sauvegardes avec traçabilité
    # ───────────────────────────────
    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)
        logger.info("🧩 AtelierTRE #%s sauvegardé par %s", obj.pk, request.user)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for inst in instances:
            try:
                inst.save(user=request.user)
            except TypeError:
                inst.save()
        formset.save_m2m()

    # ───────────────────────────────
    # Actions utilitaires : présence
    # ───────────────────────────────
    @admin.action(description="🟢 Marquer tous les candidats comme présents")
    def act_tous_presents(self, request, queryset):
        total = 0
        for atelier in queryset:
            for presence in atelier.presences.all():
                if presence.statut != PresenceStatut.PRESENT:
                    presence.statut = PresenceStatut.PRESENT
                    presence.save(user=request.user)
                    total += 1
        if total:
            self.message_user(request, _(f"{total} présences marquées comme 'Présent'."), level=messages.SUCCESS)
        else:
            self.message_user(request, _("Aucune présence modifiée."), level=messages.INFO)

    @admin.action(description="🚫 Marquer tous les candidats comme absents")
    def act_tous_absents(self, request, queryset):
        total = 0
        for atelier in queryset:
            for presence in atelier.presences.all():
                if presence.statut != PresenceStatut.ABSENT:
                    presence.statut = PresenceStatut.ABSENT
                    presence.save(user=request.user)
                    total += 1
        if total:
            self.message_user(request, _(f"{total} présences marquées comme 'Absent'."), level=messages.SUCCESS)
        else:
            self.message_user(request, _("Aucune présence modifiée."), level=messages.INFO)

    actions = ("act_tous_presents", "act_tous_absents")
