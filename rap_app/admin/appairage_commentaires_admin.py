import logging
from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

from ..models.commentaires_appairage import CommentaireAppairage

logger = logging.getLogger("application.commentaires_appairage")


# ───────────────────────────────────────────────
# Inline pour affichage dans AppairageAdmin
# ───────────────────────────────────────────────
class CommentaireAppairageInline(admin.TabularInline):
    model = CommentaireAppairage
    extra = 0
    can_delete = False
    readonly_fields = ("created_at", "created_by", "statut_snapshot")
    fields = ("body", "statut_snapshot", "created_by", "created_at")
    ordering = ("-created_at",)
    verbose_name = _("Commentaire")
    verbose_name_plural = _("Commentaires d’appairage")

    def has_add_permission(self, request, obj=None):
        """Empêche la création directe via l’inline (lecture seule)."""
        return False


# ───────────────────────────────────────────────
# Admin principal : CommentaireAppairage
# ───────────────────────────────────────────────
@admin.register(CommentaireAppairage)
class CommentaireAppairageAdmin(admin.ModelAdmin):
    """Interface d’administration complète des commentaires d’appairage."""

    date_hierarchy = "created_at"
    ordering = ("-created_at", "-id")

    list_display = (
        "id",
        "appairage",
        "auteur_nom",
        "short_body",
        "statut_snapshot",
        "statut_commentaire",
        "created_at",
    )
    list_filter = (
        "statut_commentaire",
        "statut_snapshot",
        ("created_at", admin.DateFieldListFilter),
        "created_by",
    )
    search_fields = (
        "body",
        "created_by__username",
        "created_by__first_name",
        "created_by__last_name",
        "appairage__id",
        "appairage__candidat__nom",
        "appairage__partenaire__nom",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "statut_snapshot",
    )

    fieldsets = (
        (_("Commentaire"), {"fields": ("appairage", "body", "statut_snapshot")}),
        (_("Statut"), {"fields": ("statut_commentaire",)}),
        (
            _("Métadonnées"),
            {"fields": ("created_by", "updated_by", "created_at", "updated_at")},
        ),
    )

    raw_id_fields = ("appairage", "created_by", "updated_by")

    # ───────────────────────────────
    # Méthodes d’affichage
    # ───────────────────────────────
    def auteur_nom(self, obj):
        return obj.auteur_nom()
    auteur_nom.short_description = _("Auteur")

    def short_body(self, obj):
        """Aperçu raccourci du texte."""
        if not obj.body:
            return "-"
        return (obj.body[:70] + "…") if len(obj.body) > 70 else obj.body
    short_body.short_description = _("Aperçu")

    # ───────────────────────────────
    # Optimisation du queryset
    # ───────────────────────────────
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("appairage", "created_by", "updated_by")

    # ───────────────────────────────
    # Sauvegarde avec traçabilité
    # ───────────────────────────────
    def save_model(self, request, obj, form, change):
        """Sauvegarde en associant automatiquement l’utilisateur."""
        obj.save(user=request.user)
        logger.info("💬 CommentaireAppairage #%s enregistré par %s", obj.pk, request.user)

    def save_formset(self, request, form, formset, change):
        """Applique save(user=request.user) sur les inlines éventuels."""
        instances = formset.save(commit=False)
        for inst in instances:
            try:
                inst.save(user=request.user)
            except TypeError:
                inst.save()
        formset.save_m2m()

    # ───────────────────────────────
    # Actions de masse : archivage
    # ───────────────────────────────
    @admin.action(description="📦 Archiver les commentaires sélectionnés")
    def act_archiver(self, request, queryset):
        updated = 0
        for c in queryset:
            if not c.est_archive:
                c.archiver(save=True)
                updated += 1
        if updated:
            self.message_user(
                request,
                _(f"{updated} commentaire(s) archivé(s)."),
                level=messages.SUCCESS,
            )
        else:
            self.message_user(request, _("Aucun commentaire à archiver."), level=messages.INFO)

    @admin.action(description="♻️ Désarchiver les commentaires sélectionnés")
    def act_desarchiver(self, request, queryset):
        updated = 0
        for c in queryset:
            if c.est_archive:
                c.desarchiver(save=True)
                updated += 1
        if updated:
            self.message_user(
                request,
                _(f"{updated} commentaire(s) désarchivé(s)."),
                level=messages.SUCCESS,
            )
        else:
            self.message_user(request, _("Aucun commentaire à désarchiver."), level=messages.INFO)

    # Liste des actions
    actions = ("act_archiver", "act_desarchiver")
