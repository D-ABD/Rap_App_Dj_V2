from datetime import timezone
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Count, Q
import csv
from django.http import HttpResponse

from ..forms.company_form import CompanyForm
from ..models.company import Company, CHOICES_TYPE_OF_ACTION
from ..models.prospection import Prospection

# Configuration du logger
logger = logging.getLogger(__name__)

# Liste des entreprises
class CompanyListView(LoginRequiredMixin, ListView):
    """
    Vue affichant la liste de toutes les entreprises avec options de filtrage.
    """
    model = Company
    template_name = 'company/company_list.html'
    context_object_name = 'companies'
    ordering = ['-created_at']
    paginate_by = 20
    
    def get_queryset(self):
        """Récupère les entreprises avec options de filtrage."""
        queryset = super().get_queryset()
        
        # Récupération des paramètres de filtrage
        search_query = self.request.GET.get('q', '').strip()
        sector = self.request.GET.get('sector', '').strip()
        city = self.request.GET.get('city', '').strip()
        action = self.request.GET.get('action', '').strip()
        
        # Ajoute une annotation pour le nombre de prospections
        queryset = queryset.annotate(prospections_count=Count('prospections'))
        
        # Application des filtres
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(contact_name__icontains=search_query) |
                Q(contact_email__icontains=search_query)
            )
            logger.debug(f"Filtrage des entreprises par recherche: '{search_query}'")
            
        if sector:
            queryset = queryset.filter(sector_name__icontains=sector)
            logger.debug(f"Filtrage des entreprises par secteur: '{sector}'")
            
        if city:
            queryset = queryset.filter(city__icontains=city)
            logger.debug(f"Filtrage des entreprises par ville: '{city}'")
            
        if action:
            queryset = queryset.filter(actions=action)
            logger.debug(f"Filtrage des entreprises par action: '{action}'")
        
        logger.debug(f"Liste des entreprises: {queryset.count()} résultats trouvés")
        return queryset
    
    def get_context_data(self, **kwargs):
        """Ajoute des données contextuelles pour le filtrage et les statistiques."""
        context = super().get_context_data(**kwargs)
        
        
        # Valeurs pour les filtres
        sectors = Company.objects.exclude(sector_name__isnull=True).exclude(sector_name='') \
                         .values_list('sector_name', flat=True).distinct().order_by('sector_name')
        
        cities = Company.objects.exclude(city__isnull=True).exclude(city='') \
                        .values_list('city', flat=True).distinct().order_by('city')
        
        # Statistiques
        context.update({
            'total_companies': Company.objects.count(),
            'sectors': sectors,
            'cities': cities,
            'action_choices': dict(CHOICES_TYPE_OF_ACTION),
            'filters': {
                'q': self.request.GET.get('q', ''),
                'sector': self.request.GET.get('sector', ''),
                'city': self.request.GET.get('city', ''),
                'action': self.request.GET.get('action', '')
            }
        })
        
        return context

# Détail d'une entreprise
class CompanyDetailView(LoginRequiredMixin, DetailView):
    """
    Vue affichant les détails d'une entreprise spécifique.
    """
    model = Company
    template_name = 'company/company_detail.html'
    
    def get_context_data(self, **kwargs):
        """Ajoute des données contextuelles comme les prospections associées."""
        context = super().get_context_data(**kwargs)
        company = self.object
        
        logger.info(f"Consultation des détails de l'entreprise #{company.pk}: {company.name} par {self.request.user.username}")
        
        # Récupération des prospections associées
        prospections = Prospection.objects.filter(company=company).select_related('formation', 'responsable') \
                                 .order_by('-date_prospection')
        
        context.update({
            'prospections': prospections,
            'prospections_count': prospections.count(),
            'company_age_days': (timezone.now().date() - company.created_at.date()).days
        })
        
        return context

# Création d'une entreprise
class CompanyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vue permettant de créer une nouvelle entreprise.
    """
    model = Company
    form_class = CompanyForm
    template_name = 'company/company_form.html'
    success_url = reverse_lazy('company-list')
    permission_required = 'rap_app.add_company'
    
    def get_context_data(self, **kwargs):
        """Ajoute des données contextuelles pour le formulaire."""
        context = super().get_context_data(**kwargs)
        context['title'] = "Créer une nouvelle entreprise"
        context['action'] = "create"
        return context
    
    def form_valid(self, form):
        """Associe l'utilisateur courant comme créateur de l'entreprise."""
        form.instance.created_by = self.request.user
        
        # Journalisation
        logger.info(
            f"Création d'une nouvelle entreprise '{form.cleaned_data.get('name')}' "
            f"par {self.request.user.username}"
        )
        
        # Message de succès
        messages.success(
            self.request,
            f"Entreprise '{form.cleaned_data.get('name')}' créée avec succès."
        )
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Journalise les erreurs de validation du formulaire."""
        logger.warning(
            f"Échec de création d'une entreprise: {form.errors.as_json()}"
        )
        
        # Message d'erreur
        messages.error(
            self.request,
            "L'entreprise n'a pas pu être créée. Veuillez corriger les erreurs dans le formulaire."
        )
        
        return super().form_invalid(form)

