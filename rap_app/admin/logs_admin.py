from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import localtime
from ..models.logs import LogUtilisateur


@admin.register(LogUtilisateur)
class LogUtilisateurAdmin(admin.ModelAdmin):
    """
    🧾 Admin pour les logs utilisateurs — consultation, export, audit rapide.
    """

    list_display = (
        "id",
        "action",
        "model_display",
        "object_link",
        "user_display",
        "created_at_display",
    )
    list_filter = (
        "action",
        "content_type",
        "created_at",
    )
    search_fields = (
        "details",
        "created_by__username",
        "created_by__email",
        "object_id",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "content_type",
        "object_id",
        "action",
        "details",
        "created_by",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("📝 Détail du log", {
            "fields": (
                "content_type",
                "object_id",
                "action",
                "details",
            ),
        }),
        ("👤 Utilisateur", {
            "fields": (
                "created_by",
                "created_at",
                "updated_at",
            ),
            "classes": ("collapse",),
        }),
    )

    # ==== Champs calculés / affichage ====

    def created_at_display(self, obj):
        return localtime(obj.created_at).strftime("%Y-%m-%d %H:%M")
    created_at_display.short_description = "Date"

    def model_display(self, obj):
        return obj.content_type.model_class().__name__ if obj.content_type else "—"
    model_display.short_description = "Modèle"

    def object_link(self, obj):
        if obj.content_object and hasattr(obj.content_object, "get_admin_url"):
            return format_html(
                '<a href="{}">#{} ({})</a>',
                obj.content_object.get_admin_url(),
                obj.object_id,
                obj.content_type.model,
            )
        return f"#{obj.object_id}" if obj.object_id else "—"
    object_link.short_description = "Objet"

    def user_display(self, obj):
        if obj.created_by:
            return f"{obj.created_by.get_full_name()} ({obj.created_by.username})"
        return "Système"
    user_display.short_description = "Utilisateur"

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
