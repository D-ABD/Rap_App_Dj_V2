import logging
from django.urls import reverse_lazy
from django.db.models import Count, Q, Prefetch
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.db import transaction

from ..models import TypeOffre, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView

# Configuration du logger
logger = logging.getLogger("application.typeoffre.views")


class TypeOffreListView(BaseListView):
    """
    Vue listant tous les types d'offres de formation avec statistiques.
    
    Cette vue implémente:
    - Annotation du nombre de formations par type d'offre
    - Recherche textuelle sur le nom et le champ "autre"
    - Tri par nom par défaut
    """
    model = TypeOffre
    context_object_name = 'types_offre'
    template_name = "types_offres/typeoffre_list.html"
    
    def get_queryset(self):
        """
        Récupère la liste des types d'offre avec le nombre de formations associées.
        Filtre selon les paramètres de recherche.
        
        Returns:
            QuerySet: Types d'offre filtrés et annotés
        """
        # Requête de base avec annotations
        queryset = super().get_queryset().annotate(
            nb_formations=Count('formations', distinct=True)
        )
        
        # Logging de la requête initiale
        logger.debug(f"TypeOffreListView: Requête initiale avec {queryset.count()} types d'offre")
        
        # Recherche par nom ou champ "autre"
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(nom__icontains=q) | 
                Q(autre__icontains=q)
            )
            logger.debug(f"TypeOffreListView: Recherche de '{q}' avec {queryset.count()} résultats")
        
        # Tri par nom par défaut
        return queryset.order_by('nom')
    
    def get_context_data(self, **kwargs):
        """
        Enrichit le contexte avec des filtres et statistiques.
        
        Args:
            **kwargs: Arguments de contexte par défaut
            
        Returns:
            dict: Contexte enrichi pour le template
        """
        context = super().get_context_data(**kwargs)
        
        # Filtres appliqués pour maintenir l'état du formulaire
        context['filters'] = {
            'q': self.request.GET.get('q', ''),
        }
        
        # Statistiques sur les types d'offre
        context['stats'] = {
            'total': TypeOffre.objects.count(),
            'with_formations': TypeOffre.objects.filter(formations__isnull=False).distinct().count(),
            'without_formations': TypeOffre.objects.filter(formations__isnull=True).count(),
            'custom_types': TypeOffre.objects.filter(nom=TypeOffre.AUTRE).count(),
        }
        
        return context


class TypeOffreDetailView(BaseDetailView):
    """
    Vue affichant les détails d'un type d'offre avec ses formations associées.
    
    Cette vue enrichit le contexte avec:
    - La liste des formations utilisant ce type d'offre
    - Des statistiques sur ces formations
    """
    model = TypeOffre
    context_object_name = 'type_offre'
    template_name = "types_offres/typeoffre_detail.html"
    
    def get_object(self, queryset=None):
        """
        Récupère l'objet TypeOffre avec optimisation des requêtes.
        
        Returns:
            TypeOffre: Instance du type d'offre
        """
        obj = super().get_object(queryset)
        
        # Journalisation de la consultation
        logger.info(f"Consultation du type d'offre '{obj}' (ID: {obj.pk})")
        
        return obj
    
    def get_context_data(self, **kwargs):
        """
        Enrichit le contexte avec des données supplémentaires.
        
        Args:
            **kwargs: Arguments de contexte par défaut
            
        Returns:
            dict: Contexte enrichi pour le template
        """
        context = super().get_context_data(**kwargs)
        
        # Récupération optimisée des formations associées
        formations = Formation.objects.filter(
            type_offre=self.object
        ).select_related(
            'centre', 'statut', 'utilisateur'
        ).order_by('-start_date')
        
        # Statistiques sur les formations
        stats = {
            'total': formations.count(),
            'actives': formations.filter(statut__nom__in=['active', 'en_cours']).count(),
            'terminees': formations.filter(statut__nom='terminee').count(),
            'a_venir': formations.filter(statut__nom='a_venir').count(),
        }
        
        # Ajout au contexte
        context['formations'] = formations
        context['stats'] = stats
        
        # Ajout d'un prévisualisation du badge
        context['badge_html'] = self.object.get_badge_html()
        
        return context


