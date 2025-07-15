from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.forms import HiddenInput  

from ..models.prospection import HistoriqueProspection, Prospection
from ..models.prospection_choices import ProspectionChoices


class HistoriqueProspectionInline(admin.TabularInline):
    model = HistoriqueProspection
    extra = 0
    can_delete = False
    show_change_link = True
    ordering = ("-date_modification",)
    verbose_name = _("Historique")
    verbose_name_plural = _("Historique de la prospection")

    # Ne pas inclure created_by / updated_by ici
    readonly_fields = (
        "date_modification",
        "ancien_statut",
        "nouveau_statut",
        "type_prospection",
        "resultat",
        "prochain_contact",
        "moyen_contact",
        "commentaire",
    )

    # Masque tous les champs non éditables
    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
@admin.action(description=_("Marquer comme à relancer"))
def marquer_a_relancer(modeladmin, request, queryset):
    updated = queryset.update(statut=ProspectionChoices.STATUT_A_RELANCER)
    modeladmin.message_user(request, f"{updated} prospections mises à relancer.")


@admin.register(HistoriqueProspection)
class HistoriqueProspectionAdmin(admin.ModelAdmin):
    list_display = (
        "id", "prospection",  "ancien_statut",
        "nouveau_statut", "type_prospection", "prochain_contact",
        "created_by", "est_recent", "relance_urgente"
    )
    list_filter = (
        "type_prospection", "ancien_statut", "nouveau_statut",
        "moyen_contact", "created_by"
    )
    search_fields = (
        "prospection__partenaire__nom", "commentaire", "resultat"
    )
    ordering = ("-date_modification",)
    date_hierarchy = "date_modification"
    list_per_page = 50
    autocomplete_fields = ("prospection",)

    readonly_fields = (
        "created_at", "updated_at", "updated_by", "created_by", 
    )

    fieldsets = (
        (_("Informations"), {
            "fields": (
                "prospection",  "ancien_statut", "nouveau_statut",
                "type_prospection", "moyen_contact", "resultat", "prochain_contact",
                "commentaire"
            )
        }),
        (_("Métadonnées"), {
            "classes": ("collapse",),
            "fields": ("created_by", "updated_by", "created_at", "updated_at")
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("prospection", "created_by")

    def save_model(self, request, obj, form, change):
        """Définit automatiquement le user qui modifie"""
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        """Masque les champs created_by et updated_by en admin"""
        form = super().get_form(request, obj, **kwargs)
        for field in ("created_by", "updated_by"):
            if field in form.base_fields:
                form.base_fields[field].widget = HiddenInput()  # ✅ Plus d'erreur ici
        return form


@admin.register(Prospection)
class ProspectionAdmin(admin.ModelAdmin):
    list_display = (
        "id", "partenaire_link", "formation_link", "statut_badge", "objectif",
        "type_prospection", "date_prospection", "created_by", "prochain_contact",
        "relance_necessaire", "is_active"
    )
    list_display_links = ("id", "partenaire_link", "formation_link")
    list_filter = (
        "statut", "objectif", "type_prospection", "motif", "created_by", "formation", "partenaire"
    )
    search_fields = ("partenaire__nom", "formation__nom", "commentaire")
    ordering = ("-date_prospection",)
    date_hierarchy = "date_prospection"
    list_per_page = 50
    autocomplete_fields = ("formation", "partenaire")
    actions = [marquer_a_relancer]
    inlines = [HistoriqueProspectionInline]

    # Champs en lecture seule (non modifiables)
    readonly_fields = (
        "created_at", "updated_at", "created_by", "updated_by", "prochain_contact"
    )

    # Champs affichés dans l’admin
    fieldsets = (
        (_("Informations principales"), {
            "fields": ("partenaire", "formation", "date_prospection", "type_prospection", "motif")
        }),
        (_("Statut et objectif"), {
            "fields": ("statut", "objectif")
        }),
        (_("Commentaire"), {
            "fields": ("commentaire",)
        }),
        (_("Suivi interne"), {
            "classes": ("collapse",),
            "fields": ("prochain_contact", "created_by", "updated_by", "created_at", "updated_at")
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("formation", "partenaire", "created_by")

    def save_model(self, request, obj, form, change):
        """Attribue automatiquement l'utilisateur en modification/création"""
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        """Cache les champs created_by / updated_by si présents dans le form"""
        form = super().get_form(request, obj, **kwargs)
        for field in ("created_by", "updated_by"):
            if field in form.base_fields:
                form.base_fields[field].widget = admin.widgets.AdminHiddenInput()
        return form

    def formation_link(self, obj):
        if obj.formation:
            return format_html('<a href="/admin/{}/{}/{}/change/">{}</a>',
                               obj.formation._meta.app_label,
                               obj.formation._meta.model_name,
                               obj.formation.id,
                               obj.formation.nom)
        return "-"
    formation_link.short_description = _("Formation")

    def partenaire_link(self, obj):
        return format_html('<a href="/admin/{}/{}/{}/change/">{}</a>',
                           obj.partenaire._meta.app_label,
                           obj.partenaire._meta.model_name,
                           obj.partenaire.id,
                           obj.partenaire.nom)
    partenaire_link.short_description = _("Partenaire")

    def statut_badge(self, obj):
        label = obj.get_statut_display()
        couleur = {
            ProspectionChoices.STATUT_A_FAIRE: "gray",
            ProspectionChoices.STATUT_EN_COURS: "blue",
            ProspectionChoices.STATUT_A_RELANCER: "orange",
            ProspectionChoices.STATUT_ACCEPTEE: "green",
            ProspectionChoices.STATUT_REFUSEE: "red",
            ProspectionChoices.STATUT_ANNULEE: "black",
            ProspectionChoices.STATUT_NON_RENSEIGNE: "lightgray",
        }.get(obj.statut, "lightgray")
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', couleur, label)
    statut_badge.short_description = _("Statut")
    statut_badge.admin_order_field = "statut"
