import logging
from django.urls import reverse_lazy
from django.db.models import Count, Q, Prefetch
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.db import transaction
from django.utils.text import slugify
import csv
from django.http import HttpResponse
from django.views import View

from ..models.partenaires import Partenaire
from ..models import Formation, TypeOffre, Statut
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView

# Configuration du logger
logger = logging.getLogger("application.partenaires.views")


class PartenaireListView(BaseListView):
    """
    Vue listant tous les partenaires avec des statistiques.
    
    Cette vue implémente:
    - Filtrage par nom et secteur d'activité
    - Annotation avec le nombre de formations par partenaire
    - Statistiques globales
    """
    model = Partenaire
    context_object_name = 'partenaires'
    template_name = 'partenaires/partenaire_list.html'
    paginate_by = 20  # Pagination pour améliorer les performances
    # Ajout d'un ordre explicite pour éviter les avertissements de pagination
    ordering = ['nom']
    
    def get_queryset(self):
        """
        Récupère la liste des partenaires en annotant des statistiques:
        - Nombre de formations associées à chaque partenaire
        
        Returns:
            QuerySet: Liste filtrée des partenaires avec annotations
        """
        # Utilisation du manager personnalisé pour la requête de base avec annotations
        queryset = Partenaire.objects.annotate(
            nb_formations=Count('formations', distinct=True)
        )
        
        # Logging de la requête initiale
        logger.debug(f"PartenaireListView: Requête initiale avec {queryset.count()} partenaires")
        
        # Application des filtres
        queryset = self._apply_filters(queryset)
        
        # Logging après filtrage
        logger.debug(f"PartenaireListView: Après filtrage, {queryset.count()} partenaires correspondent")
        
        return super().get_queryset().order_by('nom')
    
    def _apply_filters(self, queryset):
        """
        Méthode auxiliaire pour appliquer les filtres à la requête.
        
        Args:
            queryset: QuerySet initial des partenaires
            
        Returns:
            QuerySet: QuerySet filtré selon les paramètres de la requête
        """
        # Filtrage par nom du partenaire (recherche textuelle)
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(nom__icontains=q) | 
                Q(contact_nom__icontains=q) |
                Q(description__icontains=q)
            )
            
        # Filtrage par secteur d'activité
        secteur = self.request.GET.get('secteur')
        if secteur:
            queryset = queryset.filter(secteur_activite__icontains=secteur)
            
        # Filtrage par statut (avec/sans formations)
        status = self.request.GET.get('status')
        if status == 'actif':
            queryset = queryset.filter(formations__isnull=False).distinct()
        elif status == 'inactif':
            queryset = queryset.filter(formations__isnull=True)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Ajoute des statistiques générales et les filtres appliqués au contexte de la page.
        
        Args:
            **kwargs: Arguments de contexte par défaut
            
        Returns:
            dict: Contexte enrichi pour le template
        """
        context = super().get_context_data(**kwargs)
        
        # Statistiques des partenaires
        context['total_partenaires'] = Partenaire.objects.count()
        context['total_partenaires_avec_formations'] = Partenaire.objects.filter(
            formations__isnull=False
        ).distinct().count()
        
        # Préparation des statistiques de secteurs d'activité (top 5)
        secteurs = Partenaire.objects.exclude(
            secteur_activite__isnull=True
        ).exclude(
            secteur_activite=''
        ).values('secteur_activite').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        context['top_secteurs'] = secteurs
        
        # Liste complète des secteurs pour le filtre
        all_secteurs = Partenaire.objects.exclude(
            secteur_activite__isnull=True
        ).exclude(
            secteur_activite=''
        ).values_list('secteur_activite', flat=True).distinct().order_by('secteur_activite')
        
        context['secteurs'] = all_secteurs
        
        # Formations totales
        context['total_formations'] = Formation.objects.count()
        
        # Filtres actuellement appliqués
        context['filters'] = {
            'q': self.request.GET.get('q', ''),
            'secteur': self.request.GET.get('secteur', ''),
            'status': self.request.GET.get('status', ''),
        }
        
        return context


class PartenaireDetailView(BaseDetailView):
    """
    Vue affichant les détails d'un partenaire avec ses formations associées.
    
    Cette vue enrichit le contexte avec:
    - Les formations associées au partenaire
    - Les filtres pour ces formations
    - Des statistiques sur le partenaire
    """
    model = Partenaire
    context_object_name = 'partenaire'
    template_name = 'partenaires/partenaire_detail.html'

    def get_object(self, queryset=None):
        """
        Récupère l'objet partenaire en optimisant les requêtes.
        
        Returns:
            Partenaire: Instance du partenaire avec préchargement des relations
        """
        pk = self.kwargs.get(self.pk_url_kwarg)
        slug = self.kwargs.get('slug')
        
        if slug:
            return get_object_or_404(Partenaire, slug=slug)
        return get_object_or_404(Partenaire, pk=pk)

    def get_context_data(self, **kwargs):
        """
        Ajoute au contexte les formations associées au partenaire avec filtrage.
        
        Args:
            **kwargs: Arguments de contexte par défaut
            
        Returns:
            dict: Contexte enrichi pour le template
        """
        context = super().get_context_data(**kwargs)
        
        # Récupération et filtrage des formations associées au partenaire
        formations = self._get_filtered_formations()
        
        # Ajout au contexte
        context['formations'] = formations
        
        # Ajout des options de filtre pour les formations
        context['types_offre'] = TypeOffre.objects.all()
        context['statuts'] = Statut.objects.all()
        
        # Filtres actuellement appliqués
        context['filters'] = {
            'type_offre': self.request.GET.get('type_offre', ''),
            'statut': self.request.GET.get('statut', ''),
        }
        
        # Statistiques sur le partenaire
        stats = {
            'nb_formations': formations.count(),
            'nb_formations_actives': formations.filter(
                statut__code__in=['active', 'en_preparation']
            ).count(),
        }
        
        context['stats'] = stats
        
        return context
        
    def _get_filtered_formations(self):
        """
        Méthode auxiliaire pour récupérer et filtrer les formations.
        
        Returns:
            QuerySet: Formations filtrées associées au partenaire
        """
        # Récupération optimisée des formations avec relations
        formations = self.object.formations.select_related(
            'type_offre', 'statut', 'centre'
        ).order_by('-start_date')

        # Filtrage des formations par type d'offre
        type_offre = self.request.GET.get('type_offre')
        if type_offre:
            formations = formations.filter(type_offre_id=type_offre)

        # Filtrage des formations par statut
        statut = self.request.GET.get('statut')
        if statut:
            formations = formations.filter(statut_id=statut)
            
        return formations


class PartenaireCreateView(PermissionRequiredMixin, BaseCreateView):
    """
    Vue permettant de créer un nouveau partenaire.
    
    Cette vue implémente:
    - Validation des données
    - Journalisation de la création
    - Messages de confirmation
    """
    model = Partenaire
    permission_required = 'rap_app.add_partenaire'
    fields = [
        'nom', 'secteur_activite', 'contact_nom', 'contact_poste', 
        'contact_telephone', 'contact_email', 'description'
    ]
    success_url = reverse_lazy('partenaire-list')
    template_name = 'partenaires/partenaire_form.html'

    def form_valid(self, form):
        """
        Validation du formulaire avec journalisation et message de confirmation.
        
        Args:
            form: Formulaire soumis
            
        Returns:
            HttpResponse: Redirection après sauvegarde
        """
        # Utilisation d'une transaction pour garantir l'intégrité
        with transaction.atomic():
            # Création du slug à partir du nom
            form.instance.slug = slugify(form.cleaned_data['nom'])
            
            # Sauvegarde du partenaire
            self.object = form.save()
            
            # Journalisation de la création
            logger.info(
                f"Utilisateur {self.request.user} a créé le partenaire '{self.object.nom}' (ID: {self.object.pk})"
            )
            
            # Message de confirmation
            messages.success(self.request, f"✅ Partenaire '{self.object.nom}' ajouté avec succès.")
            
            return redirect('partenaire-list')
    
    def get_context_data(self, **kwargs):
        """
        Ajoute un titre personnalisé au contexte.
        
        Args:
            **kwargs: Arguments de contexte par défaut
            
        Returns:
            dict: Contexte enrichi pour le template
        """
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un partenaire"
        return context


class PartenaireCreateViewFormation(PermissionRequiredMixin, BaseCreateView):
    """
    Vue permettant de créer un partenaire et de l'associer à une formation.
    
    Cette vue implémente:
    - Création du partenaire
    - Association avec une formation spécifique
    - Journalisation détaillée
    - Gestion des erreurs
    """
    model = Partenaire
    permission_required = 'rap_app.add_partenaire'
    fields = [
        'nom', 'secteur_activite', 'contact_nom', 'contact_poste', 
        'contact_telephone', 'contact_email', 'description'
    ]
    template_name = 'partenaires/partenaire_formation_form.html'

    def form_valid(self, form):
        """
        Validation du formulaire avec association à la formation.
        
        Args:
            form: Formulaire soumis
            
        Returns:
            HttpResponse: Redirection après sauvegarde
        """
        logger.debug("Début du traitement form_valid pour PartenaireCreateViewFormation")
        formation_id = self.kwargs.get('formation_id')

        if not formation_id:
            logger.error("Aucun ID de formation fourni dans les paramètres de l'URL")
            messages.error(self.request, "❌ Erreur : Aucun ID de formation fourni.")
            return HttpResponseRedirect(reverse_lazy('formation-list'))  

        try:
            # Récupération de la formation avec gestion des erreurs
            formation = get_object_or_404(Formation, pk=formation_id)
            logger.debug(f"Formation trouvée : {formation.nom} (ID: {formation.id})")

            # Utilisation d'une transaction pour garantir l'intégrité
            with transaction.atomic():
                # Création du slug à partir du nom
                form.instance.slug = slugify(form.cleaned_data['nom'])
                
                # Sauvegarde du partenaire
                self.object = form.save()
                logger.info(f"Partenaire créé : {self.object.nom} (ID: {self.object.pk})")

                # Association avec la formation
                formation.partenaires.add(self.object)
                formation.save()
                logger.info(f"Partenaire '{self.object.nom}' associé à la formation '{formation.nom}'")

                # Message de confirmation
                messages.success(
                    self.request,
                    f"Le partenaire '{self.object.nom}' a été créé et associé à la formation '{formation.nom}'."
                )
                
                return HttpResponseRedirect(reverse_lazy('formation-detail', kwargs={'pk': formation_id}))
                
        except Exception as e:
            # Gestion des erreurs avec journalisation
            logger.error(f"Erreur lors de la création du partenaire: {str(e)}", exc_info=True)
            messages.error(
                self.request,
                f"❌ Une erreur est survenue lors de la création du partenaire: {str(e)}"
            )
            return HttpResponseRedirect(reverse_lazy('formation-list'))

    def get_context_data(self, **kwargs):
        """
        Ajoute un titre dynamique au contexte avec information sur la formation.
        
        Args:
            **kwargs: Arguments de contexte par défaut
            
        Returns:
            dict: Contexte enrichi pour le template
        """
        context = super().get_context_data(**kwargs)
        
        # Récupération de la formation pour le contexte
        formation_id = self.kwargs.get('formation_id')
        formation = get_object_or_404(Formation, pk=formation_id)
        
        # Enrichissement du contexte
        context['titre'] = f"Ajouter un partenaire à la formation : {formation.nom} - {formation.num_offre}"
        context['formation'] = formation
        
        return context


class PartenaireUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """
    Vue permettant de modifier un partenaire existant.
    
    Cette vue implémente:
    - Validation des données
    - Journalisation des modifications
    - Messages de confirmation
    """
    model = Partenaire
    permission_required = 'rap_app.change_partenaire'
    fields = [
        'nom', 'secteur_activite', 'contact_nom', 'contact_poste', 
        'contact_telephone', 'contact_email', 'description'
    ]
    template_name = 'partenaires/partenaire_form.html'
    
    def form_valid(self, form):
        """
        Validation du formulaire avec journalisation des modifications.
        
        Args:
            form: Formulaire soumis
            
        Returns:
            HttpResponse: Redirection après sauvegarde
        """
        # Récupération de l'instance originale pour comparaison
        original = Partenaire.objects.get(pk=self.object.pk)
        
        # Sauvegarde du partenaire
        self.object = form.save()
        
        # Journalisation des modifications
        changes = self._get_changes_description(original, self.object)
        if changes:
            logger.info(
                f"Utilisateur {self.request.user} a modifié le partenaire '{self.object.nom}' (ID: {self.object.pk}): {changes}"
            )
        
        # Message de confirmation
        messages.success(
            self.request, 
            f"✅ Le partenaire '{self.object.nom}' a été mis à jour avec succès."
        )
        
        return super().form_valid(form)
    
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
            'nom': 'nom',
            'secteur_activite': 'secteur d\'activité',
            'contact_nom': 'nom du contact',
            'contact_email': 'email du contact',
            'contact_telephone': 'téléphone du contact',
        }
        
        # Vérification des changements pour chaque champ
        for field, label in fields_to_check.items():
            old_value = getattr(original, field)
            new_value = getattr(updated, field)
            
            if old_value != new_value:
                old_display = old_value if old_value else 'non défini'
                new_display = new_value if new_value else 'non défini'
                changes.append(f"{label}: '{old_display}' → '{new_display}'")
        
        return ", ".join(changes) if changes else ""
    
    def get_success_url(self):
        """
        Redirige vers le détail du partenaire après modification.
        
        Returns:
            str: URL de redirection après sauvegarde réussie
        """
        return reverse_lazy('partenaire-detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        """
        Ajoute un titre dynamique au contexte en fonction du partenaire modifié.
        
        Args:
            **kwargs: Arguments de contexte par défaut
            
        Returns:
            dict: Contexte enrichi pour le template
        """
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le partenaire : {self.object.nom}"
        
        # Ajout d'informations sur les formations associées
        formations_count = self.object.formations.count()
        context['formations_count'] = formations_count
        
        return context


class PartenaireDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """
    Vue permettant de supprimer un partenaire avec confirmation.
    
    Cette vue implémente:
    - Confirmation de suppression
    - Vérification des relations
    - Journalisation
    - Messages de confirmation
    """
    model = Partenaire
    permission_required = 'rap_app.delete_partenaire'
    success_url = reverse_lazy('partenaire-list')
    template_name = 'partenaires/partenaire_confirm_delete.html'
    
    def get_context_data(self, **kwargs):
        """
        Enrichit le contexte pour la confirmation de suppression.
        
        Args:
            **kwargs: Arguments de contexte par défaut
            
        Returns:
            dict: Contexte enrichi pour le template de confirmation
        """
        context = super().get_context_data(**kwargs)
        
        # Vérification des formations associées
        formations = self.object.formations.all()
        context['formations'] = formations
        context['formations_count'] = formations.count()
        
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
        partenaire_nom = self.object.nom
        formations_count = self.object.formations.count()
        
        # Avertissement si le partenaire a des formations associées
        if formations_count > 0:
            logger.warning(
                f"Suppression du partenaire '{partenaire_nom}' avec {formations_count} formations associées"
            )
        
        # Journalisation avant suppression
        logger.info(
            f"Utilisateur {request.user} a supprimé le partenaire '{partenaire_nom}' (ID: {self.object.pk})"
        )
        
        # Suppression effective
        self.object.delete()
        
        # Message de confirmation
        messages.success(
            request,
            f"✅ Le partenaire '{partenaire_nom}' a été supprimé avec succès."
        )
        
        return HttpResponseRedirect(self.get_success_url())
class ExportPartenairesCSVView(PermissionRequiredMixin, View):
    permission_required = 'rap_app.view_partenaire'

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="partenaires.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Nom', 'Secteur', 'Contact Nom', 'Poste', 'Téléphone', 'Email', 'Formations associées'
        ])

        partenaires = Partenaire.objects.prefetch_related('formations').all()
        for partenaire in partenaires:
            writer.writerow([
                partenaire.nom,
                partenaire.secteur_activite or '',
                partenaire.contact_nom or '',
                partenaire.contact_poste or '',
                partenaire.contact_telephone or '',
                partenaire.contact_email or '',
                partenaire.get_formations_count(),
            ])

        return response