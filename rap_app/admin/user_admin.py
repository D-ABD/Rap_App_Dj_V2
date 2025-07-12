from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.html import format_html
from django.utils.timezone import localtime
from django.contrib import messages
from ..models.custom_user import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(DjangoUserAdmin):
    """
    🛠️ Admin ultra complet pour le modèle CustomUser.
    """

    model = CustomUser

    list_display = (
        "full_name_display",
         "email",
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
        # ✅ Suppression de l’accès à `created_by` (non défini dans CustomUser)
        # Si tu ajoutes un champ 'updated_by' dans le modèle, cette ligne sera utile
        # obj.updated_by = request.user
        super().save_model(request, obj, form, change)
@admin.action(description="Passer en stagiaire")
def passer_en_stagiaire(self, request, queryset):
    for user in queryset:
        old_role = user.role
        user.role = CustomUser.ROLE_STAGIAIRE
        user.save()
        self.message_user(request, f"{user.email} : rôle mis à jour ({old_role} → stagiaire)", messages.SUCCESS)
        self.message_user(request, f"{user.email} : rôle mis à jour ({old_role} → stagiaire)", messages.SUCCESS)