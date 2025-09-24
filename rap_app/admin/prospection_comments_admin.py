# rap_app/admin.py
from __future__ import annotations

from typing import Iterable, Tuple, Optional

from django.contrib import admin
from django.db.models import QuerySet
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# Adapte ces imports à ton app si besoin
from rap_app.models.prospection import Prospection
from rap_app.models.prospection_comments import ProspectionComment


# ───────────────────────────────────────────────────────────────
# Filtres personnalisés
# ───────────────────────────────────────────────────────────────
class DepartementListFilter(admin.SimpleListFilter):
    title = _("Département (centre)")
    parameter_name = "departement"

    def lookups(self, request, model_admin) -> Iterable[Tuple[str, str]]:
        # Récupère les 2 premiers chars du code postal des centres liés
        qs = Prospection.objects.filter(comments__isnull=False).values_list(
            "centre__code_postal", flat=True
        )
        codes = set()
        for cp in qs:
            if not cp:
                continue
            code = str(cp).strip()[:2]
            if code:
                codes.add(code)
        return sorted((c, c) for c in codes)

    def queryset(self, request, queryset: QuerySet[ProspectionComment]):
        val = self.value()
        if not val:
            return queryset
        return queryset.filter(prospection__centre__code_postal__startswith=str(val)[:2])


# ───────────────────────────────────────────────────────────────
# Admin ProspectionComment
# ───────────────────────────────────────────────────────────────
@admin.register(ProspectionComment)
class ProspectionCommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "prospection_link",
        "body_preview",
        "is_internal",
        "created_by_display",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "is_internal",
        ("prospection__centre", admin.RelatedOnlyFieldListFilter),
        DepartementListFilter,
        ("created_by", admin.RelatedOnlyFieldListFilter),
        ("created_at", admin.DateFieldListFilter),
    )
    search_fields = (
        "body",
        "created_by__username",
        "created_by__email",
        "prospection__formation__nom",
        "prospection__partenaire__nom",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    list_select_related = (
        "prospection",
        "prospection__centre",
        "prospection__formation",
        "prospection__partenaire",
        "created_by",
    )

    # Selon ton BaseModel : ajuste si created_by/updated_by sont gérés ailleurs
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("prospection",)  # + "created_by" si tu veux l’autocomplete
    autocomplete_fields: list[str] = []  # ex: ["created_by"]

    fieldsets = (
        (None, {"fields": ("prospection", "body", "is_internal")}),
        (_("Métadonnées"), {"fields": ("created_by", "created_at", "updated_at")}),
    )

    # ── Affichages custom
    @admin.display(description=_("Prospection"), ordering="prospection_id")
    def prospection_link(self, obj: ProspectionComment):
        if not obj.prospection_id:
            return "—"
        # libellé lisible
        label = getattr(obj, "prospection_text", None) or f"#{obj.prospection_id}"
        try:
            url = reverse(
                f"admin:{Prospection._meta.app_label}_{Prospection._meta.model_name}_change",
                args=[obj.prospection_id],
            )
            return format_html('<a href="{}">{}</a>', url, label)
        except Exception:
            return label

    @admin.display(description=_("Aperçu"))
    def body_preview(self, obj: ProspectionComment) -> str:
        body = (obj.body or "").strip().replace("\n", " ")
        return (body[:120] + "…") if len(body) > 120 else body or "—"

    @admin.display(description=_("Auteur"), ordering="created_by__username")
    def created_by_display(self, obj: ProspectionComment) -> str:
        u = getattr(obj, "created_by", None)
        if not u:
            return "—"
        full = f"{(getattr(u, 'first_name', '') or '').strip()} {(getattr(u, 'last_name', '') or '').strip()}".strip()
        return full or getattr(u, "username", None) or getattr(u, "email", None) or "—"

    # ── Actions
    actions = ("mark_as_internal", "mark_as_external")

    @admin.action(description=_("Marquer comme interne"))
    def mark_as_internal(self, request, queryset: QuerySet[ProspectionComment]):
        updated = queryset.update(is_internal=True)
        self.message_user(request, _("%(n)d commentaire(s) marqué(s) interne.") % {"n": updated})

    @admin.action(description=_("Marquer comme externe"))
    def mark_as_external(self, request, queryset: QuerySet[ProspectionComment]):
        updated = queryset.update(is_internal=False)
        self.message_user(request, _("%(n)d commentaire(s) marqué(s) externe.") % {"n": updated})

    # ── created_by auto (si champ présent sur BaseModel)
    def save_model(self, request, obj: ProspectionComment, form, change):
        if not change and hasattr(obj, "created_by") and not getattr(obj, "created_by_id", None):
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    # (Optionnel) restreindre la vue si tu ouvres l'admin à des non-staff
    # def has_view_permission(self, request, obj=None) -> bool:
    #     return bool(getattr(request.user, "is_staff", False) or getattr(request.user, "is_superuser", False))
