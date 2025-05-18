from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import localtime, now, timedelta
from ..models.evenements import Evenement


class StatutTemporelFilter(admin.SimpleListFilter):
    title = "Statut temporel"
    parameter_name = "statut"

    def lookups(self, request, model_admin):
        return [
            ("past", "Passés"),
            ("today", "Aujourd'hui"),
            ("soon", "Bientôt"),
            ("future", "À venir"),
        ]

    def queryset(self, request, queryset):
        today = now().date()
        if self.value() == "past":
            return queryset.filter(event_date__lt=today)
        elif self.value() == "today":
            return queryset.filter(event_date=today)
        elif self.value() == "soon":
            return queryset.filter(event_date__gt=today, event_date__lte=today + timedelta(days=7))
        elif self.value() == "future":
            return queryset.filter(event_date__gt=today + timedelta(days=7))
        return queryset


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    """
    📅 Admin avancé pour la gestion des événements liés aux formations.
    """

    list_display = (
        "id",
        "type_evenement_display",
        "event_date_display",
        "formation_nom_display",
        "lieu",
        "participants_prevus",
        "participants_reels",
        "taux_participation_display",
        "status_badge",
        "is_active",
    )
    list_display_links = ("id", "type_evenement_display")
    list_filter = ("type_evenement", "is_active", "event_date", "formation", StatutTemporelFilter)
    search_fields = (
        "description_autre",
        "lieu",
        "formation__nom",
        "details",
    )
    ordering = ("-event_date",)
    actions = ["activer_evenements", "desactiver_evenements"]
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")

    fieldsets = (
        ("📅 Informations générales", {
            "fields": ("type_evenement", "description_autre", "formation", "event_date", "lieu"),
        }),
        ("👥 Participants", {
            "fields": ("participants_prevus", "participants_reels"),
        }),
        ("📌 Détails complémentaires", {
            "fields": ("details", "is_active"),
        }),
        ("🧾 Suivi", {
            "fields": ("created_by", "created_at", "updated_by", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # ==== Affichage ====

    def type_evenement_display(self, obj):
        return obj.get_type_evenement_display()
    type_evenement_display.short_description = "Type"

    def event_date_display(self, obj):
        return localtime(obj.event_date).strftime("%d/%m/%Y") if obj.event_date else "—"
    event_date_display.short_description = "Date"

    def formation_nom_display(self, obj):
        if not obj.formation:
            return "—"
        url = getattr(obj.formation, "get_admin_url", lambda: "#")()
        return format_html('<a href="{}">{}</a>', url, obj.formation.nom)
    formation_nom_display.short_description = "Formation"

    def taux_participation_display(self, obj):
        taux = obj.taux_participation
        if taux is None:
            return "—"
        color = {
            "success": "green",
            "warning": "orange",
            "danger": "red",
        }.get(obj.participation_status, "gray")
        return format_html('<span style="color:{};">{}%</span>', color, taux)
    taux_participation_display.short_description = "Taux de participation"

    def status_badge(self, obj):
        return format_html('<span class="badge {}">{}</span>', obj.status_badge_class, obj.status_label)
    status_badge.short_description = "Statut"

    # ==== Actions ====

    @admin.action(description="✅ Activer les événements sélectionnés")
    def activer_evenements(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} événement(s) activé(s).")

    @admin.action(description="🚫 Désactiver les événements sélectionnés")
    def desactiver_evenements(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} événement(s) désactivé(s).")
   
    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
