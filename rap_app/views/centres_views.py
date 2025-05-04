import logging
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.db.models import Count, Sum, F, Q, Value, CharField
from django.db.models.functions import Concat
from django.utils import timezone
from django.contrib import messages

from ..models import Centre, Formation, TypeOffre, Statut
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView

# Configuration du logger pour ce module
logger = logging.getLogger(__name__)

class CentreListView(BaseListView):
    """
    Vue listant tous les centres de formation avec des statistiques.
    
    Fonctionnalités:
    - Affichage paginé des centres
    - Statistiques agrégées pour chaque centre (nombre de formations, formations actives, inscrits)
    - Filtrage par nom et code postal
    - Statistiques globales dans le contexte
    """
    model = Centre
    context_object_name = 'centres'
    template_name = 'centres/centre_list.html'
    # Ajout d'un ordre explicite pour éviter les avertissements de pagination
    ordering = ['nom']
        
    def get_queryset(self):
        """
        Récupère la liste des centres de formation en annotant des statistiques :
        - Nombre total de formations liées à chaque centre.
        - Nombre de formations actives (date de fin >= aujourd'hui OU sans date de fin).
        - Nombre total d'inscrits (CRIF + MP).
        """
        today = timezone.now().date()
        
        # Construction du queryset avec annotations
        queryset = super().get_queryset().annotate(
            # Nombre total de formations
            nb_formations=Count('formations'),
            
            # Nombre de formations actives
            nb_formations_actives=Count(
                'formations',
                filter=Q(formations__end_date__gte=today) | Q(formations__end_date__isnull=True)
            ),
            
            # Nombre total d'inscrits
            nb_inscrits=Sum(
                F('formations__inscrits_crif') + F('formations__inscrits_mp'),
                default=0
            ),
            
            # Pour le tri et l'affichage, concaténer le nom et le code postal
            nom_complet=Concat(
                'nom', 
                Value(' ('), 
                'code_postal', 
                Value(')'),
                output_field=CharField()
            )
        )
        
        # Récupération des filtres depuis les paramètres GET
        q = self.request.GET.get('q', '').strip()
        cp = self.request.GET.get('code_postal', '').strip()
        
        # Application des filtres si présents
        if q:
            logger.debug(f"Filtrage des centres par nom contenant: '{q}'")
            queryset = queryset.filter(nom__icontains=q)
            
        if cp:
            logger.debug(f"Filtrage des centres par code postal commençant par: '{cp}'")
            queryset = queryset.filter(code_postal__startswith=cp)
        
        # Log du résultat de la requête
        logger.debug(f"Requête centres: {queryset.count()} résultats")
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Ajoute des statistiques générales et les filtres appliqués au contexte de la page.
        """
        context = super().get_context_data(**kwargs)
        
        # Statistiques globales
        total_centres = Centre.objects.count()
        total_formations = Formation.objects.count()
        
        # Calcul du nombre total d'inscrits
        total_inscrits = Formation.objects.aggregate(
            total=Sum(F('inscrits_crif') + F('inscrits_mp'), default=0)
        )['total'] or 0
        
        # Statistiques des centres avec le plus de formations
        top_centres = Centre.objects.annotate(
            nb_formations=Count('formations')
        ).order_by('-nb_formations')[:5]
        
        # Ajout au contexte
        context.update({
            'total_centres': total_centres,
            'total_formations': total_formations,
            'total_inscrits': total_inscrits,
            'top_centres': top_centres,
            'filters': {
                'q': self.request.GET.get('q', ''),
                'code_postal': self.request.GET.get('code_postal', ''),
            }
        })
        
        logger.debug(f"Contexte préparé pour la liste des centres: {total_centres} centres, {total_formations} formations")
        
        return context


class CentreDetailView(BaseDetailView):
    """
    Vue affichant les détails d'un centre de formation avec:
    - Informations générales sur le centre
    - Liste des formations associées avec filtres
    - Statistiques sur les formations du centre
    """
    model = Centre
    context_object_name = 'centre'
    template_name = 'centres/centre_detail.html'

    def get_context_data(self, **kwargs):
        """
        Ajoute au contexte les formations associées au centre
        avec possibilité de filtrage par type d'offre et statut.
        """
        context = super().get_context_data(**kwargs)
        centre = self.object
        
        logger.info(f"Accès aux détails du centre #{centre.pk}: {centre.nom}")
        
        # Récupération des formations avec optimisation des requêtes (select_related)
        formations = centre.formations.select_related(
            'type_offre', 'statut'
        ).order_by('-start_date')
        
        # Récupération des filtres depuis les paramètres GET
        type_offre_id = self.request.GET.get('type_offre')
        statut_id = self.request.GET.get('statut')
        periode = self.request.GET.get('periode')
        
        # Filtres appliqués
        filters_applied = {}
        
        # Filtrage par type d'offre
        if type_offre_id:
            try:
                type_offre = TypeOffre.objects.get(pk=type_offre_id)
                formations = formations.filter(type_offre=type_offre)
                filters_applied['type_offre'] = type_offre.nom
                logger.debug(f"Filtre par type d'offre appliqué: {type_offre.nom}")
            except (TypeOffre.DoesNotExist, ValueError):
                logger.warning(f"Type d'offre invalide: {type_offre_id}")

        # Filtrage par statut
        if statut_id:
            try:
                statut = Statut.objects.get(pk=statut_id)
                formations = formations.filter(statut=statut)
                filters_applied['statut'] = statut.nom
                logger.debug(f"Filtre par statut appliqué: {statut.nom}")
            except (Statut.DoesNotExist, ValueError):
                logger.warning(f"Statut invalide: {statut_id}")
                
        # Filtrage par période
        today = timezone.now().date()
        if periode == 'actives':
            formations = formations.filter(
                Q(start_date__lte=today) & 
                (Q(end_date__gte=today) | Q(end_date__isnull=True))
            )
            filters_applied['periode'] = 'Formations actives'
            logger.debug(f"Filtre par période appliqué: formations actives")
        elif periode == 'a_venir':
            formations = formations.filter(start_date__gt=today)
            filters_applied['periode'] = 'Formations à venir'
            logger.debug(f"Filtre par période appliqué: formations à venir")
        elif periode == 'terminees':
            formations = formations.filter(end_date__lt=today)
            filters_applied['periode'] = 'Formations terminées'
            logger.debug(f"Filtre par période appliqué: formations terminées")

        # Comptage des formations filtrées
        nb_formations = formations.count()
        logger.debug(f"Centre #{centre.pk}: {nb_formations} formations après filtrage")

        # Extraction des listes de filtres disponibles
        all_type_offres = TypeOffre.objects.all()
        all_statuts = Statut.objects.all()

        # Calcul de statistiques
        stats = formations.aggregate(
            total_inscrits=Sum(F('inscrits_crif') + F('inscrits_mp'), default=0),
            total_places=Sum(F('prevus_crif') + F('prevus_mp'), default=0),
        )
        
        # Calcul du taux de remplissage
        total_places = stats['total_places'] or 0
        total_inscrits = stats['total_inscrits'] or 0
        taux_remplissage = (total_inscrits / total_places * 100) if total_places > 0 else 0

        # Ajout au contexte
        context.update({
            'formations': formations,
            'type_offres': all_type_offres,
            'statuts': all_statuts,
            'nb_formations': nb_formations,
            'total_inscrits': total_inscrits,
            'total_places': total_places,
            'taux_remplissage': taux_remplissage,
            'filters_applied': filters_applied,
            'current_filters': {
                'type_offre': type_offre_id or '',
                'statut': statut_id or '',
                'periode': periode or '',
            }
        })

        return context


class CentreCreateView( BaseCreateView):
    """
    Vue permettant de créer un nouveau centre de formation.
    
    Sécurité:
    - Vérifie la permission 'rap_app.add_centre'
    - Validation complète des champs (notamment format du code postal)
    """
    model = Centre
    permission_required = 'rap_app.add_centre'
    fields = ['nom', 'code_postal']
    success_url = reverse_lazy('centre-list')
    template_name = 'centres/centre_form.html'
    
    def form_valid(self, form):
        """
        Validation du formulaire avec ajout de logs détaillés.
        """
        # Récupération des données du formulaire
        nom = form.cleaned_data['nom']
        code_postal = form.cleaned_data.get('code_postal')
        
        # Log détaillé des informations
        logger.info(
            f"Création d'un nouveau centre par {self.request.user}: "
            f"nom='{nom}', code_postal='{code_postal}'"
        )
        
        # Vérification si un centre avec le même nom existe déjà
        if Centre.objects.filter(nom__iexact=nom).exists():
            form.add_error('nom', "Un centre avec ce nom existe déjà (vérification insensible à la casse)")
            logger.warning(f"Tentative de création d'un centre avec un nom déjà existant: '{nom}'")
            return self.form_invalid(form)
        
        # Ajout d'un message de succès plus informatif
        messages.success(
            self.request, 
            f"Centre '{nom}' créé avec succès."
        )
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """
        Ajoute un titre personnalisé et des infos supplémentaires au contexte.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'titre': "Ajouter un centre de formation",
            'total_centres': Centre.objects.count(),
            'action': 'create'
        })
        return context


