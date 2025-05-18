from django.contrib import admin
from django.db.models import Count
from django.utils.timezone import localtime
from ..models.centres import Centre


@admin.register(Centre)
class CentreAdmin(admin.ModelAdmin):
    """
    🛠️ Interface d'administration avancée pour le modèle Centre.
    """

    list_display = (
        "id",
        "nom",
        "code_postal",
        "is_active",
        "nb_prepa_display",
        "created_at_display",
        "updated_at_display",
        "created_by_display",
        "updated_by_display",
    )
    list_filter = ("is_active", "code_postal", "created_at", "updated_at")
    search_fields = ("nom", "code_postal")
    ordering = ("nom",)
    date_hierarchy = "created_at"
    actions = ["activer_centres", "desactiver_centres"]

    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "nb_prepa_display",
    )

    fieldsets = (
        ("📌 Informations générales", {
            "fields": ("nom", "code_postal", "is_active"),
        }),
        ("📊 Statistiques", {
            "fields": ("nb_prepa_display",),
            "classes": ("collapse",),
        }),
        ("🧾 Suivi & Métadonnées", {
            "fields": ("created_at", "updated_at", "created_by", "updated_by"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(prepa_count=Count("prepa_globaux"))

    def nb_prepa_display(self, obj):
        return obj.nb_prepa_comp_global
    nb_prepa_display.short_description = "Nb objectifs annuels"
    nb_prepa_display.admin_order_field = "prepa_count"

    def created_at_display(self, obj):
        return localtime(obj.created_at).strftime("%Y-%m-%d %H:%M")
    created_at_display.short_description = "Créé le"

    def updated_at_display(self, obj):
        return localtime(obj.updated_at).strftime("%Y-%m-%d %H:%M")
    updated_at_display.short_description = "Modifié le"

    def created_by_display(self, obj):
        return str(obj.created_by) if obj.created_by else "-"
    created_by_display.short_description = "Créé par"

    def updated_by_display(self, obj):
        return str(obj.updated_by) if obj.updated_by else "-"
    updated_by_display.short_description = "Modifié par"

    @admin.action(description="✅ Réactiver les centres sélectionnés")
    def activer_centres(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} centre(s) activé(s).")

    @admin.action(description="🚫 Désactiver les centres sélectionnés")
    def desactiver_centres(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} centre(s) désactivé(s).")

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
