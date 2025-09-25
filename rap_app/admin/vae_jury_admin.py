from django.contrib import admin
from django.utils.html import format_html
from ..models.vae import VAE, HistoriqueStatutVAE


@admin.register(VAE)
class VAEAdmin(admin.ModelAdmin):
    """
    🎓 Suivi des parcours VAE.
    """

    list_display = (
        "reference",
        "centre",
        "statut_badge",
        "created_at",
        "is_en_cours",
        "is_terminee",
        "duree_jours",
    )
    list_filter = ("statut", "centre")
    search_fields = ("reference", "centre__nom", "commentaire")
    readonly_fields = ("reference", "created_at", "updated_at")

    def statut_badge(self, obj):
        color_map = {
            "info": "gray",
            "dossier": "blue",
            "attente_financement": "orange",
            "accompagnement": "purple",
            "jury": "goldenrod",
            "terminee": "green",
            "abandonnee": "red",
        }
        color = color_map.get(obj.statut, "black")
        label = obj.get_statut_display()
        return format_html(
            '<span style="color:white; background:{}; padding:2px 6px; border-radius:4px;">{}</span>',
            color,
            label,
        )

    statut_badge.short_description = "Statut"


@admin.register(HistoriqueStatutVAE)
class HistoriqueStatutVAEAdmin(admin.ModelAdmin):
    """
    🕓 Historique des changements de statuts des VAE.
    """

    list_display = (
        "vae",
        "statut",
        "date_changement_effectif",
        "commentaire",
        "created_at",
    )
    list_filter = ("statut", "date_changement_effectif")
    search_fields = ("vae__reference", "commentaire")
    autocomplete_fields = ("vae",)

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
