from django.contrib import admin
from ..models.jury import SuiviJury


@admin.register(SuiviJury)
class SuiviJuryAdmin(admin.ModelAdmin):
    """
    📊 Suivi mensuel des jurys par centre.
    """

    list_display = (
        "centre",
        "annee",
        "mois",
        "objectif_jury",
        "jurys_realises",
        "ecart",
        "pourcentage_affiche",
        "created_at",
    )
    list_filter = ("centre", "annee", "mois")
    search_fields = ("centre__nom",)
    ordering = ("-annee", "-mois", "centre")

    def pourcentage_affiche(self, obj):
        return f"{obj.pourcentage_mensuel:.1f} %"

    pourcentage_affiche.short_description = "Taux atteint"
