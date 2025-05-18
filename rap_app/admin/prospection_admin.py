from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import now
from ..models.prospection import Prospection, HistoriqueProspection


class HistoriqueProspectionInline(admin.TabularInline):
    model = HistoriqueProspection
    extra = 0
    can_delete = False
    show_change_link = False

    readonly_fields = (
        "date_modification",
        "ancien_statut",
        "nouveau_statut",
        "type_contact",
        "commentaire",
        "resultat",
        "prochain_contact",
        "moyen_contact",
        "created_by",
    )

    verbose_name = "Historique"
    verbose_name_plural = "Historique de prospection"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Prospection)
class ProspectionAdmin(admin.ModelAdmin):
    """
    📞 Admin pour la gestion des prospections.
    """

    list_display = (
        "id",
        "partenaire",
        "formation",
        "statut_colore",
        "objectif",
        "motif",
        "type_contact",
        "date_prospection",
        "prochain_contact_affiche",
        "created_by",
    )
    list_filter = (
        "statut",
        "objectif",
        "motif",
        "type_contact",
        ("date_prospection", admin.DateFieldListFilter),
    )
    search_fields = (
        "partenaire__nom",
        "formation__nom",
        "commentaire",
    )
    ordering = ("-date_prospection",)
    autocomplete_fields = ("partenaire", "formation")
    inlines = [HistoriqueProspectionInline]

    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )

    fieldsets = (
        (None, {
            "fields": (
                "partenaire",
                "formation",
                ("date_prospection", "type_contact"),
                ("statut", "objectif", "motif"),
                "commentaire",
            ),
        }),
        ("🧾 Suivi & Métadonnées", {
            "fields": ("created_at", "updated_at", "created_by", "updated_by"),
            "classes": ("collapse",),
        }),
    )

    def statut_colore(self, obj):
        if obj.historiques.exists():
            label, icone, classe = obj.historiques.last().statut_avec_icone
        else:
            label, icone, classe = obj.get_statut_display(), "", ""
        return format_html('<i class="{} {}"></i> {}', icone, classe, label)
    statut_colore.short_description = "Statut"

    def prochain_contact_affiche(self, obj):
        if obj.prochain_contact:
            couleur = "red" if obj.relance_necessaire else "green"
            return format_html(
                '<span style="color:{};">{}</span>',
                couleur,
                obj.prochain_contact.strftime("%d/%m/%Y"),
            )
        return "—"
    prochain_contact_affiche.short_description = "Prochain contact"

    def changelist_view(self, request, extra_context=None):
        stats = Prospection.custom.statistiques_par_statut()
        extra_context = extra_context or {}
        extra_context["statistiques_par_statut"] = stats
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(HistoriqueProspection)
class HistoriqueProspectionAdmin(admin.ModelAdmin):
    """
    📈 Admin en lecture seule pour l’historique des prospections.
    """

    list_display = (
        "id",
        "prospection",
        "date_modification",
        "ancien_statut",
        "nouveau_statut",
        "type_contact",
        "prochain_contact",
        "created_by",
    )
    list_filter = (
        "nouveau_statut",
        "type_contact",
        "moyen_contact",
        ("date_modification", admin.DateFieldListFilter),
        ("prochain_contact", admin.DateFieldListFilter),
    )
    search_fields = (
        "prospection__partenaire__nom",
        "commentaire",
        "resultat",
    )
    ordering = ("-date_modification",)
    autocomplete_fields = ("prospection",)

    readonly_fields = (
        "prospection",
        "ancien_statut",
        "nouveau_statut",
        "type_contact",
        "commentaire",
        "resultat",
        "prochain_contact",
        "moyen_contact",
        "date_modification",
        "created_by",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
