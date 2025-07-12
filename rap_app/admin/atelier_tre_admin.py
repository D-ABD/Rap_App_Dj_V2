from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from ..models.atelier_tre import AtelierTRE, ParticipationAtelierTRE


class ParticipationAtelierTREInline(admin.TabularInline):
    model = ParticipationAtelierTRE
    extra = 0
    autocomplete_fields = ("candidat",)
    fields = ("candidat", "present", "commentaire_individuel")
    verbose_name = _("Candidat inscrit")
    verbose_name_plural = _("Candidats inscrits")


@admin.register(AtelierTRE)
class AtelierTREAdmin(admin.ModelAdmin):
    list_display = (
        "type_atelier",
        "date",
        "nb_participants_prevus",
        "nb_participants_presents",
        "remarque_courte",
    )
    list_filter = ("type_atelier", "date")
    search_fields = ("remarque",)
    inlines = [ParticipationAtelierTREInline]
    ordering = ("-date",)

    def nb_participants_prevus(self, obj):
        return obj.nb_participants_prevus
    nb_participants_prevus.short_description = _("Prévu")

    def nb_participants_presents(self, obj):
        return obj.nb_participants_presents
    nb_participants_presents.short_description = _("Présents")

    def remarque_courte(self, obj):
        if obj.remarque:
            return (obj.remarque[:40] + "...") if len(obj.remarque) > 40 else obj.remarque
        return ""
    remarque_courte.short_description = _("Remarque courte")
