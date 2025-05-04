import logging
import mimetypes
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, Http404
from django.contrib import messages
from django.utils import timezone

from ..models import Document, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView

# Configuration du logger
logger = logging.getLogger(__name__)

class DocumentListView(BaseListView):
    """
    Vue listant tous les documents avec options de filtrage par
    formation, type de document et recherche textuelle.
    """
    model = Document
    context_object_name = 'documents'
    template_name = 'documents/document_list.html'
    paginate_by = 25
    
    def get_queryset(self):
        """
        Récupère la liste des documents avec possibilité de filtrage par:
        - Formation associée
        - Type de document
        - Nom de fichier (recherche textuelle)
        """
        logger.debug("Construction du queryset pour la liste des documents")
        
        queryset = super().get_queryset().select_related('formation', 'formation__centre', 'utilisateur')
        
        # Récupération des paramètres de filtrage
        formation_id = self.request.GET.get('formation')
        type_doc = self.request.GET.get('type_document')
        q = self.request.GET.get('q')
        date_filter = self.request.GET.get('date')
        
        # Filtre appliqués (pour les logs)
        filters_applied = []
        
        # Filtrage par formation
        if formation_id:
            try:
                formation = Formation.objects.get(pk=formation_id)
                queryset = queryset.filter(formation_id=formation_id)
                filters_applied.append(f"formation: {formation.nom}")
            except Formation.DoesNotExist:
                logger.warning(f"Tentative de filtrage par formation inexistante: ID={formation_id}")
            
        # Filtrage par type de document
        if type_doc:
            queryset = queryset.filter(type_document=type_doc)
            type_doc_display = dict(Document.TYPE_DOCUMENT_CHOICES).get(type_doc, type_doc)
            filters_applied.append(f"type: {type_doc_display}")
            
        # Recherche textuelle
        if q:
            queryset = queryset.filter(
                Q(nom_fichier__icontains=q) | 
                Q(source__icontains=q)
            )
            filters_applied.append(f"recherche: '{q}'")
            
        # Filtrage par date
        if date_filter:
            today = timezone.now().date()
            if date_filter == 'today':
                queryset = queryset.filter(created_at__date=today)
                filters_applied.append("date: aujourd'hui")
            elif date_filter == 'week':
                queryset = queryset.filter(created_at__date__gte=today - timezone.timedelta(days=7))
                filters_applied.append("date: 7 derniers jours")
            elif date_filter == 'month':
                queryset = queryset.filter(created_at__date__gte=today - timezone.timedelta(days=30))
                filters_applied.append("date: 30 derniers jours")
        
        # Log des filtres appliqués
        if filters_applied:
            logger.debug(f"Filtres appliqués: {', '.join(filters_applied)}")
            
        result_count = queryset.count()
        logger.debug(f"Nombre de documents trouvés: {result_count}")
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Enrichit le contexte avec:
        - Filtres actuellement appliqués
        - Liste des formations pour le filtrage
        - Types de documents pour le filtrage
        - Statistiques sur les documents
        """
        context = super().get_context_data(**kwargs)
        
        # Récupération des valeurs de filtres
        formation_id = self.request.GET.get('formation', '')
        type_doc = self.request.GET.get('type_document', '')
        q = self.request.GET.get('q', '')
        date_filter = self.request.GET.get('date', '')
        
        # Filtres actuellement appliqués
        context['filters'] = {
            'formation': formation_id,
            'type_document': type_doc,
            'q': q,
            'date': date_filter,
        }
        
        # Statistiques
        stats = {
            'total': Document.objects.count(),
            'total_pdf': Document.objects.filter(type_document=Document.PDF).count(),
            'total_image': Document.objects.filter(type_document=Document.IMAGE).count(),
            'total_contrat': Document.objects.filter(type_document=Document.CONTRAT).count(),
            'total_autre': Document.objects.filter(type_document=Document.AUTRE).count(),
            'taille_totale': Document.objects.aggregate(total=Sum('taille_fichier'))['total'] or 0,
        }
        
        # Formations les plus documentées
        top_formations = Formation.objects.annotate(
            nb_documents=Count('documents')
        ).filter(nb_documents__gt=0).order_by('-nb_documents')[:5]
        
        # Liste des formations pour le filtrage (avec annotations pour le tri)
        formations = Formation.objects.annotate(
            nb_documents=Count('documents')
        ).filter(nb_documents__gt=0).order_by('nom')
        
        # Types de documents pour le filtrage
        types_document = Document.TYPE_DOCUMENT_CHOICES
        
        # Ajout au contexte
        context.update({
            'formations': formations,
            'types_document': types_document,
            'stats': stats,
            'top_formations': top_formations,
            'date_options': [
                {'value': 'today', 'label': "Aujourd'hui"},
                {'value': 'week', 'label': '7 derniers jours'},
                {'value': 'month', 'label': '30 derniers jours'},
            ]
        })
        
        logger.debug(f"Contexte préparé pour la liste des documents")
        return context


class DocumentDownloadView(BaseDetailView):
    """
    Vue pour télécharger un document avec gestion du type MIME
    et comptage des téléchargements.
    """
    
    def get(self, request, pk):
        """Gère le téléchargement du document."""
        try:
            document = get_object_or_404(Document, pk=pk)
            
            # Détermination du type MIME approprié
            content_type = document.mime_type if hasattr(document, 'mime_type') and document.mime_type else None
            
            if not content_type:
                content_type = mimetypes.guess_type(document.fichier.name)[0]
                
            if not content_type:
                # Fallback pour éviter des problèmes avec certains navigateurs
                content_type = 'application/octet-stream'
            
            # Configuration de la réponse HTTP
            response = HttpResponse(document.fichier, content_type=content_type)
            
            # Définition des en-têtes pour le téléchargement
            filename = document.nom_fichier
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Journalisation du téléchargement
            logger.info(
                f"Téléchargement du document #{document.pk}: {document.nom_fichier} "
                f"par {request.user.username if request.user.is_authenticated else 'Anonyme'}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement du document #{pk}: {str(e)}")
            messages.error(request, f"Une erreur est survenue lors du téléchargement: {str(e)}")
            return redirect('document-list')


class DocumentDetailView(BaseDetailView):
    """Vue affichant les détails d'un document"""
    model = Document
    context_object_name = 'document'
    template_name = 'documents/document_detail.html'
    
    def get_context_data(self, **kwargs):
        """Enrichit le contexte avec des informations supplémentaires."""
        context = super().get_context_data(**kwargs)
        document = self.object
        
        logger.info(f"Consultation du document #{document.pk}: {document.nom_fichier} par {self.request.user.username}")
        
        # Détermination du type MIME et de l'icône
        mimetype = document.mime_type if hasattr(document, 'mime_type') else mimetypes.guess_type(document.fichier.name)[0]
        
        # Autres documents de la même formation
        autres_documents = Document.objects.filter(
            formation=document.formation
        ).exclude(pk=document.pk).order_by('-created_at')[:5]
        
        # Informations sur la formation
        formation_info = {
            'nom': document.formation.nom,
            'centre': document.formation.centre.nom if document.formation.centre else "N/A",
            'nb_documents': document.formation.documents.count(),
        }
        
        context.update({
            'mimetype': mimetype,
            'icon_class': document.get_icon_class() if hasattr(document, 'get_icon_class') else 'fa-file',
            'autres_documents': autres_documents,
            'formation_info': formation_info,
            'extension': document.get_file_extension() if hasattr(document, 'get_file_extension') else None,
        })
        
        return context


