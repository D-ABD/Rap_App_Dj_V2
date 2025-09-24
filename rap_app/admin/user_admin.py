from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.html import format_html
from django.utils.timezone import localtime

from ..models.custom_user import CustomUser


# ---- Action admin (hors classe) ----
@admin.action(description="Passer en stagiaire")
def passer_en_stagiaire(modeladmin, request, queryset):
    updated = 0
    for user in queryset:
        old_role = user.role
        if old_role != CustomUser.ROLE_STAGIAIRE:
            user.role = CustomUser.ROLE_STAGIAIRE
            user.save()
            updated += 1
    if updated:
        messages.success(request, f"{updated} utilisateur(s) passé(s) au rôle 'stagiaire'.")


@admin.register(CustomUser)
class CustomUserAdmin(DjangoUserAdmin):
    """
    🛠️ Admin complet pour CustomUser, avec portée par centres pour le staff.
    - Staff : ne voit/édite que les utilisateurs rattachés à ses centres.
    - Admin/Superadmin : accès global.
    """

    model = CustomUser

    # ---- Liste ----
    list_display = (
        "full_name_display",
        "email",
        "role",
        "centres_display",
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
        "centres",  # filtre par centre (M2M)
    )
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("-date_joined",)

    # ---- Formulaire ----
    readonly_fields = ("date_joined", "last_login", "avatar_preview")
    filter_horizontal = ("groups", "user_permissions", "centres")  # edition M2M confortable
    # Si tu préfères: autocomplete_fields = ("centres",)

    fieldsets = (
        ("🧾 Informations de connexion", {
            "fields": ("email", "username", "password"),
        }),
        ("👤 Informations personnelles", {
            "fields": ("first_name", "last_name", "phone", "avatar", "avatar_preview", "bio"),
        }),
        ("🏢 Portée par centres", {
            "fields": ("centres",),
            "description": "Les membres du staff ne peuvent voir/éditer que les utilisateurs de leurs centres.",
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
                "role", "is_active", "is_staff", "is_superuser", "centres",
            ),
        }),
    )

    actions = [passer_en_stagiaire]

    # ---- Affichages utiles ----
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
            return format_html('<img src="{}" style="max-height:80px; border-radius:5px;" />', obj.avatar.url)
        return "Aucun avatar"
    avatar_preview.short_description = "Aperçu de l'avatar"

    def centres_display(self, obj):
        noms = list(obj.centres.values_list("nom", flat=True))
        if not noms:
            return "—"
        # Affiche max 3 centres pour éviter une ligne trop longue
        text = ", ".join(noms[:3])
        if len(noms) > 3:
            text += f" +{len(noms) - 3}"
        return text
    centres_display.short_description = "Centres"

    # ---- Scopage par centres (liste + édition) ----
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        u = request.user
        # Admin/Superadmin : accès complet
        if u.is_superuser or (hasattr(u, "is_admin") and u.is_admin()):
            return qs
        # Staff : restreint aux utilisateurs liés à AU MOINS un centre du staff
        if u.is_staff:
            centre_ids = list(u.centres.values_list("id", flat=True))
            if not centre_ids:
                return qs.none()
            return qs.filter(
                admin.models.Q(centres__in=centre_ids) |
                admin.models.Q(candidat_associe__formation__centre_id__in=centre_ids)
            ).distinct()
        # Par défaut (non-staff) : rien
        return qs.none()

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """
        Limite les choix de centres dans le formulaire pour le staff
        (admin/superadmin gardent tous les centres).
        """
        if db_field.name == "centres":
            u = request.user
            if u.is_staff and not (u.is_superuser or (hasattr(u, "is_admin") and u.is_admin())):
                kwargs["queryset"] = db_field.related_model.objects.filter(
                    id__in=u.centres.values_list("id", flat=True)
                )
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        # Exemple si tu ajoutes plus tard un champ updated_by :
        # obj.updated_by = request.user
        super().save_model(request, obj, form, change)
