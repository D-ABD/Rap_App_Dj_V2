import logging
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from django.contrib.admin.filters import SimpleListFilter
from django.utils.safestring import mark_safe

from ..models.company import Company
from ..models.prospection import Prospection

# Configuration du logger
logger = logging.getLogger(__name__)

# Filtre personnalisé pour les entreprises avec/sans prospections
class HasProspectionsFilter(SimpleListFilter):
    title = 'a des prospections'
    parameter_name = 'has_prospections'
    
    def lookups(self, request, model_admin):
        return (
            ('yes', 'Avec prospections'),
            ('no', 'Sans prospection')
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.annotate(prospections_count=Count('prospections')).filter(prospections_count__gt=0)
        if self.value() == 'no':
            return queryset.annotate(prospections_count=Count('prospections')).filter(prospections_count=0)
        return queryset

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """
    Interface d'administration personnalisée pour le modèle Company.
    """
    list_display = (
        'name',                 # Nom de l'entreprise
        'city_with_code',       # Ville avec code postal
        'contact_info',         # Informations de contact
        'sector_name',          # Secteur d'activité
        'actions_display',      # Type d'action
        'prospections_count',   # Nombre de prospections
        'website_link',         # Lien vers le site web
        'created_at',           # Date de création
        'created_by',           # Utilisateur qui a créé l'entrée
    )

    list_display_links = ('name',)

    list_filter = (
        'city',                # Filtre par ville
        'sector_name',         # Filtre par secteur d'activité
        'actions',             # Filtre par type d'action
        HasProspectionsFilter, # Filtre personnalisé
        'created_at',          # Filtre par date
    )

    search_fields = (
        'name',               # Recherche par nom d'entreprise
        'contact_name',       # Recherche par nom du contact
        'contact_email',      # Recherche par email du contact
        'contact_job',        # Recherche par poste du contact
        'sector_name',        # Recherche par secteur
        'city',               # Recherche par ville
        'zip_code',           # Recherche par code postal
    )

    fieldsets = (
        ("Informations générales", {
            'fields': (('name', 'sector_name'), ('street_name', 'zip_code', 'city', 'country')),
            'description': 'Informations principales de l\'entreprise'
        }),
        ("Contact", {
            'fields': (('contact_name', 'contact_job'), ('contact_email', 'contact_phone_number')),
            'description': 'Coordonnées du contact principal'
        }),
        ("Opportunités", {
            'fields': ('actions', 'action_description'),
            'description': 'Actions possibles avec cette entreprise'
        }),
        ("Présence en ligne", {
            'fields': ('website', 'social_network_url'),
            'description': 'Sites web et profils sur les réseaux sociaux'
        }),
        ("Métadonnées", {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'Informations sur la création et les modifications'
        }),
    )

    readonly_fields = ('created_at', 'updated_at', 'prospections_list')
    list_per_page = 20
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        """
        Optimise les requêtes en préchargeant les relations
        et en calculant le nombre de prospections.
        """
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('created_by').annotate(
            num_prospections=Count('prospections', distinct=True)
        )
        return queryset
    
    def city_with_code(self, obj):
        """Affiche la ville avec le code postal."""
        if obj.city and obj.zip_code:
            return f"{obj.city} ({obj.zip_code})"
        elif obj.city:
            return obj.city
        elif obj.zip_code:
            return f"CP: {obj.zip_code}"
        return "—"
    city_with_code.short_description = "Localisation"
    city_with_code.admin_order_field = 'city'
    
    def contact_info(self, obj):
        """Affiche les informations de contact de manière compacte."""
        if obj.contact_name:
            contact_parts = [obj.contact_name]
            if obj.contact_job:
                contact_parts.append(f"<em>{obj.contact_job}</em>")
            if obj.contact_email:
                contact_parts.append(f'<a href="mailto:{obj.contact_email}">{obj.contact_email}</a>')
            return format_html(' - '.join(contact_parts))
        return "—"
    contact_info.short_description = "Contact"
    contact_info.admin_order_field = 'contact_name'
    
    def actions_display(self, obj):
        """Affiche le type d'action avec une étiquette colorée."""
        if not obj.actions:
            return "—"
            
        action_labels = {
            'accueil_stagiaires': ('bg-info', 'Stagiaires'),
            'recrutement_cdi': ('bg-success', 'CDI'),
            'recrutement_cdd': ('bg-success', 'CDD'),
            'recrutement_stage': ('bg-info', 'Stage'),
            'recrutement_formation': ('bg-primary', 'Formation'),
            'recrutement_apprentissage': ('bg-warning', 'Apprentissage'),
            'partenariat': ('bg-primary', 'Partenariat'),
            'taxe_apprentissage': ('bg-warning', 'Taxe'),
        }
        
        # Valeur par défaut pour les actions non spécifiées
        bg_class, label = action_labels.get(obj.actions, ('bg-secondary', dict(obj.CHOICES_TYPE_OF_ACTION).get(obj.actions, 'Autre')))
        
        return format_html(
            '<span class="badge {}">{}</span>',
            bg_class, label
        )
    actions_display.short_description = "Action"
    actions_display.admin_order_field = 'actions'
    
    def website_link(self, obj):
        """Affiche un lien vers le site web s'il existe."""
        if obj.website:
            return format_html('<a href="{}" target="_blank">Visiter</a>', obj.website)
        return "—"
    website_link.short_description = "Site Web"
    
    def prospections_count(self, obj):
        """Affiche le nombre de prospections avec un lien vers le filtre."""
        count = getattr(obj, 'num_prospections', 0)
        if count > 0:
            url = reverse('admin:rap_app_prospection_changelist') + f'?company__id__exact={obj.pk}'
            return format_html('<a href="{}">{} prospection(s)</a>', url, count)
        return "Aucune"
    prospections_count.short_description = "Prospections"
    prospections_count.admin_order_field = 'num_prospections'
    
    def prospections_list(self, obj):
        """Affiche la liste des prospections associées dans le détail."""
        prospections = Prospection.objects.filter(company=obj).select_related('formation', 'responsable')
        if not prospections.exists():
            return "Aucune prospection associée à cette entreprise."
            
        html = ['<table class="table"><thead><tr>',
                '<th>Date</th><th>Formation</th><th>Statut</th><th>Objectif</th><th>Responsable</th>',
                '</tr></thead><tbody>']
        
        for p in prospections:
            formation_name = p.formation.nom if p.formation else "—"
            responsable_name = p.responsable.username if p.responsable else "—"
            
            html.append(f'<tr>')
            html.append(f'<td>{p.date_prospection.strftime("%d/%m/%Y")}</td>')
            html.append(f'<td>{formation_name}</td>')
            html.append(f'<td>{p.get_statut_display()}</td>')
            html.append(f'<td>{p.get_objectif_display()}</td>')
            html.append(f'<td>{responsable_name}</td>')
            html.append('</tr>')
            
        html.append('</tbody></table>')
        
        return mark_safe(''.join(html))
    prospections_list.short_description = "Activités de prospection"

    def save_model(self, request, obj, form, change):
        """
        Assigne l'utilisateur actuel comme créateur si nécessaire
        et journalise l'action.
        """
        is_new = not obj.pk
        
        if not obj.created_by:
            obj.created_by = request.user
        
        if is_new:
            logger.info(f"Admin - Création d'une nouvelle entreprise '{obj.name}' par {request.user.username}")
        else:
            if form.changed_data:
                logger.info(
                    f"Admin - Modification de l'entreprise #{obj.pk} '{obj.name}' par {request.user.username}. "
                    f"Champs modifiés: {', '.join(form.changed_data)}"
                )
                
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        """Journalise la suppression d'une entreprise."""
        logger.warning(
            f"Admin - Suppression de l'entreprise #{obj.pk} '{obj.name}' "
            f"par {request.user.username}"
        )
        super().delete_model(request, obj)

    def has_delete_permission(self, request, obj=None):
        """
        Empêche la suppression si l'entreprise a des prospections associées.
        """
        if obj is None:
            return True
            
        prospections_count = Prospection.objects.filter(company=obj).count()
        
        if prospections_count > 0:
            return False
            
        return True
    
    class Media:
        """Ressources CSS et JS pour l'interface d'admin."""
        css = {
            'all': ('css/admin/company_admin.css',)
        }