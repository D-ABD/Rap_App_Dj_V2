# rap_app/admin/partenaire_admin.py
from django.contrib import admin
from django.utils.timezone import localtime
from django.http import HttpResponse
import csv

from ..models.partenaires import Partenaire


@admin.register(Partenaire)
class PartenaireAdmin(admin.ModelAdmin):
    """
    🏢 Interface d'administration avancée pour les partenaires.
    """

    # === Affichages custom / compteurs =================================================

    @admin.display(description="Appairages")
    def nb_appairages(self, obj):
        return obj.nb_appairages

    def contact_display(self, obj):
        return obj.contact_info or "—"
    contact_display.short_description = "Contact"

    def has_web_presence_display(self, obj):
        return "✅" if obj.has_web_presence else "—"
    has_web_presence_display.short_description = "Web"

    def nb_prospections(self, obj):
        return obj.get_prospections_info()["count"]
    nb_prospections.short_description = "Prospections"

    def nb_formations(self, obj):
        return obj.get_formations_info()["count"]
    nb_formations.short_description = "Formations"

    def created_at_display(self, obj):
        return localtime(obj.created_at).strftime("%Y-%m-%d") if obj.created_at else "—"
    created_at_display.short_description = "Créé le"

    # === Listes / filtres / recherche ==================================================

    list_display = (
        "nom",
        "type",
        "secteur_activite",
        "default_centre",       # ✅ nouveau : centre par défaut visible
        "zip_code",
        "contact_display",
        "has_web_presence_display",
        "nb_formations",
        "nb_prospections",
        "nb_appairages",
        "created_at_display",
    )

    list_filter = (
        "type",
        "secteur_activite",
        "city",
        "actions",
        "created_at",
        "default_centre",       # ✅ filtre par centre
    )

    search_fields = (
        "nom",
        "secteur_activite",
        "contact_nom",
        "contact_email",
        "contact_telephone",
        "city",
        "default_centre__nom",  # ✅ recherche par nom du centre
    )

    ordering = ("nom",)
    actions = ["exporter_selection"]

    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )

    # Si votre modèle Centre a beaucoup d’entrées, raw_id_fields évite le widget géant
    raw_id_fields = ("default_centre", "created_by", "updated_by")

    fieldsets = (
        ("🏷️ Informations générales", {
            "fields": ("type", "nom", "secteur_activite", "description"),
        }),
        ("🏫 Centre", {
            "fields": ("default_centre",),  # ✅ nouveau : rattachement par défaut
        }),
        ("📍 Localisation", {
            "fields": ("street_name", "zip_code", "city", "country"),
        }),
        ("📞 Contact", {
            "fields": ("contact_nom", "contact_poste", "contact_email", "contact_telephone"),
        }),
        ("🌐 Web & Réseaux sociaux", {
            "fields": ("website", "social_network_url"),
        }),
        ("🤝 Actions & Partenariat", {
            "fields": ("actions", "action_description"),
        }),
        ("🧾 Suivi", {
            "fields": ("created_by", "created_at", "updated_by", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # === Perf ==========================================================================

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # on précharge le centre et les users pour la liste
        return qs.select_related("default_centre", "created_by", "updated_by")

    # === Export CSV ====================================================================

    @admin.action(description="📥 Exporter les partenaires sélectionnés (CSV)")
    def exporter_selection(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=partenaires.csv"

        writer = csv.writer(response)
        writer.writerow([
            "ID", "Nom", "Type", "Secteur", "Ville", "Code postal",
            "Centre par défaut",           # ✅ nouvelle colonne
            "Contact", "Email", "Téléphone",
            "Site web", "Réseau",
            "Nombre prospections", "Nombre formations"
        ])

        for obj in queryset:
            writer.writerow([
                obj.pk,
                obj.nom,
                obj.get_type_display(),
                obj.secteur_activite or "",
                obj.city or "",
                obj.zip_code or "",
                getattr(obj.default_centre, "nom", "") or "",   # ✅ export centre
                obj.contact_nom or "",
                obj.contact_email or "",
                obj.contact_telephone or "",
                obj.website or "",
                obj.social_network_url or "",
                obj.get_prospections_info()["count"],
                obj.get_formations_info()["count"],
            ])

        return response

    # === Sauvegarde : propage l'user à BaseModel/Partenaire.save =======================

    def save_model(self, request, obj, form, change):
        # Laisse BaseModel/Partenaire.save gérer created_by/updated_by via user=
        obj.save(user=request.user)
