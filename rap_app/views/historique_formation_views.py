from datetime import timedelta
import logging
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, DeleteView
from django.utils.timezone import datetime
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.db import transaction
from django.db.models import Q

from ..models.formations import Formation
from ..models import HistoriqueFormation

# Configuration du logger
logger = logging.getLogger("application.historique_formation.views")


class HistoriqueFormationListView(LoginRequiredMixin, ListView):
    """
    Vue listant l'historique des modifications des formations avec options de filtrage.
    
    Cette vue implémente:
    - Filtrage par formation
    - Filtrage par date
    - Pagination des résultats
    - Préchargement des relations pour optimiser les performances
    """
    model = HistoriqueFormation
    template_name = 'historiqueformation/historiqueformation_list.html'
    context_object_name = 'historiques'
    paginate_by = 20  # Augmentation pour une meilleure expérience utilisateur
    
    def get_queryset(self):
        """
        Récupère la liste des entrées d'historique avec filtrage.
        
        Returns:
            QuerySet: Liste filtrée d'entrées d'historique avec préchargement des relations
        """
        # Récupération de la requête de base avec optimisation
        queryset = super().get_queryset().select_related(
            "formation", "formation__centre", "formation__type_offre", 
            "formation__statut", "modifie_par"
        )
        
        # Journalisation du début de la requête
        logger.debug(f"HistoriqueFormationListView: Début de la récupération des historiques")
        
        # Application des filtres
        queryset = self._apply_filters(queryset)
        
        # Journalisation après filtrage
        logger.debug(f"HistoriqueFormationListView: {queryset.count()} historiques après filtrage")
        
        # Tri par date de modification (plus récent d'abord)
        return queryset.order_by("-date_modification")
    
    def _apply_filters(self, queryset):
        """
        Méthode auxiliaire pour appliquer les filtres à la requête.
        
        Args:
            queryset (QuerySet): QuerySet initial des historiques
            
        Returns:
            QuerySet: QuerySet filtré selon les paramètres de la requête
        """
        # Récupération des paramètres de filtrage
        formation_id = self.request.GET.get("formation")
        date = self.request.GET.get("date")
        champ = self.request.GET.get("champ")
        utilisateur = self.request.GET.get("utilisateur")
        action = self.request.GET.get("action")
        periode = self.request.GET.get("periode")
        q = self.request.GET.get("q")
        
        # Filtrage par formation
        if formation_id:
            queryset = queryset.filter(formation__id=formation_id)
            logger.debug(f"Filtre par formation: {formation_id}")
        
        # Filtrage par date spécifique
        if date:
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
                queryset = queryset.filter(date_modification__date=parsed_date)
                logger.debug(f"Filtre par date: {parsed_date}")
            except ValueError:
                logger.warning(f"Format de date invalide: {date}")
                # Ignorer les dates mal formatées
        
        # Filtrage par champ modifié
        if champ:
            queryset = queryset.filter(champ_modifie=champ)
            logger.debug(f"Filtre par champ: {champ}")
        
        # Filtrage par utilisateur (modifie_par)
        if utilisateur and utilisateur.isdigit():
            queryset = queryset.filter(modifie_par_id=utilisateur)
            logger.debug(f"Filtre par utilisateur: {utilisateur}")
        
        # Filtrage par type d'action
        if action:
            queryset = queryset.filter(action=action)
            logger.debug(f"Filtre par action: {action}")
        
        # Filtrage par période
        if periode:
            today = datetime.now().date()
            if periode == "today":
                queryset = queryset.filter(date_modification__date=today)
            elif periode == "week":
                # Cette semaine (7 derniers jours)
                queryset = queryset.filter(
                    date_modification__date__gte=today - timedelta(days=7),
                    date_modification__date__lte=today
                )
            elif periode == "month":
                # Ce mois-ci (30 derniers jours)
                queryset = queryset.filter(
                    date_modification__date__gte=today - timedelta(days=30),
                    date_modification__date__lte=today
                )
            logger.debug(f"Filtre par période: {periode}")
        
        # Recherche textuelle
        if q:
            queryset = queryset.filter(
                Q(champ_modifie__icontains=q) |
                Q(ancienne_valeur__icontains=q) |
                Q(nouvelle_valeur__icontains=q) |
                Q(commentaire__icontains=q) |
                Q(formation__nom__icontains=q)
            )
            logger.debug(f"Recherche de: {q}")
        
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
        
        # Récupération de toutes les formations pour le filtre
        context['formations'] = Formation.objects.all().order_by("nom")
        
        # État des filtres pour maintenir la sélection
        context['filtres'] = {
            'formation': self.request.GET.get("formation", ""),
            'date': self.request.GET.get("date", ""),
            'champ': self.request.GET.get("champ", ""),
            'utilisateur': self.request.GET.get("utilisateur", ""),
            'action': self.request.GET.get("action", ""),
            'periode': self.request.GET.get("periode", ""),
            'q': self.request.GET.get("q", ""),
        }
        
        # Statistiques sur les modifications
        context['stats'] = {
            'total': HistoriqueFormation.objects.count(),
            'champs_courants': HistoriqueFormation.objects.values('champ_modifie').distinct().count(),
            'actions': HistoriqueFormation.objects.values('action').distinct().count(),
        }
        
        # Liste des champs modifiés pour le filtre
        champs_modifies = HistoriqueFormation.objects.values_list(
            'champ_modifie', flat=True
        ).distinct().order_by('champ_modifie')
        context['champs_modifies'] = champs_modifies
        
        # Liste des actions pour le filtre
        actions = HistoriqueFormation.objects.values_list(
            'action', flat=True
        ).distinct().order_by('action')
        context['actions'] = actions
        
        # Si une formation spécifique est sélectionnée, ajouter ses détails
        formation_id = self.request.GET.get("formation")
        if formation_id:
            try:
                formation = Formation.objects.get(pk=formation_id)
                context['formation_selectionnee'] = formation
                
                # Nombre total de modifications pour cette formation
                context['total_modifications'] = HistoriqueFormation.objects.filter(
                    formation=formation
                ).count()
            except Formation.DoesNotExist:
                # La formation n'existe pas, ignorer
                pass
        
        return context


