from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from ..models.appairage import Appairage, HistoriqueAppairage, AppairageStatut


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


@admin.register(Appairage)
class AppairageAdmin(admin.ModelAdmin):
    list_display = (
        'candidat_link',
        'partenaire_link',
        'formation_link',
        'statut_badge',
        'date_appairage',
        'date_retour',
        'voir_historique',
    )
    list_filter = (
        'statut',
        ('date_appairage', admin.DateFieldListFilter),
        'formation',
        'partenaire',
    )
    search_fields = (
        'candidat__nom',
        'candidat__prenom',
        'partenaire__nom',
        'formation__nom',
        'commentaire',
        'retour_partenaire',
    )
    autocomplete_fields = ('candidat', 'partenaire', 'formation')
    ordering = ('-date_appairage',)
    readonly_fields = ('date_appairage',)

    fieldsets = (
        (_("Informations principales"), {
            "fields": (
                'candidat', 'partenaire', 'formation', 'statut',
                'date_appairage', 'date_retour',
            )
        }),
        (_("Commentaires et retour"), {
            "fields": (
                'commentaire', 'retour_partenaire',
            )
        }),
    )

    actions = ['changer_statut_en_transmis', 'changer_statut_en_refuse', 'changer_statut_en_accepte']

    @admin.display(description="Statut")
    def statut_badge(self, obj):
        color = {
            'transmis': '#6c757d',
            'en_attente': '#fd7e14',
            'accepte': '#198754',
            'refuse': '#dc3545',
            'annule': '#343a40',
            'a_faire': '#0dcaf0',
        }.get(obj.statut, '#adb5bd')
        label = obj.get_statut_display() if obj.statut else "-"
        return format_html('<span style="color:{}; font-weight:bold;">{}</span>', color, label)

    @admin.display(description="Candidat")
    def candidat_link(self, obj):
        if obj.candidat:
            url = reverse("admin:rap_app_candidat_change", args=[obj.candidat.pk])
            return format_html('<a href="{}">{}</a>', url, obj.candidat)
        return "-"

    @admin.display(description="Partenaire")
    def partenaire_link(self, obj):
        if obj.partenaire:
            url = reverse("admin:rap_app_partenaire_change", args=[obj.partenaire.pk])
            return format_html('<a href="{}">{}</a>', url, obj.partenaire)
        return "-"

    @admin.display(description="Formation")
    def formation_link(self, obj):
        if obj.formation:
            url = reverse("admin:rap_app_formation_change", args=[obj.formation.pk])
            return format_html('<a href="{}">{}</a>', url, obj.formation)
        return "-"

    @admin.display(description="Historique")
    def voir_historique(self, obj):
        url = f"/admin/rap_app/historiqueappairage/?appairage__id__exact={obj.pk}"
        return format_html('<a href="{}">Voir</a>', url)

    @admin.action(description="Changer le statut en 'Transmis'")
    def changer_statut_en_transmis(self, request, queryset):
        updated = queryset.update(statut=AppairageStatut.TRANSMIS)
        messages.success(request, _(f"{updated} appairage(s) mis à jour en 'Transmis'."))

    @admin.action(description="Changer le statut en 'Refusé'")
    def changer_statut_en_refuse(self, request, queryset):
        updated = queryset.update(statut=AppairageStatut.REFUSE)
        messages.success(request, _(f"{updated} appairage(s) mis à jour en 'Refusé'."))

    @admin.action(description="Changer le statut en 'Accepté'")
    def changer_statut_en_accepte(self, request, queryset):
        updated = queryset.update(statut=AppairageStatut.ACCEPTE)
        messages.success(request, _(f"{updated} appairage(s) mis à jour en 'Accepté'."))

    @admin.display(description="Date retour")
    def date_retour(self, obj):
        return obj.date_retour.strftime("%d/%m/%Y %H:%M") if obj.date_retour else "-"

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


__all__ = ["AppairageAdmin", "HistoriqueAppairageAdmin", "AppairageInline"]
