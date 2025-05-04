# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.utils import timezone

from ..models.vae_jury import SuiviJury, VAE, HistoriqueStatutVAE, Centre
from ..forms.vae_jury_form import ObjectifCentreForm, SuiviJuryForm, VAEForm, HistoriqueStatutVAEForm


# VAE / Jury Home – Vue d’accueil synthétique
def vae_jury_home(request):
    total_vae = VAE.objects.count()
    total_en_cours = VAE.objects.exclude(statut__in=['terminee', 'abandonnee']).count()
    total_jurys = SuiviJury.objects.aggregate(Sum('jurys_realises'))['jurys_realises__sum'] or 0

    derniers_vae = VAE.objects.order_by('-date_creation')[:5]
    derniers_jurys = SuiviJury.objects.order_by('-annee', '-mois')[:5]

    context = {
        'total_vae': total_vae,
        'total_en_cours': total_en_cours,
        'total_jurys': total_jurys,
        'derniers_vae': derniers_vae,
        'derniers_jurys': derniers_jurys,
    }

    return render(request, 'vae_jury/vae_jury_home.html', context)


# Vues pour SuiviJury
class SuiviJuryListView(LoginRequiredMixin, ListView):
    model = SuiviJury
    template_name = 'vae_jury/jury_list.html'
    context_object_name = 'suivis'

    def get_queryset(self):
        queryset = SuiviJury.objects.all()

        # Filtrage par centre
        centre_id = self.request.GET.get('centre')
        if centre_id:
            queryset = queryset.filter(centre_id=centre_id)

        # Filtrage par année
        annee = self.request.GET.get('annee')
        if annee:
            queryset = queryset.filter(annee=annee)

        # Filtrage par mois
        mois = self.request.GET.get('mois')
        if mois:
            queryset = queryset.filter(mois=mois)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context['centres'] = Centre.objects.all()

        # Années disponibles
        context['annees'] = SuiviJury.objects.values_list('annee', flat=True).distinct().order_by('-annee')

        # ✅ Calcul automatique du total objectif avec fallback sur l'objectif du centre
        total_objectif = 0
        for suivi in queryset:
            total_objectif += suivi.get_objectif_auto()  # méthode définie dans ton modèle

        total_realises = queryset.aggregate(Sum('jurys_realises'))['jurys_realises__sum'] or 0

        context['total_objectif'] = total_objectif
        context['total_realises'] = total_realises
        context['pourcentage_global'] = round((total_realises / total_objectif) * 100, 2) if total_objectif > 0 else 0

        return context


class SuiviJuryDetailView(LoginRequiredMixin, DetailView):
    model = SuiviJury
    template_name = 'vae_jury/jury_detail.html'
    context_object_name = 'suivi'

class SuiviJuryCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = SuiviJury
    form_class = SuiviJuryForm
    template_name = 'vae_jury/jury_form.html'
    success_url = reverse_lazy('jury-list')
    success_message = "Le suivi des jurys a été créé avec succès."

    def get_initial(self):
        initial = super().get_initial()
        
        centre_id = self.request.GET.get('centre')
        if centre_id:
            try:
                centre = Centre.objects.get(pk=centre_id)
                initial['centre'] = centre
                initial['annee'] = timezone.now().year
                initial['mois'] = timezone.now().month
                initial['objectif_jury'] = centre.objectif_mensuel_jury or 0
            except Centre.DoesNotExist:
                pass

        return initial


class SuiviJuryUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = SuiviJury
    form_class = SuiviJuryForm
    template_name = 'vae_jury/jury_form.html'
    success_message = "Le suivi des jurys a été mis à jour avec succès."
    
    def get_success_url(self):
        return reverse('jury-detail', kwargs={'pk': self.object.pk})

