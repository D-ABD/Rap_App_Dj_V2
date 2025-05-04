import logging
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count
from django.contrib.admin import SimpleListFilter
from django.utils import timezone

from ..models import Evenement


# Filtre personnalisé pour le statut de l'événement
class EventStatusFilter(SimpleListFilter):
    """
    Filtre personnalisé permettant de filtrer les événements par statut
    (passés, aujourd'hui, à venir, imminents).
    """
    title = 'Statut'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('past', 'Passés'),
            ('today', 'Aujourd\'hui'),
            ('coming_soon', 'Imminents (7 jours)'),
            ('future', 'À venir'),
        )

    def queryset(self, request, queryset):
        today = timezone.now().date()
        
        if self.value() == 'past':
            return queryset.filter(event_date__lt=today)
        elif self.value() == 'today':
            return queryset.filter(event_date=today)
        elif self.value() == 'coming_soon':
            return queryset.filter(event_date__gt=today, 
                                  event_date__lte=today + timezone.timedelta(days=7))
        elif self.value() == 'future':
            return queryset.filter(event_date__gt=today)
        return queryset


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour le modèle Evenement.
    
    Cette classe définit l'affichage, le filtrage, la recherche et les formulaires
    dans l'interface d'administration Django.
    """
    list_display = (
        'type_evenement_display', 
        'event_date_formatted', 
        'formation_link', 
        'lieu_display',
        'details_preview', 
        'participants_display',
        'status_badge',
        'created_at',
    )
    list_filter = (
        EventStatusFilter,
        'type_evenement', 
        'formation__centre',
        'event_date',
    )
    search_fields = (
        'formation__nom', 
        'details', 
        'description_autre',
        'lieu',
    )
    readonly_fields = (
        'created_at', 
        'updated_at', 
        'participation_rate_display',
        'status_display',
    )
    date_hierarchy = 'event_date'
    autocomplete_fields = ['formation']
    list_select_related = ('formation', 'formation__centre')
    save_on_top = True
    list_per_page = 25
    
    # Regroupement des champs par sections
    fieldsets = (
        ('Informations générales', {
            'fields': (
                'formation', 
                'type_evenement', 
                'description_autre', 
                'event_date',
                'lieu',
                'status_display',
            )
        }),
        ('Participants', {
            'fields': (
                'participants_prevus', 
                'participants_reels',
                'participation_rate_display',
            ),
            'description': 'Information sur la participation à l\'événement.'
        }),
        ('Détails', {
            'fields': ('details',),
            'classes': ('wide',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Personnalisation des actions disponibles
    actions = ['mark_as_completed']
    
    def get_queryset(self, request):
        """
        Optimise les requêtes en préchargeant les relations.
        """
        return super().get_queryset(request).select_related(
            'formation', 
            'formation__centre'
        )
    
    def formation_link(self, obj):
        """
        Génère un lien vers la formation associée à l'événement.
        """
        if obj.formation and obj.formation.id:
            url = reverse('admin:rap_app_formation_change', args=[obj.formation.id])
            return format_html(
                '<a href="{}" title="{}">{}</a>', 
                url, 
                f"Centre: {obj.formation.centre.nom if obj.formation.centre else 'N/A'}", 
                obj.formation.nom
            )
        return "Aucune formation"
    formation_link.short_description = "Formation"
    formation_link.admin_order_field = 'formation__nom'

    def type_evenement_display(self, obj):
        """
        Affiche le type d'événement ou la description personnalisée.
        """
        if obj.type_evenement == Evenement.AUTRE and obj.description_autre:
            return format_html('<span title="Type: Autre">{}</span>', obj.description_autre)
        return obj.get_type_evenement_display()
    type_evenement_display.short_description = "Type d'événement"
    type_evenement_display.admin_order_field = 'type_evenement'

    def event_date_formatted(self, obj):
        """
        Formate la date de l'événement de manière lisible.
        """
        if not obj.event_date:
            return "Non définie"
        
        today = timezone.now().date()
        formatted_date = obj.event_date.strftime('%d/%m/%Y')
        
        # Ajouter une indication visuelle selon la date
        if obj.event_date == today:
            return format_html('<b style="color: #d35400;">{} (Aujourd\'hui)</b>', formatted_date)
        elif obj.event_date < today:
            return format_html('<span style="color: #7f8c8d;">{}</span>', formatted_date)
        elif obj.event_date <= today + timezone.timedelta(days=7):
            return format_html('<b style="color: #2980b9;">{}</b>', formatted_date)
        
        return formatted_date
    event_date_formatted.short_description = "Date"
    event_date_formatted.admin_order_field = 'event_date'

    def details_preview(self, obj):
        """
        Génère un aperçu des détails avec bouton d'affichage complet.
        """
        if not obj.details:
            return "-"
            
        # Tronquer les détails s'ils sont trop longs
        max_length = 50
        preview = obj.details[:max_length] + ('...' if len(obj.details) > max_length else '')
        
        # Ajouter un bouton pour voir les détails complets
        if len(obj.details) > max_length:
            return format_html(
                '<span title="Cliquer pour voir tout le texte">{}</span> '
                '<button type="button" class="button" '
                'onclick="alert(\'{}\')">Voir</button>',
                preview, 
                obj.details.replace("'", "\\'").replace("\n", "\\n")
            )
        return preview
    details_preview.short_description = 'Détails'
    
    def participants_display(self, obj):
        """
        Affiche les informations sur les participants avec formatage conditionnel.
        """
        if obj.participants_prevus is None:
            return "-"
            
        if obj.participants_reels is not None:
            # Calcul du taux et couleur selon la valeur
            rate = (obj.participants_reels / obj.participants_prevus) * 100
            if rate >= 90:
                color = "green"
            elif rate >= 70:
                color = "orange"
            else:
                color = "red"
                
            return format_html(
                '<span title="Taux: {:.1f}%">'
                '<b style="color: {};">{}/{}</b>'
                '</span>',
                rate, color, obj.participants_reels, obj.participants_prevus
            )
        else:
            return f"{obj.participants_prevus} prévus"
    participants_display.short_description = "Participants"
    
    def participation_rate_display(self, obj):
        """
        Calcule et affiche le taux de participation.
        """
        rate = obj.get_participation_rate()
        if rate is None:
            return "Données incomplètes"
            
        # Formatage avec code couleur selon le taux
        if rate >= 90:
            color_class = "success"
        elif rate >= 70:
            color_class = "warning"
        else:
            color_class = "error"
            
        return format_html(
            '<span style="font-weight: bold; color: {};">{:.1f}%</span>',
            {"success": "green", "warning": "orange", "error": "red"}[color_class],
            rate
        )
    participation_rate_display.short_description = "Taux de participation"
    
    def status_display(self, obj):
        """
        Affiche le statut actuel de l'événement.
        """
        status = obj.get_status_display()
        
        # Définition des couleurs selon le statut
        colors = {
            "Passé": "#7f8c8d",
            "Aujourd'hui": "#d35400",
            "À venir": "#2980b9"
        }
        
        return format_html(
            '<span style="font-weight: bold; color: {};">{}</span>',
            colors.get(status, "black"),
            status
        )
    status_display.short_description = "Statut"
    
    def status_badge(self, obj):
        """
        Génère un badge visuel pour indiquer le statut de l'événement.
        """
        if obj.is_past():
            return mark_safe('<span style="color: white; background-color: #7f8c8d; padding: 3px 6px; border-radius: 3px;">Passé</span>')
        elif obj.is_today():
            return mark_safe('<span style="color: white; background-color: #d35400; padding: 3px 6px; border-radius: 3px;">Aujourd\'hui</span>')
        elif obj.is_coming_soon():
            return mark_safe('<span style="color: white; background-color: #2980b9; padding: 3px 6px; border-radius: 3px;">Imminent</span>')
        else:
            return mark_safe('<span style="color: white; background-color: #27ae60; padding: 3px 6px; border-radius: 3px;">À venir</span>')
    status_badge.short_description = "Statut"
    
    def lieu_display(self, obj):
        """
        Affiche le lieu de l'événement ou une valeur par défaut.
        """
        if obj.lieu:
            return obj.lieu
        return format_html('<span style="color: #999;">Non défini</span>')
    lieu_display.short_description = "Lieu"
    lieu_display.admin_order_field = 'lieu'
    
    def mark_as_completed(self, request, queryset):
        """
        Action personnalisée pour marquer les événements comme terminés.
        
        Cette action permet de mettre à jour les événements sélectionnés
        pour indiquer qu'ils sont terminés, en mettant participants_reels
        égal à participants_prevus s'il n'est pas défini.
        """
        updated = 0
        for event in queryset:
            if event.participants_prevus and event.participants_reels is None:
                event.participants_reels = event.participants_prevus
                event.save()
                updated += 1
                
        if updated:
            self.message_user(
                request, 
                f"{updated} événement(s) ont été marqués comme terminés."
            )
        else:
            self.message_user(
                request,
                "Aucun événement n'a été mis à jour. Vérifiez que les événements "
                "sélectionnés ont des participants prévus mais pas de participants réels.",
                level='WARNING'
            )
    mark_as_completed.short_description = "Marquer les événements sélectionnés comme terminés"
    
    # Personnalisation de l'interface d'édition
    def get_fieldsets(self, request, obj=None):
        """
        Ajuste les sections du formulaire selon que l'objet existe ou non.
        """
        fieldsets = super().get_fieldsets(request, obj)
        
        # Pour un nouvel événement, simplifie le formulaire
        if obj is None:
            return (
                ('Informations générales', {
                    'fields': (
                        'formation', 
                        'type_evenement', 
                        'description_autre', 
                        'event_date',
                        'lieu',
                    )
                }),
                ('Participants', {
                    'fields': ('participants_prevus',),
                }),
                ('Détails', {
                    'fields': ('details',),
                }),
            )
        return fieldsets
    
    def save_model(self, request, obj, form, change):
        """
        Personnalise la sauvegarde pour journaliser l'action d'administration.
        """
        # Journaliser l'action
        logger = logging.getLogger("application.admin")
        
        if change:
            logger.info(
                f"Admin: Utilisateur {request.user} a modifié l'événement #{obj.pk}"
            )
        else:
            logger.info(
                f"Admin: Utilisateur {request.user} a créé un nouvel événement de type '{obj.get_type_evenement_display()}'"
            )
            
        super().save_model(request, obj, form, change)