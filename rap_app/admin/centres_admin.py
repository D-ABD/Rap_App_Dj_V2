import logging
from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q

from ..models.centres import Centre


logger = logging.getLogger("application.centres")


# ───────────────────────────────────────────────
# ADMIN : CENTRE
# ───────────────────────────────────────────────
@admin.register(Centre)
class CentreAdmin(admin.ModelAdmin):
    """Administration complète des centres de formation."""

    date_hierarchy = "created_at"
    ordering = ("nom",)
    list_per_page = 50

    # ───────────────────────────────
    # Affichage liste
    # ───────────────────────────────
    list_display = (
        "id",
        "nom",
        "code_postal",
        "commune",
        "cfa_entreprise",
        "nb_prepa",
        "created_by",
        "created_at",
    )
    list_filter = (
        "cfa_entreprise",
        ("code_postal", admin.AllValuesFieldListFilter),
        ("created_at", admin.DateFieldListFilter),
    )
    search_fields = ("nom", "code_postal", "commune", "siret_centre", "numero_uai_centre")

    # ───────────────────────────────
    # Champs détaillés
    # ───────────────────────────────
    readonly_fields = (
        "id",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
        "nb_prepa_display",
    )

    fieldsets = (
        (_("Informations principales"), {
            "fields": (
                "nom",
                "cfa_entreprise",
                "numero_voie",
                "nom_voie",
                "complement_adresse",
                "code_postal",
                "commune",
            )
        }),
        (_("Informations administratives"), {
            "fields": (
                "numero_uai_centre",
                "siret_centre",
            )
        }),
        (_("CFA responsable"), {
            "fields": (
                "cfa_responsable_est_lieu_principal",
                "cfa_responsable_denomination",
                "cfa_responsable_uai",
                "cfa_responsable_siret",
                "cfa_responsable_numero",
                "cfa_responsable_voie",
                "cfa_responsable_complement",
                "cfa_responsable_code_postal",
                "cfa_responsable_commune",
            ),
            "classes": ("collapse",),
        }),
        (_("Statistiques"), {
            "fields": ("nb_prepa_display",),
        }),
        (_("Métadonnées"), {
            "fields": (
                "created_by",
                "created_at",
                "updated_by",
                "updated_at",
            )
        }),
    )

    # ───────────────────────────────
    # Helpers d’affichage
    # ───────────────────────────────


    # ───────────────────────────────
    # Queryset optimisé
    # ───────────────────────────────
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("created_by", "updated_by").annotate(prepa_count=Count("prepa_globaux", distinct=True))

    # ───────────────────────────────
    # Sauvegarde avec traçabilité
    # ───────────────────────────────
    def save_model(self, request, obj, form, change):
        """Enregistre le centre avec log + user injecté."""
        obj.save(user=request.user)
        logger.info("🏫 Centre #%s sauvegardé (%s) par %s", obj.pk, obj.nom, request.user)

    def delete_model(self, request, obj):
        """Suppression avec journalisation."""
        logger.warning("❌ Suppression du centre #%s (%s) par %s", obj.pk, obj.nom, request.user)
        super().delete_model(request, obj)

    # ───────────────────────────────
    # Actions de masse
    # ───────────────────────────────
    @admin.action(description="🟢 Exporter la sélection en CSV (fichier local)")
    def act_export_csv(self, request, queryset):
        """Export CSV rapide depuis admin."""
        import csv
        from io import StringIO
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(Centre.get_csv_headers())
        for centre in queryset:
            writer.writerow(centre.to_csv_row())

        buffer.seek(0)
        response = admin.utils.stream_response(buffer, filename="centres_export.csv")
        return response

    @admin.action(description="♻️ Rafraîchir les caches (nb_prepa_comp_global)")
    def act_refresh_caches(self, request, queryset):
        count = 0
        for centre in queryset:
            centre.invalidate_caches()
            count += 1
        self.message_user(
            request,
            _(f"{count} cache(s) invalidé(s) avec succès."),
            level=messages.SUCCESS,
        )

    actions = ("act_export_csv", "act_refresh_caches")
