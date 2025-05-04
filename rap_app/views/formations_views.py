import csv
from django.contrib.auth import get_user_model
from django.views.generic import ListView
from django.urls import reverse_lazy
from django.db.models import Q, F, ExpressionWrapper, IntegerField, FloatField
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from datetime import datetime, date  # ✅ Ajoute cette ligne en haut du fichier
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from django.views import View
from django.views.decorators.http import require_POST
from datetime import datetime

from django.contrib import messages
from django.http import HttpResponseBadRequest

from ..models.company import Company

from ..models.formations import HistoriqueFormation

from ..models.partenaires import Partenaire
from ..models import Formation


from ..models.centres import Centre
from ..models.statut import Statut
from ..models.types_offre import TypeOffre

from ..models.commentaires import Commentaire, User
from ..models import Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView

User = get_user_model()
import logging
logger = logging.getLogger(__name__)


from django.db.models import Case, When, Value
from django.db.models.functions import NullIf  # ✅ pour éviter division par zéro SQL

class FormationListView(BaseListView):
    """Vue listant toutes les formations avec options de filtrage et indicateurs dynamiques."""
    model = Formation
    context_object_name = 'formations'
    template_name = 'formations/formation_list.html'
    paginate_by = 10

    def get_queryset(self):
        today = timezone.now().date()

        queryset = Formation.objects.select_related('centre', 'type_offre', 'statut').annotate(
            total_places=ExpressionWrapper(
                F('prevus_crif') + F('prevus_mp'), output_field=IntegerField()
            ),
            total_inscrits=ExpressionWrapper(
                F('inscrits_crif') + F('inscrits_mp'), output_field=IntegerField()
            ),
            places_restantes_crif=ExpressionWrapper(
                F('prevus_crif') - F('inscrits_crif'), output_field=IntegerField()
            ),
            places_restantes_mp=ExpressionWrapper(
                F('prevus_mp') - F('inscrits_mp'), output_field=IntegerField()
            ),
            taux_saturation=Case(
                When(prevus_crif=0, prevus_mp=0, then=Value(0.0)),
                default=ExpressionWrapper(
                    100.0 * (F('inscrits_crif') + F('inscrits_mp')) / 
                    NullIf(F('prevus_crif') + F('prevus_mp'), 0),
                    output_field=FloatField()
                ),
                output_field=FloatField()
            ),
            taux_transformation=Case(
                When(nombre_candidats=0, then=Value(0.0)),
                default=ExpressionWrapper(
                    100.0 * (F('inscrits_crif') + F('inscrits_mp')) / 
                    NullIf(F('nombre_candidats'), 0),
                    output_field=FloatField()
                ),
                output_field=FloatField()
            ),
        )

        mot_cle = self.request.GET.get('q', '').strip()
        if mot_cle:
            queryset = queryset.filter(
                Q(nom__icontains=mot_cle) |
                Q(num_offre__icontains=mot_cle) |
                Q(centre__nom__icontains=mot_cle) |
                Q(type_offre__nom__icontains=mot_cle) |
                Q(statut__nom__icontains=mot_cle)
            )

        centre_id = self.request.GET.get('centre', '').strip()
        type_offre_id = self.request.GET.get('type_offre', '').strip()
        statut_id = self.request.GET.get('statut', '').strip()
        periode = self.request.GET.get('periode', '').strip()

        if centre_id:
            queryset = queryset.filter(centre_id=centre_id)
        if type_offre_id:
            queryset = queryset.filter(type_offre_id=type_offre_id)
        if statut_id:
            queryset = queryset.filter(statut_id=statut_id)
        if periode:
            if periode == 'active':
                queryset = queryset.filter(start_date__lte=today, end_date__gte=today)
            elif periode == 'a_venir':
                queryset = queryset.filter(start_date__gt=today)
            elif periode == 'terminee':
                queryset = queryset.filter(end_date__lt=today)
            elif periode == 'a_recruter':
                queryset = queryset.filter(total_places__gt=F('total_inscrits'))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = [
            (Formation.objects.count(), "Total formations", "primary", "fa-graduation-cap"),
            (Formation.objects.formations_actives().count(), "Formations Actives", "success", "fa-check-circle"),
            (Formation.objects.formations_a_venir().count(), "Formations À venir", "info", "fa-clock"),
            (Formation.objects.formations_terminees().count(), "Formations Terminées", "secondary", "fa-times-circle"),
            (Formation.objects.formations_a_recruter().count(), "Formations À recruter", "danger", "fa-users"),
        ]
        context['centres'] = Centre.objects.all()
        context['types_offre'] = TypeOffre.objects.all()
        context['statuts'] = Statut.objects.all()
        context['filters'] = {
            'centre': self.request.GET.get('centre', ''),
            'type_offre': self.request.GET.get('type_offre', ''),
            'statut': self.request.GET.get('statut', ''),
            'periode': self.request.GET.get('periode', ''),
            'q': self.request.GET.get('q', ''),
        }
        return context

    def post(self, request, *args, **kwargs):
        formation = self.get_object()
        action = request.POST.get("action")

        if action == "add_company":
            return self.add_company(request, formation)
        elif action == "add_prospection":
            return self.add_prospection(request, formation)

        return super().post(request, *args, **kwargs)

    def add_company(self, request, formation):
        from ..forms.company_form import CompanyForm
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.created_by = request.user
            company.save()
            messages.success(request, "✅ Entreprise ajoutée avec succès.")
        else:
            messages.error(request, "❌ Erreur lors de l'ajout de l'entreprise.")
        return redirect(request.path)

    def add_prospection(self, request, formation):
        from ..forms.ProspectionForm import ProspectionForm
        form = ProspectionForm(request.POST)
        if form.is_valid():
            prospection = form.save(commit=False)
            prospection.formation = formation
            prospection.responsable = request.user
            prospection.save()
            messages.success(request, "✅ Prospection ajoutée avec succès.")
        else:
            messages.error(request, "❌ Erreur lors de l'ajout de la prospection.")
        return redirect(request.path)



