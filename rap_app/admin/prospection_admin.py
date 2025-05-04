import logging
from django.contrib import admin
from django.utils.html import format_html
from ..models.prospection import Prospection, HistoriqueProspection

# Logger pour suivre les actions dans l'admin
logger = logging.getLogger("admin.prospection")


@admin.register(Prospection)
class ProspectionAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour la gestion des prospections commerciales.
    Permet un suivi visuel, des filtres pratiques et une journalisation des actions.
    """
    list_display = (
        'company', 'formation', 'statut_color', 'objectif', 'responsable', 'date_prospection',
    )
    list_filter = ('statut', 'objectif', 'date_prospection', 'responsable')
    search_fields = ('company__name', 'formation__nom', 'commentaire')
    readonly_fields = ('date_prospection', 'statut_color', 'historique_display')
    ordering = ['-date_prospection']
    date_hierarchy = 'date_prospection'

    fieldsets = (
        ("Informations générales", {
            'fields': ('company', 'formation', 'responsable', 'statut', 'statut_color', 'objectif', 'motif'),
        }),
        ("Commentaires et historique", {
            'fields': ('commentaire', 'historique_display')
        }),
        ("Date", {
            'fields': ('date_prospection',),
        }),
    )

    def statut_color(self, obj):
        """Affiche le statut avec une couleur de fond CSS."""
        classes = {
            'a_faire': 'primary',
            'en_cours': 'info',
            'a_relancer': 'warning',
            'acceptee': 'success',
            'refusee': 'danger',
            'annulee': 'secondary',
            'non_renseigne': 'light',
        }
        css_class = classes.get(obj.statut, 'light')
        return format_html('<span class="badge bg-{}">{}</span>', css_class, obj.get_statut_display())
    
    statut_color.short_description = "Statut"
    statut_color.admin_order_field = "statut"

    def historique_display(self, obj):
        """Affiche un résumé HTML des historiques de cette prospection."""
        historiques = obj.historiques.all().order_by('-date_modification')[:5]
        if not historiques:
            return "Aucun historique."
        rows = []
        for h in historiques:
            rows.append(f"<li><strong>{h.date_modification.strftime('%d/%m/%Y')}:</strong> {h.get_ancien_statut_display()} ➔ {h.get_nouveau_statut_display()}</li>")
        return format_html('<ul>{}</ul>', format_html(''.join(rows)))

    historique_display.short_description = "Historique récent"

    def save_model(self, request, obj, form, change):
        """Journalisation personnalisée à la sauvegarde."""
        if change:
            logger.info(f"Admin: modification de la prospection #{obj.pk} par {request.user.username}")
        else:
            logger.info(f"Admin: création de la prospection pour {obj.company.name} par {request.user.username}")
        super().save_model(request, obj, form, change)


@admin.register(HistoriqueProspection)
class HistoriqueProspectionAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour visualiser les historiques de prospection.
    """
    list_display = ('prospection', 'ancien_statut', 'nouveau_statut', 'date_modification', 'modifie_par')
    list_filter = ('nouveau_statut', 'modifie_par', 'date_modification')
    search_fields = ('prospection__company__name', 'commentaire', 'resultat')
    ordering = ['-date_modification']
    readonly_fields = [f.name for f in HistoriqueProspection._meta.fields]

    def has_add_permission(self, request):
        """On empêche l'ajout manuel d'historique depuis l'admin."""
        return False
