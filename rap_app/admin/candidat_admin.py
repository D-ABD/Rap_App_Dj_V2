from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from ..models.atelier_tre import AtelierTRE
from ..models.candidat import Candidat, HistoriquePlacement
from .appairage_admin import AppairageInline


class HistoriquePlacementInline(admin.TabularInline):
    model = HistoriquePlacement
    extra = 0
    fields = ("date", "entreprise", "resultat", "responsable", "commentaire")
    autocomplete_fields = ("entreprise", "responsable")
    show_change_link = True


class AtelierTREParticipationInline(admin.TabularInline):
    model = AtelierTRE.candidats.through  # Utilise la table intermédiaire
    extra = 0
    verbose_name = "Atelier TRE"
    verbose_name_plural = "Ateliers TRE suivis"
    fields = ("ateliertre",)  # Affiche la colonne de liaison
    autocomplete_fields = ("ateliertre",)


@admin.register(Candidat)
class CandidatAdmin(admin.ModelAdmin):
    def voir_appairages(self, obj):
        url = f"/admin/rap_app/appairage/?candidat__id__exact={obj.pk}"
        return format_html(f'<a href="{url}">Voir</a>')

    voir_appairages.short_description = "Appairages"

    def ateliers_resume(self, obj):
        return obj.ateliers_resume
    ateliers_resume.short_description = "Ateliers suivis"

    list_display = (
        "prenom", "nom", "statut", "age", "formation", "resultat_placement",
        "date_inscription", "admissible", "entretien_done", "test_is_ok",
        "voir_appairages", "vu_par", "responsable_placement", "ateliers_resume",
        "date_placement", "contrat_signe", "courrier_rentree", "date_rentree", "origine_sourcing"
    )
    list_filter = (
        "statut", "formation", "type_contrat", "disponibilite", "admissible",
        "entretien_done", "test_is_ok", "rqth", "permis_b",
        "resultat_placement", "contrat_signe", "vu_par", "origine_sourcing", "responsable_placement",
    )
    search_fields = ("prenom", "nom", "email", "telephone", "ville", "code_postal")
    readonly_fields = ("date_inscription", "age")
    autocomplete_fields = (
        "formation", "evenement", "compte_utilisateur",
        "entreprise_placement", "entreprise_validee",
        "vu_par", "responsable_placement",
    )
    ordering = ("-date_inscription",)
    inlines = [HistoriquePlacementInline, AppairageInline, AtelierTREParticipationInline]

    fieldsets = (
        (_("Identité"), {
            "fields": (
                ("prenom", "nom"), "date_naissance", "age", "email",
                "telephone", "ville", "code_postal", "origine_sourcing"
            )
        }),
        (_("Compte et inscription"), {
            "fields": ("compte_utilisateur", "date_inscription")
        }),
        (_("Formation et accompagnement"), {
            "fields": (
                "statut", "formation", "evenement",
                "entretien_done", "test_is_ok", "admissible"
            )
        }),
        (_("Placement"), {
            "fields": (
                "date_placement", "entreprise_placement", "entreprise_validee",
                "resultat_placement", "responsable_placement",
                "contrat_signe", "courrier_rentree", "date_rentree"
            )
        }),
        (_("Informations socio-pro & dispo"), {
            "fields": (
                "type_contrat", "disponibilite", "permis_b", "rqth",
                "csp", "communication", "experience", "vu_par"
            )
        }),
        (_("Notes"), {
            "fields": ("notes",)
        }),
    )


@admin.register(HistoriquePlacement)
class HistoriquePlacementAdmin(admin.ModelAdmin):
    list_display = ("candidat", "date", "entreprise", "resultat", "responsable")
    list_filter = ("resultat", "entreprise", "responsable")
    search_fields = (
        "candidat__nom", "candidat__prenom", "entreprise__nom", "commentaire"
    ) 
    autocomplete_fields = ("candidat", "entreprise", "responsable")
    ordering = ("-date",)