class FormationDetailView(BaseDetailView):
    """Vue affichant les détails d'une formation"""
    model = Formation
    context_object_name = 'formation'
    template_name = 'formations/formation_detail.html'


    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            formation = self.object

            # Commentaires paginés
            commentaires = formation.get_commentaires().order_by('-created_at')
            paginator = Paginator(commentaires, 5)  # 5 commentaires par page
            page = self.request.GET.get("page")
            context["commentaires_page"] = paginator.get_page(page)

            # Dernier commentaire
            context['dernier_commentaire'] = commentaires.first()

            # Autres données contextuelles
            context['evenements'] = formation.get_evenements().order_by('-event_date')
            context['documents'] = formation.documents.all().order_by('-created_at')
            context['partenaires'] = formation.get_partenaires()
            context['partenaires_disponibles'] = Partenaire.objects.exclude(id__in=formation.partenaires.values_list('id', flat=True))
            context['historique'] = formation.historiques.order_by('-date_modification')[:10]
            context['places_restantes_crif'] = formation.get_places_restantes_crif()
            context['places_restantes_mp'] = formation.get_places_restantes_mp()
            context['taux_saturation'] = formation.get_taux_saturation()

            context['prospections'] = formation.prospections.select_related('company', 'responsable')
            context['entreprises'] = Company.objects.filter(prospections__formation=formation).distinct()

            from ..forms.company_form import CompanyForm
            from ..forms.ProspectionForm import ProspectionForm
            context['company_form'] = CompanyForm()
            context['prospection_form'] = ProspectionForm(initial={'formation': formation})

            return context
    def post(self, request, *args, **kwargs):
            """
            Gère l'ajout de commentaires, événements, documents et partenaires via POST.
            L'action est déterminée par le champ `action` du formulaire.
            """
            formation = self.get_object()
            action = request.POST.get('action')

            if action == 'add_commentaire':
                return self.add_commentaire(request, formation)

            elif action == 'add_evenement':
                return self.add_evenement(request, formation)

            elif action == 'add_document':
                return self.add_document(request, formation)

            elif action == 'add_partenaire':
                return self.add_partenaire(request, formation)

            return HttpResponseBadRequest("Action non valide.")

    def add_commentaire(self, request, formation):
        """Ajoute un commentaire à la formation"""
        contenu = request.POST.get('contenu', '').strip()

        if not contenu:
            return HttpResponseBadRequest("Le commentaire ne peut pas être vide.")

        formation.add_commentaire(request.user, contenu)
        messages.success(request, "Commentaire ajouté avec succès.")
        return redirect(self.request.path)
        

    def add_evenement(self, request, formation):
        """Ajoute un événement à la formation"""
        type_evenement = request.POST.get('type_evenement', '').strip()
        date = request.POST.get('date')
        details = request.POST.get('details', '').strip()
        description_autre = request.POST.get('description_autre', '').strip()

        if not type_evenement or not date:
            return HttpResponseBadRequest("Le type et la date de l'événement sont obligatoires.")

    # ✅ On appelle la méthode avec les bons arguments (4 au total)
        formation.add_evenement(type_evenement, date, details, description_autre)
        messages.success(request, "Événement ajouté avec succès.")
        return redirect(self.request.path)

    def add_document(self, request, formation):
        """Ajoute un document à la formation."""
        nom = request.POST.get('nom', '').strip()
        fichier = request.FILES.get('fichier')

        if not nom or not fichier:
            return HttpResponseBadRequest("Le nom et le fichier sont obligatoires.")

        # ✅ Ajout du document directement avec `.create()`
        formation.documents.create(
            utilisateur=request.user, 
            nom_fichier=nom, 
            fichier=fichier
        )

        messages.success(request, "Document ajouté avec succès.")
        return redirect(self.request.path)

