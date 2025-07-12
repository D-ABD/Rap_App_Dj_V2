from django.contrib import messages
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.core.exceptions import ValidationError

from ..models.atelier_tre import AtelierTRE
from ..models.candidat import Candidat, HistoriquePlacement
from .appairage_admin import AppairageInline

# ✅ Ajout de la fonction utilitaire
def etoiles(val: int) -> str:
    return "★" * val + "☆" * (5 - val)




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
    actions = ["valider_comme_stagiaire", "valider_comme_candidatuser"]


    def role_utilisateur(self, obj):
        return obj.compte_utilisateur.get_role_display() if obj.compte_utilisateur else "-"
    role_utilisateur.short_description = "Rôle compte"


    @admin.action(description="Valider comme candidatuser")
    def valider_comme_candidatuser(modeladmin, request, queryset):
        for candidat in queryset:
            try:
                user = candidat.valider_comme_candidatuser()
                messages.success(request, _(f"{candidat} → {user.email} candidat validé."))
            except ValidationError as e:
                messages.error(request, _(f"Erreur pour {candidat} : {e.messages[0]}"))

    @admin.action(description="Valider comme 'Candidat utilisateur'")
    def est_valide_comme_candidatuser(self, obj):
        return obj.est_valide_comme_candidatuser


    def voir_appairages(self, obj):
        url = f"/admin/rap_app/appairage/?candidat__id__exact={obj.pk}"
        return format_html(f'<a href="{url}">Voir</a>')

    voir_appairages.short_description = "Appairages"

    @admin.action(description="Valider comme stagiaire")
    def valider_comme_stagiaire(modeladmin, request, queryset):
        for candidat in queryset:
            try:
                user = candidat.valider_comme_stagiaire()
                messages.success(request, _(f"{candidat} → {user.email} stagiaire validé."))
            except ValidationError as e:
                messages.error(request, _(f"Erreur pour {candidat} : {e.message}"))

    @admin.display(boolean=True, description="Validé stagiaire ?")
    def est_valide_comme_stagiaire(self, obj):
        return obj.est_valide_comme_stagiaire
    
    @admin.display(description="Rôle utilisateur")
    def role_utilisateur(self, obj):
        return obj.role_utilisateur
    
    def ateliers_resume(self, obj):
        return obj.ateliers_resume
    ateliers_resume.short_description = "Ateliers suivis"

    @admin.display(description="Communication")
    def communication_etoiles(self, obj):
        return etoiles(obj.communication) if obj.communication else "-"

    @admin.display(description="Expérience")
    def experience_etoiles(self, obj):
        return etoiles(obj.experience) if obj.experience else "-"

    @admin.display(description="CSP")
    def csp_etoiles(self, obj):
        return etoiles(obj.csp) if obj.csp else "-"


    list_display = (
        "role_utilisateur", "prenom", "nom", "statut", "age", "formation", "resultat_placement",
        "date_inscription", "admissible", "est_valide_comme_candidatuser", "est_valide_comme_stagiaire", "entretien_done", "test_is_ok",
        "voir_appairages", "vu_par", "responsable_placement", "ateliers_resume",
        "communication_etoiles", "experience_etoiles", "csp_etoiles", 
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
    def etoiles(val: int) -> str:
        return "★" * val + "☆" * (5 - val)

@admin.register(HistoriquePlacement)
class HistoriquePlacementAdmin(admin.ModelAdmin):
    list_display = ("candidat", "date", "entreprise", "resultat", "responsable")
    list_filter = ("resultat", "entreprise", "responsable")
    search_fields = (
        "candidat__nom", "candidat__prenom", "entreprise__nom", "commentaire"
    ) 
    autocomplete_fields = ("candidat", "entreprise", "responsable")
    ordering = ("-date",)