class HistoriqueFormationDetailView(LoginRequiredMixin, DetailView):
    """
    Vue affichant les détails d'une entrée d'historique de formation.
    
    Cette vue affiche les informations complètes sur une modification
    spécifique, y compris l'utilisateur qui l'a effectuée et les
    valeurs avant/après modification.
    """
    model = HistoriqueFormation
    template_name = 'historiqueformation/historiqueformation_detail.html'
    context_object_name = 'historique'
    
    def get_object(self, queryset=None):
        """
        Récupère l'objet HistoriqueFormation avec optimisation des requêtes.
        
        Returns:
            HistoriqueFormation: Instance de l'historique avec préchargement des relations
        """
        # Récupération de l'objet avec ses relations
        obj = super().get_object(queryset)
        
        # Journalisation de la consultation
        logger.info(f"Consultation de l'historique de formation #{obj.pk} par {self.request.user}")
        
        return obj
    
    def get_context_data(self, **kwargs):
        """
        Enrichit le contexte avec des informations supplémentaires.
        
        Args:
            **kwargs: Arguments de contexte par défaut
            
        Returns:
            dict: Contexte enrichi pour le template
        """
        context = super().get_context_data(**kwargs)
        historique = self.object
        
        # Récupération de l'entrée précédente et suivante pour faciliter la navigation
        try:
            context['historique_precedent'] = HistoriqueFormation.objects.filter(
                formation=historique.formation,
                date_modification__lt=historique.date_modification
            ).order_by('-date_modification').first()
        except:
            context['historique_precedent'] = None
            
        try:
            context['historique_suivant'] = HistoriqueFormation.objects.filter(
                formation=historique.formation,
                date_modification__gt=historique.date_modification
            ).order_by('date_modification').first()
        except:
            context['historique_suivant'] = None
        
        # Autres modifications de la même formation
        context['autres_modifications'] = HistoriqueFormation.objects.filter(
            formation=historique.formation
        ).exclude(
            pk=historique.pk
        ).order_by('-date_modification')[:5]
        
        # Modifications du même champ
        if historique.champ_modifie:
            context['modifications_meme_champ'] = HistoriqueFormation.objects.filter(
                champ_modifie=historique.champ_modifie
            ).exclude(
                pk=historique.pk
            ).order_by('-date_modification')[:5]
        
        return context


class HistoriqueFormationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Vue permettant de supprimer une entrée d'historique de formation.
    
    Cette vue n'est accessible qu'aux utilisateurs ayant les permissions
    nécessaires, car la suppression d'historique est une action sensible.
    """
    model = HistoriqueFormation
    template_name = "historiqueformation/historiqueformation_confirm_delete.html"
    success_url = reverse_lazy("historique-formation-list")
    permission_required = "rap_app.delete_historiqueformation"
    
    def get_object(self, queryset=None):
        """
        Récupère l'objet HistoriqueFormation à supprimer.
        
        Returns:
            HistoriqueFormation: Instance de l'historique à supprimer
        """
        obj = super().get_object(queryset)
        
        # Journalisation de la tentative de suppression
        logger.warning(
            f"Tentative de suppression de l'historique de formation #{obj.pk} "
            f"par {self.request.user}"
        )
        
        return obj
    
    def get_context_data(self, **kwargs):
        """
        Enrichit le contexte pour la confirmation de suppression.
        
        Args:
            **kwargs: Arguments de contexte par défaut
            
        Returns:
            dict: Contexte enrichi pour le template
        """
        context = super().get_context_data(**kwargs)
        
        # Information sur le risque de suppression
        context['warning_message'] = (
            "Attention : La suppression d'une entrée d'historique est irréversible "
            "et peut compromettre la traçabilité des modifications. "
            "Cette action est déconseillée sauf en cas d'erreur manifeste."
        )
        
        return context

    def delete(self, request, *args, **kwargs):
        """
        Personnalisation de la suppression avec journalisation.
        
        Args:
            request: Requête HTTP
            *args, **kwargs: Arguments supplémentaires
            
        Returns:
            HttpResponse: Redirection après suppression
        """
        self.object = self.get_object()
        historique_pk = self.object.pk
        formation = self.object.formation
        champ = self.object.champ_modifie
        
        # Transaction pour garantir l'intégrité
        with transaction.atomic():
            # Suppression effective
            self.object.delete()
            
            # Journalisation détaillée de la suppression
            logger.warning(
                f"Suppression de l'historique #{historique_pk} "
                f"(formation: {formation.nom if formation else 'N/A'}, "
                f"champ: {champ}) "
                f"par {request.user}"
            )
            
            # Message de confirmation
            messages.success(
                request, 
                "✅ Entrée historique supprimée avec succès. "
                "Notez que cette action ne peut pas être annulée."
            )
        
        return redirect(self.success_url)