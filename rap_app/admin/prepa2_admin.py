from django.contrib import admin
from django.db.models import Sum
from django.urls import path
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import localdate
from django.contrib.admin import SimpleListFilter

from ..models.prepa2 import Prepa2, ObjectifPrepa


# -------------------------------------------------------------------
# 🔎 Filtre Département (fiabilisé)
# -------------------------------------------------------------------
class DepartementFilter(SimpleListFilter):
    title = _("Département")
    parameter_name = "departement"

    def lookups(self, request, model_admin):
        # Récupère les départements existants depuis les centres liés
        qs = model_admin.model.objects.select_related("centre").all()
        deps = sorted({getattr(o.centre, "departement", None) for o in qs if getattr(o.centre, "departement", None)})
        return [(dep, dep) for dep in deps]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            # Filtre direct sur le code postal du centre (évite la collecte d'IDs)
            return queryset.filter(centre__code_postal__startswith=value)
        return queryset


# -------------------------------------------------------------------
# 📊 ADMIN : SÉANCES (Prepa2) — Vue 100% « tout en colonnes »
# -------------------------------------------------------------------
@admin.register(Prepa2)
class Prepa2Admin(admin.ModelAdmin):
    """
    Tableau complet : infos générales, IC, Ateliers, Objectif.
    """

    list_display = (
        # Contexte
        "date_prepa",
        "centre",
        "departement",
        "type_prepa",

        # IC (toujours visibles, '-' si non pertinent)
        "nombre_places_ouvertes",
        "nombre_prescriptions",
        "nb_presents_info",
        "nb_absents_info",
        "nb_adhesions",
        "taux_prescription_col",
        "taux_presence_info_col",
        "taux_adhesion_colored",   # coloré

        # Ateliers (toujours visibles, '-' si non pertinent)
        "nb_inscrits_atelier",
        "nb_presents_atelier",
        "nb_absents_atelier",
        "taux_presence_atelier_col",

        # Objectif annuel (toujours visibles)
        "objectif_annuel",
        "taux_atteinte_annuel_colored",  # coloré
        "reste_a_faire",
    )

    list_filter = (
        "type_prepa",
        DepartementFilter,
        "centre",
        ("date_prepa", admin.DateFieldListFilter),
    )
    search_fields = ("centre__nom", "commentaire")
    date_hierarchy = "date_prepa"
    ordering = ("-date_prepa", "-id")
    list_per_page = 50
    list_select_related = ("centre",)  # ⚡️ perfs

    # Optionnel : édition en ligne pour les champs saisis fréquemment
    list_editable = (
        "nombre_places_ouvertes",
        "nombre_prescriptions",
        "nb_presents_info",
        "nb_adhesions",
        "nb_inscrits_atelier",
        "nb_presents_atelier",
    )

    readonly_fields = (
        "taux_prescription",
        "taux_presence_info",
        "taux_adhesion",
        "taux_presence_atelier",
        "objectif_annuel",
        "taux_atteinte_annuel",
        "reste_a_faire",
    )

    fieldsets = (
        (_("Informations générales"), {
            "fields": ("type_prepa", "date_prepa", "centre", "commentaire"),
        }),
        (_("Information collective"), {
            "classes": ("collapse",),
            "fields": (
                ("nombre_places_ouvertes", "nombre_prescriptions"),
                ("nb_presents_info", "nb_absents_info"),
                "nb_adhesions",
                ("taux_prescription", "taux_presence_info", "taux_adhesion"),
            ),
        }),
        (_("Ateliers"), {
            "classes": ("collapse",),
            "fields": (
                ("nb_inscrits_atelier", "nb_presents_atelier", "nb_absents_atelier"),
                "taux_presence_atelier",
            ),
        }),
        (_("Objectif annuel"), {
            "fields": ("objectif_annuel", "taux_atteinte_annuel", "reste_a_faire"),
        }),
    )

    # --------- Helpers d’affichage / colonnes calculées ---------
    def departement(self, obj):
        return getattr(obj.centre, "departement", None) or "-"
    departement.short_description = _("Département")

    # Taux IC en texte pour colonnes (avec '-' si non IC)
    def _dash_if_not_ic(self, obj, value):
        return value if obj.type_prepa == Prepa2.TypePrepa.INFO_COLLECTIVE else "-"

    def taux_prescription_col(self, obj):
        return self._dash_if_not_ic(obj, f"{obj.taux_prescription}%")
    taux_prescription_col.short_description = _("Taux prescr. (IC)")

    def taux_presence_info_col(self, obj):
        return self._dash_if_not_ic(obj, f"{obj.taux_presence_info}%")
    taux_presence_info_col.short_description = _("Taux présence (IC)")

    def taux_adhesion_colored(self, obj):
        if obj.type_prepa != Prepa2.TypePrepa.INFO_COLLECTIVE:
            return "-"
        taux = obj.taux_adhesion
        color = "green" if taux >= 70 else "orange" if taux >= 50 else "red"
        return format_html('<span style="color:{};">{}%</span>', color, taux)
    taux_adhesion_colored.short_description = _("Taux adhésion (IC)")

    # Taux Atelier en texte pour colonnes (avec '-' si non atelier)
    def _dash_if_not_atelier(self, obj, value):
        return value if str(obj.type_prepa).startswith("atelier") else "-"

    def taux_presence_atelier_col(self, obj):
        if not str(obj.type_prepa).startswith("atelier"):
            return "-"
        return f"{obj.taux_presence_atelier}%"
    taux_presence_atelier_col.short_description = _("Taux présence (At.)")

    def taux_atteinte_annuel_colored(self, obj):
        taux = obj.taux_atteinte_annuel
        color = "green" if taux >= 100 else "orange" if taux >= 70 else "red"
        return format_html('<b style="color:{};">{}%</b>', color, taux)
    taux_atteinte_annuel_colored.short_description = _("Atteinte obj.")

    # Actions
    actions = ["recalculer_absents"]

    @admin.action(description=_("🔄 Recalculer les absents"))
    def recalculer_absents(self, request, queryset):
        count = 0
        for obj in queryset:
            obj.save(user=request.user)  # conserve l’historique
            count += 1
        self.message_user(request, f"{count} séances mises à jour.")

    # Dashboard et récap list
    def get_urls(self):
        urls = super().get_urls()
        custom = [path("dashboard/", self.admin_site.admin_view(self.dashboard_view), name="prepa2_dashboard")]
        return custom + urls

    def get_search_results(self, request, queryset, search_term):
        """Recherche par nom de centre, commentaire OU code département (ex: '92')."""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if search_term.isdigit() and len(search_term) in (2, 3):
            queryset |= self.model.objects.filter(centre__code_postal__startswith=search_term)
        return queryset, use_distinct

    def dashboard_view(self, request):
        """Vue synthétique avec graphiques (Chart.js)."""
        annee = localdate().year
        synthese = Prepa2.synthese_objectifs(annee)
        data_centres = []
        for centre_obj in ObjectifPrepa.objects.filter(annee=annee).select_related("centre"):
            nom = getattr(centre_obj.centre, "nom", str(centre_obj.centre))
            realise = Prepa2.total_accueillis(
                annee=annee, centre=centre_obj.centre, type_prepa=Prepa2.TypePrepa.INFO_COLLECTIVE
            )
            data_centres.append({
                "centre": nom,
                "objectif": centre_obj.valeur_objectif,
                "realise": realise,
                "reste": max(centre_obj.valeur_objectif - realise, 0),
            })

        context = dict(
            self.admin_site.each_context(request),
            title=_("Tableau de bord PrépaComp"),
            annee=annee,
            synthese=synthese,
            data_centres=data_centres,
        )
        return TemplateResponse(request, "admin/prepa2_dashboard.html", context)

    def changelist_view(self, request, extra_context=None):
        """Ajoute un résumé rapide IC / Ateliers / Total sur la liste courante (après filtres)."""
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data["cl"].queryset
            total_ic = qs.filter(type_prepa=Prepa2.TypePrepa.INFO_COLLECTIVE).aggregate(
                total=Sum("nb_presents_info")
            )["total"] or 0
            total_at = qs.filter(type_prepa__startswith="atelier").aggregate(
                total=Sum("nb_presents_atelier")
            )["total"] or 0
            response.context_data["totaux"] = {"IC": total_ic, "Ateliers": total_at, "Total": total_ic + total_at}
        except Exception:
            pass
        return response

    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)