class CentreUpdateView( BaseUpdateView):
    """
    Vue permettant de modifier un centre de formation existant.
    
    Sécurité:
    - Vérifie la permission 'rap_app.change_centre'
    - Journalisation des modifications
    """
    model = Centre
    permission_required = 'rap_app.change_centre'
    fields = ['nom', 'code_postal']
    template_name = 'centres/centre_form.html'
    
    def get_success_url(self):
        """
        Redirige vers la page de détail du centre après modification
        """
        return reverse_lazy('centre-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        """
        Validation du formulaire avec comparaison des valeurs avant/après.
        """
        # Récupération de l'objet original avant modifications
        original = Centre.objects.get(pk=self.object.pk)
        
        # Récupération des données du formulaire
        new_nom = form.cleaned_data['nom']
        new_code_postal = form.cleaned_data.get('code_postal')
        
        # Détection des changements
        changes = []
        if original.nom != new_nom:
            changes.append(f"nom: '{original.nom}' → '{new_nom}'")
        
        if original.code_postal != new_code_postal:
            changes.append(f"code_postal: '{original.code_postal}' → '{new_code_postal}'")
        
        # Log détaillé des modifications
        if changes:
            logger.info(
                f"Modification du centre #{self.object.pk} par {self.request.user}: "
                f"{', '.join(changes)}"
            )
            
            # Message plus informatif pour l'utilisateur
            messages.success(
                self.request, 
                f"Centre '{new_nom}' mis à jour avec succès. Modifications: {', '.join(changes)}"
            )
        else:
            logger.info(f"Formulaire soumis sans modifications pour le centre #{self.object.pk}")
            messages.info(self.request, "Aucune modification n'a été effectuée.")
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """
        Ajoute un titre dynamique au contexte en fonction du centre modifié.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'titre': f"Modifier le centre : {self.object.nom}",
            'action': 'update',
            'centre_formations': self.object.formations.count()
        })
        return context


