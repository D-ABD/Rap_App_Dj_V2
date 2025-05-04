# admin/statut.py
import logging
from django.contrib import admin
from django.utils.html import format_html

from ..models import Statut

# Configuration du logger pour les actions d'administration
logger = logging.getLogger('admin.statut')


@admin.register(Statut)
class StatutAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour le modèle Statut.
    Permet un affichage visuel de la couleur, des filtres par nom,
    et un aperçu rapide des statuts enregistrés.
    """
    list_display = ('get_nom_display', 'couleur_display', 'description_autre', 'created_at')
    list_filter = ('nom',)
    search_fields = ('nom', 'description_autre')
    readonly_fields = ('created_at', 'updated_at', 'couleur_display')

    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'couleur', 'couleur_display', 'description_autre'),
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_nom_display(self, obj):
        """
        Affiche le nom du statut avec gestion du cas 'Autre'.
        """
        return obj.get_nom_display()

    get_nom_display.short_description = 'Statut'
    get_nom_display.admin_order_field = 'nom'

    def couleur_display(self, obj):
        """
        Affiche un bloc coloré représentant visuellement la couleur du statut.
        """
        if obj.couleur:
            return format_html(
                '<div style="display:inline-block; width:100px; height:25px; background-color:{}; '
                'border:1px solid #ddd; border-radius:3px;"></div>', 
                obj.couleur
            )
        return "-"
    
    couleur_display.short_description = 'Aperçu couleur'

    # ➕ Logging lors des actions en admin
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        action = "Créé" if not change else "Modifié"
        logger.info(f"{action} statut : {obj} (par {request.user})")

    def delete_model(self, request, obj):
        logger.warning(f"Suppression du statut : {obj} (par {request.user})")
        super().delete_model(request, obj)
