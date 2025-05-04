import logging
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import F, Sum, Case, When, Value, IntegerField, FloatField, Q, Count
from django.urls import reverse
from django.utils import timezone

from ..models.formations import Formation, HistoriqueFormation

# Configuration du logger
logger = logging.getLogger("application.formation.admin")


class HistoriqueFormationInline(admin.TabularInline):
    """
    Inline pour afficher l'historique des modifications des formations.
    Permet de voir les changements récents directement dans la page d'édition de la formation.
    """
    model = HistoriqueFormation
    extra = 0
    readonly_fields = (
        'date_modification', 'action', 'champ_modifie', 
        'ancienne_valeur', 'nouvelle_valeur', 'modifie_par'
    )
    fields = readonly_fields
    can_delete = False
    max_num = 0  # Empêche l'ajout manuel
    verbose_name = "Historique de modification"
    verbose_name_plural = "Historique des modifications"
    
    def has_add_permission(self, request, obj=None):
        """Désactive l'ajout manuel d'historique"""
        return False
    
    def get_queryset(self, request):
        """Récupère les 10 dernières modifications"""
        queryset = super().get_queryset(request)
        return queryset.order_by('-date_modification')[:10]


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    """
    Administration du modèle Formation avec fonctionnalités avancées:
    - Affichage optimisé avec indicateurs visuels
    - Filtres contextuels
    - Statistiques globales
    - Actions personnalisées
    - Interface responsive
    """
    # Champs affichés dans la liste des formations
    list_display = (
        'nom', 
        'centre_display', 
        'type_offre_display', 
        'statut_display', 
        'statut',  # Ajout de ce champ pour list_editable
        'periode_display',
        'places_dispo_display', 
        'taux_saturation_display',
        'prospections_count',
        'evenements_count'
    )
    
    # Filtres dans la barre latérale avec filtres personnalisés
    list_filter = (
        'centre', 
        'statut', 
        'type_offre',
        ('start_date', admin.DateFieldListFilter),
        ('end_date', admin.DateFieldListFilter),
        'convocation_envoie',
    )
    
    # Champs de recherche
    search_fields = (
        'nom', 
        'num_kairos', 
        'num_offre', 
        'num_produit', 
        'assistante',
        'centre__nom',
        'type_offre__nom',
        'statut__nom'
    )
    
    # Actions personnalisées
    actions = [
        'marquer_convocation_envoyee', 
        'reset_convocation_envoyee',
        'export_selected_formations',
        'dupliquer_formations'
    ]
    
    # Champs pour édition rapide depuis la liste
    list_editable = (
        'statut',
    )
    
    # Champs cliquables dans la liste
    list_display_links = (
        'nom',
    )
    
    # Pagination pour la liste des formations
    list_per_page = 25
    
    # Filtres date dans le panneau latéral
    date_hierarchy = 'start_date'
    
    # Relations préchargées pour optimiser les performances
    list_select_related = ('centre', 'type_offre', 'statut', 'utilisateur')
    
    # Inlines pour afficher les relations
    inlines = [HistoriqueFormationInline]
    
    # Groupes de champs dans le formulaire d'édition
    fieldsets = (
        ('Informations générales', {
            'fields': (
                'nom', 
                'centre', 
                'type_offre', 
                'statut',
                'utilisateur'
            ),
            'description': 'Informations principales de la formation'
        }),
        ('Dates et identifiants', {
            'fields': (
                ('start_date', 'end_date'), 
                ('num_kairos', 'num_offre', 'num_produit'),
            ),
            'description': 'Dates et codes de référence pour la formation'
        }),
        ('Gestion des places', {
            'fields': (
                ('prevus_crif', 'inscrits_crif'),
                ('prevus_mp', 'inscrits_mp'),
                'cap',
                'entresformation',
                'calcul_places_disponibles'
            ),
            'description': 'Configuration des places et inscriptions'
        }),
        ('Recrutement', {
            'fields': (
                'nombre_candidats', 
                'nombre_entretiens', 
                'convocation_envoie',
                'calcul_taux_transformation'
            ),
            'description': 'Données liées au recrutement et à la sélection des candidats'
        }),
        ('Informations supplémentaires', {
            'fields': (
                'assistante', 
                'nombre_evenements',
                'dernier_commentaire',
                'partenaires'
            ),
            'classes': ('collapse',),
            'description': 'Informations complémentaires et associations'
        })
    )
    
    # Champs en lecture seule (calculés automatiquement)
    readonly_fields = (
        'calcul_places_disponibles',
        'calcul_taux_transformation',
    )
    
    # Sauvegarde en haut de page pour les longs formulaires
    save_on_top = True
    
    # Relations many-to-many dans un widget filtrable
    filter_horizontal = ('partenaires',)
    
    # Méthodes pour les champs personnalisés dans l'affichage en liste
    
    def centre_display(self, obj):
        """Affiche le centre avec lien vers sa page d'administration"""
        if obj.centre:
            url = reverse('admin:rap_app_centre_change', args=[obj.centre.id])
            return format_html('<a href="{}">{}</a>', url, obj.centre.nom)
        return "-"
    centre_display.short_description = "Centre"
    centre_display.admin_order_field = 'centre__nom'
    
    def type_offre_display(self, obj):
        """Affiche le type d'offre avec une pastille de couleur"""
        if obj.type_offre:
            color = "#3498db"  # Bleu par défaut
            return format_html(
                '<span style="color: white; background-color: {}; padding: 3px 7px; border-radius: 3px;">{}</span>',
                color, obj.type_offre.nom
            )
        return "-"
    type_offre_display.short_description = "Type d'offre"
    type_offre_display.admin_order_field = 'type_offre__nom'
    
    def statut_display(self, obj):
        """Affiche le statut avec une pastille de couleur basée sur sa valeur"""
        if obj.statut:
            # Récupérer la couleur depuis le modèle statut ou utiliser une couleur par défaut
            color = obj.get_status_color() if hasattr(obj, 'get_status_color') else "#7f8c8d"
            return format_html(
                '<span style="color: white; background-color: {}; padding: 3px 7px; border-radius: 3px;">{}</span>',
                color, obj.statut.nom
            )
        return "-"
    statut_display.short_description = "Statut"
    statut_display.admin_order_field = 'statut__nom'
    
    def periode_display(self, obj):
        """Affiche la période (à venir, en cours, terminée) avec formatage visuel"""
        today = timezone.now().date()
        
        if not obj.start_date:
            return format_html('<span style="color: #95a5a6;">Non programmée</span>')
        
        if obj.start_date > today:
            days = (obj.start_date - today).days
            return format_html(
                '<span style="color: #3498db;">À venir</span> <small>(dans {} jour{})</small>',
                days, 's' if days > 1 else ''
            )
        
        if not obj.end_date or obj.end_date >= today:
            if obj.end_date:
                days = (obj.end_date - today).days
                return format_html(
                    '<span style="color: #27ae60;">En cours</span> <small>({} jour{} restant{})</small>',
                    days, 's' if days > 1 else '', 's' if days > 1 else ''
                )
            return format_html('<span style="color: #27ae60;">En cours</span>')
        
        days = (today - obj.end_date).days
        return format_html(
            '<span style="color: #7f8c8d;">Terminée</span> <small>(depuis {} jour{})</small>',
            days, 's' if days > 1 else ''
        )
    periode_display.short_description = "Période"
    periode_display.admin_order_field = 'start_date'
    
    def places_dispo_display(self, obj):
        """Affiche le nombre de places disponibles avec formatage visuel"""
        if hasattr(obj, 'places_disponibles'):
            places = obj.places_disponibles
        else:
            places = obj.get_places_disponibles()
            
        total = obj.prevus_crif + obj.prevus_mp
        if total == 0:
            return format_html('<span style="color: #95a5a6;">N/A</span>')
            
        if places <= 0:
            return format_html('<span style="color: #e74c3c;">Complet</span>')
            
        color = '#27ae60' if places > 5 else '#f39c12' if places > 0 else '#e74c3c'
        return format_html(
            '<span style="color: {};">{}/{}</span>',
            color, places, total
        )
    places_dispo_display.short_description = "Places disponibles"
    places_dispo_display.admin_order_field = 'places_disponibles'
    
    def taux_saturation_display(self, obj):
        """Affiche le taux de saturation avec une barre de progression interactive"""
        if hasattr(obj, 'taux_saturation'):
            taux = obj.taux_saturation
        else:
            taux = obj.get_taux_saturation()
            
        if obj.prevus_crif + obj.prevus_mp == 0:
            return format_html('<span style="color: #95a5a6;">N/A</span>')
            
        taux = min(100, max(0, taux))  # Garantit que le taux est entre 0 et 100
        
        # Définition de la couleur en fonction du taux
        if taux < 70:
            color = '#27ae60'  # Vert
        elif taux < 95:
            color = '#f39c12'  # Orange
        else:
            color = '#e74c3c'  # Rouge
            
        return format_html(
            '<div class="progress" style="width:100px; height:10px; background-color:#ecf0f1; border-radius:5px;">'
            '<div style="width:{}%; height:100%; background-color:{}; border-radius:5px;" '
            'title="{}% de saturation"></div>'
            '</div>'
            '<span style="color: {};">{:.1f}%</span>',
            taux, color, taux, color, taux
        )
    taux_saturation_display.short_description = "Taux de saturation"
    taux_saturation_display.admin_order_field = 'taux_saturation'
    
    def evenements_count(self, obj):
        """Affiche le nombre d'événements avec lien vers la liste filtrée"""
        count = obj.nombre_evenements
        if count > 0:
            url = reverse('admin:rap_app_evenement_changelist') + f'?formation__id__exact={obj.id}'
            return format_html('<a href="{}" title="Voir les événements">{}</a>', url, count)
        return "0"
    evenements_count.short_description = "Événements"
    
    def prospections_count(self, obj):
        """Affiche le nombre de prospections avec lien vers la liste filtrée"""
        if hasattr(obj, 'nb_prospections'):
            count = obj.nb_prospections
        else:
            count = obj.prospections.count()
            
        if count > 0:
            url = reverse('admin:rap_app_prospection_changelist') + f'?formation__id__exact={obj.id}'
            return format_html('<a href="{}" title="Voir les prospections">{}</a>', url, count)
        return "0"
    prospections_count.short_description = "Prospections"
    
    def calcul_places_disponibles(self, obj):
        """Affiche le calcul détaillé des places disponibles"""
        places_crif = max(0, obj.prevus_crif - obj.inscrits_crif)
        places_mp = max(0, obj.prevus_mp - obj.inscrits_mp)
        total = places_crif + places_mp
        
        return format_html(
            '<div style="margin-top: 10px;">'
            '<p><strong>Places CRIF:</strong> {} - {} = <span style="color:#27ae60;">{}</span></p>'
            '<p><strong>Places MP:</strong> {} - {} = <span style="color:#27ae60;">{}</span></p>'
            '<p><strong>Total disponible:</strong> <span style="color:#2980b9; font-weight:bold;">{}</span></p>'
            '</div>',
            obj.prevus_crif, obj.inscrits_crif, places_crif,
            obj.prevus_mp, obj.inscrits_mp, places_mp,
            total
        )
    calcul_places_disponibles.short_description = "Calcul des places disponibles"
    
    def calcul_taux_transformation(self, obj):
        """Affiche le calcul du taux de transformation (candidats -> inscrits)"""
        inscrits = obj.inscrits_crif + obj.inscrits_mp
        
        if obj.nombre_candidats == 0:
            return format_html('<p>Pas de candidats enregistrés</p>')
            
        taux = (inscrits / obj.nombre_candidats) * 100
        
        if taux < 40:
            color = '#e74c3c'  # Rouge
        elif taux < 70:
            color = '#f39c12'  # Orange
        else:
            color = '#27ae60'  # Vert
            
        return format_html(
            '<div style="margin-top: 10px;">'
            '<p><strong>Candidats:</strong> {}</p>'
            '<p><strong>Inscrits:</strong> {}</p>'
            '<p><strong>Taux de transformation:</strong> <span style="color:{}; font-weight:bold;">{:.1f}%</span></p>'
            '</div>',
            obj.nombre_candidats, inscrits, color, taux
        )
    calcul_taux_transformation.short_description = "Calcul du taux de transformation"
    
    # Actions personnalisées
    
    def marquer_convocation_envoyee(self, request, queryset):
        """Marque les convocations comme envoyées pour les formations sélectionnées"""
        updated = queryset.update(convocation_envoie=True)
        logger.info(f"Admin: {request.user} a marqué {updated} formations avec convocations envoyées")
        self.message_user(request, f"{updated} formations marquées avec convocations envoyées.")
    marquer_convocation_envoyee.short_description = "Marquer les convocations comme envoyées"
    
    def reset_convocation_envoyee(self, request, queryset):
        """Réinitialise le statut d'envoi des convocations"""
        updated = queryset.update(convocation_envoie=False)
        logger.info(f"Admin: {request.user} a réinitialisé le statut des convocations pour {updated} formations")
        self.message_user(request, f"Statut d'envoi des convocations réinitialisé pour {updated} formations.")
    reset_convocation_envoyee.short_description = "Réinitialiser statut d'envoi des convocations"
    
    def export_selected_formations(self, request, queryset):
        """Exporte les formations sélectionnées au format CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="formations_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            "Nom", "Centre", "Type d'offre", "Statut", "Début", "Fin",
            "Places CRIF", "Inscrits CRIF", "Places MP", "Inscrits MP",
            "Candidats", "Entretiens", "Places disponibles", "Taux de saturation"
        ])
        
        for formation in queryset:
            writer.writerow([
                formation.nom,
                formation.centre.nom if formation.centre else "",
                formation.type_offre.nom if formation.type_offre else "",
                formation.statut.nom if formation.statut else "",
                formation.start_date.strftime('%d/%m/%Y') if formation.start_date else "",
                formation.end_date.strftime('%d/%m/%Y') if formation.end_date else "",
                formation.prevus_crif,
                formation.inscrits_crif,
                formation.prevus_mp,
                formation.inscrits_mp,
                formation.nombre_candidats,
                formation.nombre_entretiens,
                formation.get_places_disponibles(),
                f"{formation.get_taux_saturation():.1f}%"
            ])
            
        logger.info(f"Admin: {request.user} a exporté {queryset.count()} formations en CSV")
        return response
    export_selected_formations.short_description = "Exporter les formations sélectionnées"
    
    def dupliquer_formations(self, request, queryset):
        """Duplique les formations sélectionnées"""
        count = 0
        for formation in queryset:
            # Sauvegarde des relations many-to-many
            partenaires = list(formation.partenaires.all())
            
            # Duplication de la formation
            formation.pk = None
            formation.nom = f"Copie de {formation.nom}"
            formation.save()
            
            # Restauration des relations many-to-many
            formation.partenaires.add(*partenaires)
            
            count += 1
            
        logger.info(f"Admin: {request.user} a dupliqué {count} formations")
        self.message_user(request, f"{count} formations ont été dupliquées avec succès.")
    dupliquer_formations.short_description = "Dupliquer les formations sélectionnées"
    
    # Surcharge pour ajouter des annotations
    def get_queryset(self, request):
        """
        Optimise la requête avec des annotations pour les champs calculés.
        Ajoute des calculs pour les places disponibles, taux de saturation, etc.
        """
        queryset = super().get_queryset(request)
        
        # Ajout des calculs pour éviter les requêtes N+1
        queryset = queryset.annotate(
            # Places disponibles
            places_disponibles=F('prevus_crif') + F('prevus_mp') - F('inscrits_crif') - F('inscrits_mp'),
            
            # Taux de saturation
            taux_saturation=Case(
                When(Q(prevus_crif=0) & Q(prevus_mp=0), then=Value(0)),
                default=100 * (F('inscrits_crif') + F('inscrits_mp')) / 
                         (F('prevus_crif') + F('prevus_mp')),
                output_field=FloatField()
            ),
            
            # Nombre de prospections
            nb_prospections=Count('prospections', distinct=True),
        )
        
        return queryset

    # Statistiques personnalisées
    def changelist_view(self, request, extra_context=None):
        """
        Enrichit la vue de liste avec des statistiques globales.
        Ajoute des informations utiles pour avoir une vue d'ensemble.
        """
        response = super().changelist_view(request, extra_context)
        
        # Uniquement si nous ne faisons pas face à une erreur 404
        if hasattr(response, 'context_data'):
            queryset = self.get_queryset(request)
            today = timezone.now().date()
            
            # Calculer les statistiques globales
            stats = queryset.aggregate(
                total_formations=Count('id', distinct=True),
                total_places=Sum(F('prevus_crif') + F('prevus_mp')),
                total_inscrits=Sum(F('inscrits_crif') + F('inscrits_mp')),
                places_disponibles=Sum(F('prevus_crif') + F('prevus_mp') - F('inscrits_crif') - F('inscrits_mp')),
            )
            
            # Statistiques par période
            actives = queryset.filter(start_date__lte=today, end_date__gte=today).count()
            a_venir = queryset.filter(start_date__gt=today).count()
            terminees = queryset.filter(end_date__lt=today).count()
            
            # Créer le contexte enrichi
            if not extra_context:
                extra_context = {}
            
            # Vérifier que les valeurs ne sont pas None avant de calculer
            if stats['total_places'] and stats['total_inscrits']:
                taux_remplissage = (stats['total_inscrits'] / stats['total_places']) * 100
                extra_context['taux_remplissage_global'] = round(taux_remplissage, 1)
            else:
                extra_context['taux_remplissage_global'] = 0
                
            # Ajouter les statistiques supplémentaires
            extra_context.update(stats)
            extra_context.update({
                'formations_actives': actives,
                'formations_a_venir': a_venir,
                'formations_terminees': terminees,
            })
            
            # Mise à jour du contexte de la réponse
            response.context_data.update(extra_context)
            
        return response
    
    # Personnalisation de l'affichage
    
    class Media:
        """
        Ressources CSS et JS pour l'interface d'admin.
        Améliore l'expérience utilisateur avec des styles et fonctionnalités personnalisés.
        """
        css = {
            'all': ('css/admin/formation_admin.css',)
        }
        js = ('js/admin/formation_admin.js',)