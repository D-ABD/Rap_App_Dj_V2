import logging
import csv
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.views import View
from django.shortcuts import get_list_or_404, redirect
from django.contrib.auth import get_user_model
from django.views.generic import ListView
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib import messages
from django.utils import timezone

from ..models import Commentaire, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView

# Configuration du logger
logger = logging.getLogger(__name__)

User = get_user_model()

class CommentaireListView(BaseListView):
    """
    Vue listant tous les commentaires avec options de filtrage par formation,
    utilisateur et contenu.
    """
    model = Commentaire
    context_object_name = 'commentaires'
    template_name = 'commentaires/commentaire_list.html'
    paginate_by = 5

    def get_queryset(self):
        """
        Récupère la liste des commentaires avec possibilité de filtrage par :
        - Formation associée
        - Utilisateur
        - Contenu (recherche textuelle)
        """
        logger.debug("Construction du queryset pour la liste des commentaires")
        
        queryset = super().get_queryset().select_related('formation', 'utilisateur')

        # Récupération des filtres
        formation_id = self.request.GET.get('formation')
        utilisateur_id = self.request.GET.get('utilisateur')
        search_query = self.request.GET.get('q')
        
        # Filtres appliqués (pour les logs)
        filters_applied = []

        # Application des filtres
        if formation_id:
            try:
                formation = Formation.objects.get(pk=formation_id)
                queryset = queryset.filter(formation_id=formation_id)
                filters_applied.append(f"formation: {formation.nom}")
            except Formation.DoesNotExist:
                logger.warning(f"Tentative de filtrage par formation inexistante: ID={formation_id}")

        if utilisateur_id:
            try:
                user = User.objects.get(pk=utilisateur_id)
                queryset = queryset.filter(utilisateur_id=utilisateur_id)
                filters_applied.append(f"utilisateur: {user.username}")
            except User.DoesNotExist:
                logger.warning(f"Tentative de filtrage par utilisateur inexistant: ID={utilisateur_id}")

        if search_query:
            queryset = queryset.filter(contenu__icontains=search_query)
            filters_applied.append(f"recherche: '{search_query}'")

        # Log des filtres appliqués
        if filters_applied:
            logger.debug(f"Filtres appliqués: {', '.join(filters_applied)}")
            
        result_count = queryset.count()
        logger.debug(f"Nombre de commentaires trouvés: {result_count}")

        return queryset

    def get_context_data(self, **kwargs):
        """
        Ajoute les options de filtre au contexte pour le template:
        - Filtres actuellement appliqués
        - Liste des formations disponibles
        - Liste des utilisateurs disponibles
        """
        context = super().get_context_data(**kwargs)
        
        # Récupération des valeurs de filtres
        formation_id = self.request.GET.get('formation', '')
        utilisateur_id = self.request.GET.get('utilisateur', '')
        search_query = self.request.GET.get('q', '')

        # Ajout des filtres et options de filtrage
        context['filters'] = {
            'formation': formation_id,
            'utilisateur': utilisateur_id,
            'q': search_query,
        }

        # Statistiques de commentaires
        context['stats'] = {
            'total': Commentaire.objects.count(),
            'this_month': Commentaire.objects.filter(
                created_at__month=timezone.now().month,
                created_at__year=timezone.now().year
            ).count(),
            'today': Commentaire.objects.filter(
                created_at__date=timezone.now().date()
            ).count(),
        }

        # Liste des formations et utilisateurs pour les filtres
        # Optimisé pour montrer les formations et utilisateurs ayant le plus de commentaires
        context['formations'] = Formation.objects.annotate(
            nb_commentaires=Count('commentaires')
        ).filter(nb_commentaires__gt=0).order_by('-nb_commentaires')
        
        context['utilisateurs'] = User.objects.annotate(
            nb_commentaires=Count('commentaires')
        ).filter(nb_commentaires__gt=0).order_by('-nb_commentaires')

        logger.debug(f"Contexte préparé pour la liste des commentaires")
        return context


class CommentaireDetailView(BaseDetailView):
    """Vue affichant les détails d'un commentaire spécifique"""
    model = Commentaire
    context_object_name = 'commentaire'
    template_name = 'commentaires/commentaire_detail.html'
    
    def get_context_data(self, **kwargs):
        """Ajoute des informations contextuelles supplémentaires."""
        context = super().get_context_data(**kwargs)
        commentaire = self.object
        
        logger.info(f"Consultation du commentaire #{commentaire.pk} par {getattr(self.request.user, 'username', 'Anonyme')}")
        
        # Récupère les autres commentaires de la même formation
        context['commentaires_lies'] = Commentaire.objects.filter(
            formation=commentaire.formation
        ).exclude(pk=commentaire.pk).order_by('-created_at')[:5]
        
        # Récupère les autres commentaires du même utilisateur
        if commentaire.utilisateur:
            context['commentaires_utilisateur'] = Commentaire.objects.filter(
                utilisateur=commentaire.utilisateur
            ).exclude(pk=commentaire.pk).order_by('-created_at')[:5]
        
        return context


