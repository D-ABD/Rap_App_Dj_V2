import csv
import logging
from io import StringIO
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.html import format_html
from django.utils.timezone import localtime
from django.http import HttpResponse
from django.db.models import Q

from ..models.custom_user import CustomUser

logger = logging.getLogger("application.customuser")


# ───────────────────────────────────────────────
# ACTIONS ADMIN GLOBALES
# ───────────────────────────────────────────────
@admin.action(description="🎓 Passer en stagiaire")
def passer_en_stagiaire(modeladmin, request, queryset):
    updated = 0
    for user in queryset:
        if user.role != CustomUser.ROLE_STAGIAIRE:
            user.role = CustomUser.ROLE_STAGIAIRE
            user.save()
            updated += 1
    if updated:
        messages.success(request, f"{updated} utilisateur(s) passé(s) au rôle « stagiaire ».")
        logger.info("🎓 %s utilisateur(s) passés en stagiaire par %s", updated, request.user)


@admin.action(description="📤 Exporter la sélection en CSV")
def export_csv(modeladmin, request, queryset):
    """Export CSV rapide depuis l’admin."""
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CustomUser.get_csv_headers())
    for u in queryset:
        writer.writerow([
            u.pk,
            u.email,
            u.username,
            u.first_name,
            u.last_name,
            u.get_role_display(),
            u.date_joined.strftime("%Y-%m-%d %H:%M") if u.date_joined else "",
            "Oui" if u.is_active else "Non",
        ])
    buffer.seek(0)
    response = HttpResponse(buffer, content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=utilisateurs_export.csv"
    logger.info("📤 Export CSV %s lignes par %s", queryset.count(), request.user)
    return response


# ───────────────────────────────────────────────
# ADMIN PRINCIPAL
# ───────────────────────────────────────────────
@admin.register(CustomUser)
class CustomUserAdmin(DjangoUserAdmin):
    """
    🛠️ Interface d'administration complète pour CustomUser.
    - Accès scoped pour staff selon ses centres.
    - Actions utilitaires et export CSV.
    - UX homogène avec les autres modules.
    """

    model = CustomUser

    # Liste
    list_display = (
        "full_name_display",
        "email",
        "role_badge",
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
        "centres",
        ("date_joined", admin.DateFieldListFilter),
    )
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("-date_joined",)
    list_per_page = 50

    # Formulaire
    readonly_fields = ("date_joined", "last_login", "avatar_preview")
    filter_horizontal = ("groups", "user_permissions", "centres")

    fieldsets = (
        ("🧾 Informations de connexion", {
            "fields": ("email", "username", "password"),
        }),
        ("👤 Informations personnelles", {
            "fields": ("first_name", "last_name", "phone", "avatar", "avatar_preview", "bio"),
        }),
        ("🏢 Portée par centres", {
            "fields": ("centres",),
            "description": "Les membres du staff ne voient que les utilisateurs liés à leurs centres.",
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

    actions = [passer_en_stagiaire, export_csv]

    # ───────────────────────────────
    # Helpers d'affichage
    # ───────────────────────────────
    def full_name_display(self, obj):
        return obj.full_name or "—"
    full_name_display.short_description = "Nom complet"

    def role_badge(self, obj):
        """Affichage stylisé du rôle."""
        color = {
            CustomUser.ROLE_SUPERADMIN: "#b71c1c",
            CustomUser.ROLE_ADMIN: "#d84315",
            CustomUser.ROLE_STAFF: "#1565c0",
            CustomUser.ROLE_STAFF_READ: "#0277bd",
            CustomUser.ROLE_STAGIAIRE: "#2e7d32",
            CustomUser.ROLE_CANDIDAT: "#6a1b9a",
            CustomUser.ROLE_CANDIDAT_USER: "#8e24aa",
            CustomUser.ROLE_TEST: "#757575",
        }.get(obj.role, "#444")
        return format_html(
            f'<span style="color:white; background:{color}; padding:2px 8px; border-radius:8px;">{obj.get_role_display()}</span>'
        )
    role_badge.short_description = "Rôle"

    def centres_display(self, obj):
        noms = list(obj.centres.values_list("nom", flat=True))
        if not noms:
            return "—"
        text = ", ".join(noms[:3])
        if len(noms) > 3:
            text += f" +{len(noms) - 3}"
        return text
    centres_display.short_description = "Centres"

    def last_login_display(self, obj):
        return localtime(obj.last_login).strftime("%Y-%m-%d %H:%M") if obj.last_login else "—"
    last_login_display.short_description = "Dernière connexion"

    def date_joined_display(self, obj):
        return localtime(obj.date_joined).strftime("%Y-%m-%d %H:%M") if obj.date_joined else "—"
    date_joined_display.short_description = "Inscrit le"

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" style="max-height:80px; border-radius:5px;" />', obj.avatar.url)
        return "—"
    avatar_preview.short_description = "Aperçu de l’avatar"

    # ───────────────────────────────
    # Queryset & permissions de visibilité
    # ───────────────────────────────
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        u = request.user
        # Admin complet
        if u.is_superuser or getattr(u, "is_admin", lambda: False)():
            return qs
        # Staff restreint : uniquement ses centres
        if u.is_staff:
            centre_ids = list(u.centres.values_list("id", flat=True))
            if not centre_ids:
                return qs.none()
            return qs.filter(Q(centres__in=centre_ids)).distinct()
        return qs.none()

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Restreint le choix de centres pour les staff non-admins."""
        if db_field.name == "centres":
            u = request.user
            if u.is_staff and not (u.is_superuser or getattr(u, "is_admin", lambda: False)()):
                kwargs["queryset"] = db_field.related_model.objects.filter(
                    id__in=u.centres.values_list("id", flat=True)
                )
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    # ───────────────────────────────
    # Sauvegarde & logs
    # ───────────────────────────────
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        action = "créé" if not change else "modifié"
        logger.info(f"👤 Utilisateur {action} : {obj.email} par {request.user}")
