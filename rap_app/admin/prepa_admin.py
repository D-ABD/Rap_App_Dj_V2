from django.contrib import admin
from ..models.prepacomp import Semaine, PrepaCompGlobal


@admin.register(Semaine)
class SemaineAdmin(admin.ModelAdmin):
    """
    📅 Admin des semaines de suivi Prépa Comp.
    """

    list_display = (
        "numero_semaine",
        "annee",
        "mois",
        "centre",
        "nombre_adhesions",
        "objectif_hebdo_prepa",
        "ecart_objectif_display",
        "taux_adhesion_display",
        "taux_transformation_display",
        "is_courante_display",
    )
    list_filter = ("centre", "annee", "mois")
    search_fields = ("centre__nom",)
    ordering = ("-date_debut_semaine",)
    list_select_related = ("centre",)
    readonly_fields = ("created_at", "updated_at")

    def taux_adhesion_display(self, obj):
        return f"{obj.taux_adhesion():.1f}%" if obj.taux_adhesion() is not None else "—"
    taux_adhesion_display.short_description = "Taux adhésion"

    def taux_transformation_display(self, obj):
        return f"{obj.taux_transformation():.1f}%" if obj.taux_transformation() is not None else "—"
    taux_transformation_display.short_description = "Taux transfo"

    def ecart_objectif_display(self, obj):
        return obj.ecart_objectif if obj.ecart_objectif is not None else "—"
    ecart_objectif_display.short_description = "Écart objectif"

    def is_courante_display(self, obj):
        return "✅" if obj.is_courante else "—"
    is_courante_display.short_description = "Semaine en cours"


@admin.register(PrepaCompGlobal)
class PrepaCompGlobalAdmin(admin.ModelAdmin):
    """
    📊 Admin des objectifs annuels Prépa Comp par centre.
    """

    list_display = (
        "centre",
        "annee",
        "adhesions",
        "total_presents",
        "objectif_annuel_prepa",
        "taux_transformation_display",
        "taux_objectif_display",
        "semaines_restantes",
        "adhesions_hebdo_necessaires_display",
    )
    list_filter = ("annee", "centre")
    search_fields = ("centre__nom",)
    ordering = ("-annee",)
    readonly_fields = ("created_at", "updated_at")

    def taux_transformation_display(self, obj):
        return f"{obj.taux_transformation():.1f}%" if obj.taux_transformation() is not None else "—"
    taux_transformation_display.short_description = "Taux transformation"

    def taux_objectif_display(self, obj):
        return f"{obj.taux_objectif_annee():.1f}%" if obj.taux_objectif_annee() is not None else "—"
    taux_objectif_display.short_description = "Objectif atteint"

    def adhesions_hebdo_necessaires_display(self, obj):
        return f"{obj.adhesions_hebdo_necessaires:.1f}" if obj.adhesions_hebdo_necessaires is not None else "—"
    adhesions_hebdo_necessaires_display.short_description = "Adhésions/semaine nécessaires"

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