# Mise à jour d'une entreprise
class CompanyUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Vue permettant de modifier une entreprise existante.
    """
    model = Company
    form_class = CompanyForm
    template_name = 'company/company_form.html'
    permission_required = 'rap_app.change_company'
    
    def get_success_url(self):
        """Retourne l'URL de redirection après mise à jour réussie."""
        return reverse_lazy('company-detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        """Ajoute des données contextuelles pour le formulaire."""
        context = super().get_context_data(**kwargs)
        context['title'] = f"Modifier l'entreprise: {self.object.name}"
        context['action'] = "update"
        return context
    
    def form_valid(self, form):
        """Journalise les modifications et ajoute un message de succès."""
        original = Company.objects.get(pk=self.object.pk)
        changes = []
        
        # Détection des changements
        for field in ('name', 'city', 'contact_name', 'contact_email', 'sector_name'):
            old_value = getattr(original, field)
            new_value = form.cleaned_data.get(field)
            if old_value != new_value:
                changes.append(f"{field}: '{old_value or 'Non spécifié'}' → '{new_value or 'Non spécifié'}'")
        
        # Journalisation
        if changes:
            logger.info(
                f"Modification de l'entreprise #{self.object.pk} par {self.request.user.username}: "
                f"{', '.join(changes)}"
            )
            
            # Message de succès détaillé
            messages.success(
                self.request,
                f"Entreprise '{self.object.name}' mise à jour avec succès. Modifications: {', '.join(changes)}"
            )
        else:
            logger.info(f"Formulaire soumis sans modifications pour l'entreprise #{self.object.pk}")
            messages.info(self.request, "Aucune modification n'a été effectuée.")
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Journalise les erreurs de validation du formulaire."""
        logger.warning(
            f"Échec de modification de l'entreprise #{self.object.pk}: {form.errors.as_json()}"
        )
        
        # Message d'erreur
        messages.error(
            self.request,
            "L'entreprise n'a pas pu être modifiée. Veuillez corriger les erreurs dans le formulaire."
        )
        
        return super().form_invalid(form)

# Suppression d'une entreprise
class CompanyDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Vue permettant de supprimer une entreprise.
    """
    model = Company
    template_name = 'company/company_confirm_delete.html'
    success_url = reverse_lazy('company-list')
    permission_required = 'rap_app.delete_company'
    
    def get_context_data(self, **kwargs):
        """Ajoute des informations pour la confirmation de suppression."""
        context = super().get_context_data(**kwargs)
        company = self.object
        
        # Vérification des dépendances
        prospections_count = company.prospections.count()
        
        context.update({
            'prospections_count': prospections_count,
            'can_delete': prospections_count == 0  # Empêcher la suppression si des prospections existent
        })
        
        return context
    
    def delete(self, request, *args, **kwargs):
        """Personnalise la suppression avec vérification des dépendances."""
        self.object = self.get_object()
        company = self.object
        
        # Vérification des dépendances
        prospections_count = company.prospections.count()
        
        if prospections_count > 0:
            logger.warning(
                f"Tentative de suppression de l'entreprise #{company.pk} '{company.name}' "
                f"par {request.user.username} bloquée: {prospections_count} prospections associées"
            )
            
            messages.error(
                request,
                f"Impossible de supprimer l'entreprise '{company.name}' car elle possède {prospections_count} prospection(s). "
                f"Veuillez d'abord supprimer les prospections associées."
            )
            
            return redirect('company-detail', pk=company.pk)
        
        # Journalisation avant suppression
        logger.info(f"Suppression de l'entreprise #{company.pk} '{company.name}' par {request.user.username}")
        
        # Message de succès
        messages.success(request, f"Entreprise '{company.name}' supprimée avec succès.")
        
        # Suppression effective
        return super().delete(request, *args, **kwargs)

def export_companies_csv(request):
    """
    Exporte les entreprises filtrées au format CSV.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="entreprises.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Nom',
        'Ville',
        'Secteur',
        'Nom du contact',
        'Email',
        'Téléphone',
        'Nombre de prospections',
        'Date de création',
    ])

    # Récupération du queryset filtré (comme dans CompanyListView)
    queryset = Company.objects.all().annotate(prospections_count=Count('prospections'))

    q = request.GET.get('q', '').strip()
    sector = request.GET.get('sector', '').strip()
    city = request.GET.get('city', '').strip()
    action = request.GET.get('action', '').strip()

    if q:
        queryset = queryset.filter(
            Q(name__icontains=q) |
            Q(contact_name__icontains=q) |
            Q(contact_email__icontains=q)
        )
    if sector:
        queryset = queryset.filter(sector_name__icontains=sector)
    if city:
        queryset = queryset.filter(city__icontains=city)
    if action:
        queryset = queryset.filter(actions=action)

    for company in queryset:
        writer.writerow([
            company.name,
            company.city or '',
            company.sector_name or '',
            company.contact_name or '',
            company.contact_email or '',
            company.contact_phone_number or '',
            company.actions,
            company.prospections_count,
            company.created_at.strftime('%d/%m/%Y') if company.created_at else '',
        ])

    return response