from django.contrib import admin

from ..models.commentaires_appairage import CommentaireAppairage


class CommentaireAppairageInline(admin.TabularInline):
    model = CommentaireAppairage
    extra = 0
    fields = ("body", "created_by", "statut_snapshot", "created_at")
    readonly_fields = ("created_at", "statut_snapshot", "created_by")
    ordering = ("-created_at",)


@admin.register(CommentaireAppairage)
class CommentaireAppairageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "appairage",
        "auteur_nom",
        "statut_snapshot",
        "created_at",
    )
    list_filter = ("statut_snapshot", "created_at")
    search_fields = ("body", "created_by__username", "created_by__first_name", "created_by__last_name")
    readonly_fields = ("created_at", "updated_at", "statut_snapshot", "created_by", "updated_by")

    def auteur_nom(self, obj):
        return obj.auteur_nom()
    auteur_nom.short_description = "Auteur"

    # 🔑 injection automatique du user lors de l’enregistrement
    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for inst in instances:
            if hasattr(inst, "save"):
                try:
                    inst.save(user=request.user)
                except TypeError:
                    inst.save()
        formset.save_m2m()
