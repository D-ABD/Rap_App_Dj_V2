from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from ..models.statut import Statut


@admin.register(Statut)
class StatutAdmin(admin.ModelAdmin):
    """
    🏷️ Admin avancé pour la gestion des statuts.
    """

    list_display = (
        "badge_color",
        "nom",
        "description_autre",
        "couleur",
        "created_at",
        "updated_at",
        "created_by_display",
    )
    list_filter = ("nom", "created_at", "updated_at")
    search_fields = ("nom", "description_autre", "couleur")
    ordering = ("nom",)
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at", "badge_preview", "created_by")

    fieldsets = (
        (_("Informations générales"), {
            "fields": ("nom", "description_autre", "couleur", "badge_preview"),
        }),
        (_("🧾 Métadonnées"), {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("created_by")

    def badge_color(self, obj):
        return format_html(obj.get_badge_html())
    badge_color.short_description = _("Aperçu")

    def badge_preview(self, obj):
        if obj.pk:
            return format_html(obj.get_badge_html())
        return _("Le badge s'affichera après l'enregistrement.")
    badge_preview.short_description = _("Aperçu du badge")

    def created_by_display(self, obj):
        return str(obj.created_by) if obj.created_by else "—"
    created_by_display.short_description = _("Créé par")

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
