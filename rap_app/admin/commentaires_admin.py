import logging
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from ..models.commentaires import Commentaire
from ..models.formations import Formation

# Configuration du logger
logger = logging.getLogger(__name__)

Utilisateur = get_user_model()

@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour la gestion des commentaires liés aux formations.
    
    Caractéristiques:
    - Liste avec formation, utilisateur, contenu, saturation et date
    - Filtres par formation, utilisateur, saturation et date
    - Recherche par formation, utilisateur et contenu
    - Vue détaillée organisée en sections
    - Attribution automatique de l'utilisateur lors de la création
    """

    # Affichage des principales informations
    list_display = ("formation_link", "utilisateur_link", "contenu_preview", "saturation_display", "created_at")

    # Ajout de filtres pour faciliter la recherche
    list_filter = (
        "formation__centre", 
        "utilisateur", 
        "saturation", 
        "created_at",
        ("saturation", admin.EmptyFieldListFilter),  # Filtrer les commentaires sans saturation
    )

    # Recherche rapide sur certains champs
    search_fields = ("formation__nom", "utilisateur__username", "utilisateur__email", "contenu")

    # Rendre certains champs en lecture seule
    readonly_fields = ("utilisateur", "created_at", "updated_at", "formation_details")

    # Organisation des champs
    fieldsets = (
        ("Informations générales", {
            "fields": ("formation", "formation_details", "utilisateur"),
            "description": "Information sur la formation et l'utilisateur concernés",
        }),
        ("Contenu du commentaire", {
            "fields": ("contenu",),
            "description": "Texte du commentaire",
        }),
        ("Données complémentaires", {
            "fields": ("saturation",),
            "description": "Données additionnelles liées au commentaire",
        }),
        ("Métadonnées", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
            "description": "Informations temporelles automatiques",
        }),
    )

    ordering = ("-created_at",)
    list_per_page = 20
    date_hierarchy = "created_at"  # Navigation par date
    
    def get_queryset(self, request):
        """Optimise les requêtes avec des jointures."""
        queryset = super().get_queryset(request)
        return queryset.select_related('formation', 'formation__centre', 'utilisateur')

    def formation_link(self, obj):
        """Affiche un lien vers la formation associée."""
        if obj.formation:
            url = reverse('admin:rap_app_formation_change', args=[obj.formation.id])
            return format_html('<a href="{}">{}</a>', url, obj.formation.nom)
        return "—"
    formation_link.short_description = "Formation"
    formation_link.admin_order_field = "formation__nom"

    def utilisateur_link(self, obj):
        """Affiche un lien vers l'utilisateur associé."""
        if obj.utilisateur:
            url = reverse('admin:auth_user_change', args=[obj.utilisateur.id])
            return format_html('<a href="{}">{}</a>', url, obj.utilisateur.username)
        return "Anonyme"
    utilisateur_link.short_description = "Utilisateur"
    utilisateur_link.admin_order_field = "utilisateur__username"

    def contenu_preview(self, obj):
        """Affiche un aperçu tronqué du contenu du commentaire."""
        max_length = 50
        if len(obj.contenu) <= max_length:
            return obj.contenu
        return format_html(
            '{}... <span class="viewlink">(<a href="{}">Voir tout</a>)</span>', 
            obj.contenu[:max_length], 
            reverse('admin:rap_app_commentaire_change', args=[obj.id])
        )
    contenu_preview.short_description = "Contenu"

    def saturation_display(self, obj):
        """Affiche le niveau de saturation avec code couleur."""
        if obj.saturation is None:
            return "—"
            
        # Détermination de la couleur selon le pourcentage
        if obj.saturation < 50:
            color = "green"
        elif obj.saturation < 80:
            color = "orange"
        else:
            color = "red"
            
        return format_html(
            '<div style="width:100%%; background-color: #f8f9fa; border-radius: 3px;">'
            '<div style="width:{}%%; background-color: {}; height: 10px; border-radius: 3px;"></div>'
            '</div>'
            '<span>{} %</span>', 
            min(obj.saturation, 100), color, obj.saturation
        )
    saturation_display.short_description = "Saturation"
    saturation_display.admin_order_field = "saturation"
    
    def formation_details(self, obj):
        """Affiche les détails de la formation associée."""
        if not obj.formation:
            return "Aucune formation associée"
            
        formation = obj.formation
        return format_html(
            '<table class="formation-details">'
            '<tr><th>Nom:</th><td>{}</td></tr>'
            '<tr><th>Centre:</th><td>{}</td></tr>'
            '<tr><th>Statut:</th><td>{}</td></tr>'
            '<tr><th>Dates:</th><td>{} → {}</td></tr>'
            '<tr><th>Commentaires:</th><td>{}</td></tr>'
            '</table>',
            formation.nom,
            formation.centre.nom if formation.centre else "—",
            formation.statut.nom if formation.statut else "—",
            formation.start_date.strftime('%d/%m/%Y') if formation.start_date else "—",
            formation.end_date.strftime('%d/%m/%Y') if formation.end_date else "—",
            formation.commentaires.count()
        )
    formation_details.short_description = "Détails de la formation"

    def save_model(self, request, obj, form, change):
        """
        Assigne l'utilisateur connecté à l'ajout d'un commentaire et
        journalise l'opération.
        """
        if not change:  # Création d'un nouveau commentaire
            if not obj.utilisateur:
                # Vérifie que request.user est bien du bon type
                if isinstance(request.user, Utilisateur):
                    obj.utilisateur = request.user
                else:
                    obj.utilisateur = Utilisateur.objects.get(pk=request.user.pk)
                    
            logger.info(
                f"Admin - Création d'un commentaire par {request.user.username} "
                f"pour la formation '{obj.formation.nom if obj.formation else 'N/A'}'"
            )
        else:  # Modification d'un commentaire existant
            original = Commentaire.objects.get(pk=obj.pk)
            changes = []
            
            if original.contenu != obj.contenu:
                changes.append("contenu modifié")
                
            if original.saturation != obj.saturation:
                changes.append(f"saturation: {original.saturation}% → {obj.saturation}%")
                
            if original.formation != obj.formation:
                changes.append(
                    f"formation: '{original.formation.nom if original.formation else 'N/A'}' → "
                    f"'{obj.formation.nom if obj.formation else 'N/A'}'"
                )
                
            if changes:
                logger.info(
                    f"Admin - Modification du commentaire #{obj.pk} par {request.user.username}: "
                    f"{', '.join(changes)}"
                )
                
        obj.save()

    def delete_model(self, request, obj):
        """Journalise la suppression d'un commentaire depuis l'admin."""
        logger.warning(
            f"Admin - Suppression du commentaire #{obj.pk} "
            f"(créé le {obj.created_at.strftime('%d/%m/%Y')} "
            f"par {obj.utilisateur.username if obj.utilisateur else 'Anonyme'}) "
            f"pour la formation '{obj.formation.nom if obj.formation else 'N/A'}' "
            f"par {request.user.username}"
        )
        super().delete_model(request, obj)
        
    class Media:
        """Ressources CSS et JS pour l'interface d'admin."""
        css = {
            'all': ('css/admin/commentaire_admin.css',)
        }