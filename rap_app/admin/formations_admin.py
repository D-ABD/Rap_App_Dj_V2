import logging
from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from ..models.formations import Formation

logger = logging.getLogger("application.formation")


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    """
    📚 Administration complète et homogène des formations.
    Inclut affichage enrichi, filtres pertinents, actions groupées et audit.
    """

    model = Formation

    # ───────────────────────────────
    # Liste principale
    # ───────────────────────────────
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
        "saturation_display",
        "status_temporel_badge",
        "activite_badge",
    )
    list_filter = (
        "centre",
        "type_offre",
        "statut",
        "convocation_envoie",
        "entree_formation",
        "start_date",
        "end_date",
        "activite",
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
    list_per_page = 50

    # ───────────────────────────────
    # Champs en lecture seule
    # ───────────────────────────────
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "saturation",
        "total_places",
        "total_inscrits",
        "places_disponibles",
        "taux_saturation",
    )

    # ───────────────────────────────
    # Actions personnalisées
    # ───────────────────────────────
    actions = [
        "dupliquer_formations",
        "archiver_selection",
        "restaurer_selection",
    ]

    # ───────────────────────────────
    # Organisation du formulaire
    # ───────────────────────────────
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
                "total_places", "total_inscrits", "places_disponibles", "taux_saturation",
            ),
        }),
        ("🎓 Diplôme & Durée", {
            "fields": (
                "intitule_diplome", "code_diplome", "code_rncp",
                "total_heures", "heures_distanciel",
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
            "fields": ("activite", "created_by", "created_at", "updated_by", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # ───────────────────────────────
    # Méthodes d’affichage lisibles
    # ───────────────────────────────
    def centre_nom(self, obj):
        return obj.centre.nom if obj.centre else "—"
    centre_nom.short_description = "Centre"

    def type_offre_nom(self, obj):
        return obj.type_offre.nom if obj.type_offre else "—"
    type_offre_nom.short_description = "Type d’offre"

    def statut_colored(self, obj):
        if not obj.statut:
            return "—"
        color = obj.get_status_color()
        return format_html('<b style="color:{};">{}</b>', color, obj.statut.nom)
    statut_colored.short_description = "Statut"

    def start_date_display(self, obj):
        return obj.start_date.strftime("%d/%m/%Y") if obj.start_date else "—"
    start_date_display.short_description = "Début"

    def end_date_display(self, obj):
        return obj.end_date.strftime("%d/%m/%Y") if obj.end_date else "—"
    end_date_display.short_description = "Fin"

    def taux_saturation_display(self, obj):
        if obj.total_places == 0:
            return "—"
        val = obj.taux_saturation or 0
        color = (
            "#dc3545" if val >= 90 else
            "#fd7e14" if val >= 70 else
            "#ffc107" if val >= 50 else
            "#28a745"
        )
        return format_html("<b style='color:{}'>{:.1f}%</b>", color, val)
    taux_saturation_display.short_description = "Taux occ."

    def saturation_display(self, obj):
        if obj.saturation is None:
            return "—"
        val = obj.saturation
        color = (
            "#dc3545" if val >= 90 else
            "#fd7e14" if val >= 70 else
            "#ffc107" if val >= 50 else
            "#28a745"
        )
        return format_html("<b style='color:{}'>{:.1f}%</b>", color, val)
    saturation_display.short_description = "Saturation"

    def status_temporel_badge(self, obj):
        mapping = {
            "active": ("🟢", "En cours"),
            "future": ("🔵", "À venir"),
            "past": ("⚪", "Terminée"),
            "unknown": ("⚫", "Inconnue"),
        }
        icon, label = mapping.get(obj.status_temporel, ("⚫", "Inconnue"))
        return format_html("<span title='{}'>{}</span>", label, icon)
    status_temporel_badge.short_description = "État"

    def activite_badge(self, obj):
        if obj.est_archivee:
            return format_html('<span style="color:#999;">🗃️ Archivée</span>')
        return format_html('<span style="color:#28a745;">✅ Active</span>')
    activite_badge.short_description = "Activité"

    # ───────────────────────────────
    # Actions personnalisées
    # ───────────────────────────────
    @admin.action(description="📄 Dupliquer les formations sélectionnées")
    def dupliquer_formations(self, request, queryset):
        count = 0
        for formation in queryset:
            formation.duplicate(user=request.user)
            count += 1
        self.message_user(request, f"{count} formation(s) dupliquée(s).", messages.SUCCESS)
        logger.info("[Admin] %s formation(s) dupliquée(s) par %s", count, request.user)

    @admin.action(description="🗃️ Archiver les formations sélectionnées")
    def archiver_selection(self, request, queryset):
        total, deja = 0, 0
        for f in queryset:
            if f.est_archivee:
                deja += 1
            else:
                f.archiver(user=request.user)
                total += 1
        msg = f"{total} formation(s) archivée(s)."
        if deja:
            msg += f" ({deja} déjà archivées ignorées)"
        self.message_user(request, msg, messages.WARNING)
        logger.info("[Admin] %s formation(s) archivées (%s ignorées) par %s", total, deja, request.user)

    @admin.action(description="🔁 Restaurer les formations archivées")
    def restaurer_selection(self, request, queryset):
        total, actives = 0, 0
        for f in queryset:
            if f.est_archivee:
                f.desarchiver(user=request.user)
                total += 1
            else:
                actives += 1
        msg = f"{total} formation(s) restaurée(s)."
        if actives:
            msg += f" ({actives} déjà actives ignorées)"
        self.message_user(request, msg, messages.SUCCESS)
        logger.info("[Admin] %s formation(s) restaurées (%s actives ignorées) par %s", total, actives, request.user)

    # ───────────────────────────────
    # Audit : auteur auto
    # ───────────────────────────────
    def save_model(self, request, obj, form, change):
        """Assure la traçabilité de création/modification."""
        if not change and not obj.created_by:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
        action = "créée" if not change else "modifiée"
        logger.info("[Admin] Formation %s : %s par %s", action, obj.nom, request.user)
