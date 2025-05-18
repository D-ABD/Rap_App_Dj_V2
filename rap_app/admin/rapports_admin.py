from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from ..models.rapports import Rapport


@admin.register(Rapport)
class RapportAdmin(admin.ModelAdmin):
    """
    📄 Admin pour les rapports générés (statistiques, exports...).
    """

    list_display = (
        "nom",
        "type_rapport",
        "periode",
        "format",
        "centre",
        "formation",
        "date_debut",
        "date_fin",
        "temps_generation",
        "created_at",
        "updated_at",
        "affichage_duree",
    )
    list_filter = (
        "type_rapport",
        "periode",
        "format",
        "centre",
        "formation",
        "type_offre",
        "statut",
        "created_at",
    )
    search_fields = (
        "nom",
        "centre__nom",
        "formation__nom",
        "type_offre__nom",
        "statut__nom",
    )
    autocomplete_fields = ("centre", "formation", "type_offre", "statut")
    date_hierarchy = "date_debut"
    ordering = ("-created_at",)

    readonly_fields = (
        "temps_generation",
        "created_at",
        "updated_at",
        "affichage_duree",
    )

    fieldsets = (
        (None, {
            "fields": (
                "nom",
                "type_rapport",
                "periode",
                "format",
                "centre",
                "formation",
                "type_offre",
                "statut",
                "date_debut",
                "date_fin",
            )
        }),
        (_("Performance"), {
            "fields": ("temps_generation", "affichage_duree"),
        }),
        (_("🧾 Suivi & Métadonnées"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def affichage_duree(self, obj):
        if obj.temps_generation:
            return format_html(
                "<span style='color: #2d862d;'>⏱ {:.2f} sec</span>",
                obj.temps_generation
            )
        return "—"
    affichage_duree.short_description = _("Durée de génération")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "centre", "formation", "type_offre", "statut"
        )

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
