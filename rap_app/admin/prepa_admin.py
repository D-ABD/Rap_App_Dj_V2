from django.contrib import admin
from ..models.prepacomp import Semaine, PrepaCompGlobal

@admin.register(Semaine)
class SemaineAdmin(admin.ModelAdmin):
    list_display = (
        'numero_semaine', 'annee', 'centre', 'mois',
        'date_debut_semaine', 'date_fin_semaine',
        'nombre_adhesions', 'nombre_presents_ic',
        'objectif_hebdo_prepa', 'pourcentage_objectif_display'
    )
    list_filter = ('annee', 'mois', 'centre')
    search_fields = ('centre__nom', 'numero_semaine', 'annee')
    ordering = ('-date_debut_semaine',)
    readonly_fields = ('taux_adhesion_display', 'pourcentage_objectif_display')

    def taux_adhesion_display(self, obj):
        return f"{obj.taux_adhesion():.1f} %"
    taux_adhesion_display.short_description = "Taux d’adhésion"

    def pourcentage_objectif_display(self, obj):
        return f"{obj.pourcentage_objectif():.1f} %"
    pourcentage_objectif_display.short_description = "Réalisation hebdo"

@admin.register(PrepaCompGlobal)
class PrepaCompGlobalAdmin(admin.ModelAdmin):
    list_display = (
        'annee', 'centre', 'adhesions',
        'total_presents', 'taux_transformation_display',
        'taux_objectif_annee_display'
    )
    list_filter = ('annee', 'centre')
    search_fields = ('centre__nom', 'annee')

    def taux_transformation_display(self, obj):
        return f"{obj.taux_transformation():.1f} %"
    taux_transformation_display.short_description = "Taux de transformation"

    def taux_objectif_annee_display(self, obj):
        return f"{obj.taux_objectif_annee():.1f} %"
    taux_objectif_annee_display.short_description = "Objectif annuel atteint"
