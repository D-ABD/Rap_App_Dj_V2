import logging
from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from ..models.formations import Formation, HistoriqueFormation, Activite

logger = logging.getLogger("application.formation")


# =====================================================
# 🔹 Filtres personnalisés
# =====================================================

class ActiviteFilter(admin.SimpleListFilter):
    title = _("Activité")
    parameter_name = "activite"

    def lookups(self, request, model_admin):
        return [
            (Activite.ACTIVE, _("Active")),
            (Activite.ARCHIVEE, _("Archivée")),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(activite=self.value())
        return queryset


class StatutTemporelFilter(admin.SimpleListFilter):
    title = _("Statut temporel")
    parameter_name = "status_temporel"

    def lookups(self, request, model_admin):
        return [
            ("active", _("En cours")),
            ("future", _("À venir")),
            ("past", _("Terminée")),
        ]

    def queryset(self, request, queryset):
        today = timezone.now().date()
        if self.value() == "active":
            return queryset.filter(start_date__lte=today, end_date__gte=today)
        elif self.value() == "future":
            return queryset.filter(start_date__gt=today)
        elif self.value() == "past":
            return queryset.filter(end_date__lt=today)
        return queryset


class SaturationFilter(admin.SimpleListFilter):
    title = _("Saturation")
    parameter_name = "saturation"

    def lookups(self, request, model_admin):
        return [
            ("low", _("🟢 Faible (<50%)")),
            ("medium", _("🟡 Moyenne (50–79%)")),
            ("high", _("🔴 Saturée (≥80%)")),
        ]

    def queryset(self, request, queryset):
        if self.value() == "low":
            return queryset.filter(saturation__lt=50)
        elif self.value() == "medium":
            return queryset.filter(saturation__gte=50, saturation__lt=80)
        elif self.value() == "high":
            return queryset.filter(saturation__gte=80)
        return queryset


# =====================================================
# 🔹 Inline : Historique des modifications
# =====================================================

class HistoriqueFormationInline(admin.TabularInline):
    model = HistoriqueFormation
    extra = 0
    can_delete = False
    readonly_fields = (
        "created_at",
        "created_by",
        "action",
        "champ_modifie",
        "ancienne_valeur",
        "nouvelle_valeur",
        "commentaire",
    )
    ordering = ("-created_at",)
    verbose_name_plural = _("Historique des modifications")
    show_change_link = False

    def has_add_permission(self, request, obj=None):
        return False


# =====================================================
# 🔹 Admin principal : Formation
# =====================================================

@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "centre_display",
        "type_offre_display",
        "statut_display",
        "start_date",
        "end_date",
        "saturation_badge",
        "places_disponibles_display",
        "status_temporel_display",
        "activite_display",
    )

    list_filter = (
        ActiviteFilter,
        StatutTemporelFilter,
        SaturationFilter,
        "centre",
        "type_offre",
        "statut",
        "convocation_envoie",
    )

    search_fields = (
        "nom",
        "num_kairos",
        "num_offre",
        "num_produit",
        "assistante",
        "centre__nom",
        "type_offre__nom",
        "statut__nom",
    )

    ordering = ("-start_date", "nom")
    date_hierarchy = "start_date"
    inlines = [HistoriqueFormationInline]

    readonly_fields = (
        "saturation",
        "total_places_display",
        "total_inscrits_display",
        "places_disponibles_display",
        "taux_saturation_display",
        "status_temporel_display",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (_("Informations générales"), {
            "fields": (
                "nom",
                "centre",
                "type_offre",
                "statut",
                "activite",
                "assistante",
            )
        }),
        (_("Dates et identifiants"), {
            "fields": (
                "start_date",
                "end_date",
                "num_kairos",
                "num_offre",
                "num_produit",
            )
        }),
        (_("Places et inscriptions"), {
            "fields": (
                ("prevus_crif", "inscrits_crif"),
                ("prevus_mp", "inscrits_mp"),
                "saturation",
                "total_places_display",
                "total_inscrits_display",
                "places_disponibles_display",
                "taux_saturation_display",
            )
        }),
        (_("Suivi et activité"), {
            "fields": (
                "convocation_envoie",
                "entree_formation",
                "nombre_candidats",
                "nombre_entretiens",
                "nombre_evenements",
                "dernier_commentaire",
                "status_temporel_display",
            )
        }),
        (_("Méta"), {
            "classes": ("collapse",),
            "fields": (
                "created_at",
                "updated_at",
            ),
        }),
    )

    # =================================================
    # 🧮 Méthodes d’affichage
    # =================================================

    @admin.display(description=_("Centre"))
    def centre_display(self, obj):
        return obj.centre.nom if obj.centre else "—"

    @admin.display(description=_("Type d’offre"))
    def type_offre_display(self, obj):
        return obj.type_offre.nom if obj.type_offre else "—"

    @admin.display(description=_("Statut"))
    def statut_display(self, obj):
        if obj.statut:
            color = obj.get_status_color()
            return format_html(
                '<span style="color:{}; font-weight:bold;">{}</span>',
                color,
                obj.statut.nom,
            )
        return "—"

    @admin.display(description=_("Activité"))
    def activite_display(self, obj):
        color = "#16a34a" if obj.activite == Activite.ACTIVE else "#9ca3af"
        label = _("Active") if obj.activite == Activite.ACTIVE else _("Archivée")
        return format_html('<span style="color:{};">{}</span>', color, label)

    @admin.display(description=_("Saturation"))
    def saturation_badge(self, obj):
        if obj.saturation is None:
            return "—"
        try:
            value = float(obj.saturation)
        except (ValueError, TypeError):
            value = 0.0
        color = "green" if value < 50 else "orange" if value < 80 else "red"
        return format_html('<b><span style="color:{};">{}%</span></b>', color, f"{value:.1f}")

    @admin.display(description=_("Statut temporel"))
    def status_temporel_display(self, obj):
        mapping = {
            "active": _("🟢 En cours"),
            "future": _("🟡 À venir"),
            "past": _("🔴 Terminée"),
        }
        return mapping.get(obj.status_temporel, "❓ Inconnu")

    @admin.display(description=_("Total places"))
    def total_places_display(self, obj):
        return obj.total_places

    @admin.display(description=_("Total inscrits"))
    def total_inscrits_display(self, obj):
        return obj.total_inscrits

    @admin.display(description=_("Places disponibles"))
    def places_disponibles_display(self, obj):
        return obj.places_disponibles

    @admin.display(description=_("Taux saturation"))
    def taux_saturation_display(self, obj):
        return f"{obj.taux_saturation:.1f}%"

    # =================================================
    # ⚙️ Actions personnalisées
    # =================================================

    @admin.action(description=_("🗃️ Archiver les formations sélectionnées"))
    def action_archiver(self, request, queryset):
        count = 0
        for formation in queryset:
            if formation.activite != Activite.ARCHIVEE:
                formation.archiver(user=request.user, commentaire="Archivage via admin Django")
                count += 1
        self.message_user(request, _(f"{count} formation(s) archivée(s)."), messages.SUCCESS)

    @admin.action(description=_("♻️ Désarchiver les formations sélectionnées"))
    def action_desarchiver(self, request, queryset):
        count = 0
        for formation in queryset:
            if formation.activite != Activite.ACTIVE:
                formation.desarchiver(user=request.user, commentaire="Restauration via admin Django")
                count += 1
        self.message_user(request, _(f"{count} formation(s) restaurée(s)."), messages.SUCCESS)

    @admin.action(description=_("📄 Dupliquer les formations sélectionnées"))
    def action_dupliquer(self, request, queryset):
        count = 0
        for formation in queryset:
            formation.duplicate(user=request.user)
            count += 1
        self.message_user(request, _(f"{count} formation(s) dupliquée(s)."), messages.SUCCESS)

    actions = ("action_archiver", "action_desarchiver", "action_dupliquer")

    # =================================================
    # ⚡ Optimisation queryset
    # =================================================

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("centre", "type_offre", "statut")


# =====================================================
# 🔹 Admin HistoriqueFormation
# =====================================================

@admin.register(HistoriqueFormation)
class HistoriqueFormationAdmin(admin.ModelAdmin):
    list_display = (
        "formation",
        "champ_modifie",
        "valeur_changement",
        "action",
        "created_by",
        "created_at",
    )
    list_filter = ("action", "champ_modifie", "created_by", "created_at")
    search_fields = (
        "formation__nom",
        "champ_modifie",
        "nouvelle_valeur",
        "commentaire",
        "created_by__username",
    )
    readonly_fields = (
        "formation",
        "action",
        "champ_modifie",
        "ancienne_valeur",
        "nouvelle_valeur",
        "commentaire",
        "details",
        "created_by",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
