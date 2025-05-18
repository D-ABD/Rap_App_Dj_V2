from django.contrib import admin
from django.utils.html import format_html
from ..models.formations import Formation


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    """
    📚 Admin avancé pour la gestion des formations.
    """

    list_display = (
        "id",
        "nom",
        "centre_nom",
        "type_offre_nom",
        "statut_colored",
        "start_date_display",
        "end_date_display",
        "total_places",
        "total_inscrits",
        "places_disponibles",
        "taux_saturation_display",
        "status_temporel_badge",
    )
    list_filter = (
        "centre",
        "type_offre",
        "statut",
        "start_date",
        "end_date",
    )
    search_fields = (
        "nom",
        "num_kairos",
        "num_offre",
        "num_produit",
        "assistante",
    )
    ordering = ("-start_date",)
    date_hierarchy = "start_date"
    actions = ["dupliquer_formations"]

    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )

    fieldsets = (
        ("📘 Informations générales", {
            "fields": ("nom", "centre", "type_offre", "statut", "assistante"),
        }),
        ("📅 Dates & Références", {
            "fields": ("start_date", "end_date", "num_kairos", "num_offre", "num_produit"),
        }),
        ("📊 Capacités & Inscriptions", {
            "fields": (
                "prevus_crif", "prevus_mp",
                "inscrits_crif", "inscrits_mp",
                "cap", "convocation_envoie", "entree_formation",
            ),
        }),
        ("👥 Statistiques & Commentaires", {
            "fields": (
                "nombre_candidats", "nombre_entretiens", "nombre_evenements",
                "dernier_commentaire", "saturation",
            ),
        }),
        ("🔗 Partenaires", {
            "fields": ("partenaires",),
        }),
        ("🧾 Suivi & Métadonnées", {
            "fields": ("created_by", "created_at", "updated_by", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # ==== Champs calculés ====

    def centre_nom(self, obj):
        return obj.centre.nom if obj.centre else "—"
    centre_nom.short_description = "Centre"

    def type_offre_nom(self, obj):
        return obj.type_offre.nom if obj.type_offre else "—"
    type_offre_nom.short_description = "Type d’offre"

    def statut_colored(self, obj):
        label = obj.statut.nom if obj.statut else "—"
        color = obj.get_status_color()
        return format_html('<span style="color: {};">{}</span>', color, label)
    statut_colored.short_description = "Statut"

    def start_date_display(self, obj):
        return obj.start_date.strftime("%d/%m/%Y") if obj.start_date else "—"
    start_date_display.short_description = "Début"

    def end_date_display(self, obj):
        return obj.end_date.strftime("%d/%m/%Y") if obj.end_date else "—"
    end_date_display.short_description = "Fin"

    def taux_saturation_display(self, obj):
        return f"{obj.taux_saturation:.1f} %" if obj.total_places else "—"
    taux_saturation_display.short_description = "Saturation"

    def status_temporel_badge(self, obj):
        label = obj.status_temporel.capitalize()
        css_class = {
            "active": "badge-success",
            "future": "badge-primary",
            "past": "badge-secondary",
            "unknown": "badge-light",
        }.get(obj.status_temporel, "badge-light")
        return format_html('<span class="badge {}">{}</span>', css_class, label)
    status_temporel_badge.short_description = "État"

    # ==== Actions personnalisées ====

    @admin.action(description="📄 Dupliquer les formations sélectionnées")
    def dupliquer_formations(self, request, queryset):
        count = 0
        for formation in queryset:
            formation.duplicate(user=request.user)
            count += 1
        self.message_user(request, f"{count} formation(s) dupliquée(s).")

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