class SuiviJuryDeleteView(LoginRequiredMixin, DeleteView):
    model = SuiviJury
    template_name = 'vae_jury/jury_confirm_delete.html'
    success_url = reverse_lazy('jury-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Le suivi des jurys a été supprimé avec succès.")
        return super().delete(request, *args, **kwargs)

# Vues pour VAE
class VAEListView(LoginRequiredMixin, ListView):
    model = VAE
    template_name = 'vae_jury/vae_list.html'
    context_object_name = 'vaes'
    
    def get_queryset(self):
        queryset = VAE.objects.all()
        
        # Filtrage par centre
        centre_id = self.request.GET.get('centre')
        if centre_id:
            queryset = queryset.filter(centre_id=centre_id)
            
        # Filtrage par année
        annee = self.request.GET.get('annee')
        if annee:
            queryset = queryset.filter(date_creation__year=annee)
            
        # Filtrage par mois
        mois = self.request.GET.get('mois')
        if mois:
            queryset = queryset.filter(date_creation__month=mois)
            
        # Filtrage par statut
        statut = self.request.GET.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['centres'] = Centre.objects.all()
        context['statuts'] = VAE.STATUT_CHOICES
        
        # Années disponibles
        context['annees'] = VAE.objects.dates('date_creation', 'year', order='DESC')
        
        # Calcul des statistiques
        queryset = self.get_queryset()
        context['total_vae'] = queryset.count()
        context['vae_par_statut'] = {
            statut: queryset.filter(statut=statut).count()
            for statut, _ in VAE.STATUT_CHOICES
        }
        context['vae_en_cours'] = queryset.exclude(statut__in=['terminee', 'abandonnee']).count()
        
        return context

class VAEDetailView(LoginRequiredMixin, DetailView):
    model = VAE
    template_name = 'vae_jury/vae_detail.html'
    context_object_name = 'vae'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['historique'] = self.object.historique_statuts.all().order_by('-date_changement_effectif')
        return context

class VAECreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = VAE
    form_class = VAEForm
    template_name = 'vae_jury/vae_form.html'
    success_url = reverse_lazy('vae-list')
    success_message = "La VAE a été créée avec succès."
    
    def get_initial(self):
        initial = super().get_initial()
        # Préremplir la date de création avec aujourd'hui
        initial['date_creation'] = timezone.now().date()
        return initial

class VAEUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = VAE
    form_class = VAEForm
    template_name = 'vae_jury/vae_form.html'
    success_message = "La VAE a été mise à jour avec succès."
    
    def get_success_url(self):
        return reverse('vae-detail', kwargs={'pk': self.object.pk})

class VAEDeleteView(LoginRequiredMixin, DeleteView):
    model = VAE
    template_name = 'vae_jury/vae_confirm_delete.html'
    success_url = reverse_lazy('vae-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "La VAE a été supprimée avec succès.")
        return super().delete(request, *args, **kwargs)

# Vue pour l'ajout d'un nouvel historique de statut
class HistoriqueStatutCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = HistoriqueStatutVAE
    form_class = HistoriqueStatutVAEForm
    template_name = 'vae_jury/vae_jury_historique_form.html'
    success_message = "Le changement de statut a été enregistré avec succès."
    
    def get_initial(self):
        initial = super().get_initial()
        vae = get_object_or_404(VAE, pk=self.kwargs['vae_id'])
        initial['vae'] = vae
        initial['statut'] = vae.statut
        initial['date_changement_effectif'] = timezone.now().date()
        return initial
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Mettre à jour le statut de la VAE
        vae = form.cleaned_data['vae']
        vae.statut = form.cleaned_data['statut']
        vae.save()
        return response
    
    def get_success_url(self):
        return reverse('vae-detail', kwargs={'pk': self.kwargs['vae_id']})

# Vues pour le tableau de bord
def vae_jury_dashboard(request):
    annee = int(request.GET.get('annee', timezone.now().year))

    jurys_par_mois = SuiviJury.objects.filter(annee=annee).values('mois').annotate(
        objectifs=Sum('objectif_jury'),
        realises=Sum('jurys_realises')
    ).order_by('mois')

    vae_par_statut = VAE.objects.filter(date_creation__year=annee).values('statut').annotate(
        total=Count('id')
    )

    vae_par_mois = {}
    for mois in range(1, 13):
        vae_par_mois[mois] = VAE.objects.filter(
            date_creation__year=annee,
            date_creation__month=mois
        ).values('statut').annotate(total=Count('id'))

    centres = Centre.objects.all()
    objectif_annuel_global = sum(c.objectif_annuel_jury or 0 for c in centres)
    objectif_mensuel_global = sum(c.objectif_mensuel_jury or 0 for c in centres)
    total_realises = SuiviJury.objects.filter(annee=annee).aggregate(total=Sum('jurys_realises'))['total'] or 0
    taux_realisation_global = round((total_realises / objectif_annuel_global) * 100, 1) if objectif_annuel_global else 0

    # 👉 Nouveau : statistiques globales VAE
    total_vae = VAE.objects.filter(date_creation__year=annee).count()
    vae_en_cours = VAE.objects.filter(date_creation__year=annee).exclude(statut__in=['terminee', 'abandonnee']).count()

    annees_jurys = SuiviJury.objects.values_list('annee', flat=True).distinct().order_by('-annee')
    annees_vae = VAE.objects.dates('date_creation', 'year', order='DESC')
    annees = sorted(set([a.year for a in annees_vae] + list(annees_jurys)), reverse=True)

    context = {
        'annee_selectionnee': annee,
        'annees': annees,
        'jurys_par_mois': jurys_par_mois,
        'vae_par_statut': vae_par_statut,
        'vae_par_mois': vae_par_mois,
        'objectif_annuel_global': objectif_annuel_global,
        'objectif_mensuel_global': objectif_mensuel_global,
        'total_realises': total_realises,
        'taux_realisation_global': taux_realisation_global,
        'objectifs_par_centre': centres,
        'total_vae': total_vae,
        'total_vae_en_cours': vae_en_cours,
    }

    return render(request, 'vae_jury/vae_jury_dashboard.html', context)


# API pour les graphiques
def api_jurys_data(request):
    annee = request.GET.get('annee', timezone.now().year)
    
    # Données pour chaque mois
    data = []
    for mois in range(1, 13):
        suivi = SuiviJury.objects.filter(annee=annee, mois=mois).aggregate(
            objectifs=Sum('objectif_jury'),
            realises=Sum('jurys_realises')
        )
        
        mois_name = dict(SuiviJury.MOIS_CHOICES).get(mois, str(mois))
        data.append({
            'mois': mois_name,
            'objectifs': suivi['objectifs'] or 0,
            'realises': suivi['realises'] or 0
        })
    
    return JsonResponse(data, safe=False)

def api_vae_data(request):
    annee = request.GET.get('annee', timezone.now().year)
    
    # Statistiques globales par statut
    vae_par_statut = []
    for statut, label in VAE.STATUT_CHOICES:
        count = VAE.objects.filter(
            date_creation__year=annee,
            statut=statut
        ).count()
        
        vae_par_statut.append({
            'statut': label,
            'count': count
        })
    
    # Évolution mensuelle des VAE
    vae_par_mois = []
    for mois in range(1, 13):
        count = VAE.objects.filter(
            date_creation__year=annee,
            date_creation__month=mois
        ).count()
        
        mois_name = dict(SuiviJury.MOIS_CHOICES).get(mois, str(mois))
        vae_par_mois.append({
            'mois': mois_name,
            'count': count
        })
    
    data = {
        'vae_par_statut': vae_par_statut,
        'vae_par_mois': vae_par_mois
    }
    
    return JsonResponse(data)






class ObjectifCentreUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Centre
    form_class = ObjectifCentreForm
    template_name = 'vae_jury/centre_objectif_form.html'
    success_message = "Objectifs mis à jour avec succès"

    def get_success_url(self):
        return reverse('jury-list')  # ou autre redirection
    





def modifier_objectifs_tous_centres(request):
    centres = Centre.objects.all()

    if request.method == 'POST':
        try:
            for centre in centres:
                prefix = f'centre_{centre.id}'
                objectif_annuel = request.POST.get(f'{prefix}_objectif_annuel')
                objectif_mensuel = request.POST.get(f'{prefix}_objectif_mensuel')

                centre.objectif_annuel_jury = int(objectif_annuel or 0)
                centre.objectif_mensuel_jury = int(objectif_mensuel or 0)
                centre.save()
            messages.success(request, "Objectifs mis à jour avec succès.")
            return redirect('vae-jury-dashboard')
        except Exception as e:
            messages.error(request, f"Erreur lors de la mise à jour : {e}")

    return render(request, 'vae_jury/objectifs_centres_form.html', {'centres': centres})