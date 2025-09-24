# rap_app/atelier_tre_admin.py
from django.contrib import admin
from django.db.models import Count

from ..models.atelier_tre import AtelierTRE
@admin.register(AtelierTRE)
class AtelierTREAdmin(admin.ModelAdmin):
    # Liste
    list_display = (
        "id",
        "type_atelier",
        "type_atelier_label",
        "date_atelier",
        "centre",
        "nb_inscrits_col",
        "created_by",
        "created_at",
        "updated_at",
    )
    list_filter = ("type_atelier", "centre", "date_atelier")
    search_fields = (
        "id",
        "centre__nom",
        "candidats__nom",
        "candidats__prenom",
    )
    ordering = ("-date_atelier", "-id")
    date_hierarchy = "date_atelier"

    # Édition
    autocomplete_fields = ("centre", "candidats")  # nécessite search_fields sur Centre/Candidat
    # ou, si tu préfères l’ancien widget multi-sélecteur :
    # filter_horizontal = ("candidats",)

    readonly_fields = ("created_by", "created_at", "updated_at")

    # Optimisation & annotation du count
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return (
            qs.select_related("centre", "created_by")
              .prefetch_related("candidats")
              .annotate(_nb_inscrits=Count("candidats", distinct=True))
        )

    # Colonnes calculées
    @admin.display(description="Libellé")
    def type_atelier_label(self, obj: AtelierTRE):
        return obj.get_type_atelier_display()

    @admin.display(description="Inscrits", ordering="_nb_inscrits")
    def nb_inscrits_col(self, obj: AtelierTRE):
        # utilise l’annotation pour éviter un count() par ligne
        return getattr(obj, "_nb_inscrits", 0)

    # Définit automatiquement le created_by
    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
