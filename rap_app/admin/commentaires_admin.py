import logging
import csv
from io import StringIO
from django.contrib import admin, messages
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse

from ..models.commentaires import Commentaire

logger = logging.getLogger("application.commentaires")


@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    """
    💬 Administration complète des commentaires de formation.
    Gère : affichage, archivage logique, export CSV, traçabilité.
    """

    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 50

    # ───────────────────────────────
    # Liste principale
    # ───────────────────────────────
    list_display = (
        "id",
        "formation_nom",
        "auteur_nom",
        "short_contenu",
        "saturation",
        "statut_commentaire",
        "created_at_display",
        "updated_at_display",
    )
    list_filter = (
        "statut_commentaire",
        "formation",
        ("created_at", admin.DateFieldListFilter),
        ("updated_at", admin.DateFieldListFilter),
    )
    search_fields = (
        "contenu",
        "formation__nom",
        "created_by__username",
        "created_by__first_name",
        "created_by__last_name",
    )

    readonly_fields = (
        "id",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
    )

    fieldsets = (
        ("💬 Commentaire", {
            "fields": ("formation", "contenu", "saturation", "statut_commentaire"),
        }),
        ("🧾 Suivi", {
            "fields": ("created_by", "created_at", "updated_by", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # ───────────────────────────────
    # Helpers d’affichage
    # ───────────────────────────────
    def auteur_nom(self, obj):
        return obj.auteur_nom
    auteur_nom.short_description = _("Auteur")

    def formation_nom(self, obj):
        return obj.formation_nom
    formation_nom.short_description = _("Formation")

    def short_contenu(self, obj):
        return obj.get_content_preview(50)
    short_contenu.short_description = _("Aperçu")

    def created_at_display(self, obj):
        return localtime(obj.created_at).strftime("%d/%m/%Y %H:%M") if obj.created_at else "-"
    created_at_display.short_description = _("Créé le")

    def updated_at_display(self, obj):
        return localtime(obj.updated_at).strftime("%d/%m/%Y %H:%M") if obj.updated_at else "-"
    updated_at_display.short_description = _("Modifié le")

    # ───────────────────────────────
    # Queryset optimisé
    # ───────────────────────────────
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("formation", "created_by", "updated_by")

    # ───────────────────────────────
    # Sauvegarde avec traçabilité
    # ───────────────────────────────
    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by:
            obj.created_by = request.user
        obj.save(user=request.user)
        logger.info("💬 Commentaire #%s sauvegardé par %s", obj.pk, request.user)

    # ───────────────────────────────
    # Actions de masse
    # ───────────────────────────────
    @admin.action(description="📦 Archiver les commentaires sélectionnés")
    def act_archiver(self, request, queryset):
        count = 0
        for c in queryset:
            if not c.est_archive:
                c.archiver(user=request.user)
                count += 1
        self.message_user(request, f"{count} commentaire(s) archivé(s).", level=messages.SUCCESS)

    @admin.action(description="♻️ Restaurer les commentaires archivés")
    def act_desarchiver(self, request, queryset):
        count = 0
        for c in queryset:
            if c.est_archive:
                c.desarchiver()
                count += 1
        self.message_user(request, f"{count} commentaire(s) restauré(s).", level=messages.SUCCESS)

    @admin.action(description="📤 Exporter la sélection en CSV")
    def act_export_csv(self, request, queryset):
        """Export CSV simple et lisible directement depuis l’admin."""
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            "ID", "Formation", "Auteur", "Contenu", "Saturation", "Statut", "Créé le", "Modifié le"
        ])
        for c in queryset:
            writer.writerow([
                c.pk,
                c.formation_nom,
                c.auteur_nom,
                c.contenu_sans_html.replace("\n", " ")[:200],
                c.saturation or "",
                c.statut_commentaire,
                c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else "",
                c.updated_at.strftime("%Y-%m-%d %H:%M") if c.updated_at else "",
            ])
        buffer.seek(0)
        response = HttpResponse(buffer, content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=commentaires_export.csv"
        logger.info("📤 Export CSV (%s lignes) par %s", queryset.count(), request.user)
        return response

    actions = ("act_archiver", "act_desarchiver", "act_export_csv")