class FormationCreateView(PermissionRequiredMixin, BaseCreateView):
    """Vue permettant de créer une nouvelle formation"""
    model = Formation
    permission_required = 'rap_app.add_formation'
    template_name = 'formations/formation_form.html'
    fields = [
        'nom', 'centre', 'type_offre', 'statut', 'start_date', 'end_date',
        'num_kairos', 'num_offre', 'num_produit', 'prevus_crif', 'prevus_mp',
        'inscrits_crif', 'inscrits_mp', 'assistante', 'cap', 'convocation_envoie',
        'entresformation', 'nombre_candidats', 'nombre_entretiens'
    ]

    def form_valid(self, form):
        """Associe l'utilisateur connecté à la formation et crée un historique"""
        with transaction.atomic():
            # ✅ Associe l'utilisateur à la formation créée
            form.instance.utilisateur = self.request.user

            # ✅ Enregistre la formation
            response = super().form_valid(form)

            # ✅ Création d'un historique lié à la création
            HistoriqueFormation.objects.create(
                formation=self.object,
                modifie_par=self.request.user,  # 🔁 correction ici (anciennement `utilisateur=`)
                action='création',
                details={'nom': self.object.nom}
            )

            return response


    def get_success_url(self):
        return reverse_lazy('formation-detail', kwargs={'pk': self.object.pk})


class FormationUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Vue permettant de modifier une formation existante"""
    model = Formation
    permission_required = 'rap_app.change_formation'
    template_name = 'formations/formation_form.html'
    fields = FormationCreateView.fields  # ✅ Réutilisation des champs

    def form_valid(self, form):
        """Détecte les modifications et enregistre un historique si nécessaire"""

        def serialize(value):
            """Convertit les valeurs en chaînes pour comparaison"""
            if isinstance(value, (datetime, date)):
                return value.isoformat()
            elif hasattr(value, '__str__'):
                return str(value)
            return value

        with transaction.atomic():
            # ✅ On récupère l'ancienne version de l'objet
            old_obj = Formation.objects.get(pk=self.object.pk)

            # ✅ On sauvegarde la nouvelle version via la méthode parent
            response = super().form_valid(form)

            # 🔍 Détection des champs modifiés
            changes = {}
            for field in self.fields:
                old_value = getattr(old_obj, field)
                new_value = getattr(self.object, field)

                if serialize(old_value) != serialize(new_value):
                    changes[field] = {
                        'ancien': serialize(old_value),
                        'nouveau': serialize(new_value)
                    }

            # 📝 Création d’un historique si des modifications ont été faites
            if changes:
                HistoriqueFormation.objects.create(
                    formation=self.object,
                    modifie_par=self.request.user,  # ✅ champ correct
                    action='modification',
                    details=changes
                )
                # logger.debug(f"📚 Historique enregistré pour la formation {self.object.id} : {changes}")

            return response



    def get_success_url(self):
        return reverse_lazy('formation-detail', kwargs={'pk': self.object.pk})


class FormationDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Vue permettant de supprimer une formation"""
    model = Formation
    permission_required = 'rap_app.delete_formation'
    success_url = reverse_lazy('formation-list')
    template_name = 'formations/formation_confirm_delete.html'


