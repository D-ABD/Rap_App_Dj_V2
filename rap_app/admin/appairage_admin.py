# admin.py
from django.contrib import admin
from ..models.appairage import Appairage, HistoriqueAppairage


@admin.register(Appairage)
class AppairageAdmin(admin.ModelAdmin):
    list_display = (
        'candidat',
        'partenaire',
        'formation',
        'statut',
        'date_appairage',
        'date_retour',
    )
    list_filter = (
        'statut',
        'date_appairage',
        'formation',
    )
    search_fields = (
        'candidat__nom',
        'candidat__prenom',
        'partenaire__nom',
        'formation__nom',
        'commentaire',
    )
    autocomplete_fields = ('candidat', 'partenaire', 'formation')
    ordering = ('-date_appairage',)

class AppairageInline(admin.TabularInline):
    model = Appairage
    extra = 0
    fields = (
        "partenaire", "formation", "date_appairage", "statut",
        "commentaire", "retour_partenaire", "date_retour"
    )
    autocomplete_fields = ("partenaire", "formation")
    readonly_fields = ("date_appairage",)
    show_change_link = True

@admin.register(HistoriqueAppairage)
class HistoriqueAppairageAdmin(admin.ModelAdmin):
    list_display = (
        'appairage',
        'statut',
        'date',
        'auteur',
        'commentaire',
    )
    list_filter = (
        'statut',
        'date',
    )
    search_fields = (
        'appairage__candidat__nom',
        'appairage__candidat__prenom',
        'appairage__partenaire__nom',
        'commentaire',
    )
    autocomplete_fields = ('appairage', 'auteur')
    readonly_fields = ('date',)
    ordering = ('-date',)
