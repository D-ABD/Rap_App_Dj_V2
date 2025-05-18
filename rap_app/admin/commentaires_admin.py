from django.contrib import admin
from django.utils.timezone import localtime
from ..models.commentaires import Commentaire


@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    """
    💬 Admin avancé pour la gestion des commentaires.
    """

    list_display = (
        "id",
        "auteur_nom_display",
        "formation_nom_display",
        "short_contenu",
        "saturation",
        "is_active",
        "created_at_display",
        "updated_at_display",
    )
    list_filter = (
        "is_active",
        "formation",
        "saturation",
        "created_at",
    )
    search_fields = (
        "contenu",
        "created_by__username",
        "created_by__first_name",
        "created_by__last_name",
        "formation__nom",
    )
    ordering = ("-created_at",)
    actions = ["activer_commentaires", "desactiver_commentaires"]

    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )

    fieldsets = (
        ("💬 Contenu du commentaire", {
            "fields": ("formation", "contenu", "saturation", "is_active"),
        }),
        ("🧾 Suivi & Métadonnées", {
            "fields": ("created_at", "updated_at", "created_by", "updated_by"),
            "classes": ("collapse",),
        }),
    )

    def auteur_nom_display(self, obj):
        return obj.auteur_nom
    auteur_nom_display.short_description = "Auteur"

    def formation_nom_display(self, obj):
        return obj.formation.nom
    formation_nom_display.short_description = "Formation"

    def short_contenu(self, obj):
        return obj.get_content_preview(40)
    short_contenu.short_description = "Aperçu"

    def created_at_display(self, obj):
        return localtime(obj.created_at).strftime("%Y-%m-%d %H:%M")
    created_at_display.short_description = "Créé le"

    def updated_at_display(self, obj):
        return localtime(obj.updated_at).strftime("%Y-%m-%d %H:%M")
    updated_at_display.short_description = "Modifié le"

    @admin.action(description="✅ Réactiver les commentaires sélectionnés")
    def activer_commentaires(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} commentaire(s) activé(s).")

    @admin.action(description="🚫 Désactiver les commentaires sélectionnés")
    def desactiver_commentaires(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} commentaire(s) désactivé(s).")

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
