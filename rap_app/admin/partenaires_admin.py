# rap_app/admin/partenaire_admin.py
from django.contrib import admin
from django.utils.timezone import localtime
from django.http import HttpResponse
import csv

from ..models.partenaires import Partenaire


@admin.register(Partenaire)
class PartenaireAdmin(admin.ModelAdmin):
    """
    🏢 Interface d'administration complète pour le modèle Partenaire,
    intégrant toutes les données du Cerfa apprentissage.
    """

    # === Affichages custom =============================================================
    @admin.display(description="Appairages")
    def nb_appairages(self, obj):
        return obj.nb_appairages

    @admin.display(description="Prospections")
    def nb_prospections(self, obj):
        return obj.nb_prospections

    @admin.display(description="Formations")
    def nb_formations(self, obj):
        return obj.nb_formations

    def contact_display(self, obj):
        return obj.contact_info or "—"
    contact_display.short_description = "Contact"

    def has_web_presence_display(self, obj):
        return "✅" if obj.has_web_presence else "—"
    has_web_presence_display.short_description = "Web"

    def created_at_display(self, obj):
        return localtime(obj.created_at).strftime("%Y-%m-%d") if obj.created_at else "—"
    created_at_display.short_description = "Créé le"

    # === Listes / filtres / recherche ==================================================
    list_display = (
        "nom",
        "type",
        "secteur_activite",
        "zip_code",
        "city",
        "default_centre",
        "siret",
        "type_employeur",
        "nb_formations",
        "nb_prospections",
        "nb_appairages",
        "contact_display",
        "has_web_presence_display",
        "created_at_display",
    )

    list_filter = (
        "type",
        "secteur_activite",
        "city",
        "actions",
        "type_employeur",
        "assurance_chomage_speciale",
        "default_centre",
        "created_at",
    )

    search_fields = (
        "nom",
        "secteur_activite",
        "contact_nom",
        "contact_email",
        "contact_telephone",
        "email",
        "siret",
        "city",
        "code_ape",
        "idcc",
        "maitre1_nom_naissance",
        "maitre2_nom_naissance",
        "default_centre__nom",
    )

    ordering = ("nom",)
    actions = ["exporter_selection"]

    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    raw_id_fields = ("default_centre", "created_by", "updated_by")

    # === Organisation par sections (fieldsets) =========================================
    fieldsets = (
        ("🏷️ Informations générales", {
            "fields": ("type", "nom", "secteur_activite", "description", "actions", "action_description"),
        }),
        ("🏫 Centre", {
            "fields": ("default_centre",),
        }),
        ("📍 Localisation", {
            "fields": (
                "street_number", "street_name", "street_complement",
                "zip_code", "city", "country"
            ),
        }),
        ("📞 Coordonnées générales", {
            "fields": ("telephone", "email"),
        }),
        ("👤 Contact principal", {
            "fields": ("contact_nom", "contact_poste", "contact_email", "contact_telephone"),
        }),
        ("🌐 Web & Réseaux sociaux", {
            "fields": ("website", "social_network_url"),
        }),
        ("🏢 Données employeur", {
            "fields": (
                "siret",
                "type_employeur",
                "employeur_specifique",
                "code_ape",
                "effectif_total",
                "idcc",
                "assurance_chomage_speciale",
            ),
        }),
        ("🎓 Maître d’apprentissage n°1", {
            "fields": (
                "maitre1_nom_naissance", "maitre1_prenom", "maitre1_date_naissance",
                "maitre1_courriel", "maitre1_emploi_occupe",
                "maitre1_diplome_titre", "maitre1_niveau_diplome",
            ),
        }),
        ("🎓 Maître d’apprentissage n°2", {
            "fields": (
                "maitre2_nom_naissance", "maitre2_prenom", "maitre2_date_naissance",
                "maitre2_courriel", "maitre2_emploi_occupe",
                "maitre2_diplome_titre", "maitre2_niveau_diplome",
            ),
        }),
        ("🧾 Suivi", {
            "fields": ("created_by", "created_at", "updated_by", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # === Optimisations ================================================================
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("default_centre", "created_by", "updated_by")

    # === Export CSV ===================================================================
    @admin.action(description="📥 Exporter les partenaires sélectionnés (CSV)")
    def exporter_selection(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=partenaires.csv"

        writer = csv.writer(response)
        writer.writerow([
            "ID", "Nom", "Type", "Secteur", "SIRET", "Type employeur",
            "Code APE", "Effectif", "IDCC", "Ville", "CP", "Centre",
            "Téléphone", "Email", "Contact", "Web",
            "Maitre1 Nom", "Maitre1 Prénom", "Maitre1 Courriel",
            "Maitre2 Nom", "Maitre2 Prénom", "Maitre2 Courriel",
            "Prospections", "Formations", "Appairages",
            "Créé le", "Créé par",
        ])

        for p in queryset:
            writer.writerow([
                p.pk, p.nom, p.get_type_display(), p.secteur_activite or "",
                p.siret or "", p.get_type_employeur_display() if p.type_employeur else "",
                p.code_ape or "", p.effectif_total or "", p.idcc or "",
                p.city or "", p.zip_code or "", getattr(p.default_centre, "nom", "") or "",
                p.telephone or "", p.email or "", p.contact_info or "",
                p.website or "",
                p.maitre1_nom_naissance or "", p.maitre1_prenom or "", p.maitre1_courriel or "",
                p.maitre2_nom_naissance or "", p.maitre2_prenom or "", p.maitre2_courriel or "",
                p.nb_prospections, p.nb_formations, p.nb_appairages,
                localtime(p.created_at).strftime("%d/%m/%Y") if p.created_at else "",
                getattr(p.created_by, "username", ""),
            ])
        return response

    # === Sauvegarde enrichie ==========================================================
    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)
