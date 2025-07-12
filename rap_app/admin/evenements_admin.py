from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..models.evenements import Evenement


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "formation_nom",
        "type_evenement_display",
        "event_date",
        "lieu",
        "participants_prevus",
        "participants_reels",
        "taux_participation_affiche",
        "status_label_colore",
        "created_at",
    )
    list_filter = ("type_evenement", "event_date", "formation__centre")
    search_fields = ("formation__nom", "lieu", "description_autre", "details")
    date_hierarchy = "event_date"
    ordering = ("-event_date",)

    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "taux_participation_affiche",
        "status_label_colore",
    )

    fieldsets = (
        (_("Informations générales"), {
            "fields": (
                "formation",
                "type_evenement",
                "description_autre",
                "event_date",
                "lieu",
                "details",
            )
        }),
        (_("Participants"), {
            "fields": (
                "participants_prevus",
                "participants_reels",
                "taux_participation_affiche",
            )
        }),
        (_("Statut calculé"), {
            "fields": ("status_label_colore",),
        }),
        (_("Audit"), {
            "fields": (
                "created_by",
                "updated_by",
                "created_at",
                "updated_at",
            )
        }),
    )

    def formation_nom(self, obj):
        return obj.formation.nom if obj.formation else "-"
    formation_nom.short_description = "Formation"

    def type_evenement_display(self, obj):
        return obj.get_type_evenement_display()
    type_evenement_display.short_description = "Type"

    def taux_participation_affiche(self, obj):
        return f"{obj.taux_participation}%" if obj.taux_participation is not None else "N/A"
    taux_participation_affiche.short_description = "Taux de participation"

    def status_label_colore(self, obj):
        return format_html('<span class="{}">{}</span>', obj.status_color, obj.status_label)
    status_label_colore.short_description = "Statut"

    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)  # Injecte l'utilisateur dans `BaseModel.save()`
