import logging
from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.db.models import Count
from django.urls import reverse
from django.contrib import messages

from ..models.types_offre import TypeOffre

# Configuration du logger
logger = logging.getLogger("application.typeoffre.admin")


class FormationInline(admin.TabularInline):
    """
    Inline pour afficher les formations associées à un type d'offre.
    """
    model = 'Formation'  # Remplacer par le chemin complet du modèle si nécessaire
    verbose_name = "Formation associée"
    verbose_name_plural = "Formations associées"
    extra = 0
    fields = ('nom', 'centre', 'start_date', 'end_date', 'places_disponibles')
    readonly_fields = fields
    can_delete = False
    max_num = 10
    
    def has_add_permission(self, request, obj=None):
        """Désactive l'ajout manuel de formations via l'inline"""
        return False


@admin.register(TypeOffre)
class TypeOffreAdmin(admin.ModelAdmin):
    """
    Administration du modèle TypeOffre avec fonctionnalités avancées:
    - Affichage des couleurs avec prévisualisation
    - Statistiques sur l'utilisation des types d'offre
    - Validation avancée des codes couleur
    - Interface intuitive pour la gestion des types d'offre
    """
    # Champs affichés dans la liste des types d'offre
    list_display = (
        'nom_display',
        'color_preview',
        'autre_display',
        'formations_count',
        'is_personnalise_display',
        'created_at',
        'updated_at',
    )
    
    # Filtres dans la barre latérale
    list_filter = (
        'nom',
        'created_at',
    )
    
    # Champs de recherche
    search_fields = (
        'nom',
        'autre',
    )
    
    # Regroupement des champs dans le formulaire d'édition
    fieldsets = (
        ('Informations générales', {
            'fields': (
                'nom',
                'autre',
            ),
            'description': "Définition du type d'offre, avec option pour un type personnalisé"
        }),
        ('Apparence', {
            'fields': (
                'couleur',
                'color_preview_large',
                'badge_preview',
            ),
            'description': "Configuration visuelle pour l'affichage du type d'offre"
        }),
        ('Métadonnées', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
            'description': "Informations de suivi et d'audit"
        }),
    )
    
    # Champs en lecture seule (calculés automatiquement)
    readonly_fields = (
        'color_preview_large',
        'badge_preview',
        'created_at',
        'updated_at',
    )
    
    # Actions personnalisées
    actions = [
        'reset_default_colors',
        'export_selected_types',
    ]
    
    # Méthodes pour les champs calculés et l'affichage personnalisé
    
    def nom_display(self, obj):
        """
        Affiche le nom du type d'offre formaté avec distinction pour les personnalisés.
        """
        if obj.is_personnalise():
            return format_html(
                '{} <small style="color:#6c757d;">({})</small>',
                obj.autre,
                obj.get_nom_display()
            )
        return obj.get_nom_display()
    nom_display.short_description = "Type d'offre"
    nom_display.admin_order_field = 'nom'
    
    def autre_display(self, obj):
        """
        Affiche le champ 'autre' avec formatage conditionnel.
        """
        if obj.is_personnalise() and obj.autre:
            return obj.autre
        return format_html(
            '<span style="color:#999;">-</span>'
        )
    autre_display.short_description = "Personnalisé"
    autre_display.admin_order_field = 'autre'
    
    def color_preview(self, obj):
        """
        Affiche un aperçu de la couleur sous forme d'un carré coloré.
        """
        text_color = obj.text_color()
        return format_html(
            '<div style="background-color:{}; width:20px; height:20px; border-radius:3px; display:inline-block;" title="{}"></div>',
            obj.couleur,
            obj.couleur
        )
    color_preview.short_description = "Couleur"
    
    def color_preview_large(self, obj):
        """
        Affiche un grand aperçu de la couleur avec code hexadécimal.
        """
        text_color = obj.text_color()
        return format_html(
            '<div style="background-color:{}; color:{}; padding:15px; border-radius:5px; text-align:center; margin:10px 0;">'
            '<strong style="font-size:16px;">{}</strong>'
            '</div>',
            obj.couleur,
            text_color,
            obj.couleur
        )
    color_preview_large.short_description = "Aperçu de la couleur"
    
    def badge_preview(self, obj):
        """
        Affiche un aperçu du badge tel qu'il apparaîtra dans l'interface.
        """
        return format_html(
            '<div style="margin:10px 0;">{}</div>',
            mark_safe(obj.get_badge_html())
        )
    badge_preview.short_description = "Aperçu du badge"
    
    def formations_count(self, obj):
        """
        Affiche le nombre de formations associées à ce type d'offre.
        """
        count = getattr(obj, 'formations_count', None)
        if count is None:
            count = obj.get_formations_count()
            
        if count > 0:
            url = reverse('admin:rap_app_formation_changelist') + f'?type_offre__id__exact={obj.id}'
            return format_html(
                '<a href="{}" title="Voir les formations associées" style="font-weight:bold;">{}</a>',
                url,
                count
            )
        return "0"
    formations_count.short_description = "Formations"
    formations_count.admin_order_field = 'formations_count'
    
    def is_personnalise_display(self, obj):
        """
        Affiche si le type d'offre est personnalisé.
        """
        if obj.is_personnalise():
            return format_html(
                '<span style="color:green;">✓</span>'
            )
        return format_html(
            '<span style="color:#999;">-</span>'
        )
    is_personnalise_display.short_description = "Personnalisé"
    is_personnalise_display.boolean = True
    
    # Actions personnalisées
    
    def reset_default_colors(self, request, queryset):
        """
        Réinitialise les couleurs par défaut pour les types d'offre sélectionnés.
        """
        updated = 0
        for type_offre in queryset:
            original_color = type_offre.couleur
            
            # Réinitialisation de la couleur pour forcer l'assignation par défaut
            type_offre.couleur = '#6c757d'
            type_offre.assign_default_color()
            
            # Sauvegarder uniquement si la couleur a changé
            if original_color != type_offre.couleur:
                type_offre.save()
                updated += 1
                logger.info(
                    f"Admin: Couleur réinitialisée pour le type d'offre #{type_offre.pk} "
                    f"de {original_color} à {type_offre.couleur}"
                )
        
        if updated:
            self.message_user(
                request, 
                f"Couleurs réinitialisées pour {updated} types d'offre.",
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                "Aucune couleur n'a été modifiée. Les types d'offre avaient déjà leurs couleurs par défaut.",
                messages.INFO
            )
    reset_default_colors.short_description = "Réinitialiser les couleurs par défaut"
    
    def export_selected_types(self, request, queryset):
        """
        Exporte les types d'offre sélectionnés au format CSV.
        """
        import csv
        from django.http import HttpResponse
        from django.utils import timezone
        
        # Configuration de la réponse HTTP
        timestamp = timezone.now().strftime('%Y%m%d-%H%M%S')
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="types_offre_export_{timestamp}.csv"'
        
        # En-têtes CSV
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Nom', 'Personnalisé', 'Couleur', 'Nombre de formations', 
            'Date de création', 'Dernière modification'
        ])
        
        # Données des types d'offre
        for type_offre in queryset:
            writer.writerow([
                type_offre.pk,
                str(type_offre),
                'Oui' if type_offre.is_personnalise() else 'Non',
                type_offre.couleur,
                type_offre.get_formations_count(),
                type_offre.created_at.strftime('%d/%m/%Y %H:%M'),
                type_offre.updated_at.strftime('%d/%m/%Y %H:%M'),
            ])
        
        # Journalisation
        logger.info(f"Admin: Export CSV de {queryset.count()} types d'offre par {request.user}")
        
        return response
    export_selected_types.short_description = "Exporter les types d'offre sélectionnés"
    
    def get_queryset(self, request):
        """
        Optimise la requête avec des annotations pour les champs calculés.
        """
        queryset = super().get_queryset(request)
        
        # Annoter avec le nombre de formations pour optimiser les performances
        queryset = queryset.annotate(
            formations_count=Count('formations', distinct=True)
        )
        
        return queryset
    
    def save_model(self, request, obj, form, change):
        """
        Personnalisation de la sauvegarde avec journalisation.
        """
        is_new = not change
        
        # Sauvegarde du modèle
        super().save_model(request, obj, form, change)
        
        # Journalisation de l'action administrative
        if is_new:
            logger.info(
                f"Admin: Type d'offre '{obj}' créé par {request.user}"
            )
            messages.success(
                request, 
                f"Type d'offre '{obj}' créé avec succès."
            )
        else:
            logger.info(
                f"Admin: Type d'offre '{obj}' modifié par {request.user}"
            )
            messages.success(
                request, 
                f"Type d'offre '{obj}' mis à jour avec succès."
            )
    
    class Media:
        """
        Ressources CSS et JS pour l'interface d'admin.
        """
        css = {
            'all': ('css/admin/type_offre_admin.css',)
        }
        js = ('js/admin/type_offre_admin.js',)