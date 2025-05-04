
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages


class BaseListView(LoginRequiredMixin, ListView):
    """Vue de base pour les listes"""
    paginate_by = 20
    template_name_suffix = '_list'


class BaseDetailView(LoginRequiredMixin, DetailView):
    """Vue de base pour les détails"""
    template_name_suffix = '_detail'


class BaseCreateView(LoginRequiredMixin, CreateView):
    """Vue de base pour la création"""
    template_name_suffix = '_form'
    
    def form_valid(self, form):
        messages.success(self.request, f"{self.model._meta.verbose_name} créé avec succès.")
        return super().form_valid(form)


class BaseUpdateView(LoginRequiredMixin, UpdateView):
    """Vue de base pour la mise à jour"""
    template_name_suffix = '_form'
    
    def form_valid(self, form):
        messages.success(self.request, f"{self.model._meta.verbose_name} mis à jour avec succès.")
        return super().form_valid(form)


class BaseDeleteView(LoginRequiredMixin, DeleteView):
    """Vue de base pour la suppression"""
    template_name_suffix = '_confirm_delete'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, f"{self.model._meta.verbose_name} supprimé avec succès.")
        return super().delete(request, *args, **kwargs)

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.urls import reverse_lazy
from django.db.models import Count, Sum, F, Value, CharField
from django.db.models.functions import Concat
from django.contrib.auth.mixins import PermissionRequiredMixin

from ..models import Centre, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class CentreListView(BaseListView):
    """Liste des centres de formation"""
    model = Centre
    context_object_name = 'centres'
    
    def get_queryset(self):
        queryset = super().get_queryset().annotate(
            nb_formations=Count('formations'),
            nb_formations_actives=Count('formations', filter=F('formations__end_date__gte') | F('formations__end_date__isnull=True')),
            nb_inscrits=Sum(F('formations__inscrits_crif') + F('formations__inscrits_mp'), default=0)
        )
        
        # Filtrage par recherche
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(nom__icontains=q)
            
        # Filtrage par code postal
        cp = self.request.GET.get('code_postal')
        if cp:
            queryset = queryset.filter(code_postal__startswith=cp)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques globales
        context['total_centres'] = Centre.objects.count()
        context['total_formations'] = Formation.objects.count()
        
        # Filtres appliqués
        context['filters'] = {
            'q': self.request.GET.get('q', ''),
            'code_postal': self.request.GET.get('code_postal', ''),
        }
        
        return context


class CentreDetailView(BaseDetailView):
    """Détail d'un centre de formation"""
    model = Centre
    context_object_name = 'centre'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les formations associées
        formations = self.object.formations.select_related('type_offre', 'statut').order_by('-start_date')
        
        # Filtrer par type d'offre si demandé
        type_offre = self.request.GET.get('type_offre')
        if type_offre:
            formations = formations.filter(type_offre_id=type_offre)
        
        # Filtrer par statut si demandé
        statut = self.request.GET.get('statut')
        if statut:
            formations = formations.filter(statut_id=statut)
        
        context['formations'] = formations
        
        # Statistiques
        context['stats'] = {
            'nb_formations': formations.count(),
            'nb_formations_actives': formations.filter(end_date__gte=F('start_date')).count(),
            'nb_inscrits_total': formations.aggregate(
                total=Sum(F('inscrits_crif') + F('inscrits_mp'), default=0)
            )['total'],
            'formations_par_type': formations.values('type_offre__nom').annotate(
                total=Count('id')
            ).order_by('-total'),
            'formations_par_statut': formations.values('statut__nom', 'statut__couleur').annotate(
                total=Count('id')
            ).order_by('-total'),
        }
        
        return context


