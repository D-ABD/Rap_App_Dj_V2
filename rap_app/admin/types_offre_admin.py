from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from ..models.types_offre import TypeOffre


@admin.register(TypeOffre)
class TypeOffreAdmin(admin.ModelAdmin):
    """
    🧾 Admin avancé pour les types d'offre.
    """

    list_display = (
        "badge_affichage",
        "nom",
        "autre",
        "couleur",
        "is_active",  # 👈 Ajout ici
        "get_formations_count",
        "created_at",
        "updated_at",
        "created_by_display",
    )
    list_filter = ("nom", "is_active", "created_at", "updated_at")  # 👈 Ajout ici
    search_fields = ("nom", "autre", "couleur")
    ordering = ("nom",)
    date_hierarchy = "created_at"

    readonly_fields = (
        "created_at",
        "updated_at",
        "badge_preview",
        "created_by",
    )

    fieldsets = (
        (_("Informations générales"), {
            "fields": ("nom", "autre", "couleur", "is_active", "badge_preview"),  # 👈 Ajout ici
        }),
        (_("🧾 Métadonnées"), {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("created_by").prefetch_related("formations")

    def badge_affichage(self, obj):
        return format_html(obj.get_badge_html())
    badge_affichage.short_description = _("Aperçu")

    def badge_preview(self, obj):
        if obj.pk:
            return format_html(obj.get_badge_html())
        return _("Le badge sera affiché après enregistrement.")
    badge_preview.short_description = _("Aperçu du badge")

    def get_formations_count(self, obj):
        return obj.get_formations_count()
    get_formations_count.short_description = _("Nb formations")
    get_formations_count.admin_order_field = "formations"

    def created_by_display(self, obj):
        return str(obj.created_by) if obj.created_by else "—"
    created_by_display.short_description = _("Créé par")

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
