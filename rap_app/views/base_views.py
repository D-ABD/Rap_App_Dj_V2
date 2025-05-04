import logging
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect
from django.http import HttpResponseForbidden

# Configuration du logger pour les vues de base
logger = logging.getLogger(__name__)

class CustomLoginRequiredMixin(LoginRequiredMixin):
    """
    Mixin personnalisé pour gérer les utilisateurs non connectés.
    
    Étend le mixin LoginRequiredMixin de Django en ajoutant:
    - Un message d'erreur explicite
    - Une redirection personnalisée vers la page de connexion
    
    Avantages:
    - Amélioration de l'expérience utilisateur en expliquant pourquoi la redirection a lieu
    - Centralisation de la logique d'authentification
    """
    def handle_no_permission(self):
        """
        Méthode appelée lorsqu'un utilisateur non authentifié tente d'accéder
        à une vue protégée.
        """
        logger.info(f"Tentative d'accès non autorisé à {self.request.path} par un utilisateur anonyme")
        messages.error(self.request, "Vous devez être connecté pour accéder à cette page.")
        return redirect('login')  # URL de la page de connexion


class BaseListView(CustomLoginRequiredMixin, ListView):
    """
    Vue de base pour les listes d'objets avec pagination.
    
    Caractéristiques:
    - Authentification requise
    - Pagination automatique (20 éléments par page)
    - Convention de nommage des templates automatique (suffixe '_list')
    
    Usage:
    ```python
    class MaListeView(BaseListView):
        model = MonModel
        context_object_name = 'elements'
        # Le template sera automatiquement 'app/monmodel_list.html'
    ```
    """
    paginate_by = 20
    template_name_suffix = '_list'
    
    def get_queryset(self):
        """
        Surcharge pour ajouter des logs et possibilité de filtrage.
        """
        queryset = super().get_queryset()
        logger.debug(f"Liste {self.model.__name__} récupérée, {queryset.count()} éléments")
        return queryset
    
    def dispatch(self, request, *args, **kwargs):
        """
        Surcharge pour journaliser les accès aux listes.
        """
        logger.info(f"Accès à la liste {self.model.__name__} par {request.user}")
        return super().dispatch(request, *args, **kwargs)