class CentreCreateView(PermissionRequiredMixin, BaseCreateView):
    """Création d'un centre de formation"""
    model = Centre
    permission_required = 'rap_app.add_centre'
    fields = ['nom', 'code_postal']
    success_url = reverse_lazy('centre-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un centre de formation"
        return context


class CentreUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Mise à jour d'un centre de formation"""
    model = Centre
    permission_required = 'rap_app.change_centre'
    fields = ['nom', 'code_postal']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le centre : {self.object.nom}"
        return context


class CentreDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Suppression d'un centre de formation"""
    model = Centre
    permission_required = 'rap_app.delete_centre'
    success_url = reverse_lazy('centre-list')

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import Commentaire, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class CommentaireListView(BaseListView):
    """Liste des commentaires"""
    model = Commentaire
    context_object_name = 'commentaires'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('formation', 'utilisateur')
        
        # Filtrer par formation si spécifié
        formation_id = self.request.GET.get('formation')
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
        
        # Filtrer par utilisateur si spécifié
        utilisateur_id = self.request.GET.get('utilisateur')
        if utilisateur_id:
            queryset = queryset.filter(utilisateur_id=utilisateur_id)
        
        # Recherche dans le contenu
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(contenu__icontains=q)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Formations pour le filtre
        context['formations'] = Formation.objects.formations_actives().order_by('nom')
        
        # Filtres appliqués
        context['filters'] = {
            'formation': self.request.GET.get('formation', ''),
            'utilisateur': self.request.GET.get('utilisateur', ''),
            'q': self.request.GET.get('q', ''),
        }
        
        return context


class CommentaireCreateView(PermissionRequiredMixin, BaseCreateView):
    """Création d'un commentaire"""
    model = Commentaire
    permission_required = 'rap_app.add_commentaire'
    fields = ['formation', 'auteur', 'contenu']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un commentaire"
        
        # Pré-sélectionner la formation si fournie dans l'URL
        formation_id = self.request.GET.get('formation')
        if formation_id:
            try:
                formation = Formation.objects.get(pk=formation_id)
                context['formation_preselected'] = formation
            except Formation.DoesNotExist:
                pass
        
        return context
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Pré-sélectionner la formation si fournie dans l'URL
        formation_id = self.request.GET.get('formation')
        if formation_id:
            try:
                formation = Formation.objects.get(pk=formation_id)
                form.initial['formation'] = formation
            except Formation.DoesNotExist:
                pass
        
        return form
    
    def form_valid(self, form):
        # Associer l'utilisateur courant au commentaire
        form.instance.utilisateur = self.request.user
        
        # Si le champ auteur est vide, utiliser le nom de l'utilisateur courant
        if not form.instance.auteur:
            form.instance.auteur = self.request.user.get_full_name() or self.request.user.username
        
        return super().form_valid(form)
    
    def get_success_url(self):
        # Si redirigé depuis la vue détaillée d'une formation, y retourner
        if self.object.formation and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': self.object.formation.id})
        return reverse('commentaire-list')


class CommentaireUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Mise à jour d'un commentaire"""
    model = Commentaire
    permission_required = 'rap_app.change_commentaire'
    fields = ['formation', 'auteur', 'contenu']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le commentaire"
        return context
    
    def get_success_url(self):
        # Si redirigé depuis la vue détaillée d'une formation, y retourner
        if self.object.formation and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': self.object.formation.id})
        return reverse('commentaire-detail', kwargs={'pk': self.object.pk})


class CommentaireDetailView(BaseDetailView):
    """Détail d'un commentaire"""
    model = Commentaire
    context_object_name = 'commentaire'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer d'autres commentaires de la même formation
        if self.object.formation:
            context['autres_commentaires'] = self.object.formation.commentaires.exclude(
                id=self.object.id
            ).order_by('-created_at')[:5]
        
        return context


class CommentaireDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Suppression d'un commentaire"""
    model = Commentaire
    permission_required = 'rap_app.delete_commentaire'
    
    def get_success_url(self):
        # Rediriger vers la formation si le commentaire est lié à une formation
        formation_id = self.object.formation.id if self.object.formation else None
        if formation_id and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': formation_id})
        return reverse('commentaire-list')

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, Avg, F, Q, Case, When, IntegerField, Value
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta

from ..models import Formation, Centre, TypeOffre, Statut, Evenement, HistoriqueFormation, Recherche


class DashboardView(LoginRequiredMixin, TemplateView):
    """Vue du tableau de bord principal"""
    template_name = 'rap_app/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques globales
        context['total_formations'] = Formation.objects.count()
        context['formations_actives'] = Formation.objects.formations_actives().count()
        context['formations_a_venir'] = Formation.objects.formations_a_venir().count()
        
        # Formations par statut
        statuts = Statut.objects.annotate(
            nb_formations=Count('formations')
        ).filter(nb_formations__gt=0).order_by('-nb_formations')
        
        context['statuts'] = statuts
        
        # Taux de remplissage moyen des formations actives
        from django.db.models.functions import Coalesce
        
        taux_remplissage = Formation.objects.formations_actives().aggregate(
            taux=Avg(
                100 * (F('inscrits_crif') + F('inscrits_mp')) / 
                Coalesce(F('prevus_crif') + F('prevus_mp'), Value(1), output_field=IntegerField())
            )
        )
        
        context['taux_remplissage_moyen'] = taux_remplissage['taux'] or 0
        
        # Formations récentes
        context['formations_recentes'] = Formation.objects.select_related(
            'centre', 'type_offre', 'statut'
        ).order_by('-created_at')[:5]
        
        # Événements à venir
        context['evenements_a_venir'] = Evenement.objects.select_related(
            'formation'
        ).filter(
            event_date__gte=timezone.now().date()
        ).order_by('event_date')[:5]
        
        # Récentes recherches (pour administrateurs)
        if self.request.user.is_staff:
            context['recherches_recentes'] = Recherche.objects.select_related(
                'utilisateur'
            ).order_by('-created_at')[:10]
        
        return context


class StatsAPIView(LoginRequiredMixin, TemplateView):
    """API pour les données statistiques"""
    
    def get(self, request, *args, **kwargs):
        action = request.GET.get('action')
        
        if action == 'formations_par_statut':
            return self.formations_par_statut()
        elif action == 'evolution_formations':
            return self.evolution_formations()
        elif action == 'formations_par_type':
            return self.formations_par_type()
        elif action == 'taux_remplissage':
            return self.taux_remplissage()
        else:
            return JsonResponse({'error': 'Action non reconnue'}, status=400)
    
    def formations_par_statut(self):
        """Renvoie le nombre de formations par statut"""
        from django.db.models.functions import Coalesce
        
        statuts = Statut.objects.annotate(
            nb_formations=Count('formations'),
            taux_moyen=Coalesce(
                Avg(
                    100 * (F('formations__inscrits_crif') + F('formations__inscrits_mp')) / 
                    Coalesce(F('formations__prevus_crif') + F('formations__prevus_mp'), Value(1), output_field=IntegerField())
                ),
                0
            )
        ).values('nom', 'nb_formations', 'taux_moyen', 'couleur')
        
        return JsonResponse({
            'statuts': list(statuts)
        })
    
    def evolution_formations(self):
        """Renvoie l'évolution du nombre de formations et d'inscrits par mois"""
        from django.db.models.functions import TruncMonth
        
        # Historique des 12 derniers mois
        date_limite = timezone.now().date() - timedelta(days=365)
        
        evolution = HistoriqueFormation.objects.filter(
            created_at__gte=date_limite
        ).annotate(
            mois=TruncMonth('created_at')
        ).values('mois').annotate(
            nb_inscrits=Sum('inscrits_total'),
            nb_formations=Count('formation', distinct=True)
        ).order_by('mois')
        
        # Convertir les dates en chaînes pour JSON
        for item in evolution:
            if item['mois']:
                item['mois'] = item['mois'].strftime('%Y-%m')
        
        return JsonResponse({
            'evolution': list(evolution)
        })
    
    def formations_par_type(self):
        """Renvoie le nombre de formations par type d'offre"""
        types = TypeOffre.objects.annotate(
            nb_formations=Count('formations')
        ).filter(nb_formations__gt=0).values('nom', 'nb_formations')
        
        return JsonResponse({
            'types': list(types)
        })
    
    def taux_remplissage(self):
        """Renvoie le taux de remplissage des formations actives"""
        from django.db.models.functions import Coalesce
        
        formations = Formation.objects.formations_actives().annotate(
            taux=100 * (F('inscrits_crif') + F('inscrits_mp')) / 
                Coalesce(F('prevus_crif') + F('prevus_mp'), Value(1), output_field=IntegerField())
        ).values('id', 'nom', 'taux')
        
        # Calculer la répartition par tranches
        tranches = {
            '0-25%': 0,
            '25-50%': 0,
            '50-75%': 0,
            '75-100%': 0,
            '>100%': 0
        }
        
        for f in formations:
            taux = f['taux']
            if taux <= 25:
                tranches['0-25%'] += 1
            elif taux <= 50:
                tranches['25-50%'] += 1
            elif taux <= 75:
                tranches['50-75%'] += 1
            elif taux <= 100:
                tranches['75-100%'] += 1
            else:
                tranches['>100%'] += 1
        
        return JsonResponse({
            'formations': list(formations),
            'tranches': tranches
        })

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.urls import reverse
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import FileResponse, Http404
from django.conf import settings
from django.views.generic import View
import os

from ..models import Document, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class DocumentListView(BaseListView):
    """Liste des documents"""
    model = Document
    context_object_name = 'documents'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('formation')
        
        # Filtrer par formation si spécifié
        formation_id = self.request.GET.get('formation')
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
        
        # Recherche par nom de fichier
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(nom_fichier__icontains=q)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Formations pour le filtre
        context['formations'] = Formation.objects.formations_actives().order_by('nom')
        
        # Filtres appliqués
        context['filters'] = {
            'formation': self.request.GET.get('formation', ''),
            'q': self.request.GET.get('q', ''),
        }
        
        return context


class DocumentDetailView(BaseDetailView):
    """Détail d'un document"""
    model = Document
    context_object_name = 'document'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer d'autres documents de la même formation
        if self.object.formation:
            context['autres_documents'] = self.object.formation.documents.exclude(
                id=self.object.id
            ).order_by('-created_at')[:5]
        
        return context


class DocumentCreateView(PermissionRequiredMixin, BaseCreateView):
    """Création d'un document"""
    model = Document
    permission_required = 'rap_app.add_document'
    fields = ['formation', 'nom_fichier', 'fichier', 'source']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un document"
        
        # Pré-sélectionner la formation si fournie dans l'URL
        formation_id = self.request.GET.get('formation')
        if formation_id:
            try:
                formation = Formation.objects.get(pk=formation_id)
                context['formation_preselected'] = formation
            except Formation.DoesNotExist:
                pass
                
        return context
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Pré-sélectionner la formation si fournie dans l'URL
        formation_id = self.request.GET.get('formation')
        if formation_id:
            try:
                formation = Formation.objects.get(pk=formation_id)
                form.initial['formation'] = formation
            except Formation.DoesNotExist:
                pass
        
        return form
    
    def get_success_url(self):
        # Si redirigé depuis la vue détaillée d'une formation, y retourner
        if self.object.formation and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': self.object.formation.id})
        return reverse('document-detail', kwargs={'pk': self.object.pk})


class DocumentUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Mise à jour d'un document"""
    model = Document
    permission_required = 'rap_app.change_document'
    fields = ['formation', 'nom_fichier', 'fichier', 'source']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le document : {self.object.nom_fichier}"
        return context
    
    def get_success_url(self):
        # Si redirigé depuis la vue détaillée d'une formation, y retourner
        if self.object.formation and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': self.object.formation.id})
        return reverse('document-detail', kwargs={'pk': self.object.pk})


class DocumentDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Suppression d'un document"""
    model = Document
    permission_required = 'rap_app.delete_document'
    
    def get_success_url(self):
        # Rediriger vers la formation si le document est lié à une formation
        formation_id = self.object.formation.id if self.object.formation else None
        if formation_id and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': formation_id})
        return reverse('document-list')


class DocumentDownloadView(View):
    """Vue pour télécharger un document"""
    
    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        
        # Vérifier que l'utilisateur est authentifié
        if not request.user.is_authenticated:
            raise Http404("Document non disponible")
            
        # Construire le chemin du fichier
        file_path = os.path.join(settings.MEDIA_ROOT, document.fichier.name)
        
        # Vérifier que le fichier existe
        if not os.path.exists(file_path):
            messages.error(request, f"Le fichier {document.nom_fichier} n'existe pas")
            return reverse('document-detail', kwargs={'pk': document.pk})
        
        # Ouvrir et retourner le fichier
        try:
            response = FileResponse(open(file_path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{document.nom_fichier}"'
            
            # Enregistrer le téléchargement dans l'historique si nécessaire
            # Ajouter votre code ici si vous souhaitez suivre les téléchargements
            
            return response
        except Exception as e:
            messages.error(request, f"Erreur lors du téléchargement : {str(e)}")
            return reverse('document-detail', kwargs={'pk': document.pk})

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import Evenement, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class EvenementListView(BaseListView):
    """Liste des événements"""
    model = Evenement
    context_object_name = 'evenements'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('formation', 'formation__centre')
        
        # Filtrage par formation
        formation_id = self.request.GET.get('formation')
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
        
        # Filtrage par type d'événement
        type_evenement = self.request.GET.get('type')
        if type_evenement:
            queryset = queryset.filter(type_evenement=type_evenement)
        
        # Filtrage par date
        date_debut = self.request.GET.get('date_debut')
        if date_debut:
            queryset = queryset.filter(event_date__gte=date_debut)
        
        date_fin = self.request.GET.get('date_fin')
        if date_fin:
            queryset = queryset.filter(event_date__lte=date_fin)
            
        # Recherche par description
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(details__icontains=q) | queryset.filter(description_autre__icontains=q)
        
        return queryset.order_by('-event_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Liste des formations pour le filtre
        context['formations'] = Formation.objects.formations_actives().order_by('nom')
        
        # Types d'événements pour le filtre
        context['types_evenement'] = Evenement.TYPE_EVENEMENT_CHOICES
        
        # Filtres appliqués
        context['filters'] = {
            'formation': self.request.GET.get('formation', ''),
            'type': self.request.GET.get('type', ''),
            'date_debut': self.request.GET.get('date_debut', ''),
            'date_fin': self.request.GET.get('date_fin', ''),
            'q': self.request.GET.get('q', ''),
        }
        
        return context


class EvenementDetailView(BaseDetailView):
    """Détail d'un événement"""
    model = Evenement
    context_object_name = 'evenement'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer d'autres événements de la même formation
        if self.object.formation:
            context['autres_evenements'] = self.object.formation.evenements.exclude(
                id=self.object.id
            ).order_by('-event_date')[:5]
        
        return context


class EvenementCreateView(PermissionRequiredMixin, BaseCreateView):
    """Création d'un événement"""
    model = Evenement
    permission_required = 'rap_app.add_evenement'
    fields = ['formation', 'type_evenement', 'event_date', 'details', 'description_autre']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un événement"
        
        # Pré-sélectionner la formation si fournie dans l'URL
        formation_id = self.request.GET.get('formation')
        if formation_id:
            try:
                formation = Formation.objects.get(pk=formation_id)
                context['formation_preselected'] = formation
            except Formation.DoesNotExist:
                pass
        
        return context
    
    def get_success_url(self):
        formation_id = self.object.formation.id if self.object.formation else None
        if formation_id and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': formation_id})
        return reverse('evenement-list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Pré-sélectionner la formation si fournie dans l'URL
        formation_id = self.request.GET.get('formation')
        if formation_id:
            try:
                formation = Formation.objects.get(pk=formation_id)
                form.initial['formation'] = formation
            except Formation.DoesNotExist:
                pass
        
        return form
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Rediriger vers la formation si demandé
        if self.object.formation and self.request.GET.get('redirect_to_formation') == 'true':
            messages.success(self.request, f"Événement ajouté à la formation {self.object.formation.nom}")
        
        return response


class EvenementUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Mise à jour d'un événement"""
    model = Evenement
    permission_required = 'rap_app.change_evenement'
    fields = ['formation', 'type_evenement', 'event_date', 'details', 'description_autre']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier l'événement du {self.object.event_date}"
        return context
    
    def get_success_url(self):
        # Rediriger vers la formation si l'événement est lié à une formation
        if self.object.formation and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': self.object.formation.id})
        return reverse('evenement-detail', kwargs={'pk': self.object.pk})


class EvenementDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Suppression d'un événement"""
    model = Evenement
    permission_required = 'rap_app.delete_evenement'
    
    def get_success_url(self):
        # Rediriger vers la formation si l'événement est lié à une formation
        formation_id = self.object.formation.id if self.object.formation else None
        if formation_id and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': formation_id})
        return reverse('evenement-list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        formation = self.object.formation
        
        # Appeler la méthode parent pour supprimer l'objet
        response = super().delete(request, *args, **kwargs)
        
        # Message de confirmation avec référence à la formation
        if formation:
            messages.success(request, f"Événement supprimé de la formation {formation.nom}")
        else:
            messages.success(request, "Événement supprimé avec succès")
            
        return response

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.views.generic import TemplateView
from django.db.models import Count, Sum, Avg, Q, F
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin

from ..models import Formation, Centre, TypeOffre, Statut, Ressource, Evenement, Document, HistoriqueFormation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class FormationListView(BaseListView):
    """Liste des formations"""
    model = Formation
    context_object_name = 'formations'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('centre', 'type_offre', 'statut')
        
        # Filtres par recherche
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(nom__icontains=q) | 
                Q(centre__nom__icontains=q) |
                Q(num_kairos__icontains=q) |
                Q(num_offre__icontains=q) |
                Q(num_produit__icontains=q)
            )
        
        # Filtre par centre
        centre_id = self.request.GET.get('centre')
        if centre_id:
            queryset = queryset.filter(centre_id=centre_id)
            
        # Filtre par type d'offre
        type_offre_id = self.request.GET.get('type_offre')
        if type_offre_id:
            queryset = queryset.filter(type_offre_id=type_offre_id)
            
        # Filtre par statut
        statut_id = self.request.GET.get('statut')
        if statut_id:
            queryset = queryset.filter(statut_id=statut_id)
            
        # Filtre par dates
        date_debut = self.request.GET.get('date_debut')
        if date_debut:
            queryset = queryset.filter(start_date__gte=date_debut)
            
        date_fin = self.request.GET.get('date_fin')
        if date_fin:
            queryset = queryset.filter(end_date__lte=date_fin)
            
        # Filtre par statut actif/terminé
        actif = self.request.GET.get('actif')
        if actif == 'true':
            queryset = queryset.formations_actives()
        elif actif == 'false':
            queryset = queryset.formations_terminees()
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['centres'] = Centre.objects.all()
        context['types_offre'] = TypeOffre.objects.all()
        context['statuts'] = Statut.objects.all()
        
        # Données pour le résumé des formations
        context['total_formations'] = Formation.objects.count()
        context['formations_actives'] = Formation.objects.formations_actives().count()
        context['formations_a_venir'] = Formation.objects.formations_a_venir().count()
        
        # Filtres appliqués
        context['filters'] = {
            'q': self.request.GET.get('q', ''),
            'centre': self.request.GET.get('centre', ''),
            'type_offre': self.request.GET.get('type_offre', ''),
            'statut': self.request.GET.get('statut', ''),
            'date_debut': self.request.GET.get('date_debut', ''),
            'date_fin': self.request.GET.get('date_fin', ''),
            'actif': self.request.GET.get('actif', ''),
        }
        
        # Enregistrer la recherche si nécessaire
        if any(context['filters'].values()) and hasattr(self.request, 'user') and self.request.user.is_authenticated:
            from ..models import Recherche
            
            try:
                temps_debut = self.request.session.get('temps_debut_recherche')
                temps_execution = None
                if temps_debut:
                    import time
                    temps_fin = time.time()
                    temps_execution = (temps_fin - float(temps_debut)) * 1000  # en ms
                
                Recherche.objects.create(
                    utilisateur=self.request.user,
                    terme_recherche=context['filters']['q'],
                    filtre_centre_id=context['filters']['centre'] or None,
                    filtre_type_offre_id=context['filters']['type_offre'] or None,
                    filtre_statut_id=context['filters']['statut'] or None,
                    date_debut=context['filters']['date_debut'] or None,
                    date_fin=context['filters']['date_fin'] or None,
                    nombre_resultats=context['paginator'].count if 'paginator' in context else 0,
                    temps_execution=temps_execution,
                    adresse_ip=self.request.META.get('REMOTE_ADDR'),
                    user_agent=self.request.META.get('HTTP_USER_AGENT')
                )
            except Exception as e:
                # Juste logger l'erreur sans impacter l'expérience utilisateur
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors de l'enregistrement de la recherche: {e}")
        
        return context
    
    def dispatch(self, request, *args, **kwargs):
        # Enregistrer le temps de début pour calculer le temps d'exécution
        import time
        request.session['temps_debut_recherche'] = time.time()
        return super().dispatch(request, *args, **kwargs)


class FormationDetailView(BaseDetailView):
    """Détail d'une formation"""
    model = Formation
    context_object_name = 'formation'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formation = self.get_object()
        
        # Récupérer les ressources associées
        try:
            context['ressource'] = formation.ressource
        except Ressource.DoesNotExist:
            context['ressource'] = None
            
        # Récupérer les événements associés
        context['evenements'] = formation.evenements.all().order_by('-event_date')
        context['commentaires'] = formation.commentaires.all().order_by('-created_at')
        context['documents'] = formation.documents.all().order_by('-created_at')
        context['historique'] = formation.historique_formations.all().order_by('-created_at')[:10]
        
        return context


class FormationCreateView(PermissionRequiredMixin, BaseCreateView):
    """Création d'une formation"""
    model = Formation
    permission_required = 'rap_app.add_formation'
    fields = [
        'nom', 'centre', 'type_offre', 'statut', 'start_date', 'end_date', 
        'num_kairos', 'num_offre', 'num_produit', 'prevus_crif', 
        'prevus_mp', 'inscrits_crif', 'inscrits_mp', 'assistante', 
        'cap', 'convocation_envoie', 'entresformation'
    ]
    success_url = reverse_lazy('formation-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter une formation"
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Créer un historique
        HistoriqueFormation.objects.create(
            formation=self.object,
            utilisateur=self.request.user,
            action="Création de la formation",
            nouveau_statut=self.object.statut.nom,
            inscrits_total=self.object.inscrits_total,
            inscrits_crif=self.object.inscrits_crif,
            inscrits_mp=self.object.inscrits_mp,
            total_places=self.object.total_places,
            semaine=timezone.now().isocalendar()[1],
            mois=timezone.now().month,
            annee=timezone.now().year
        )
        
        # Créer une ressource vide associée
        Ressource.objects.create(formation=self.object)
        
        return response


class FormationUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Mise à jour d'une formation"""
    model = Formation
    permission_required = 'rap_app.change_formation'
    fields = [
        'nom', 'centre', 'type_offre', 'statut', 'start_date', 'end_date', 
        'num_kairos', 'num_offre', 'num_produit', 'prevus_crif', 
        'prevus_mp', 'inscrits_crif', 'inscrits_mp', 'assistante', 
        'cap', 'convocation_envoie', 'entresformation'
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier la formation : {self.object.nom}"
        return context
    
    def form_valid(self, form):
        # Récupérer l'état avant modification
        ancien_statut = None
        if 'statut' in form.changed_data:
            ancien_statut = self.get_object().statut.nom
        
        # Sauvegarder les modifications
        response = super().form_valid(form)
        
        # Créer un historique si des champs importants ont été modifiés
        champs_importants = ['statut', 'inscrits_crif', 'inscrits_mp', 'prevus_crif', 'prevus_mp']
        if any(champ in form.changed_data for champ in champs_importants):
            action = "Modification du statut" if 'statut' in form.changed_data else "Modification des inscriptions"
            HistoriqueFormation.objects.create(
                formation=self.object,
                utilisateur=self.request.user,
                action=action,
                ancien_statut=ancien_statut,
                nouveau_statut=self.object.statut.nom if 'statut' in form.changed_data else None,
                inscrits_total=self.object.inscrits_total,
                inscrits_crif=self.object.inscrits_crif,
                inscrits_mp=self.object.inscrits_mp,
                total_places=self.object.total_places,
                semaine=timezone.now().isocalendar()[1],
                mois=timezone.now().month,
                annee=timezone.now().year,
                details={champ: form.cleaned_data[champ] for champ in form.changed_data}
            )
        
        return response


class FormationDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Suppression d'une formation"""
    model = Formation
    permission_required = 'rap_app.delete_formation'
    success_url = reverse_lazy('formation-list')


class FormationDashboardView(LoginRequiredMixin, TemplateView):
    """Tableau de bord des formations"""
    template_name = 'rap_app/formation_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques générales
        context['total_formations'] = Formation.objects.count()
        context['formations_actives'] = Formation.objects.formations_actives().count()
        context['formations_a_venir'] = Formation.objects.formations_a_venir().count()
        
        # Répartition par centre
        centres = Centre.objects.annotate(
            nb_formations=Count('formations'),
            nb_inscrits=Sum('formations__inscrits_crif') + Sum('formations__inscrits_mp'),
            nb_places=Sum('formations__prevus_crif') + Sum('formations__prevus_mp')
        ).filter(nb_formations__gt=0).order_by('-nb_formations')
        
        context['centres'] = centres
        
        # Répartition par type d'offre
        types_offre = TypeOffre.objects.annotate(
            nb_formations=Count('formations'),
            nb_inscrits=Sum('formations__inscrits_crif') + Sum('formations__inscrits_mp'),
            nb_places=Sum('formations__prevus_crif') + Sum('formations__prevus_mp')
        ).filter(nb_formations__gt=0).order_by('-nb_formations')
        
        context['types_offre'] = types_offre
        
        # Formations récentes
        context['formations_recentes'] = Formation.objects.order_by('-created_at')[:10]
        
        # Taux de remplissage moyen
        taux_remplissage = Formation.objects.formations_actives().aggregate(
            Avg(F('inscrits_crif') + F('inscrits_mp')) / Avg(F('prevus_crif') + F('prevus_mp')) * 100
        )
        context['taux_remplissage_moyen'] = taux_remplissage.get('expr', 0)
        
        return context


class FormationAPIView(LoginRequiredMixin, TemplateView):
    """Vue API pour les données de formation au format JSON"""
    
    def get(self, request, *args, **kwargs):
        action = request.GET.get('action')
        
        if action == 'statistiques':
            # Données statistiques pour les graphiques
            return self.get_statistiques()
        elif action == 'formations':
            # Liste simplifiée des formations
            return self.get_formations()
        else:
            return JsonResponse({'error': 'Action non reconnue'}, status=400)
    
    def get_statistiques(self):
        """Renvoie les statistiques pour les graphiques"""
        # Répartition par statut
        statuts = Statut.objects.annotate(
            nb_formations=Count('formations')
        ).values('nom', 'nb_formations', 'couleur')
        
        # Évolution des inscriptions par mois
        from django.db.models.functions import TruncMonth
        
        evolution = HistoriqueFormation.objects.annotate(
            mois=TruncMonth('created_at')
        ).values('mois').annotate(
            nb_inscrits=Sum('inscrits_total')
        ).order_by('mois')
        
        return JsonResponse({
            'statuts': list(statuts),
            'evolution': list(evolution),
        })
    
    def get_formations(self):
        """Renvoie une liste simplifiée des formations"""
        formations = Formation.objects.select_related('centre', 'type_offre', 'statut').values(
            'id', 'nom', 'centre__nom', 'type_offre__nom', 'statut__nom', 
            'start_date', 'end_date', 'inscrits_crif', 'inscrits_mp',
            'prevus_crif', 'prevus_mp'
        )
        
        # Ajouter des champs calculés
        for f in formations:
            f['inscrits_total'] = f['inscrits_crif'] + f['inscrits_mp']
            f['total_places'] = f['prevus_crif'] + f['prevus_mp']
            if f['total_places'] > 0:
                f['taux_remplissage'] = (f['inscrits_total'] / f['total_places']) * 100
            else:
                f['taux_remplissage'] = 0
        
        return JsonResponse({
            'formations': list(formations)
        })

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Count, Sum, Avg, F, Q
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
import csv
import io

from ..models import Rapport, Formation, Centre, TypeOffre, Statut, Evenement, HistoriqueFormation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class RapportListView(BaseListView):
    """Liste des rapports"""
    model = Rapport
    context_object_name = 'rapports'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('formation')
        
        # Filtrage par période
        periode = self.request.GET.get('periode')
        if periode:
            queryset = queryset.filter(periode=periode)
        
        # Filtrage par formation
        formation_id = self.request.GET.get('formation')
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
        
        # Filtrage par date
        date_debut = self.request.GET.get('date_debut')
        if date_debut:
            queryset = queryset.filter(date_fin__gte=date_debut)
            
        date_fin = self.request.GET.get('date_fin')
        if date_fin:
            queryset = queryset.filter(date_debut__lte=date_fin)
        
        return queryset.order_by('-date_fin')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Données pour les filtres
        context['formations'] = Formation.objects.formations_actives()
        context['periodes'] = Rapport.PERIODE_CHOICES
        
        # Filtres appliqués
        context['filters'] = {
            'periode': self.request.GET.get('periode', ''),
            'formation': self.request.GET.get('formation', ''),
            'date_debut': self.request.GET.get('date_debut', ''),
            'date_fin': self.request.GET.get('date_fin', ''),
        }
        
        return context


class RapportDetailView(BaseDetailView):
    """Détail d'un rapport"""
    model = Rapport
    context_object_name = 'rapport'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer d'autres rapports de la même formation
        if self.object.formation:
            context['autres_rapports'] = self.object.formation.rapports.exclude(
                id=self.object.id
            ).order_by('-date_fin')[:5]
        
        # Calculer quelques statistiques supplémentaires
        context['evolution'] = None
        if self.object.formation:
            # Chercher le rapport précédent pour cette formation et cette période
            rapport_precedent = Rapport.objects.filter(
                formation=self.object.formation,
                periode=self.object.periode,
                date_fin__lt=self.object.date_debut
            ).order_by('-date_fin').first()
            
            if rapport_precedent:
                context['evolution'] = {
                    'inscrits': self.object.total_inscrits - rapport_precedent.total_inscrits,
                    'taux_remplissage': self.object.taux_remplissage - rapport_precedent.taux_remplissage,
                    'rapport_precedent': rapport_precedent
                }
        
        return context


class RapportCreateView(PermissionRequiredMixin, BaseCreateView):
    """Création d'un rapport"""
    model = Rapport
    permission_required = 'rap_app.add_rapport'
    fields = [
        'formation', 'periode', 'date_debut', 'date_fin', 
        'total_inscrits', 'inscrits_crif', 'inscrits_mp', 'total_places',
        'nombre_evenements', 'nombre_candidats', 'nombre_entretiens'
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Créer un nouveau rapport"
        
        # Pré-sélectionner la formation si fournie dans l'URL
        formation_id = self.request.GET.get('formation')
        if formation_id:
            try:
                formation = Formation.objects.get(pk=formation_id)
                context['formation_preselected'] = formation
            except Formation.DoesNotExist:
                pass
                
        return context
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Pré-sélectionner la formation si fournie dans l'URL
        formation_id = self.request.GET.get('formation')
        if formation_id:
            try:
                formation = Formation.objects.get(pk=formation_id)
                form.initial['formation'] = formation
                
                # Pré-remplir avec les données actuelles de la formation
                form.initial['total_inscrits'] = formation.inscrits_total
                form.initial['inscrits_crif'] = formation.inscrits_crif
                form.initial['inscrits_mp'] = formation.inscrits_mp
                form.initial['total_places'] = formation.total_places
                
                # Essayer de récupérer les données de la ressource
                try:
                    ressource = formation.ressource
                    form.initial['nombre_evenements'] = ressource.nombre_evenements
                    form.initial['nombre_candidats'] = ressource.nombre_candidats
                    form.initial['nombre_entretiens'] = ressource.nombre_entretiens
                except Exception:
                    pass
                
            except Formation.DoesNotExist:
                pass
                
        # Pré-remplir les dates selon la période
        periode = self.request.GET.get('periode')
        now = timezone.now().date()
        
        if periode == Rapport.HEBDOMADAIRE:
            # Semaine précédente (lundi au dimanche)
            start_of_week = now - timedelta(days=now.weekday() + 7)
            end_of_week = start_of_week + timedelta(days=6)
            form.initial['date_debut'] = start_of_week
            form.initial['date_fin'] = end_of_week
            form.initial['periode'] = Rapport.HEBDOMADAIRE
            
        elif periode == Rapport.MENSUEL:
            # Mois précédent
            last_month = now.replace(day=1) - timedelta(days=1)
            start_of_month = last_month.replace(day=1)
            form.initial['date_debut'] = start_of_month
            form.initial['date_fin'] = last_month
            form.initial['periode'] = Rapport.MENSUEL
            
        elif periode == Rapport.ANNUEL:
            # Année précédente
            last_year = now.year - 1
            form.initial['date_debut'] = datetime(last_year, 1, 1).date()
            form.initial['date_fin'] = datetime(last_year, 12, 31).date()
            form.initial['periode'] = Rapport.ANNUEL
        
        return form
    
    def get_success_url(self):
        # Rediriger vers la formation si demandé
        if self.object.formation and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': self.object.formation.id})
        return reverse('rapport-detail', kwargs={'pk': self.object.pk})


class RapportUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Mise à jour d'un rapport"""
    model = Rapport
    permission_required = 'rap_app.change_rapport'
    fields = [
        'formation', 'periode', 'date_debut', 'date_fin', 
        'total_inscrits', 'inscrits_crif', 'inscrits_mp', 'total_places',
        'nombre_evenements', 'nombre_candidats', 'nombre_entretiens'
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le rapport {self.object.get_periode_display()} ({self.object.date_debut} - {self.object.date_fin})"
        return context
    
    def get_success_url(self):
        # Rediriger vers la formation si demandé
        if self.object.formation and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': self.object.formation.id})
        return reverse('rapport-detail', kwargs={'pk': self.object.pk})


class RapportDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Suppression d'un rapport"""
    model = Rapport
    permission_required = 'rap_app.delete_rapport'
    
    def get_success_url(self):
        # Rediriger vers la formation si le rapport est lié à une formation
        formation_id = self.object.formation.id if self.object.formation else None
        if formation_id and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': formation_id})
        return reverse('rapport-list')


class RapportGenerationView(LoginRequiredMixin, TemplateView):
    """Vue pour générer des rapports automatiquement"""
    template_name = 'rap_app/rapport_generation.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Options pour le formulaire
        context['formations'] = Formation.objects.formations_actives().order_by('nom')
        context['periodes'] = Rapport.PERIODE_CHOICES
        
        # Type de génération (par période ou par formation)
        context['type_generation'] = self.request.GET.get('type', 'periode')
        
        # Pour la génération par période
        context['periode_selectionnee'] = self.request.GET.get('periode', Rapport.HEBDOMADAIRE)
        
        # Pour la génération par formation
        formation_id = self.request.GET.get('formation')
        if formation_id:
            try:
                context['formation_selectionnee'] = Formation.objects.get(pk=formation_id)
            except Formation.DoesNotExist:
                pass
        
        return context
    
    def post(self, request, *args, **kwargs):
        from django.contrib import messages
        
        # Récupérer les paramètres du formulaire
        type_generation = request.POST.get('type_generation')
        periode = request.POST.get('periode')
        formation_id = request.POST.get('formation')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        
        rapports_crees = 0
        
        try:
            # Vérifier que les dates sont valides
            if date_debut and date_fin:
                date_debut = parse_date(date_debut)
                date_fin = parse_date(date_fin)
                
                if date_debut > date_fin:
                    messages.error(request, "La date de début doit être antérieure à la date de fin.")
                    return self.get(request, *args, **kwargs)
            
            # Génération par période (pour toutes les formations)
            if type_generation == 'periode' and periode:
                formations = Formation.objects.formations_actives()
                
                for formation in formations:
                    # Vérifier si un rapport similaire existe déjà
                    rapport_existant = Rapport.objects.filter(
                        formation=formation,
                        periode=periode,
                        date_debut=date_debut,
                        date_fin=date_fin
                    ).exists()
                    
                    if not rapport_existant:
                        # Calculer les valeurs à partir des données existantes
                        nombre_evenements = Evenement.objects.filter(
                            formation=formation,
                            event_date__gte=date_debut,
                            event_date__lte=date_fin
                        ).count()
                        
                        # Créer le rapport
                        Rapport.objects.create(
                            formation=formation,
                            periode=periode,
                            date_debut=date_debut,
                            date_fin=date_fin,
                            total_inscrits=formation.inscrits_total,
                            inscrits_crif=formation.inscrits_crif,
                            inscrits_mp=formation.inscrits_mp,
                            total_places=formation.total_places,
                            nombre_evenements=nombre_evenements,
                            nombre_candidats=getattr(formation.ressource, 'nombre_candidats', 0) or 0,
                            nombre_entretiens=getattr(formation.ressource, 'nombre_entretiens', 0) or 0
                        )
                        rapports_crees += 1
            
            # Génération pour une formation spécifique
            elif type_generation == 'formation' and formation_id:
                formation = get_object_or_404(Formation, pk=formation_id)
                
                # Vérifier si un rapport similaire existe déjà
                rapport_existant = Rapport.objects.filter(
                    formation=formation,
                    periode=periode,
                    date_debut=date_debut,
                    date_fin=date_fin
                ).exists()
                
                if not rapport_existant:
                    # Calculer les valeurs à partir des données existantes
                    nombre_evenements = Evenement.objects.filter(
                        formation=formation,
                        event_date__gte=date_debut,
                        event_date__lte=date_fin
                    ).count()
                    
                    # Créer le rapport
                    Rapport.objects.create(
                        formation=formation,
                        periode=periode,
                        date_debut=date_debut,
                        date_fin=date_fin,
                        total_inscrits=formation.inscrits_total,
                        inscrits_crif=formation.inscrits_crif,
                        inscrits_mp=formation.inscrits_mp,
                        total_places=formation.total_places,
                        nombre_evenements=nombre_evenements,
                        nombre_candidats=getattr(formation.ressource, 'nombre_candidats', 0) or 0,
                        nombre_entretiens=getattr(formation.ressource, 'nombre_entretiens', 0) or 0
                    )
                    rapports_crees += 1
            
            if rapports_crees > 0:
                messages.success(request, f"{rapports_crees} rapport(s) généré(s) avec succès.")
            else:
                messages.info(request, "Aucun nouveau rapport n'a été généré. Peut-être qu'ils existent déjà pour cette période.")
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la génération des rapports : {str(e)}")
        
        return self.get(request, *args, **kwargs)


class RapportExportView(LoginRequiredMixin, View):
    """Vue pour exporter les données des rapports"""
    
    def get(self, request, *args, **kwargs):
        from django.contrib import messages
        
        format_export = request.GET.get('format', 'csv')
        
        # Récupérer les filtres
        periode = request.GET.get('periode')
        formation_id = request.GET.get('formation')
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')
        
        # Construire la requête en fonction des filtres
        queryset = Rapport.objects.select_related('formation', 'formation__centre', 'formation__type_offre')
        
        if periode:
            queryset = queryset.filter(periode=periode)
        
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
        
        if date_debut:
            queryset = queryset.filter(date_fin__gte=date_debut)
            
        if date_fin:
            queryset = queryset.filter(date_debut__lte=date_fin)
        
        # Ordonner les résultats
        queryset = queryset.order_by('-date_fin')
        
        # Export CSV
        if format_export == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="rapports.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'ID', 'Formation', 'Centre', 'Type d\'offre', 'Période', 
                'Date début', 'Date fin', 'Inscrits CRIF', 'Inscrits MP', 
                'Total inscrits', 'Total places', 'Taux remplissage (%)',
                'Nombre événements', 'Nombre candidats', 'Nombre entretiens',
                'Taux transformation (%)', 'Date création'
            ])
            
            for rapport in queryset:
                writer.writerow([
                    rapport.id,
                    rapport.formation.nom if rapport.formation else 'Global',
                    rapport.formation.centre.nom if rapport.formation and rapport.formation.centre else '-',
                    rapport.formation.type_offre.nom if rapport.formation and rapport.formation.type_offre else '-',
                    rapport.get_periode_display(),
                    rapport.date_debut,
                    rapport.date_fin,
                    rapport.inscrits_crif,
                    rapport.inscrits_mp,
                    rapport.total_inscrits,
                    rapport.total_places,
                    "{:.2f}".format(rapport.taux_remplissage),
                    rapport.nombre_evenements,
                    rapport.nombre_candidats,
                    rapport.nombre_entretiens,
                    "{:.2f}".format(rapport.taux_transformation),
                    rapport.created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
            
            return response
            
        # Format non pris en charge
        else:
            messages.error(request, f"Format d'export '{format_export}' non pris en charge.")
            return reverse('rapport-list')

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.urls import reverse_lazy
from django.db.models import Count
from django.contrib.auth.mixins import PermissionRequiredMixin

from ..models import Statut, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class StatutListView(BaseListView):
    """Liste des statuts de formation"""
    model = Statut
    context_object_name = 'statuts'
    
    def get_queryset(self):
        queryset = super().get_queryset().annotate(
            nb_formations=Count('formations')
        )
        
        # Recherche par nom
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(nom__icontains=q)
            
        return queryset.order_by('nom')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filtres appliqués
        context['filters'] = {
            'q': self.request.GET.get('q', ''),
        }
        
        return context


class StatutDetailView(BaseDetailView):
    """Détail d'un statut de formation"""
    model = Statut
    context_object_name = 'statut'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les formations associées
        context['formations'] = Formation.objects.filter(
            statut=self.object
        ).select_related('centre', 'type_offre').order_by('-start_date')
        
        return context


class StatutCreateView(PermissionRequiredMixin, BaseCreateView):
    """Création d'un statut de formation"""
    model = Statut
    permission_required = 'rap_app.add_statut'
    fields = ['nom', 'couleur', 'description_autre']
    success_url = reverse_lazy('statut-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un statut de formation"
        return context


class StatutUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Mise à jour d'un statut de formation"""
    model = Statut
    permission_required = 'rap_app.change_statut'
    fields = ['nom', 'couleur', 'description_autre']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le statut : {self.object.get_nom_display()}"
        return context


class StatutDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Suppression d'un statut de formation"""
    model = Statut
    permission_required = 'rap_app.delete_statut'
    success_url = reverse_lazy('statut-list')


----------------------------------------------------------------------
----------------------------------------------------------------------
from django.urls import reverse_lazy
from django.db.models import Count
from django.contrib.auth.mixins import PermissionRequiredMixin

from ..models import TypeOffre, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class TypeOffreListView(BaseListView):
    """Liste des types d'offres de formation"""
    model = TypeOffre
    context_object_name = 'types_offre'
    
    def get_queryset(self):
        queryset = super().get_queryset().annotate(
            nb_formations=Count('formations')
        )
        
        # Recherche par nom
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(nom__icontains=q) | queryset.filter(autre__icontains=q)
            
        return queryset.order_by('nom')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filtres appliqués
        context['filters'] = {
            'q': self.request.GET.get('q', ''),
        }
        
        return context


class TypeOffreDetailView(BaseDetailView):
    """Détail d'un type d'offre de formation"""
    model = TypeOffre
    context_object_name = 'type_offre'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les formations associées
        context['formations'] = Formation.objects.filter(
            type_offre=self.object
        ).select_related('centre', 'statut').order_by('-start_date')
        
        return context


class TypeOffreCreateView(PermissionRequiredMixin, BaseCreateView):
    """Création d'un type d'offre de formation"""
    model = TypeOffre
    permission_required = 'rap_app.add_typeoffre'
    fields = ['nom', 'autre']
    success_url = reverse_lazy('type-offre-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un type d'offre de formation"
        return context


class TypeOffreUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Mise à jour d'un type d'offre de formation"""
    model = TypeOffre
    permission_required = 'rap_app.change_typeoffre'
    fields = ['nom', 'autre']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le type d'offre : {self.object.get_nom_display()}"
        return context


class TypeOffreDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Suppression d'un type d'offre de formation"""
    model = TypeOffre
    permission_required = 'rap_app.delete_typeoffre'
    success_url = reverse_lazy('type-offre-list')

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q
from django.http import JsonResponse, HttpResponse
import csv

from ..models import HistoriqueFormation, Formation
from .base_views import BaseListView, BaseDetailView


class HistoriqueFormationListView(BaseListView):
    """Liste des historiques de formation"""
    model = HistoriqueFormation
    context_object_name = 'historiques'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('formation', 'utilisateur')
        
        # Filtrage par formation
        formation_id = self.request.GET.get('formation')
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
        
        # Filtrage par utilisateur
        utilisateur_id = self.request.GET.get('utilisateur')
        if utilisateur_id:
            queryset = queryset.filter(utilisateur_id=utilisateur_id)
        
        # Filtrage par action
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action__icontains=action)
        
        # Filtrage par date
        date_debut = self.request.GET.get('date_debut')
        if date_debut:
            queryset = queryset.filter(created_at__date__gte=date_debut)
            
        date_fin = self.request.GET.get('date_fin')
        if date_fin:
            queryset = queryset.filter(created_at__date__lte=date_fin)
        
        # Recherche globale
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(action__icontains=q) |
                Q(formation__nom__icontains=q) |
                Q(utilisateur__username__icontains=q) |
                Q(utilisateur__first_name__icontains=q) |
                Q(utilisateur__last_name__icontains=q)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Liste des formations pour le filtre
        context['formations'] = Formation.objects.all().order_by('nom')
        
        # Filtres appliqués
        context['filters'] = {
            'formation': self.request.GET.get('formation', ''),
            'utilisateur': self.request.GET.get('utilisateur', ''),
            'action': self.request.GET.get('action', ''),
            'date_debut': self.request.GET.get('date_debut', ''),
            'date_fin': self.request.GET.get('date_fin', ''),
            'q': self.request.GET.get('q', ''),
        }
        
        return context


class HistoriqueFormationDetailView(BaseDetailView):
    """Détail d'un historique de formation"""
    model = HistoriqueFormation
    context_object_name = 'historique'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer d'autres historiques de la même formation
        if self.object.formation:
            context['autres_historiques'] = self.object.formation.historique_formations.exclude(
                id=self.object.id
            ).order_by('-created_at')[:5]
        
        return context


class HistoriqueFormationExportView(LoginRequiredMixin, TemplateView):
    """Vue pour exporter les historiques de formation"""
    
    def get(self, request, *args, **kwargs):
        # Récupérer les paramètres de filtrage
        formation_id = request.GET.get('formation')
        utilisateur_id = request.GET.get('utilisateur')
        action = request.GET.get('action')
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')
        
        # Construire la requête
        queryset = HistoriqueFormation.objects.select_related('formation', 'utilisateur')
        
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
        
        if utilisateur_id:
            queryset = queryset.filter(utilisateur_id=utilisateur_id)
        
        if action:
            queryset = queryset.filter(action__icontains=action)
        
        if date_debut:
            queryset = queryset.filter(created_at__date__gte=date_debut)
            
        if date_fin:
            queryset = queryset.filter(created_at__date__lte=date_fin)
        
        # Export en CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="historique_formations.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Formation', 'Utilisateur', 'Action', 
            'Ancien statut', 'Nouveau statut', 
            'Inscrits CRIF', 'Inscrits MP', 'Total inscrits', 'Total places', 
            'Taux remplissage', 'Date'
        ])
        
        for historique in queryset:
            writer.writerow([
                historique.id,
                historique.formation.nom if historique.formation else 'N/A',
                str(historique.utilisateur) if historique.utilisateur else 'N/A',
                historique.action,
                historique.ancien_statut or 'N/A',
                historique.nouveau_statut or 'N/A',
                historique.inscrits_crif or 0,
                historique.inscrits_mp or 0,
                historique.inscrits_total or 0,
                historique.total_places or 0,
                "{:.2f}%".format(historique.taux_remplissage) if historique.taux_remplissage else '0.00%',
                historique.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.urls import reverse_lazy
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect

from ..models import Parametre
from .base_views import BaseListView, BaseUpdateView


class ParametreListView(PermissionRequiredMixin, BaseListView):
    """Liste des paramètres de l'application"""
    model = Parametre
    context_object_name = 'parametres'
    permission_required = 'rap_app.view_parametre'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Recherche par clé ou valeur
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(cle__icontains=q) | queryset.filter(valeur__icontains=q)
            
        return queryset.order_by('cle')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filtres appliqués
        context['filters'] = {
            'q': self.request.GET.get('q', ''),
        }
        
        return context


class ParametreUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Mise à jour d'un paramètre"""
    model = Parametre
    fields = ['valeur', 'description']
    permission_required = 'rap_app.change_parametre'
    success_url = reverse_lazy('parametre-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le paramètre : {self.object.cle}"
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f"Paramètre '{self.object.cle}' mis à jour avec succès.")
        return super().form_valid(form)


class ParametreBatchCreateView(PermissionRequiredMixin, BaseListView):
    """Vue pour créer des paramètres par lot"""
    model = Parametre
    template_name = 'rap_app/parametre_batch_create.html'
    permission_required = 'rap_app.add_parametre'
    
    def post(self, request, *args, **kwargs):
        # Récupérer les paramètres prédéfinis
        parametres_predefinies = {
            'APP_NAME': 'RAP - Recrutement et Accès à la Profession',
            'EMAIL_CONTACT': 'contact@example.com',
            'LIMITE_PAGINATION': '20',
            'ALERTE_TAUX_REMPLISSAGE_FAIBLE': '50',
            'ALERTE_TAUX_REMPLISSAGE_MOYEN': '75',
            'ALERTE_TAUX_REMPLISSAGE_ELEVE': '90',
            'PERIODE_RAPPORT_PAR_DEFAUT': 'Mensuel',
            'LIMITE_EVENEMENTS_PAR_PAGE': '10',
            'LIMITE_COMMENTAIRES_PAR_PAGE': '10',
            'DATE_FORMAT': 'Y-m-d',
            'DATETIME_FORMAT': 'Y-m-d H:i:s',
        }
        
        # Paramètres créés
        crees = 0
        
        # Créer les paramètres manquants
        for cle, valeur in parametres_predefinies.items():
            if not Parametre.objects.filter(cle=cle).exists():
                Parametre.objects.create(
                    cle=cle,
                    valeur=valeur,
                    description=f"Paramètre {cle} créé automatiquement"
                )
                crees += 1
        
        if crees > 0:
            messages.success(request, f"{crees} paramètre(s) ajouté(s) avec succès.")
        else:
            messages.info(request, "Tous les paramètres prédéfinis existent déjà.")
            
        return redirect('parametre-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter des paramètres prédéfinis"
        return context

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q, F, Avg
from django.http import HttpResponse
import csv

from ..models import Recherche, Utilisateur
from .base_views import BaseListView


class RechercheListView(PermissionRequiredMixin, BaseListView):
    """Liste des recherches effectuées par les utilisateurs"""
    model = Recherche
    context_object_name = 'recherches'
    permission_required = 'rap_app.view_recherche'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('utilisateur', 'filtre_centre', 'filtre_type_offre', 'filtre_statut')
        
        # Filtrage par utilisateur
        utilisateur_id = self.request.GET.get('utilisateur')
        if utilisateur_id:
            queryset = queryset.filter(utilisateur_id=utilisateur_id)
        
        # Filtrage par terme de recherche
        terme = self.request.GET.get('terme')
        if terme:
            queryset = queryset.filter(terme_recherche__icontains=terme)
        
        # Filtrage par résultats trouvés
        resultats = self.request.GET.get('resultats')
        if resultats == 'avec':
            queryset = queryset.filter(nombre_resultats__gt=0)
        elif resultats == 'sans':
            queryset = queryset.filter(nombre_resultats=0)
        
        # Filtrage par date
        date_debut = self.request.GET.get('date_debut')
        if date_debut:
            queryset = queryset.filter(created_at__date__gte=date_debut)
            
        date_fin = self.request.GET.get('date_fin')
        if date_fin:
            queryset = queryset.filter(created_at__date__lte=date_fin)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Liste des utilisateurs pour le filtre
        context['utilisateurs'] = Utilisateur.objects.filter(
            recherches__isnull=False
        ).distinct().order_by('username')
        
        # Statistiques de recherche
        from django.db.models import Count
        
        context['stats'] = {
            'total_recherches': Recherche.objects.count(),
            'recherches_avec_resultats': Recherche.objects.filter(nombre_resultats__gt=0).count(),
            'recherches_sans_resultats': Recherche.objects.filter(nombre_resultats=0).count(),
            'termes_populaires': Recherche.objects.exclude(
                terme_recherche=''
            ).exclude(
                terme_recherche__isnull=True
            ).values('terme_recherche').annotate(
                total=Count('id')
            ).order_by('-total')[:10],
            'temps_moyen': Recherche.objects.filter(
                temps_execution__isnull=False
            ).aggregate(
                temps_moyen=Avg('temps_execution')
            ).get('temps_moyen', 0),
        }
        
        # Filtres appliqués
        context['filters'] = {
            'utilisateur': self.request.GET.get('utilisateur', ''),
            'terme': self.request.GET.get('terme', ''),
            'resultats': self.request.GET.get('resultats', ''),
            'date_debut': self.request.GET.get('date_debut', ''),
            'date_fin': self.request.GET.get('date_fin', ''),
        }
        
        return context


class RechercheExportView(PermissionRequiredMixin, TemplateView):
    """Vue pour exporter les données des recherches"""
    permission_required = 'rap_app.view_recherche'
    
    def get(self, request, *args, **kwargs):
        # Récupérer les paramètres de filtrage
        utilisateur_id = request.GET.get('utilisateur')
        terme = request.GET.get('terme')
        resultats = request.GET.get('resultats')
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')
        
        # Construire la requête
        queryset = Recherche.objects.select_related('utilisateur', 'filtre_centre', 'filtre_type_offre', 'filtre_statut')
        
        if utilisateur_id:
            queryset = queryset.filter(utilisateur_id=utilisateur_id)
        
        if terme:
            queryset = queryset.filter(terme_recherche__icontains=terme)
        
        if resultats == 'avec':
            queryset = queryset.filter(nombre_resultats__gt=0)
        elif resultats == 'sans':
            queryset = queryset.filter(nombre_resultats=0)
        
        if date_debut:
            queryset = queryset.filter(created_at__date__gte=date_debut)
            
        if date_fin:
            queryset = queryset.filter(created_at__date__lte=date_fin)
        
        # Export en CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="recherches.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Utilisateur', 'Terme de recherche', 
            'Centre filtré', 'Type d\'offre filtré', 'Statut filtré',
            'Date début', 'Date fin', 'Nombre de résultats',
            'Temps d\'exécution (ms)', 'Adresse IP', 'Date de recherche'
        ])
        
        for recherche in queryset:
            writer.writerow([
                recherche.id,
                str(recherche.utilisateur) if recherche.utilisateur else 'Anonyme',
                recherche.terme_recherche or '',
                recherche.filtre_centre.nom if recherche.filtre_centre else '',
                recherche.filtre_type_offre.nom if recherche.filtre_type_offre else '',
                recherche.filtre_statut.nom if recherche.filtre_statut else '',
                recherche.date_debut or '',
                recherche.date_fin or '',
                recherche.nombre_resultats,
                "{:.2f}".format(recherche.temps_execution) if recherche.temps_execution else '',
                recherche.adresse_ip or '',
                recherche.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response


class RechercheStatsView(PermissionRequiredMixin, TemplateView):
    """Vue pour afficher des statistiques sur les recherches"""
    template_name = 'rap_app/recherche_stats.html'
    permission_required = 'rap_app.view_recherche'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques générales
        context['stats_generales'] = {
            'total_recherches': Recherche.objects.count(),
            'recherches_avec_resultats': Recherche.objects.filter(nombre_resultats__gt=0).count(),
            'recherches_sans_resultats': Recherche.objects.filter(nombre_resultats=0).count(),
            'temps_moyen': Recherche.objects.filter(
                temps_execution__isnull=False
            ).aggregate(
                temps_moyen=Avg('temps_execution')
            ).get('temps_moyen', 0),
        }
        
        # Termes les plus recherchés
        from django.db.models import Count
        
        context['termes_populaires'] = Recherche.objects.exclude(
            terme_recherche=''
        ).exclude(
            terme_recherche__isnull=True
        ).values('terme_recherche').annotate(
            total=Count('id')
        ).order_by('-total')[:20]
        
        # Utilisateurs les plus actifs
        context['utilisateurs_actifs'] = Utilisateur.objects.annotate(
            nb_recherches=Count('recherches')
        ).filter(
            nb_recherches__gt=0
        ).order_by('-nb_recherches')[:10]
        
        # Répartition par mois
        from django.db.models.functions import TruncMonth
        
        context['recherches_par_mois'] = Recherche.objects.annotate(
            mois=TruncMonth('created_at')
        ).values('mois').annotate(
            total=Count('id'),
            avec_resultats=Count('id', filter=Q(nombre_resultats__gt=0)),
            sans_resultats=Count('id', filter=Q(nombre_resultats=0))
        ).order_by('mois')
        
        return context

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q

from ..models import Ressource, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class RessourceListView(BaseListView):
    """Liste des ressources"""
    model = Ressource
    context_object_name = 'ressources'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('formation', 'formation__centre', 'formation__type_offre')
        
        # Filtrage par formation
        formation_id = self.request.GET.get('formation')
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
        
        # Filtrage par centre
        centre_id = self.request.GET.get('centre')
        if centre_id:
            queryset = queryset.filter(formation__centre_id=centre_id)
        
        # Filtrage par type d'offre
        type_offre_id = self.request.GET.get('type_offre')
        if type_offre_id:
            queryset = queryset.filter(formation__type_offre_id=type_offre_id)
        
        # Recherche globale
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(formation__nom__icontains=q) |
                Q(formation__centre__nom__icontains=q)
            )
        
        return queryset.order_by('-formation__start_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Liste des formations pour le filtre
        context['formations'] = Formation.objects.formations_actives().order_by('nom')
        
        # Filtres appliqués
        context['filters'] = {
            'formation': self.request.GET.get('formation', ''),
            'centre': self.request.GET.get('centre', ''),
            'type_offre': self.request.GET.get('type_offre', ''),
            'q': self.request.GET.get('q', ''),
        }
        
        return context


class RessourceDetailView(BaseDetailView):
    """Détail d'une ressource"""
    model = Ressource
    context_object_name = 'ressource'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les événements associés à la formation
        if self.object.formation:
            context['evenements'] = self.object.formation.evenements.all().order_by('-event_date')
        
        return context


class RessourceCreateView(PermissionRequiredMixin, BaseCreateView):
    """Création d'une ressource"""
    model = Ressource
    permission_required = 'rap_app.add_ressource'
    fields = ['formation', 'nombre_candidats', 'nombre_entretiens']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter une ressource"
        
        # Pré-sélectionner la formation si fournie dans l'URL
        formation_id = self.request.GET.get('formation')
        if formation_id:
            try:
                formation = Formation.objects.get(pk=formation_id)
                context['formation_preselected'] = formation
            except Formation.DoesNotExist:
                pass
                
        return context
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Liste des formations sans ressource
        form.fields['formation'].queryset = Formation.objects.filter(
            ressource__isnull=True
        ).order_by('nom')
        
        # Pré-sélectionner la formation si fournie dans l'URL
        formation_id = self.request.GET.get('formation')
        if formation_id:
            try:
                formation = Formation.objects.get(pk=formation_id)
                form.initial['formation'] = formation
            except Formation.DoesNotExist:
                pass
        
        return form
    
    def get_success_url(self):
        # Si redirigé depuis la vue détaillée d'une formation, y retourner
        if self.object.formation and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': self.object.formation.id})
        return reverse('ressource-detail', kwargs={'pk': self.object.pk})


class RessourceUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Mise à jour d'une ressource"""
    model = Ressource
    permission_required = 'rap_app.change_ressource'
    fields = ['formation', 'nombre_candidats', 'nombre_entretiens']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Modifier la ressource"
        return context
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Liste des formations (la formation actuelle + formations sans ressource)
        formations_sans_ressource = Formation.objects.filter(ressource__isnull=True)
        
        if self.object.formation:
            form.fields['formation'].queryset = formations_sans_ressource | Formation.objects.filter(pk=self.object.formation.pk)
        else:
            form.fields['formation'].queryset = formations_sans_ressource
        
        return form
    
    def get_success_url(self):
        # Si redirigé depuis la vue détaillée d'une formation, y retourner
        if self.object.formation and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': self.object.formation.id})
        return reverse('ressource-detail', kwargs={'pk': self.object.pk})


class RessourceDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Suppression d'une ressource"""
    model = Ressource
    permission_required = 'rap_app.delete_ressource'
    
    def get_success_url(self):
        # Rediriger vers la formation si la ressource est liée à une formation
        formation_id = self.object.formation.id if self.object.formation else None
        if formation_id and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': formation_id})
        return reverse('ressource-list')

----------------------------------------------------------------------
----------------------------------------------------------------------
lancer les tests des views
python3 manage.py test rap_app.tests.test_views


----------------------------------------------------------------------
----------------------------------------------------------------------


----------------------------------------------------------------------
----------------------------------------------------------------------