class CommentaireCreateView(BaseCreateView):
    """Vue permettant de créer un nouveau commentaire"""
    model = Commentaire
    fields = ['formation', 'contenu', 'saturation']
    template_name = 'commentaires/commentaire_form.html'
    
    def get_initial(self):
        """Pré-remplit le formulaire avec la formation si spécifiée dans l'URL"""
        initial = super().get_initial()
        formation_id = self.request.GET.get('formation')
        
        if formation_id:
            try:
                formation = Formation.objects.get(pk=formation_id)
                initial['formation'] = formation_id
                logger.debug(f"Formulaire pré-rempli avec la formation: {formation.nom} (ID={formation_id})")
            except Formation.DoesNotExist:
                logger.warning(f"Tentative de pré-remplir avec une formation inexistante: ID={formation_id}")
                
        return initial
    
    def form_valid(self, form):
        """
        Associe automatiquement l'utilisateur connecté au commentaire 
        et journalise la création.
        """
        form.instance.utilisateur = self.request.user
        
        # Validation supplémentaire du champ saturation
        saturation = form.cleaned_data.get('saturation')
        if saturation is not None and (saturation < 0 or saturation > 100):
            form.add_error('saturation', "Le niveau de saturation doit être compris entre 0 et 100%")
            logger.warning(f"Tentative de créer un commentaire avec saturation invalide: {saturation}%")
            return self.form_invalid(form)
        
        # Log de création
        formation = form.cleaned_data.get('formation')
        logger.info(
            f"Création d'un commentaire par {self.request.user.username} "
            f"pour la formation '{formation.nom if formation else 'N/A'}'"
        )
        
        response = super().form_valid(form)
        
        # Message de succès personnalisé
        messages.success(
            self.request, 
            f"Commentaire ajouté avec succès pour la formation '{self.object.formation.nom}'."
        )
        
        return response
    
    def form_invalid(self, form):
        """Journalise les erreurs de validation du formulaire."""
        logger.warning(
            f"Échec de création d'un commentaire: {form.errors.as_json()}"
        )
        
        # Message d'erreur plus informatif
        messages.error(
            self.request,
            "Le commentaire n'a pas pu être créé. Veuillez corriger les erreurs dans le formulaire."
        )
        
        return super().form_invalid(form)
    
    def get_success_url(self):
        """Redirige vers la formation associée après création"""
        return reverse_lazy('formation-detail', kwargs={'pk': self.object.formation.pk})
    
    def get_context_data(self, **kwargs):
        """Ajoute un titre au formulaire et des formations récentes."""
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un commentaire"
        
        # Ajoute les formations récentes pour faciliter la sélection
        context['formations_recentes'] = Formation.objects.order_by('-start_date')[:10]
        
        return context


class CommentaireUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Vue permettant de modifier un commentaire existant"""
    model = Commentaire
    permission_required = 'rap_app.change_commentaire'
    fields = ['contenu', 'saturation']
    template_name = 'commentaires/commentaire_form.html'
    
    def get_success_url(self):
        """Redirige vers la formation associée après modification"""
        return reverse_lazy('formation-detail', kwargs={'pk': self.object.formation.pk})
    
    def form_valid(self, form):
        """
        Validation du formulaire avec journalisation des modifications.
        """
        # Récupération de l'objet original avant modifications
        original = Commentaire.objects.get(pk=self.object.pk)
        
        # Détection des changements
        changes = []
        if original.contenu != form.cleaned_data.get('contenu'):
            changes.append(f"contenu modifié")
            
        if original.saturation != form.cleaned_data.get('saturation'):
            changes.append(
                f"saturation: {original.saturation}% → {form.cleaned_data.get('saturation')}%"
            )
        
        # Log des modifications
        if changes:
            logger.info(
                f"Modification du commentaire #{self.object.pk} par {self.request.user.username}: "
                f"{', '.join(changes)}"
            )
            
            # Message plus informatif
            messages.success(
                self.request,
                f"Commentaire mis à jour avec succès. Modifications: {', '.join(changes)}"
            )
        else:
            logger.info(f"Formulaire soumis sans modifications pour le commentaire #{self.object.pk}")
            messages.info(self.request, "Aucune modification n'a été effectuée.")
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Journalise les erreurs de validation lors de la modification."""
        logger.warning(
            f"Échec de modification du commentaire #{self.object.pk}: {form.errors.as_json()}"
        )
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """Ajoute un titre personnalisé au formulaire."""
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le commentaire du {self.object.created_at.strftime('%d/%m/%Y')}"
        context['formation'] = self.object.formation
        return context


class CommentaireDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Vue permettant de supprimer un commentaire"""
    model = Commentaire
    permission_required = 'rap_app.delete_commentaire'
    template_name = 'commentaires/commentaire_confirm_delete.html'
    
    def get_context_data(self, **kwargs):
        """Ajoute des informations supplémentaires pour la confirmation."""
        context = super().get_context_data(**kwargs)
        commentaire = self.object
        
        context.update({
            'formation': commentaire.formation,
            'date_creation': commentaire.created_at,
            'est_recent': commentaire.is_recent(),  # Utilise la méthode du modèle amélioré
        })
        
        return context
    
    def delete(self, request, *args, **kwargs):
        """Personnalisation de la suppression avec journalisation."""
        self.object = self.get_object()
        commentaire = self.object
        
        # Stockage de l'ID de la formation pour la redirection
        formation_id = commentaire.formation.id if commentaire.formation else None
        
        # Journalisation détaillée
        logger.warning(
            f"Suppression du commentaire #{commentaire.pk} "
            f"par {request.user.username} "
            f"(créé le {commentaire.created_at.strftime('%d/%m/%Y')} "
            f"par {commentaire.utilisateur.username if commentaire.utilisateur else 'Anonyme'})"
        )
        
        # Message personnalisé
        messages.success(
            request, 
            f"Commentaire supprimé avec succès de la formation '{commentaire.formation.nom}'."
        )
        
        # Suppression et redirection
        commentaire.delete()
        return redirect('formation-detail', pk=formation_id) if formation_id else redirect('commentaire-list')
    
    def get_success_url(self):
        """Redirige vers la formation associée après suppression"""
        formation_id = self.object.formation.id
        return reverse_lazy('formation-detail', kwargs={'pk': formation_id})


class AllCommentairesView(LoginRequiredMixin, ListView):
    """
    Vue complète de tous les commentaires avec options avancées 
    de filtrage et de tri.
    """
    model = Commentaire
    template_name = 'formations/commentaires_tous.html'
    context_object_name = 'commentaires'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        """Journalise l'accès à cette vue."""
        logger.info(f"Accès à la vue d'ensemble des commentaires par {request.user.username}")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """
        Récupère tous les commentaires avec application des filtres
        et options de tri.
        """
        queryset = Commentaire.objects.select_related('formation', 'utilisateur')
        
        # Récupération des paramètres de filtrage et de tri
        formation_id = self.request.GET.get('formation')
        utilisateur_id = self.request.GET.get('utilisateur')
        search_query = self.request.GET.get('q')
        order_by = self.request.GET.get('order_by', '-created_at')
        periode = self.request.GET.get('periode')
        
        # Filtres appliqués (pour les logs)
        filters_applied = []

        # Construction du filtre combiné
        filters = Q()

        # Filtrage par formation
        if formation_id:
            filters &= Q(formation_id=formation_id)
            try:
                formation_name = Formation.objects.get(pk=formation_id).nom
                filters_applied.append(f"formation: {formation_name}")
            except Formation.DoesNotExist:
                pass

        # Filtrage par utilisateur
        if utilisateur_id:
            filters &= Q(utilisateur_id=utilisateur_id)
            try:
                username = User.objects.get(pk=utilisateur_id).username
                filters_applied.append(f"utilisateur: {username}")
            except User.DoesNotExist:
                pass

        # Filtrage par texte
        if search_query:
            filters &= Q(contenu__icontains=search_query)
            filters_applied.append(f"texte: '{search_query}'")
            
        # Filtrage par période
        today = timezone.now().date()
        if periode == 'today':
            filters &= Q(created_at__date=today)
            filters_applied.append("aujourd'hui")
        elif periode == 'week':
            filters &= Q(created_at__date__gte=today - timezone.timedelta(days=7))
            filters_applied.append("7 derniers jours")
        elif periode == 'month':
            filters &= Q(created_at__date__gte=today - timezone.timedelta(days=30))
            filters_applied.append("30 derniers jours")

        # Application des filtres
        queryset = queryset.filter(filters)
        
        # Tri des résultats
        valid_order_fields = [
            'created_at', '-created_at', 
            'formation__nom', '-formation__nom',
            'utilisateur__username', '-utilisateur__username',
            'saturation', '-saturation'
        ]
        
        if order_by in valid_order_fields:
            queryset = queryset.order_by(order_by)
            filters_applied.append(f"tri par: {order_by}")
        else:
            queryset = queryset.order_by('-created_at')  # Tri par défaut

        # Journalisation
        logger.debug(
            f"Recherche des commentaires avec filtres: {', '.join(filters_applied) if filters_applied else 'aucun'}. "
            f"Résultats: {queryset.count()} commentaires"
        )

        return queryset

    def get_context_data(self, **kwargs):
        """
        Enrichit le contexte avec des données supplémentaires pour le filtrage
        et des statistiques.
        """
        context = super().get_context_data(**kwargs)
        
        # Listes pour les filtres déroulants
        context['formations'] = Formation.objects.all().order_by('nom')
        context['utilisateurs'] = User.objects.all().order_by('username')
        
        # Options de tri
        context['sort_options'] = [
            {'value': 'created_at', 'label': 'Date (croissante)'},
            {'value': '-created_at', 'label': 'Date (décroissante)'},
            {'value': 'formation__nom', 'label': 'Formation (A-Z)'},
            {'value': '-formation__nom', 'label': 'Formation (Z-A)'},
            {'value': 'utilisateur__username', 'label': 'Utilisateur (A-Z)'},
            {'value': '-utilisateur__username', 'label': 'Utilisateur (Z-A)'},
            {'value': 'saturation', 'label': 'Saturation (croissante)'},
            {'value': '-saturation', 'label': 'Saturation (décroissante)'},
        ]
        
        # Options de période
        context['periode_options'] = [
            {'value': 'today', 'label': "Aujourd'hui"},
            {'value': 'week', 'label': '7 derniers jours'},
            {'value': 'month', 'label': '30 derniers jours'},
        ]
        
        # Filtres actuellement appliqués
        context['current_filters'] = {
            'formation': self.request.GET.get('formation', ''),
            'utilisateur': self.request.GET.get('utilisateur', ''),
            'q': self.request.GET.get('q', ''),
            'order_by': self.request.GET.get('order_by', '-created_at'),
            'periode': self.request.GET.get('periode', ''),
        }
        
        # Statistiques
        context['stats'] = {
            'total': Commentaire.objects.count(),
            'with_saturation': Commentaire.objects.exclude(saturation__isnull=True).count(),
            'today': Commentaire.objects.filter(created_at__date=timezone.now().date()).count(),
        }
        
        return context