# -------------------------------------------------------------------
# 🎯 ADMIN : OBJECTIFS — enrichi avec tous les KPI IC
# -------------------------------------------------------------------
@admin.register(ObjectifPrepa)
class ObjectifPrepaAdmin(admin.ModelAdmin):
    list_display = (
        "centre",
        "departement",
        "annee",
        "valeur_objectif",
        # IC agrégés
        "total_places",
        "total_prescriptions",
        "total_presents",
        "total_adhesions",
        # Taux
        "taux_prescription_col",
        "taux_presence_col",
        "taux_adhesion_col",
        "taux_atteinte_colored",
        # Reste
        "reste_a_faire",
    )
    list_filter = ("annee", DepartementFilter, "centre")
    search_fields = ("centre__nom",)
    ordering = ("-annee", "centre")
    list_select_related = ("centre",)

    readonly_fields = (
        "taux_prescription",
        "taux_presence",
        "taux_adhesion",
        "taux_atteinte",
        "reste_a_faire",
    )

    # --- Colonnes d'agrégats (provenant de data_prepa) ---
    def _dp(self, obj):
        return obj.data_prepa  # cache déjà géré dans le modèle

    def total_places(self, obj):
        return self._dp(obj)["places"]
    total_places.short_description = _("Places (IC)")

    def total_prescriptions(self, obj):
        return self._dp(obj)["prescriptions"]
    total_prescriptions.short_description = _("Prescr. (IC)")

    def total_presents(self, obj):
        return self._dp(obj)["presents"]
    total_presents.short_description = _("Présents (IC)")

    def total_adhesions(self, obj):
        return self._dp(obj)["adhesions"]
    total_adhesions.short_description = _("Adhésions (IC)")

    # --- Taux (textuels) + version colorée pour l’atteinte ---
    def taux_prescription_col(self, obj):
        return f"{obj.taux_prescription}%"
    taux_prescription_col.short_description = _("Taux prescr. (IC)")

    def taux_presence_col(self, obj):
        return f"{obj.taux_presence}%"
    taux_presence_col.short_description = _("Taux présence (IC)")

    def taux_adhesion_col(self, obj):
        return f"{obj.taux_adhesion}%"
    taux_adhesion_col.short_description = _("Taux adhésion (IC)")

    def taux_atteinte_colored(self, obj):
        taux = obj.taux_atteinte
        color = "green" if taux >= 100 else "orange" if taux >= 70 else "red"
        return format_html('<b style="color:{};">{}%</b>', color, taux)
    taux_atteinte_colored.short_description = _("Atteinte obj.")

    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)
