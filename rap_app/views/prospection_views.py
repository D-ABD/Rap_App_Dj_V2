from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
import csv
from django.http import HttpResponse
from ..forms.ProspectionForm import ProspectionForm
from ..models.prospection import HistoriqueProspection, Prospection


def ProspectionHomeView(request):
    """
    Vue d'accueil de la section prospection.
    """
    return render(request, 'prospection/prospection_home.html')


class ProspectionListView(ListView):
    """
    Affiche la liste des prospections avec options de filtrage.
    """
    model = Prospection
    template_name = 'prospection/prospection_list.html'
    context_object_name = 'prospections'
    ordering = ['-date_prospection']
    paginate_by = 10  # Pagination : 10 par page

    def get_queryset(self):
        """
        Permet de filtrer les prospections par statut, formation ou entreprise.
        """
        queryset = super().get_queryset()
        statut = self.request.GET.get('statut')
        formation = self.request.GET.get('formation')
        entreprise = self.request.GET.get('entreprise')

        if statut:
            queryset = queryset.filter(statut=statut)
        if formation:
            queryset = queryset.filter(formation_id=formation)
        if entreprise:
            queryset = queryset.filter(company_id=entreprise)

        return queryset


class ProspectionDetailView(DetailView):
    """
    Affiche le détail d'une prospection.
    """
    model = Prospection
    template_name = 'prospection/prospection_detail.html'
    context_object_name = 'prospection'


class ProspectionCreateView(CreateView):
    """
    Vue permettant de créer une nouvelle prospection.
    """
    model = Prospection
    form_class = ProspectionForm
    template_name = 'prospection/prospection_form.html'
    success_url = reverse_lazy('prospection-list')

    def form_valid(self, form):
        messages.success(self.request, "✅ Prospection ajoutée avec succès.")
        return super().form_valid(form)

    def get_initial(self):
        """
        Pré-remplit la formation si transmise en GET.
        """
        initial = super().get_initial()
        formation_id = self.request.GET.get('formation')
        if formation_id:
            initial['formation'] = formation_id
        return initial


class ProspectionUpdateView(UpdateView):
    """
    Permet de modifier une prospection existante.
    """
    model = Prospection
    form_class = ProspectionForm
    template_name = 'prospection/prospection_form.html'
    success_url = reverse_lazy('prospection-list')

    def form_valid(self, form):
        messages.success(self.request, "✅ Prospection mise à jour avec succès.")
        return super().form_valid(form)


class ProspectionDeleteView(DeleteView):
    """
    Supprime une prospection avec confirmation.
    """
    model = Prospection
    template_name = 'prospection/prospection_confirm_delete.html'
    success_url = reverse_lazy('prospection-list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "✅ Prospection supprimée avec succès.")
        return super().delete(request, *args, **kwargs)


class HistoriqueProspectionListView(ListView):
    """
    Liste des historiques de modification des prospections.
    Possibilité de filtrer par prospection.
    """
    model = HistoriqueProspection
    template_name = 'prospection/historiqueprospection_list.html'
    context_object_name = 'historiques'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        prospection_id = self.request.GET.get("prospection")

        if prospection_id:
            queryset = queryset.filter(prospection_id=prospection_id)

        return queryset.select_related('prospection', 'modifie_par')


class HistoriqueProspectionDetailView(DetailView):
    """
    Affiche le détail d'un historique de modification.
    """
    model = HistoriqueProspection
    template_name = 'prospection/historiqueprospection_detail.html'
    context_object_name = 'historique'

def export_prospections_csv(request):
    """
    Exporte les prospections au format CSV.
    Applique les mêmes filtres que la vue de liste.
    """
    # Création de la réponse avec en-têtes CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="prospections.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Entreprise',
        'Formation',
        'Date prospection',
        'Statut',
        'Objectif',
        'Motif',
        'Responsable',
        'Commentaire',
    ])

    # On réutilise les filtres de la liste
    prospections = Prospection.objects.select_related(
        'company', 'formation', 'responsable'
    ).all()

    statut = request.GET.get('statut')
    formation = request.GET.get('formation')
    entreprise = request.GET.get('entreprise')

    if statut:
        prospections = prospections.filter(statut=statut)
    if formation:
        prospections = prospections.filter(formation_id=formation)
    if entreprise:
        prospections = prospections.filter(company_id=entreprise)

    # On écrit chaque ligne
    for p in prospections:
        writer.writerow([
            p.company.name,
            p.formation.nom if p.formation else '',
            p.date_prospection.strftime("%d/%m/%Y %H:%M"),
            p.get_statut_display(),
            p.get_objectif_display(),
            p.get_motif_display(),
            p.responsable.username if p.responsable else '',
            p.commentaire or '',
        ])

    return response