class FormationAddCommentView(BaseCreateView):
    """Vue permettant d'ajouter un commentaire à une formation"""
    model = Commentaire
    fields = ['contenu']
    template_name = 'formations/formation_add_comment.html'

    def dispatch(self, request, *args, **kwargs):
        """Vérifie que la formation existe avant d'ajouter un commentaire"""
        self.formation = get_object_or_404(Formation, pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Associe le commentaire à la formation et à l'utilisateur"""
        form.instance.formation = self.formation
        form.instance.utilisateur = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('formation-detail', kwargs={'pk': self.formation.pk})

class ExportFormationsExcelView(View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="formations_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "Nom", "Centre", "num_offre", "Type d'offre", "Statut", "N° Kairos", 
            "Dates", "Assistante", "Candidats", "Entretiens",
            "Prévus CRIF", "Prévus MP", "Inscrits CRIF", "Inscrits MP",
            "Places restantes CRIF", "Places restantes MP",
            "Transformation", "Saturation"
        ])

        formations = Formation.objects.all()
        for formation in formations:
            writer.writerow([
                formation.nom, 
                formation.centre.nom if formation.centre else "-",
                formation.num_offre if formation.num_offre else "-",
                formation.type_offre.nom if formation.type_offre else "-",
                formation.statut.nom if formation.statut else "-",
                formation.num_kairos if formation.num_kairos else "-",
                f"{formation.start_date} - {formation.end_date}",
                formation.assistante if formation.assistante else "-",
                formation.nombre_candidats,
                formation.nombre_entretiens,
                formation.prevus_crif,
                formation.prevus_mp,
                formation.inscrits_crif,
                formation.inscrits_mp,
                formation.get_places_restantes_crif(),  # ✅ Appel correct
                formation.get_places_restantes_mp(),  # ✅ Appel correct
                formation.get_taux_saturation(),  # ✅ Ajout du taux de saturation
                formation.get_taux_saturation()  # ✅ Transformation (ajuster si différent)
            ])

        return response
    





@method_decorator(csrf_exempt, name='dispatch')
class UpdateFormationFieldView(View):
    def post(self, request, id):
        try:
            data = json.loads(request.body)
            field = data.get("field")
            value = data.get("value")

            formation = Formation.objects.get(pk=id)

            if field in ["start_date", "end_date"]:
                from datetime import datetime
                if value == "":
                    setattr(formation, field, None)
                else:
                    setattr(formation, field, datetime.strptime(value, "%Y-%m-%d").date())

            elif field in ["nombre_candidats", "nombre_entretiens", "prevus_crif", "prevus_mp", "inscrits_crif", "inscrits_mp"]:
                if value == "" or value is None:
                    setattr(formation, field, 0)
                else:
                    setattr(formation, field, int(value))

            elif field == "statut":
                from ..models import Statut
                formation.statut = Statut.objects.get(pk=value)

            else:
                setattr(formation, field, value)

            formation.save()

            return JsonResponse({
                "success": True,
                "taux_saturation": formation.get_taux_saturation(),
                "taux_transformation": formation.get_taux_transformation(),
                "places_restantes_crif": formation.get_places_restantes_crif(),
                "places_restantes_mp": formation.get_places_restantes_mp(),
            })

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