class BaseDetailView(CustomLoginRequiredMixin, DetailView):
    """
    Vue de base pour afficher le détail d'un objet.
    
    Caractéristiques:
    - Authentification requise
    - Convention de nommage des templates automatique (suffixe '_detail')
    
    Usage:
    ```python
    class MonDetailView(BaseDetailView):
        model = MonModel
        context_object_name = 'element'
        # Le template sera automatiquement 'app/monmodel_detail.html'
    ```
    """
    template_name_suffix = '_detail'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Surcharge pour journaliser les accès aux détails d'objets.
        """
        logger.info(f"Accès au détail {self.model.__name__} (ID: {kwargs.get('pk')}) par {request.user}")
        return super().dispatch(request, *args, **kwargs)


class BaseCreateView(CustomLoginRequiredMixin, CreateView):
    """
    Vue de base pour créer un nouvel objet.
    
    Caractéristiques:
    - Authentification requise
    - Message de succès automatique
    - Journalisation des créations d'objets
    
    Usage:
    ```python
    class MaCreationView(BaseCreateView):
        model = MonModel
        fields = ['champ1', 'champ2']
        success_url = reverse_lazy('ma-liste')
    ```
    """
    def form_valid(self, form):
        """
        Ajoute un message de succès et des logs après la création réussie.
        """
        response = super().form_valid(form)
        obj_name = self.model._meta.verbose_name
        
        logger.info(f"Création réussie d'un(e) {obj_name} (ID: {self.object.pk}) par {self.request.user}")
        messages.success(self.request, f"{obj_name.capitalize()} créé(e) avec succès.")
        
        return response
    
    def form_invalid(self, form):
        """
        Ajoute un message d'erreur et des logs en cas d'échec de validation du formulaire.
        """
        obj_name = self.model._meta.verbose_name
        
        logger.warning(
            f"Échec de création d'un(e) {obj_name} par {self.request.user}. "
            f"Erreurs: {form.errors}"
        )
        messages.error(
            self.request, 
            f"Impossible de créer {obj_name}. Veuillez corriger les erreurs dans le formulaire."
        )
        
        return super().form_invalid(form)


class BaseUpdateView(CustomLoginRequiredMixin, UpdateView):
    """
    Vue de base pour modifier un objet existant.
    
    Caractéristiques:
    - Authentification requise
    - Message de succès automatique
    - Journalisation des modifications
    
    Usage:
    ```python
    class MaModificationView(BaseUpdateView):
        model = MonModel
        fields = ['champ1', 'champ2']
    ```
    """
    def form_valid(self, form):
        """
        Ajoute un message de succès et des logs après la modification réussie.
        """
        response = super().form_valid(form)
        obj_name = self.model._meta.verbose_name
        
        logger.info(f"Modification réussie de {obj_name} (ID: {self.object.pk}) par {self.request.user}")
        messages.success(self.request, f"{obj_name.capitalize()} mis(e) à jour avec succès.")
        
        return response
    
    def form_invalid(self, form):
        """
        Ajoute un message d'erreur et des logs en cas d'échec de validation du formulaire.
        """
        obj_name = self.model._meta.verbose_name
        
        logger.warning(
            f"Échec de modification de {obj_name} (ID: {self.kwargs.get('pk')}) par {self.request.user}. "
            f"Erreurs: {form.errors}"
        )
        messages.error(
            self.request, 
            f"Impossible de modifier {obj_name}. Veuillez corriger les erreurs dans le formulaire."
        )
        
        return super().form_invalid(form)
    
    def dispatch(self, request, *args, **kwargs):
        """
        Surcharge pour journaliser les tentatives de modification.
        """
        logger.info(f"Tentative de modification de {self.model.__name__} (ID: {kwargs.get('pk')}) par {request.user}")
        return super().dispatch(request, *args, **kwargs)


class BaseDeleteView(CustomLoginRequiredMixin, DeleteView):
    """
    Vue de base pour supprimer un objet.
    
    Caractéristiques:
    - Authentification requise
    - Message de succès automatique
    - Redirection par défaut vers le tableau de bord
    - Journalisation des suppressions
    
    Usage:
    ```python
    class MaSuppressionView(BaseDeleteView):
        model = MonModel
        success_url = reverse_lazy('ma-liste')  # Surcharge de l'URL de redirection
    ```
    """
    success_url = reverse_lazy('dashboard')

    def delete(self, request, *args, **kwargs):
        """
        Ajoute un message de succès et des logs après la suppression.
        """
        self.object = self.get_object()
        obj_name = self.model._meta.verbose_name
        obj_id = self.object.pk
        
        # Journalisation avant la suppression
        logger.info(f"Suppression de {obj_name} (ID: {obj_id}) par {request.user}")
        
        # Suppression de l'objet
        self.object.delete()
        
        # Message de succès
        messages.success(request, f"{obj_name.capitalize()} supprimé(e) avec succès.")
        
        # Journalisation après suppression
        logger.info(f"{obj_name.capitalize()} (ID: {obj_id}) supprimé(e) avec succès")
        
        return redirect(self.get_success_url())
    
    def dispatch(self, request, *args, **kwargs):
        """
        Surcharge pour journaliser les tentatives de suppression.
        """
        logger.info(f"Tentative de suppression de {self.model.__name__} (ID: {kwargs.get('pk')}) par {request.user}")
        return super().dispatch(request, *args, **kwargs)


class BasePermissionMixin(PermissionRequiredMixin):
    """
    Mixin pour gérer les permissions de manière plus conviviale.
    
    Caractéristiques:
    - Redirige vers une page d'erreur 403 personnalisée
    - Ajoute un message explicatif
    - Journalise les tentatives d'accès non autorisées
    """
    def handle_no_permission(self):
        """
        Méthode appelée lorsqu'un utilisateur n'a pas les permissions requises.
        """
        logger.warning(
            f"Tentative d'accès non autorisé à {self.request.path} "
            f"par {self.request.user} (permissions requises: {self.permission_required})"
        )
        
        messages.error(
            self.request, 
            "Vous n'avez pas les permissions nécessaires pour effectuer cette action."
        )
        
        # Si utilisateur connecté: erreur 403, sinon redirection vers login
        if self.request.user.is_authenticated:
            return HttpResponseForbidden("Permission refusée")
        else:
            return redirect('login')