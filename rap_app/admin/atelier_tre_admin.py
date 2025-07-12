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
        "get_nb_participants_prevus",
        "get_nb_participants_presents",
        "remarque_courte",
    )
    list_filter = ("type_atelier",)
    search_fields = ("remarque",)
    inlines = [ParticipationAtelierTREInline]
    ordering = ("-date",)

    @admin.display(description=_("Prévu"))
    def get_nb_participants_prevus(self, obj):
        return obj.nb_participants_prevus

    @admin.display(description=_("Présents"))
    def get_nb_participants_presents(self, obj):
        return obj.nb_participants_presents

    @admin.display(description=_("Remarque courte"))
    def remarque_courte(self, obj):
        if obj.remarque:
            return f"{obj.remarque[:40]}…" if len(obj.remarque) > 40 else obj.remarque
        return "-"
