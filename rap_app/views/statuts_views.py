from django.urls import reverse_lazy
from django.db.models import Count
from django.contrib.auth.mixins import PermissionRequiredMixin
import random

from ..models import Statut, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


def generate_random_color():
    """
    Génère une couleur hexadécimale aléatoire si l'utilisateur ne la définit pas.
    Exemple de sortie : "#A3B2C1"
    """
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


class StatutListView(BaseListView):
    """🔵 Vue listant tous les statuts de formation, avec recherche et nombre de formations associées."""
    model = Statut
    context_object_name = 'statuts'
    template_name = 'statuts/statut_list.html'

    def get_queryset(self):
        """
        Récupère tous les statuts avec un nombre de formations associées.
        Permet aussi la recherche par nom.
        """
        queryset = super().get_queryset().annotate(nb_formations=Count('formations'))

        # 🔍 Recherche textuelle par nom (GET ?q=...)
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(nom__icontains=q)

        return queryset.order_by('nom')

    def get_context_data(self, **kwargs):
        """
        Ajoute les filtres actuellement appliqués au contexte (utile pour les formulaires de recherche).
        """
        context = super().get_context_data(**kwargs)
        context['filters'] = {
            'q': self.request.GET.get('q', ''),
        }
        return context


class StatutDetailView(BaseDetailView):
    """🔵 Vue affichant le détail d'un statut et les formations liées à ce statut."""
    model = Statut
    context_object_name = 'statut'
    template_name = 'statuts/statut_detail.html'

    def get_context_data(self, **kwargs):
        """
        Ajoute la liste des formations qui utilisent ce statut.
        """
        context = super().get_context_data(**kwargs)
        context['formations'] = Formation.objects.filter(
            statut=self.object
        ).select_related('centre', 'type_offre').order_by('-start_date')
        return context


class StatutCreateView(PermissionRequiredMixin, BaseCreateView):
    """🟢 Vue de création d'un nouveau statut de formation."""
    model = Statut
    permission_required = 'rap_app.add_statut'
    fields = ['nom', 'couleur', 'description_autre']
    success_url = reverse_lazy('statut-list')
    template_name = 'statuts/statut_form.html'

    def form_valid(self, form):
        """
        Si aucune couleur n'est fournie, une couleur aléatoire est automatiquement générée.
        """
        statut = form.save(commit=False)
        if not statut.couleur:
            statut.couleur = generate_random_color()
        statut.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """
        Ajoute un titre dynamique au contexte (utilisé dans le template pour les titres).
        """
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un statut de formation"
        return context


class StatutUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """📝 Vue de modification d'un statut existant."""
    model = Statut
    permission_required = 'rap_app.change_statut'
    fields = ['nom', 'couleur', 'description_autre']
    template_name = 'statuts/statut_form.html'

    def form_valid(self, form):
        """
        Assure qu'une couleur est présente ; sinon en génère une automatiquement.
        """
        statut = form.save(commit=False)
        if not statut.couleur:
            statut.couleur = generate_random_color()
        statut.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """
        Ajoute un titre personnalisé à afficher dans le template.
        """
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le statut : {self.object.get_nom_display()}"
        return context


class StatutDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """❌ Vue de suppression d'un statut de formation."""
    model = Statut
    permission_required = 'rap_app.delete_statut'
    success_url = reverse_lazy('statut-list')
    template_name = 'statuts/statut_confirm_delete.html'
