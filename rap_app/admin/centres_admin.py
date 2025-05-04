import logging
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from ..models import Centre, Formation
from rap_app import models

# Configuration du logger
logger = logging.getLogger(__name__)

@admin.register(Centre)
class CentreAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les centres de formation.
    
    Fonctionnalités:
    - Liste affichant nom, code postal et dates de création/modification
    - Filtrage par code postal
    - Recherche par nom ou code postal
    - Tri par nom par défaut
    - Affichage et organisation des champs en sections
    """
    
    # Colonnes affichées dans la liste des centres
    list_display = ('nom', 'code_postal', 'nombre_formations', 'created_at', 'updated_at')
    
    # Filtres disponibles dans le panneau latéral
    list_filter = ('code_postal',)
    
    # Champs pour la recherche
    search_fields = ('nom', 'code_postal')
    
    # Tri par défaut
    ordering = ('nom',)
    
    # Champs en lecture seule (non modifiables)
    readonly_fields = ('created_at', 'updated_at', 'nombre_formations', 'formations_list')
    
    # Organisation des champs en sections
    fieldsets = (
        ('Informations', {
            'fields': ('nom', 'code_postal'),
            'description': 'Informations principales du centre de formation'
        }),
        ('Formations associées', {
            'fields': ('nombre_formations', 'formations_list'),
            'classes': ('collapse',),
            'description': 'Liste des formations rattachées à ce centre'
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'Informations temporelles automatiques'
        }),
    )
    
    def nombre_formations(self, obj):
        """Affiche le nombre de formations associées au centre."""
        count = obj.formations.count()
        return format_html(
            '<span style="color:{}">{}</span>',
            'green' if count > 0 else 'grey',
            count
        )
    nombre_formations.short_description = "Nombre de formations"
    nombre_formations.admin_order_field = 'formations__count'
    
    def formations_list(self, obj):
        """Affiche une liste des formations associées avec liens."""
        formations = obj.formations.all()[:10]  # Limite à 10 formations pour éviter une liste trop longue
        
        if not formations:
            return "Aucune formation associée"
            
        formations_links = []
        for formation in formations:
            url = reverse('admin:rap_app_formation_change', args=[formation.pk])
            formations_links.append(
                f'<a href="{url}">{formation.nom}</a>'
            )
            
        html = '<ul>' + ''.join([f'<li>{link}</li>' for link in formations_links]) + '</ul>'
        
        if obj.formations.count() > 10:
            html += f'<a href="?formation__centre__id__exact={obj.pk}">Voir toutes les formations ({obj.formations.count()})</a>'
            
        return format_html(html)
    formations_list.short_description = "Formations associées"
    
    def get_queryset(self, request):
        """Surcharge pour optimiser les requêtes."""
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            formations__count=models.Count('formations')
        )
        return queryset
    
    def save_model(self, request, obj, form, change):
        """Journalise les modifications des centres via l'admin."""
        if change:  # Modification d'un centre existant
            original = Centre.objects.get(pk=obj.pk)
            changes = []
            
            if original.nom != obj.nom:
                changes.append(f"nom: '{original.nom}' → '{obj.nom}'")
                
            if original.code_postal != obj.code_postal:
                changes.append(f"code_postal: '{original.code_postal}' → '{obj.code_postal}'")
                
            if changes:
                logger.info(
                    f"Admin - Modification du centre #{obj.pk} par {request.user}: "
                    f"{', '.join(changes)}"
                )
        else:  # Création d'un nouveau centre
            logger.info(
                f"Admin - Création d'un nouveau centre par {request.user}: "
                f"nom='{obj.nom}', code_postal='{obj.code_postal}'"
            )
            
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """Journalise la suppression d'un centre via l'admin."""
        formations_count = obj.formations.count()
        
        logger.warning(
            f"Admin - Suppression du centre #{obj.pk} '{obj.nom}' par {request.user}. "
            f"{formations_count} formations associées."
        )
        
        super().delete_model(request, obj)
    
    class Media:
        """Ajout de CSS pour l'interface d'administration."""
        css = {
            'all': ('css/admin/centre_admin.css',)
        }