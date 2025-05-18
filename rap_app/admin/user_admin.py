from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.html import format_html
from django.utils.timezone import localtime
from ..models.custom_user import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(DjangoUserAdmin):
    """
    🛠️ Admin ultra complet pour le modèle CustomUser.
    """

    model = CustomUser

    list_display = (
        "id",
        "email",
        "full_name_display",
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
        "last_login_display",
        "date_joined_display",
    )
    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
    )
    search_fields = (
        "email",
        "username",
        "first_name",
        "last_name",
    )
    ordering = ("-date_joined",)

    readonly_fields = (
        "date_joined",
        "last_login",
        "avatar_preview",
    )

    fieldsets = (
        ("🧾 Informations de connexion", {
            "fields": ("email", "username", "password"),
        }),
        ("👤 Informations personnelles", {
            "fields": ("first_name", "last_name", "phone", "avatar", "avatar_preview", "bio"),
        }),
        ("🔐 Permissions", {
            "fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
        }),
        ("🕒 Dates importantes", {
            "fields": ("last_login", "date_joined"),
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email", "username", "password1", "password2",
                "role", "is_active", "is_staff", "is_superuser",
            ),
        }),
    )

    def full_name_display(self, obj):
        return obj.full_name or "—"
    full_name_display.short_description = "Nom complet"

    def last_login_display(self, obj):
        return localtime(obj.last_login).strftime("%Y-%m-%d %H:%M") if obj.last_login else "—"
    last_login_display.short_description = "Dernière connexion"

    def date_joined_display(self, obj):
        return localtime(obj.date_joined).strftime("%Y-%m-%d %H:%M") if obj.date_joined else "—"
    date_joined_display.short_description = "Inscrit le"

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="max-height:80px; border-radius:5px;" />',
                obj.avatar.url,
            )
        return "Aucun avatar"
    avatar_preview.short_description = "Aperçu de l'avatar"

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