class ExportCommentairesView(LoginRequiredMixin, View):
    """
    Vue permettant d'exporter les commentaires sélectionnés au format CSV.
    Nécessite une liste d'IDs de commentaires à exporter via POST.
    """

    def post(self, request, *args, **kwargs):
        """Traite la demande d'export en POST."""
        # Récupération des IDs des commentaires à exporter
        commentaire_ids = request.POST.getlist('commentaire_ids')
        
        # Vérification qu'au moins un commentaire est sélectionné
        if not commentaire_ids:
            logger.warning(f"Tentative d'export sans sélection de commentaires par {request.user.username}")
            return HttpResponseBadRequest("Aucun commentaire sélectionné.")

        try:
            # Récupération des commentaires
            commentaires = get_list_or_404(Commentaire, id__in=commentaire_ids)
            
            # Configuration de la réponse HTTP pour le téléchargement CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="commentaires_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

            # Création du writer CSV
            writer = csv.writer(response)
            
            # En-têtes du fichier CSV
            writer.writerow([
                "ID", "Utilisateur", "Date", "Formation", "Num Offre", 
                "Commentaire", "Saturation (%)"
            ])

            # Écriture des données
            for commentaire in commentaires:
                writer.writerow([
                    commentaire.id,
                    commentaire.utilisateur.username if commentaire.utilisateur else "Anonyme",
                    commentaire.created_at.strftime("%d/%m/%Y %H:%M"),
                    commentaire.formation.nom if commentaire.formation else "N/A",
                    commentaire.formation.num_offre if commentaire.formation and commentaire.formation.num_offre else "N/A",
                    commentaire.contenu,
                    commentaire.saturation if commentaire.saturation is not None else "N/A"
                ])

            logger.info(f"Export CSV de {len(commentaires)} commentaires par {request.user.username}")
            return response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export des commentaires: {str(e)}")
            messages.error(request, f"Une erreur est survenue lors de l'export: {str(e)}")
            return redirect('commentaire-list')