# Fichier: rap_app/views/centre_views.py

class CentreDeleteView(BaseDeleteView):
    """
    Vue permettant de supprimer un centre de formation.
    
    Sécurité:
    - Vérifie la permission 'rap_app.delete_centre'
    - Vérification des dépendances avant suppression
    - Journalisation détaillée
    """
    model = Centre
    permission_required = 'rap_app.delete_centre'
    success_url = reverse_lazy('centre-list')
    template_name = 'centres/centre_confirm_delete.html'
    
    def get_context_data(self, **kwargs):
        """
        Ajoute des informations supplémentaires au contexte pour
        aider à la décision de suppression.
        """
        context = super().get_context_data(**kwargs)
        centre = self.object
        
        # Comptage des formations associées
        formations_count = centre.formations.count()
        
        # Liste des formations actives
        today = timezone.now().date()
        formations_actives = centre.formations.filter(
            Q(start_date__lte=today) & 
            (Q(end_date__gte=today) | Q(end_date__isnull=True))
        ).count()
        
        context.update({
            'formations_count': formations_count,
            'formations_actives': formations_actives,
            'can_delete': formations_count == 0,  # Empêcher la suppression si des formations existent
        })
        
        return context
    
    def form_valid(self, form):
        """
        Validation du formulaire avec vérification des dépendances.
        Méthode appelée lors de la soumission du formulaire de suppression.
        """
        centre = self.object
        
        # Vérification des dépendances
        formations_count = centre.formations.count()
        
        if formations_count > 0:
            logger.warning(
                f"Tentative de suppression du centre #{centre.pk} '{centre.nom}' "
                f"par {self.request.user} bloquée: {formations_count} formations associées"
            )
            messages.error(
                self.request, 
                f"Impossible de supprimer le centre '{centre.nom}' car il possède {formations_count} formations. "
                f"Veuillez d'abord supprimer ou réassigner ces formations."
            )
            return redirect('centre-detail', pk=centre.pk)
        
        # Log avant suppression
        logger.info(f"Suppression du centre #{centre.pk} '{centre.nom}' par {self.request.user}")
        
        # Message de succès personnalisé
        messages.success(self.request, f"Centre '{centre.nom}' supprimé avec succès.")
        
        # Continuer avec la suppression standard
        return super().form_valid(form)
    
    # Suppression de la méthode delete() qui est maintenant gérée par form_valid()