import logging
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, mark_safe
from django.db.models import Count
from django.contrib.admin import SimpleListFilter

from ..models.partenaires import Partenaire
from ..models import Formation


class PartenaireHasFormationsFilter(SimpleListFilter):
    """
    Filtre personnalisé pour filtrer les partenaires selon qu'ils ont ou non des formations associées.
    """
    title = 'Statut d\'activité'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('actif', 'Partenaires actifs (avec formations)'),
            ('inactif', 'Partenaires inactifs (sans formation)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'actif':
            return queryset.filter(formations__isnull=False).distinct()
        elif self.value() == 'inactif':
            return queryset.filter(formations__isnull=True)
        return queryset


class SecteurActiviteFilter(SimpleListFilter):
    """
    Filtre personnalisé pour les secteurs d'activité, qui regroupe les valeurs similaires.
    """
    title = 'Secteur d\'activité'
    parameter_name = 'secteur'

    def lookups(self, request, model_admin):
        # Récupération des secteurs d'activité avec regroupement intelligent
        secteurs = Partenaire.objects.exclude(
            secteur_activite__isnull=True
        ).exclude(
            secteur_activite=''
        ).values_list('secteur_activite', flat=True).distinct()
        
        # Création des choix avec comptage
        choices = []
        for secteur in sorted(secteurs):
            count = Partenaire.objects.filter(secteur_activite__icontains=secteur).count()
            choices.append((secteur, f"{secteur} ({count})"))
        
        return choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(secteur_activite__icontains=self.value())
        return queryset


@admin.register(Partenaire)
class PartenaireAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour le modèle Partenaire.
    
    Cette classe définit l'affichage, le filtrage, la recherche et les formulaires
    pour la gestion des partenaires dans l'interface d'administration Django.
    """
    list_display = (
        'nom', 
        'secteur_activite_display',
        'contact_info_display',
        'formations_count_display',
        'last_update_display',
    )
    
    list_filter = (
        PartenaireHasFormationsFilter,
        SecteurActiviteFilter,
    )
    
    search_fields = (
        'nom', 
        'secteur_activite',
        'contact_nom',
        'contact_email',
        'description',
    )
    
    readonly_fields = (
        'created_at', 
        'updated_at',
        'formations_list_display',
        'slug',
    )
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'slug', 'secteur_activite', 'description')
        }),
        ('Contact', {
            'fields': ('contact_nom', 'contact_poste', 'contact_telephone', 'contact_email'),
            'description': 'Informations sur la personne à contacter chez ce partenaire'
        }),
        ('Formations associées', {
            'fields': ('formations_list_display',),
            'classes': ('collapse',),
            'description': 'Liste des formations qui collaborent avec ce partenaire'
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    save_on_top = True
    list_per_page = 25
    
    def get_queryset(self, request):
        """
        Optimise les requêtes en annotant le nombre de formations.
        
        Returns:
            QuerySet: Partenaires annotés avec le nombre de formations
        """
        return super().get_queryset(request).annotate(
            formations_count=Count('formations', distinct=True)
        )
    
    def formations_count_display(self, obj):
        """
        Affiche le nombre de formations avec lien vers le filtre admin.
        
        Args:
            obj: Instance du partenaire
            
        Returns:
            SafeText: Formatage HTML du compteur avec lien
        """
        count = getattr(obj, 'formations_count', obj.formations.count())
        
        if count == 0:
            return format_html('<span style="color:#999;">Aucune formation</span>')
            
        url = reverse('admin:rap_app_formation_changelist') + f'?partenaires__id__exact={obj.id}'
        return format_html(
            '<a href="{}" class="badge" style="background-color:#007bff; color:white; '
            'padding:4px 8px; border-radius:10px; text-decoration:none;">{} formation{}</a>',
            url, count, 's' if count > 1 else ''
        )
    formations_count_display.short_description = 'Formations'
    formations_count_display.admin_order_field = 'formations_count'
    
    def secteur_activite_display(self, obj):
        """
        Affiche le secteur d'activité avec une présentation améliorée.
        
        Args:
            obj: Instance du partenaire
            
        Returns:
            SafeText: Formatage HTML du secteur d'activité
        """
        if not obj.secteur_activite:
            return format_html('<span style="color:#999;">Non défini</span>')
            
        return format_html(
            '<span class="badge" style="background-color:#6c757d; color:white; '
            'padding:3px 6px; border-radius:4px;">{}</span>',
            obj.secteur_activite
        )
    secteur_activite_display.short_description = "Secteur d'activité"
    secteur_activite_display.admin_order_field = 'secteur_activite'
    
    def contact_info_display(self, obj):
        """
        Affiche les informations de contact de façon condensée.
        
        Args:
            obj: Instance du partenaire
            
        Returns:
            SafeText: Formatage HTML des informations de contact
        """
        contact_parts = []
        
        if obj.contact_nom:
            contact_parts.append(f"<strong>{obj.contact_nom}</strong>")
        
        if obj.contact_poste:
            contact_parts.append(f"<em>{obj.contact_poste}</em>")
            
        if obj.contact_email:
            contact_parts.append(f'<a href="mailto:{obj.contact_email}">{obj.contact_email}</a>')
            
        if obj.contact_telephone:
            contact_parts.append(f'<span>{obj.contact_telephone}</span>')
            
        if not contact_parts:
            return format_html('<span style="color:#999;">Aucun contact défini</span>')
            
        return format_html(' | '.join(contact_parts))
    contact_info_display.short_description = "Contact"
    
    def last_update_display(self, obj):
        """
        Affiche la date de dernière mise à jour avec formatage.
        
        Args:
            obj: Instance du partenaire
            
        Returns:
            SafeText: Formatage HTML de la date de mise à jour
        """
        if not obj.updated_at:
            return "-"
            
        return format_html(
            '<span title="Créé le: {}">{}</span>',
            obj.created_at.strftime("%d/%m/%Y %H:%M"),
            obj.updated_at.strftime("%d/%m/%Y %H:%M")
        )
    last_update_display.short_description = "Dernière mise à jour"
    last_update_display.admin_order_field = 'updated_at'
    
    def formations_list_display(self, obj):
        """
        Affiche la liste détaillée des formations associées.
        
        Args:
            obj: Instance du partenaire
            
        Returns:
            SafeText: Formatage HTML de la liste des formations
        """
        formations = obj.formations.select_related('type_offre', 'statut', 'centre').all()
        
        if not formations:
            return format_html('<span style="color:#999;">Aucune formation associée</span>')
            
        formation_list = ['<div class="formations-list" style="margin-bottom:10px;">']
        
        for formation in formations:
            url = reverse('admin:rap_app_formation_change', args=[formation.id])
            status_color = "#28a745" if formation.statut and formation.statut.code == "active" else "#6c757d"
            
            formation_list.append(
                f'<div style="margin-bottom:5px;">'
                f'<a href="{url}" style="text-decoration:none;">'
                f'<span style="display:inline-block; width:12px; height:12px; '
                f'background-color:{status_color}; border-radius:50%; margin-right:5px;"></span>'
                f'{formation.nom}</a>'
                f'<span style="color:#777; font-size:0.9em;"> - {formation.centre.nom if formation.centre else "Centre non défini"}'
                f'</span></div>'
            )
            
        formation_list.append('</div>')
        return mark_safe(''.join(formation_list))
    formations_list_display.short_description = "Formations associées"
    
    # Actions personnalisées
    actions = ['mark_as_inactive', 'export_partenaires_csv']
    
    def mark_as_inactive(self, request, queryset):
        """
        Action personnalisée pour dissocier les partenaires des formations.
        
        Args:
            request: Requête HTTP
            queryset: QuerySet des partenaires sélectionnés
        """
        total_removed = 0
        
        for partenaire in queryset:
            formations_count = partenaire.formations.count()
            if formations_count > 0:
                # Enregistrement des formations avant dissociation pour le message
                formations = list(partenaire.formations.all())
                
                # Dissociation des formations
                partenaire.formations.clear()
                
                # Journalisation
                logger = logging.getLogger("application.admin")
                logger.info(
                    f"Admin: Utilisateur {request.user} a dissocié le partenaire '{partenaire.nom}' "
                    f"de {formations_count} formations"
                )
                
                total_removed += formations_count
        
        if total_removed > 0:
            self.message_user(
                request,
                f"{total_removed} associations entre partenaires et formations ont été supprimées."
            )
        else:
            self.message_user(
                request,
                "Aucune association n'a été supprimée. Les partenaires sélectionnés n'ont pas de formations associées.",
                level='WARNING'
            )
    mark_as_inactive.short_description = "Dissocier les partenaires sélectionnés des formations"
    
    def export_partenaires_csv(self, request, queryset):
        """
        Action personnalisée pour exporter les partenaires au format CSV.
        
        Args:
            request: Requête HTTP
            queryset: QuerySet des partenaires sélectionnés
            
        Returns:
            HttpResponse: Réponse HTTP avec le fichier CSV
        """
        import csv
        from django.http import HttpResponse
        from django.utils import timezone
        
        # Configuration de la réponse HTTP
        timestamp = timezone.now().strftime('%Y%m%d-%H%M%S')
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="partenaires-export-{timestamp}.csv"'
        
        # En-têtes CSV
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Nom', 'Secteur d\'activité', 'Contact Nom', 'Contact Poste',
            'Contact Téléphone', 'Contact Email', 'Nombre de formations', 'Date de création'
        ])
        
        # Données des partenaires
        for partenaire in queryset:
            writer.writerow([
                partenaire.id,
                partenaire.nom,
                partenaire.secteur_activite or '',
                partenaire.contact_nom or '',
                partenaire.contact_poste or '',
                partenaire.contact_telephone or '',
                partenaire.contact_email or '',
                partenaire.formations.count(),
                partenaire.created_at.strftime('%d/%m/%Y')
            ])
        
        # Journalisation de l'export
        logger = logging.getLogger("application.admin")
        logger.info(
            f"Admin: Utilisateur {request.user} a exporté {queryset.count()} partenaires au format CSV"
        )
        
        return response
    export_partenaires_csv.short_description = "Exporter les partenaires sélectionnés en CSV"
    
    def save_model(self, request, obj, form, change):
        """
        Personnalise la sauvegarde pour journaliser l'action d'administration.
        
        Args:
            request: Requête HTTP
            obj: Instance du partenaire
            form: Formulaire soumis
            change: Indique s'il s'agit d'une modification ou d'une création
        """
        # Journaliser l'action
        logger = logging.getLogger("application.admin")
        
        if change:
            logger.info(
                f"Admin: Utilisateur {request.user} a modifié le partenaire '{obj.nom}' (ID: {obj.pk})"
            )
        else:
            logger.info(
                f"Admin: Utilisateur {request.user} a créé un nouveau partenaire '{obj.nom}'"
            )
            
        super().save_model(request, obj, form, change)