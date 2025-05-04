import logging
from django.urls import reverse_lazy
from django.db.models import Q, Count, Prefetch
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.db import transaction

from ..models import Evenement, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView

# Configuration du logger avec un nom plus spécifique
logger = logging.getLogger("application.evenements.views")


class EvenementListView(BaseListView):
    """
    Vue listant tous les événements avec options de filtrage avancé.
    
    Cette vue implémente:
    - Filtrage par formation, type et période
    - Recherche textuelle
    - Optimisation des requêtes avec select_related et prefetch_related
    - Pagination des résultats
    """
    model = Evenement
    context_object_name = 'evenements'
    template_name = 'evenements/evenement_list.html'
    paginate_by = 20  # Pagination pour améliorer les performances
    
    def get_queryset(self):
        """
        Récupère la liste des événements avec possibilité de filtrage par:
        - Formation associée
        - Type d'événement
        - Date (à venir, passés)
        - Recherche textuelle
        
        Returns:
            QuerySet: Liste filtrée des événements avec optimisations de requête
        """
        # Requête de base avec optimisations
        queryset = super().get_queryset().select_related(
            'formation', 
            'formation__centre',
        )
        
        # Logging de la requête initiale pour le débogage
        logger.debug(f"EvenementListView: Requête initiale avec {queryset.count()} événements")
        
        # Application des filtres
        queryset = self._apply_filters(queryset)
        
        # Logging après filtrage
        logger.debug(f"EvenementListView: Après filtrage, {queryset.count()} événements correspondent")
        
        return queryset
    
    def _apply_filters(self, queryset):
        """
        Méthode auxiliaire pour appliquer les filtres à la requête.
        
        Args:
            queryset: QuerySet initial des événements
            
        Returns:
            QuerySet: QuerySet filtré selon les paramètres de la requête
        """
        # Filtrage par formation
        formation_id = self.request.GET.get('formation')
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
            
        # Filtrage par type d'événement
        type_evt = self.request.GET.get('type')
        if type_evt:
            queryset = queryset.filter(type_evenement=type_evt)
            
        # Filtrage par période (à venir/passés)
        periode = self.request.GET.get('periode')
        today = timezone.now().date()
        
        if periode == 'future':
            queryset = queryset.filter(event_date__gte=today)
        elif periode == 'past':
            queryset = queryset.filter(event_date__lt=today)
        elif periode == 'today':
            queryset = queryset.filter(event_date=today)
        elif periode == 'week':
            next_week = today + timezone.timedelta(days=7)
            queryset = queryset.filter(event_date__gte=today, event_date__lte=next_week)
            
        # Recherche textuelle
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(details__icontains=q) | 
                Q(description_autre__icontains=q) |
                Q(formation__nom__icontains=q) |
                Q(lieu__icontains=q)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Enrichit le contexte avec des données supplémentaires pour les filtres et statistiques.
        
        Args:
            **kwargs: Arguments de contexte par défaut
            
        Returns:
            dict: Contexte enrichi pour le template
        """
        context = super().get_context_data(**kwargs)
        
        # Filtres actuellement appliqués pour maintenir l'état dans le formulaire
        context['filters'] = {
            'formation': self.request.GET.get('formation', ''),
            'type': self.request.GET.get('type', ''),
            'periode': self.request.GET.get('periode', ''),
            'q': self.request.GET.get('q', ''),
        }
        
        # Liste des formations avec nombre d'événements pour le filtrage (optimisé)
        context['formations'] = Formation.objects.annotate(
            nb_evenements=Count('evenements')
        ).filter(nb_evenements__gt=0)
        
        # Types d'événements pour le filtrage avec statistiques
        context['types_evenement'] = Evenement.TYPE_EVENEMENT_CHOICES
        
        # Statistiques sur les événements (nombre par type, par période)
        today = timezone.now().date()
        
        # Ajout de statistiques
        context.update({
            'now': today,
            'stats': {
                'total': Evenement.objects.count(),
                'today': Evenement.objects.filter(event_date=today).count(),
                'future': Evenement.objects.filter(event_date__gt=today).count(),
                'past': Evenement.objects.filter(event_date__lt=today).count(),
            },
        })
        
        return context


class EvenementDetailView(BaseDetailView):
    """
    Vue affichant les détails d'un événement avec optimisation des requêtes.
    
    Cette vue enrichit le contexte avec:
    - Les détails de l'événement
    - Des informations sur la formation associée
    - Des statistiques sur la participation
    """
    model = Evenement
    context_object_name = 'evenement'
    template_name = 'evenements/evenement_detail.html'
    
    def get_queryset(self):
        """
        Optimise la requête pour la vue détaillée.
        
        Returns:
            QuerySet: QuerySet optimisé pour charger les relations en une seule requête
        """
        return super().get_queryset().select_related(
            'formation', 
            'formation__centre'
        )
    
    def get_context_data(self, **kwargs):
        """
        Enrichit le contexte avec des données supplémentaires.
        
        Args:
            **kwargs: Arguments de contexte par défaut
            
        Returns:
            dict: Contexte enrichi pour le template
        """
        context = super().get_context_data(**kwargs)
        
        # Calcul du taux de participation si possible
        evenement = self.object
        context['taux_participation'] = evenement.get_participation_rate()
        
        # Ajout d'événements similaires (même formation ou même type)
        if evenement.formation:
            context['evenements_similaires'] = Evenement.objects.filter(
                formation=evenement.formation
            ).exclude(
                pk=evenement.pk
            ).order_by('-event_date')[:5]
        
        # Date actuelle pour comparaison
        context['now'] = timezone.now().date()
        
        return context


class EvenementCreateView(PermissionRequiredMixin, BaseCreateView):
    """
    Vue permettant de créer un nouvel événement avec validation avancée.
    
    Cette vue implémente:
    - Préremplissage du formulaire si une formation est spécifiée
    - Validation des données avant sauvegarde
    - Journalisation des actions
    - Messages de confirmation
    """
    model = Evenement
    permission_required = 'rap_app.add_evenement'
    fields = [
        'formation', 'type_evenement', 'details', 'event_date', 
        'description_autre', 'lieu', 'participants_prevus'
    ]
    template_name = 'evenements/evenement_form.html'
    
    def get_initial(self):
        """
        Pré-remplit le formulaire avec la formation si spécifiée dans l'URL.
        
        Returns:
            dict: Valeurs initiales pour le formulaire
        """
        initial = super().get_initial()
        formation_id = self.request.GET.get('formation')
        
        if formation_id:
            initial['formation'] = formation_id
            # Date par défaut = aujourd'hui pour faciliter la saisie
            initial['event_date'] = timezone.now().date()
            
        return initial
    
    def form_valid(self, form):
        """
        Validation personnalisée du formulaire avec journalisation.
        
        Args:
            form: Formulaire soumis
            
        Returns:
            HttpResponse: Redirection après sauvegarde
        """
        # Journalisation de la création
        response = super().form_valid(form)
        
        # Message de confirmation pour l'utilisateur
        messages.success(
            self.request, 
            f"L'événement '{self.object}' a été créé avec succès."
        )
        
        # Journalisation détaillée
        logger.info(
            f"Utilisateur {self.request.user} a créé l'événement #{self.object.pk}: {self.object}"
        )
        
        return response
    
    def get_success_url(self):
        """
        Redirige vers la formation associée après création.
        
        Returns:
            str: URL de redirection après sauvegarde réussie
        """
        if self.object.formation:
            return reverse_lazy('formation-detail', kwargs={'pk': self.object.formation.pk})
        return reverse_lazy('evenement-list')
    
    def get_context_data(self, **kwargs):
        """
        Enrichit le contexte avec des données supplémentaires.
        
        Args:
            **kwargs: Arguments de contexte par défaut
            
        Returns:
            dict: Contexte enrichi pour le template
        """
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un événement"
        context['types_evenement'] = Evenement.TYPE_EVENEMENT_CHOICES
        context['is_new'] = True
        
        # Ajout de la liste des formations pour la sélection
        formation_id = self.request.GET.get('formation')
        if formation_id:
            context['formation_preselected'] = Formation.objects.get(pk=formation_id)
            
        return context


class EvenementUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """
    Vue permettant de modifier un événement existant avec validation avancée.
    
    Cette vue implémente:
    - Validation des données avant sauvegarde
    - Journalisation des modifications
    - Messages de confirmation
    - Gestion des erreurs
    """
    model = Evenement
    permission_required = 'rap_app.change_evenement'
    fields = [
        'formation', 'type_evenement', 'details', 'event_date', 
        'description_autre', 'lieu', 'participants_prevus', 'participants_reels'
    ]
    template_name = 'evenements/evenement_form.html'
    
    def get_form(self, form_class=None):
        """
        Personnalisation du formulaire en fonction du statut de l'événement.
        
        Returns:
            Form: Formulaire personnalisé
        """
        form = super().get_form(form_class)
        
        # Si l'événement est passé, activer le champ des participants réels
        if self.object.is_past():
            form.fields['participants_reels'].widget.attrs['class'] = 'form-control highlight'
            form.fields['participants_reels'].help_text += " (Événement passé, merci de renseigner ce champ)"
            
        return form
    
    def form_valid(self, form):
        """
        Validation personnalisée du formulaire avec journalisation des modifications.
        
        Args:
            form: Formulaire soumis
            
        Returns:
            HttpResponse: Redirection après sauvegarde
        """
        # Sauvegarde avec transaction pour garantir l'intégrité
        with transaction.atomic():
            # Récupération de l'instance originale avant modification pour comparaison
            original = Evenement.objects.get(pk=self.object.pk)
            
            # Validation standard
            response = super().form_valid(form)
            
            # Message de confirmation pour l'utilisateur
            messages.success(
                self.request, 
                f"L'événement '{self.object}' a été mis à jour avec succès."
            )
            
            # Journalisation détaillée des modifications
            changes = self._get_changes_description(original, self.object)
            if changes:
                logger.info(
                    f"Utilisateur {self.request.user} a modifié l'événement #{self.object.pk}: {changes}"
                )
            
        return response
    
    def _get_changes_description(self, original, updated):
        """
        Méthode auxiliaire pour générer une description des modifications.
        
        Args:
            original: Instance originale avant modification
            updated: Instance après modification
            
        Returns:
            str: Description des modifications
        """
        changes = []
        
        # Définition des champs à vérifier et leur affichage
        fields_to_check = {
            'type_evenement': {
                'display': lambda obj: obj.get_type_evenement_display(), 
                'label': 'type'
            },
            'event_date': {
                'display': lambda obj: obj.event_date.strftime('%d/%m/%Y') if obj.event_date else 'non spécifiée',
                'label': 'date'
            },
            'formation': {
                'display': lambda obj: obj.formation.nom if obj.formation else 'N/A',
                'label': 'formation'
            },
            'lieu': {
                'display': lambda obj: obj.lieu if obj.lieu else 'non spécifié',
                'label': 'lieu'
            },
            'participants_prevus': {
                'display': lambda obj: str(obj.participants_prevus) if obj.participants_prevus is not None else 'non spécifié',
                'label': 'participants prévus'
            },
            'participants_reels': {
                'display': lambda obj: str(obj.participants_reels) if obj.participants_reels is not None else 'non spécifié',
                'label': 'participants réels'
            }
        }
        
        # Vérification des changements pour chaque champ
        for field, config in fields_to_check.items():
            old_value = getattr(original, field)
            new_value = getattr(updated, field)
            
            if old_value != new_value:
                old_display = config['display'](original)
                new_display = config['display'](updated)
                changes.append(f"{config['label']}: '{old_display}' → '{new_display}'")
        
        return ", ".join(changes) if changes else ""
    
    def get_success_url(self):
        """
        Redirige vers la formation associée après modification.
        
        Returns:
            str: URL de redirection après sauvegarde réussie
        """
        if self.object.formation:
            return reverse_lazy('formation-detail', kwargs={'pk': self.object.formation.pk})
        return reverse_lazy('evenement-list')
    
    def get_context_data(self, **kwargs):
        """
        Enrichit le contexte avec des données supplémentaires.
        
        Args:
            **kwargs: Arguments de contexte par défaut
            
        Returns:
            dict: Contexte enrichi pour le template
        """
        context = super().get_context_data(**kwargs)
        
        # Titre dynamique basé sur l'événement
        if self.object.event_date:
            context['titre'] = f"Modifier l'événement du {self.object.event_date.strftime('%d/%m/%Y')}"
        else:
            context['titre'] = f"Modifier l'événement: {self.object.get_type_evenement_display()}"
            
        # Ajout de la liste des types d'événements
        context['types_evenement'] = Evenement.TYPE_EVENEMENT_CHOICES
        context['is_new'] = False
        context['is_past'] = self.object.is_past()
        
        return context


class EvenementDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """
    Vue permettant de supprimer un événement avec confirmation et journalisation.
    
    Cette vue implémente:
    - Confirmation de suppression
    - Journalisation de l'action
    - Messages de confirmation
    - Redirection intelligente
    """
    model = Evenement
    permission_required = 'rap_app.delete_evenement'
    template_name = 'evenements/evenement_confirm_delete.html'
    
    def get_context_data(self, **kwargs):
        """
        Enrichit le contexte pour la confirmation de suppression.
        
        Args:
            **kwargs: Arguments de contexte par défaut
            
        Returns:
            dict: Contexte enrichi pour le template de confirmation
        """
        context = super().get_context_data(**kwargs)
        # Ajoute des informations supplémentaires pour la confirmation
        context['formation'] = self.object.formation
        context['evenement_info'] = {
            'type': self.object.get_type_evenement_display(),
            'date': self.object.event_date.strftime('%d/%m/%Y') if self.object.event_date else 'Date non spécifiée',
            'lieu': self.object.lieu if self.object.lieu else 'Non spécifié',
            'status': self.object.get_status_display(),
        }
        
        return context
    
    def get_success_url(self):
        """
        Redirige vers la formation associée après suppression.
        
        Returns:
            str: URL de redirection après suppression réussie
        """
        if hasattr(self, 'formation_id') and self.formation_id:
            return reverse_lazy('formation-detail', kwargs={'pk': self.formation_id})
        return reverse_lazy('evenement-list')
    
    def delete(self, request, *args, **kwargs):
        """
        Personnalisation de la suppression avec journalisation.
        
        Cette méthode:
        - Stocke l'ID de la formation pour la redirection
        - Journalise l'action de suppression
        - Ajoute un message de confirmation
        
        Args:
            request: Requête HTTP
            *args, **kwargs: Arguments supplémentaires
            
        Returns:
            HttpResponse: Redirection après suppression
        """
        self.object = self.get_object()
        evenement_str = str(self.object)
        self.formation_id = self.object.formation.id if self.object.formation else None
        
        # Journalisation avant suppression
        logger.info(
            f"Utilisateur {request.user} a supprimé l'événement #{self.object.pk}: {evenement_str} "
            f"(formation: {self.object.formation.nom if self.object.formation else 'N/A'})"
        )
        
        # Suppression effective
        response = super().delete(request, *args, **kwargs)
        
        # Message de confirmation
        messages.success(
            request,
            f"L'événement '{evenement_str}' a été supprimé avec succès."
        )
        
        return response