class DocumentCreateView(PermissionRequiredMixin, BaseCreateView):
    """Vue permettant de créer un nouveau document"""
    model = Document
    permission_required = 'rap_app.add_document'
    fields = ['formation', 'nom_fichier', 'fichier', 'source', 'type_document']
    template_name = 'documents/document_form.html'
    
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
        Associe l'utilisateur courant au document et valide le formulaire.
        """
        # Associer l'utilisateur courant au document
        form.instance.utilisateur = self.request.user
        
        # Validation du type de document en fonction du fichier
        fichier = form.cleaned_data.get('fichier')
        type_doc = form.cleaned_data.get('type_document')
        
        if fichier and type_doc:
            try:
                # La validation est effectuée par le modèle, mais nous pouvons
                # ajouter une journalisation spécifique ici
                logger.info(
                    f"Création d'un document '{form.cleaned_data.get('nom_fichier')}' "
                    f"de type '{type_doc}' pour la formation "
                    f"'{form.cleaned_data.get('formation').nom}' par {self.request.user.username}"
                )
            except Exception as e:
                logger.error(f"Erreur lors de la création du document: {str(e)}")
                messages.error(self.request, f"Une erreur est survenue: {str(e)}")
                return self.form_invalid(form)
        
        messages.success(
            self.request,
            f"Document '{form.cleaned_data.get('nom_fichier')}' ajouté avec succès."
        )
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Journalise les erreurs de validation du formulaire."""
        logger.warning(
            f"Échec de création d'un document: {form.errors.as_json()} "
            f"par {self.request.user.username}"
        )
        
        # Message d'erreur plus informatif
        messages.error(
            self.request,
            "Le document n'a pas pu être créé. Veuillez corriger les erreurs dans le formulaire."
        )
        
        return super().form_invalid(form)
    
    def get_success_url(self):
        """Redirige vers la formation associée après création"""
        return reverse_lazy('formation-detail', kwargs={'pk': self.object.formation.pk})
    
    def get_context_data(self, **kwargs):
        """Enrichit le contexte avec titre et liste des types de documents."""
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un document"
        context['types_document'] = Document.TYPE_DOCUMENT_CHOICES
        
        # Formations récentes pour faciliter la sélection
        context['formations_recentes'] = Formation.objects.order_by('-start_date')[:10]
        
        return context


class DocumentUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Vue permettant de modifier un document existant"""
    model = Document
    permission_required = 'rap_app.change_document'
    fields = ['nom_fichier', 'fichier', 'source', 'type_document']
    template_name = 'documents/document_form.html'
    
    def form_valid(self, form):
        """Valide le formulaire avec journalisation des modifications."""
        # Récupération de l'objet original avant modifications
        original = Document.objects.get(pk=self.object.pk)
        
        # Détection des changements
        changes = []
        if original.nom_fichier != form.cleaned_data.get('nom_fichier'):
            changes.append(f"nom_fichier: '{original.nom_fichier}' → '{form.cleaned_data.get('nom_fichier')}'")
            
        if original.source != form.cleaned_data.get('source'):
            changes.append(f"source modifiée")
            
        if original.type_document != form.cleaned_data.get('type_document'):
            changes.append(
                f"type_document: '{original.get_type_document_display()}' → "
                f"'{dict(Document.TYPE_DOCUMENT_CHOICES).get(form.cleaned_data.get('type_document'))}'"
            )
            
        if original.fichier != form.cleaned_data.get('fichier'):
            changes.append(f"fichier remplacé")
        
        # Journalisation des modifications
        if changes:
            logger.info(
                f"Modification du document #{self.object.pk} par {self.request.user.username}: "
                f"{', '.join(changes)}"
            )
            
            # Message plus informatif
            messages.success(
                self.request,
                f"Document '{self.object.nom_fichier}' mis à jour avec succès. "
                f"Modifications: {', '.join(changes)}"
            )
        else:
            logger.info(f"Formulaire soumis sans modifications pour le document #{self.object.pk}")
            messages.info(self.request, "Aucune modification n'a été effectuée.")
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Journalise les erreurs de validation lors de la modification."""
        logger.warning(
            f"Échec de modification du document #{self.object.pk}: {form.errors.as_json()} "
            f"par {self.request.user.username}"
        )
        
        # Message d'erreur
        messages.error(
            self.request,
            "Le document n'a pas pu être modifié. Veuillez corriger les erreurs dans le formulaire."
        )
        
        return super().form_invalid(form)
    
    def get_success_url(self):
        """Redirige vers la formation associée après modification"""
        return reverse_lazy('formation-detail', kwargs={'pk': self.object.formation.pk})
    
    def get_context_data(self, **kwargs):
        """Enrichit le contexte avec titre et liste des types de documents."""
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le document : {self.object.nom_fichier}"
        context['types_document'] = Document.TYPE_DOCUMENT_CHOICES
        context['formation'] = self.object.formation
        
        return context


class DocumentDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Vue permettant de supprimer un document"""
    model = Document
    permission_required = 'rap_app.delete_document'
    template_name = 'documents/document_confirm_delete.html'
    
    def get_context_data(self, **kwargs):
        """Enrichit le contexte pour la confirmation de suppression."""
        context = super().get_context_data(**kwargs)
        document = self.object
        
        context.update({
            'formation': document.formation,
            'taille': document.taille_fichier,
            'date_creation': document.created_at,
            'utilisateur': document.utilisateur,
        })
        
        return context
    
    def delete(self, request, *args, **kwargs):
        """Personnalise la suppression avec journalisation."""
        self.object = self.get_object()
        document = self.object
        
        # Stockage de l'ID de la formation pour la redirection
        formation_id = document.formation.id if document.formation else None
        
        # Journalisation détaillée
        logger.warning(
            f"Suppression du document #{document.pk} '{document.nom_fichier}' "
            f"({document.get_type_document_display()}) "
            f"par {request.user.username}"
        )
        
        # Message personnalisé
        messages.success(
            request, 
            f"Document '{document.nom_fichier}' supprimé avec succès."
        )
        
        # Suppression et redirection
        document.delete()
        
        return redirect('formation-detail', pk=formation_id) if formation_id else redirect('document-list')
    
    def get_success_url(self):
        """Redirige vers la formation associée après suppression"""
        formation_id = self.object.formation.id
        return reverse_lazy('formation-detail', kwargs={'pk': formation_id})