from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from ..models import Document, Formation


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour la gestion des documents associés aux formations.
    """
    
    # Affichage des principales informations
    list_display = ('nom_fichier', 'formation_link', 'type_document', 'taille_fichier', 'file_link', 'created_at')
    
    # Ajout de filtres pour faciliter la navigation
    list_filter = ('type_document', 'formation__centre', 'created_at')
    
    # Recherche rapide sur certains champs
    search_fields = ('nom_fichier', 'formation__nom', 'source')

    # Rendre certains champs en lecture seule pour éviter toute modification accidentelle
    readonly_fields = ('created_at', 'updated_at', 'taille_fichier', 'file_link', 'image_preview', 'formation_link')

    # Organisation des champs dans l'interface d'administration
    fieldsets = (
        ('Informations générales', {
            'fields': ('formation', 'formation_link', 'nom_fichier', 'type_document', 'taille_fichier')
        }),
        ('Fichier', {
            'fields': ('fichier', 'file_link', 'source', 'image_preview'),
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)  # Masquer cette section par défaut
        }),
    )

    ### ✅ **Ajouts de méthodes utiles**
    
    def formation_link(self, obj):
        """
        Affiche un lien vers la formation associée dans l'interface d'administration.
        """
        if obj.formation:
            url = reverse('admin:rap_app_formation_change', args=[obj.formation.id])
            return format_html('<a href="{}">{}</a>', url, obj.formation.nom)
        return "Aucune formation"
    
    formation_link.short_description = 'Formation'
    formation_link.admin_order_field = 'formation__nom'

    
    def file_link(self, obj):
        """
        Ajoute un lien pour télécharger le fichier directement depuis l'admin Django.
        """
        if obj.fichier:
            return format_html('<a href="{}" target="_blank">Télécharger</a>', obj.fichier.url)
        return "-"
    
    file_link.short_description = "Téléchargement"

    
    def image_preview(self, obj):
        """
        Affiche un aperçu de l'image si le document est de type `image`.
        """
        if obj.type_document == Document.IMAGE and obj.fichier:
            return format_html('<img src="{}" width="150" style="border:1px solid #ddd; padding:5px;"/>', obj.fichier.url)
        return "Aperçu non disponible"
    
    image_preview.short_description = "Aperçu"

    
    def taille_fichier(self, obj):
        """
        Affiche la taille du fichier en Ko pour plus d'informations.
        """
        if obj.taille_fichier:
            return f"{obj.taille_fichier:.2f} Ko"
        return "-"

    
    # Ajout de fonctionnalités supplémentaires à l'admin
    ordering = ("-created_at", "nom_fichier")  # Trie les documents par date de création descendante
    list_per_page = 20  # Nombre de documents affichés par page