class TypeOffreCreateView(PermissionRequiredMixin, BaseCreateView):
    """
    Vue permettant de créer un nouveau type d'offre.
    
    Cette vue implémente:
    - Validation des données (notamment pour le type "Autre")
    - Journalisation de la création
    - Messages de confirmation
    """
    model = TypeOffre
    permission_required = 'rap_app.add_typeoffre'
    fields = ['nom', 'autre', 'couleur']
    success_url = reverse_lazy('type-offre-list')
    template_name = "types_offres/typeoffre_form.html"
    
    def get_form(self, form_class=None):
        """
        Personnalise le formulaire pour améliorer l'interface utilisateur.
        
        Returns:
            Form: Formulaire personnalisé
        """
        form = super().get_form(form_class)
        
        # Amélioration des widgets et help texts
        if 'couleur' in form.fields:
            form.fields['couleur'].widget.attrs['type'] = 'color'
            form.fields['couleur'].widget.attrs['class'] = 'form-control'
            form.fields['couleur'].help_text = "Choisissez une couleur pour l'affichage visuel"
        
        # Amélioration du champ "autre"
        if 'autre' in form.fields:
            form.fields['autre'].widget.attrs['placeholder'] = "Précisez le type d'offre personnalisé"
            form.fields['autre'].widget.attrs['class'] = 'form-control'
        
        return form
    
    def form_valid(self, form):
        """
        Validation du formulaire avec journalisation et message de confirmation.
        
        Args:
            form: Formulaire soumis
            
        Returns:
            HttpResponse: Redirection après sauvegarde
        """
        # Validation avec transaction atomique
        with transaction.atomic():
            # Sauvegarde du type d'offre
            self.object = form.save()
            
            # Journalisation de la création
            logger.info(
                f"Type d'offre '{self.object}' créé (ID: {self.object.pk}) "
                f"par {self.request.user.username}"
            )
            
            # Message de confirmation
            messages.success(
                self.request, 
                f"Le type d'offre '{self.object}' a été ajouté avec succès."
            )
            
            return redirect('type-offre-list')
    
    def form_invalid(self, form):
        """
        Gestion des erreurs de formulaire avec journalisation.
        
        Args:
            form: Formulaire invalide
            
        Returns:
            HttpResponse: Formulaire avec erreurs
        """
        # Journalisation des erreurs
        logger.warning(
            f"Échec de création d'un type d'offre par {self.request.user.username}. "
            f"Erreurs: {form.errors}"
        )
        
        # Message d'erreur pour l'utilisateur
        messages.error(
            self.request,
            "Le formulaire contient des erreurs. Veuillez les corriger et réessayer."
        )
        
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """
        Enrichit le contexte avec un titre et des informations supplémentaires.
        
        Args:
            **kwargs: Arguments de contexte par défaut
            
        Returns:
            dict: Contexte enrichi pour le template
        """
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un type d'offre de formation"
        context['is_creation'] = True
        context['color_picker'] = True  # Pour activer un éventuel sélecteur de couleur amélioré dans le template
        
        # Ajout d'une prévisualisation des types d'offre existants pour référence
        context['existing_types'] = TypeOffre.objects.all()[:5]
        
        return context


class TypeOffreUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """
    Vue permettant de modifier un type d'offre existant.
    
    Cette vue implémente:
    - Validation des données modifiées
    - Journalisation des modifications
    - Messages de confirmation
    """
    model = TypeOffre
    permission_required = 'rap_app.change_typeoffre'
    fields = ['nom', 'autre', 'couleur']
    template_name = "types_offres/typeoffre_form.html"
    
    def get_form(self, form_class=None):
        """
        Personnalise le formulaire pour améliorer l'interface utilisateur.
        
        Returns:
            Form: Formulaire personnalisé
        """
        form = super().get_form(form_class)
        
        # Amélioration des widgets et help texts
        if 'couleur' in form.fields:
            form.fields['couleur'].widget.attrs['type'] = 'color'
            form.fields['couleur'].widget.attrs['class'] = 'form-control'
            form.fields['couleur'].help_text = "Choisissez une couleur pour l'affichage visuel"
        
        # Si le type d'offre est "Autre", mettre en évidence le champ "autre"
        if self.object.nom == TypeOffre.AUTRE:
            if 'autre' in form.fields:
                form.fields['autre'].widget.attrs['class'] = 'form-control is-required'
                form.fields['autre'].widget.attrs['style'] = 'border: 1px solid #007bff;'
        
        return form
    
    def form_valid(self, form):
        """
        Validation du formulaire avec journalisation et message de confirmation.
        
        Args:
            form: Formulaire soumis
            
        Returns:
            HttpResponse: Redirection après sauvegarde
        """
        # Récupération de l'objet original pour comparaison
        original = TypeOffre.objects.get(pk=self.object.pk)
        
        # Validation avec transaction atomique
        with transaction.atomic():
            # Sauvegarde du type d'offre
            self.object = form.save()
            
            # Description des modifications
            changes = []
            if original.nom != self.object.nom:
                changes.append(f"nom: {original.get_nom_display()} → {self.object.get_nom_display()}")
            if original.autre != self.object.autre:
                changes.append(f"autre: {original.autre or 'vide'} → {self.object.autre or 'vide'}")
            if original.couleur != self.object.couleur:
                changes.append(f"couleur: {original.couleur} → {self.object.couleur}")
            
            # Journalisation des modifications
            if changes:
                logger.info(
                    f"Type d'offre '{self.object}' (ID: {self.object.pk}) modifié par {self.request.user.username}. "
                    f"Modifications: {', '.join(changes)}"
                )
            
            # Message de confirmation
            messages.success(
                self.request, 
                f"Le type d'offre '{self.object}' a été mis à jour avec succès."
            )
            
            return redirect(self.get_success_url())
    
    def form_invalid(self, form):
        """
        Gestion des erreurs de formulaire avec journalisation.
        
        Args:
            form: Formulaire invalide
            
        Returns:
            HttpResponse: Formulaire avec erreurs
        """
        # Journalisation des erreurs
        logger.warning(
            f"Échec de modification du type d'offre (ID: {self.object.pk}) par {self.request.user.username}. "
            f"Erreurs: {form.errors}"
        )
        
        # Message d'erreur pour l'utilisateur
        messages.error(
            self.request,
            "Le formulaire contient des erreurs. Veuillez les corriger et réessayer."
        )
        
        return super().form_invalid(form)
    
    def get_success_url(self):
        """
        Retourne l'URL de redirection après la modification.
        
        Returns:
            str: URL de détail du type d'offre
        """
        return reverse_lazy('type-offre-detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        """
        Enrichit le contexte avec un titre et des informations supplémentaires.
        
        Args:
            **kwargs: Arguments de contexte par défaut
            
        Returns:
            dict: Contexte enrichi pour le template
        """
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le type d'offre : {self.object.__str__()}"
        context['is_creation'] = False
        context['color_picker'] = True
        
        # Prévisualisation du badge actuel
        context['badge_html'] = self.object.get_badge_html()
        
        # Statistiques sur l'utilisation
        formations_count = self.object.get_formations_count()
        context['formations_count'] = formations_count
        context['in_use'] = formations_count > 0
        
        return context


class TypeOffreDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """
    Vue permettant de supprimer un type d'offre.
    
    Cette vue implémente:
    - Vérification des dépendances avant suppression
    - Journalisation de la suppression
    - Messages de confirmation
    """
    model = TypeOffre
    permission_required = 'rap_app.delete_typeoffre'
    success_url = reverse_lazy('type-offre-list')
    template_name = "types_offres/typeoffre_confirm_delete.html"
    
    def get_context_data(self, **kwargs):
        """
        Enrichit le contexte pour la confirmation de suppression.
        
        Args:
            **kwargs: Arguments de contexte par défaut
            
        Returns:
            dict: Contexte enrichi pour le template
        """
        context = super().get_context_data(**kwargs)
        
        # Vérification des formations associées
        formations = Formation.objects.filter(type_offre=self.object)
        formations_count = formations.count()
        
        context['formations'] = formations[:5]  # Limite pour éviter de surcharger la page
        context['formations_count'] = formations_count
        context['has_formations'] = formations_count > 0
        
        # Prévisualisation du badge qui sera supprimé
        context['badge_html'] = self.object.get_badge_html()
        
        return context
    
    def delete(self, request, *args, **kwargs):
        """
        Personnalisation de la suppression avec vérification et journalisation.
        
        Args:
            request: Requête HTTP
            *args, **kwargs: Arguments supplémentaires
            
        Returns:
            HttpResponse: Redirection après suppression
        """
        self.object = self.get_object()
        type_name = str(self.object)
        type_id = self.object.pk
        
        # Vérification des dépendances
        formations_count = Formation.objects.filter(type_offre=self.object).count()
        
        if formations_count > 0:
            # Journalisation de la tentative échouée
            logger.warning(
                f"Tentative de suppression du type d'offre '{type_name}' (ID: {type_id}) "
                f"par {request.user.username} échouée : {formations_count} formations associées"
            )
            
            # Message d'erreur
            messages.error(
                request,
                f"Impossible de supprimer le type d'offre '{type_name}' car il est utilisé par {formations_count} formation(s). "
                f"Veuillez d'abord modifier ces formations pour utiliser un autre type d'offre."
            )
            
            # Redirection vers la page de détail
            return redirect('type-offre-detail', pk=type_id)
        
        # Suppression avec transaction atomique
        with transaction.atomic():
            # Journalisation avant suppression
            logger.info(
                f"Type d'offre '{type_name}' (ID: {type_id}) supprimé par {request.user.username}"
            )
            
            # Suppression effective
            self.object.delete()
            
            # Message de confirmation
            messages.success(
                request,
                f"Le type d'offre '{type_name}' a été supprimé avec succès."
            )
            
            return redirect(self.success_url)
        