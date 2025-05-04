import logging
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django.db.models import (
    Count, Sum, Avg, F, Q, Case, When, 
    IntegerField, Value, FloatField
)
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse, HttpRequest
from django.views import View
from django.db.models.functions import Coalesce, TruncMonth
from django.db import transaction
from django.db.models import ExpressionWrapper

from ..models.vae_jury import VAE, SuiviJury

from ..models.prepacomp import PrepaCompGlobal, Semaine

# Import des modèles
from ..models.company import Company
from ..models.prospection import PROSPECTION_STATUS_CHOICES, Prospection
from ..models.formations import Formation, HistoriqueFormation
from ..views.base_views import BaseListView
from ..models.partenaires import Partenaire
from ..models.centres import Centre
from ..models.commentaires import Commentaire
from ..models.types_offre import TypeOffre
from ..models.statut import Statut
from ..models.evenements import Evenement

# Configuration du logger
logger = logging.getLogger("application.dashboard.views")


class DashboardView(BaseListView):
    """
    Vue principale du tableau de bord affichant des statistiques globales et détaillées.
    
    Cette vue regroupe l'ensemble des indicateurs clés de l'application:
    - Formations par centre, type d'offre et statut
    - Statistiques de recrutement et d'inscription
    - Taux d'occupation et de transformation
    - Informations sur les événements et prospections
    - Dernières activités
    
    Le contexte généré est utilisé pour alimenter les graphiques et tableaux du dashboard.
    """
    model = Formation
    template_name = 'dashboard.html'
    context_object_name = 'formations'
    
    def get_queryset(self):
        """
        Récupère les formations avec optimisation des requêtes.
        
        Returns:
            QuerySet: Formations avec préchargement des relations
        """
        # Optimisation des requêtes avec select_related
        return Formation.objects.select_related(
            'centre', 'type_offre', 'statut', 'utilisateur'
        ).order_by('-start_date')[:20]  # Limite pour éviter de surcharger le dashboard
    
    def get_context_data(self, **kwargs):
        """
        Génère l'ensemble des données statistiques pour le tableau de bord.
        
        Cette méthode construit de nombreux indicateurs clés qui sont regroupés
        par catégorie et optimisés pour minimiser les requêtes à la base de données.
        
        Args:
            **kwargs: Arguments de contexte par défaut
            
        Returns:
            dict: Contexte enrichi avec toutes les statistiques
        """
        logger.debug("Génération des statistiques du dashboard")
        context = super().get_context_data(**kwargs)

        # Utilisation d'une transaction atomique pour chaque bloc de statistiques
        # Si une erreur se produit, la transaction est annulée et on continue
        self._safely_add_stats(self._add_basic_formation_stats, context, "basic_formation_stats")
        self._safely_add_stats(self._add_centre_stats, context, "centre_stats")
        self._safely_add_stats(self._add_type_and_status_stats, context, "type_and_status_stats")
        self._safely_add_stats(self._add_recruitment_stats, context, "recruitment_stats")
        self._safely_add_stats(self._add_partner_stats, context, "partner_stats")
        self._safely_add_stats(self._add_prospection_stats, context, "prospection_stats")
        self._safely_add_stats(self._add_event_stats, context, "event_stats")
        self._safely_add_stats(self._add_recent_activity, context, "recent_activity")
        self._safely_add_stats(self._add_stats_cards, context, "stats_cards")
        self._safely_add_stats(self._add_prepa_stats, context, "prepa_stats")
        self._safely_add_stats(self._add_vae_jury_stats, context, "vae_jury_stats")

        logger.info("Génération du dashboard terminée.")
        return context

    def _safely_add_stats(self, stats_method, context, stats_name):
        """
        Exécute une méthode de statistiques dans une transaction atomique.
        Si une erreur se produit, la transaction est annulée et on continue.
        
        Args:
            stats_method: Méthode à exécuter
            context: Contexte à enrichir
            stats_name: Nom des statistiques pour le log
        """
        try:
            # Exécution dans une transaction séparée
            with transaction.atomic():
                stats_method(context)
        except Exception as e:
            # En cas d'erreur, on annule la transaction et on log l'erreur
            logger.error(f"Erreur dans {stats_name}: {e}", exc_info=True)
            # On ajoute une entrée dans le contexte pour indiquer que ces statistiques sont manquantes
            context[f"{stats_name}_error"] = str(e)
                   
    def _add_prepa_stats(self, context):
        annee = timezone.now().year
        objectif = PrepaCompGlobal.objectif_annuel_global() or 0  # ⚠️ éviter None

        adhesions = Semaine.objects.filter(annee=annee).aggregate(
            total=Sum('nombre_adhesions')
        )['total'] or 0

        taux = 0
        if objectif > 0:
            try:
                taux = round((adhesions / objectif) * 100, 1)
            except ZeroDivisionError:
                taux = 0

            context['objectif_annuel_prepa'] = objectif
            context['adhesions_globales_prepa'] = adhesions
            context['taux_objectif_prepa'] = taux

            return context
    
    def _add_basic_formation_stats(self, context):
        """
        Ajoute les statistiques de base sur les formations.
        
        Args:
            context: Dictionnaire de contexte à enrichir
        """
        context['total_formations'] = Formation.objects.count()
        context['formations_actives'] = Formation.objects.formations_actives().count()
        context['formations_a_venir'] = Formation.objects.formations_a_venir().count()
        context['formations_terminees'] = Formation.objects.formations_terminees().count()
        context['formations_a_recruter'] = Formation.objects.formations_a_recruter().count()
        
        # Places prévues et disponibles
        # On fait les agrégations simples uniquement
        places_stats = Formation.objects.aggregate(
            total_prevus_crif=Sum('prevus_crif'),
            total_prevus_mp=Sum('prevus_mp'),
            total_inscrits_crif=Sum('inscrits_crif'),
            total_inscrits_mp=Sum('inscrits_mp')
        )

        # On sécurise les None
        prevus_crif = places_stats['total_prevus_crif'] or 0
        prevus_mp = places_stats['total_prevus_mp'] or 0
        inscrits_crif = places_stats['total_inscrits_crif'] or 0
        inscrits_mp = places_stats['total_inscrits_mp'] or 0

        # Calculs en Python
        total_places_prevues = prevus_crif + prevus_mp
        total_inscrits = inscrits_crif + inscrits_mp
        total_places_restantes = total_places_prevues - total_inscrits

        context['total_places_prevues'] = total_places_prevues
        context['total_places_prevues_crif'] = prevus_crif
        context['total_places_prevues_mp'] = prevus_mp

        context['total_inscrits'] = total_inscrits
        context['total_inscrits_crif'] = inscrits_crif
        context['total_inscrits_mp'] = inscrits_mp

        context['total_places_restantes'] = total_places_restantes
        context['total_places_restantes_crif'] = prevus_crif - inscrits_crif
        context['total_places_restantes_mp'] = prevus_mp - inscrits_mp
    

    def _add_centre_stats(self, context):
        """
        Ajoute les statistiques regroupées par centre.

        Args:
            context: Dictionnaire de contexte à enrichir
        """
        # Nombre total de formations par centre
        context['formations_par_centre'] = Centre.objects.annotate(
            total_formations=Count('formations')
        ).order_by('-total_formations')

        # Candidats et entretiens par centre
        context['candidats_par_centre'] = Centre.objects.annotate(
            total_candidats=Sum('formations__nombre_candidats'),
            total_entretiens=Sum('formations__nombre_entretiens')
        ).filter(
            Q(total_candidats__gt=0) | Q(total_entretiens__gt=0)
        ).order_by('-total_candidats')

        # Calcul sécurisé avec ExpressionWrapper pour les F() + F()
        total_places_expr = ExpressionWrapper(
            F('formations__prevus_crif') + F('formations__prevus_mp'),
            output_field=IntegerField()
        )
        total_inscrits_expr = ExpressionWrapper(
            F('formations__inscrits_crif') + F('formations__inscrits_mp'),
            output_field=IntegerField()
        )

        # Places prévues et inscrits par centre
        context['places_par_centre'] = Centre.objects.annotate(
            total_places_prevues=Sum(total_places_expr),
            total_inscrits=Sum(total_inscrits_expr),
            places_prevues_crif=Sum('formations__prevus_crif'),
            places_prevues_mp=Sum('formations__prevus_mp'),
            inscrits_crif=Sum('formations__inscrits_crif'),
            inscrits_mp=Sum('formations__inscrits_mp')
        ).filter(
            total_places_prevues__gt=0
        ).order_by('-total_places_prevues')

        # Taux de transformation et saturation par centre
        context['taux_par_centre'] = Centre.objects.annotate(
            total_formations=Count('formations'),
            total_candidats=Sum('formations__nombre_candidats'),
            total_entretiens=Sum('formations__nombre_entretiens'),
            places_prevues_crif=Sum('formations__prevus_crif'),
            inscrits_crif=Sum('formations__inscrits_crif'),
            places_prevues_mp=Sum('formations__prevus_mp'),
            inscrits_mp=Sum('formations__inscrits_mp'),
            total_inscrits=Sum(total_inscrits_expr),
            total_places_prevues=Sum(total_places_expr),
            taux_transformation=Case(
                When(total_candidats__gt=0,
                    then=100.0 * Sum(total_inscrits_expr) /
                        Coalesce(Sum('formations__nombre_candidats'), Value(1))),
                default=Value(0.0)
            ),
            taux_saturation=Case(
                When(total_places_prevues__gt=0,
                    then=100.0 * Sum(total_inscrits_expr) /
                        Coalesce(Sum(total_places_expr), Value(1))),
                default=Value(0.0)
            )
        ).filter(
            Q(total_candidats__gt=0) | Q(total_places_prevues__gt=0)
        ).order_by('-taux_saturation')
    
    def _add_type_and_status_stats(self, context):
        """
        Ajoute les statistiques par type d'offre et statut.
        
        Args:
            context: Dictionnaire de contexte à enrichir
        """
        # Formations par type d'offre
        context['formations_par_type_offre'] = TypeOffre.objects.annotate(
            total=Count('formations')
        ).order_by('-total')
        
        # Formations par statut
        context['formations_par_statut'] = Statut.objects.annotate(
            total=Count('formations')
        ).order_by('-total')
    
    def _add_recruitment_stats(self, context):
        """
        Ajoute les statistiques de recrutement.
        
        Args:
            context: Dictionnaire de contexte à enrichir
        """
        # Recrutement et inscriptions
        recruitment_stats = Formation.objects.aggregate(
            total_candidats=Sum('nombre_candidats'),
            total_entretiens=Sum('nombre_entretiens')
        )
        
        # Sécurisation contre les valeurs None
        context['total_candidats'] = recruitment_stats['total_candidats'] or 0
        context['total_entretiens'] = recruitment_stats['total_entretiens'] or 0
        
        # Calcul des taux moyens avec gestion d'erreur (division par zéro)
        try:
            context['taux_transformation_moyen'] = Formation.objects.aggregate(
                taux=Avg(100 * (F('inscrits_crif') + F('inscrits_mp')) / 
                         Coalesce(F('nombre_candidats'), Value(1)))
            )['taux'] or 0
        except:
            context['taux_transformation_moyen'] = 0
        
        try:
            context['taux_saturation_moyen'] = Formation.objects.aggregate(
                taux=Avg(100 * (F('inscrits_crif') + F('inscrits_mp')) / 
                         Coalesce(F('prevus_crif') + F('prevus_mp'), Value(1)))
            )['taux'] or 0
        except:
            context['taux_saturation_moyen'] = 0
    
    def _add_partner_stats(self, context):
        """
        Ajoute les statistiques relatives aux partenaires.
        
        Args:
            context: Dictionnaire de contexte à enrichir
        """
        context['total_partenaires'] = Partenaire.objects.count()
    
    def _add_prospection_stats(self, context):
        """
        Ajoute les statistiques de prospection.
        
        Args:
            context: Dictionnaire de contexte à enrichir
        """
        # Nombre total de prospections
        context['total_prospections'] = Prospection.objects.count()
        
        # Prospections par statut
        context['nb_prospections_en_cours'] = Prospection.objects.filter(statut='en_cours').count()
        context['nb_prospections_acceptees'] = Prospection.objects.filter(statut='acceptee').count()
        context['nb_prospections_a_faire'] = Prospection.objects.filter(statut='a_faire').count()
        context['nb_prospections_a_relancer'] = Prospection.objects.filter(statut='a_relancer').count()
        
        # Calcul du taux de transformation des prospections
        try:
            prospections_acceptees = context['nb_prospections_acceptees']
            total_prospections = context['total_prospections']
            
            context['taux_transformation_prospections'] = (
                (prospections_acceptees / total_prospections) * 100
                if total_prospections > 0 else 0
            )
        except:
            context['taux_transformation_prospections'] = 0
        
        # Prospections par statut (détails pour graphiques)
        context['prospections_par_statut'] = Prospection.objects.values('statut').annotate(
            total=Count('id')
        )
        
        # Prospections par statut (complet avec tous les statuts possibles)
        statuts_db = {
            item['statut']: item['total']
            for item in Prospection.objects.values('statut').annotate(total=Count('id'))
        }
        
        prospections_par_statut_complet = []
        for key, label in PROSPECTION_STATUS_CHOICES:
            prospections_par_statut_complet.append({
                'statut': key,
                'label': label,
                'total': statuts_db.get(key, 0)
            })
        
        context['prospections_par_statut_complet'] = prospections_par_statut_complet
        
        # Prospections par objectif
        context['prospections_par_objectif'] = Prospection.objects.values('objectif').annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Nombre total d'entreprises
        context['total_entreprises'] = Company.objects.count()
        
        # Entreprises avec au moins une prospection
        context['entreprises_avec_prospections'] = Company.objects.annotate(
            nb_prospections=Count('prospections')
        ).filter(
            nb_prospections__gt=0
        ).order_by('-nb_prospections')[:10]
    
    def _add_event_stats(self, context):
        """
        Ajoute les statistiques d'événements.
        
        Args:
            context: Dictionnaire de contexte à enrichir
        """
        # Événements par type
        context['evenements_par_type'] = Evenement.objects.values('type_evenement').annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Récupération du nombre total d'événements par centre + détails par type
        evenements_par_centre = Centre.objects.annotate(
            total_evenements=Count('formations__evenements', distinct=True)
        )
        
        details_evenements_par_centre = []
        for centre in evenements_par_centre:
            evenements = Evenement.objects.filter(
                formation__centre=centre
            ).values('type_evenement').annotate(
                total=Count('id')
            ).order_by('-total')
            
            details_evenements_par_centre.append({
                'centre': centre,
                'total_evenements': centre.total_evenements,
                'evenements': evenements
            })
        
        context['evenements_par_centre'] = details_evenements_par_centre
    
    def _add_recent_activity(self, context):
        """
        Ajoute les éléments d'activité récente au contexte.
        
        Args:
            context: Dictionnaire de contexte à enrichir
        """
        # Derniers commentaires des formations
        context['derniers_commentaires'] = Commentaire.objects.select_related(
            'formation', 'utilisateur'
        ).order_by('-created_at')[:5]

    def _add_vae_jury_stats(self, context):
        """
        Ajoute les statistiques globales sur les VAE et les Jurys.

        Args:
            context: Dictionnaire de contexte à enrichir
        """
        annee = timezone.now().year

        # VAE
        context['total_vae'] = VAE.objects.count()
        context['vae_en_cours'] = VAE.objects.exclude(statut__in=['terminee', 'abandonnee']).count()

        # Jurys réalisés cette année
        context['total_jurys'] = SuiviJury.objects.aggregate(
            total=Sum('jurys_realises')
        )['total'] or 0

        context['jurys_realises_annee'] = SuiviJury.objects.filter(annee=annee).aggregate(
            total=Sum('jurys_realises')
        )['total'] or 0

        # Objectif annuel global via les centres
        objectif = sum(c.objectif_annuel_jury or 0 for c in Centre.objects.all())
        context['objectif_annuel_jury'] = objectif

        if objectif > 0:
            context['taux_objectif_jury'] = round((context['jurys_realises_annee'] / objectif) * 100, 1)
        else:
            context['taux_objectif_jury'] = 0
    
    def _add_stats_cards(self, context):
        """
        Ajoute les cartes de statistiques pour l'en-tête du dashboard.
        
        Args:
            context: Dictionnaire de contexte à enrichir
        """
        context['stats'] = [
            (context['total_formations'], "Formations", "primary", "fa-graduation-cap"),
            (context['total_candidats'], "Candidats", "secondary", "fa-users"),
            (context['total_entretiens'], "Entretiens", "warning", "fa-handshake"),
            (context['total_inscrits'], "Inscrits", "success", "fa-user-check"),
            (context['total_places_prevues'], "Places prévues", "info", "fa-calendar-alt"),
            (context['total_places_restantes'], "Places restantes", "danger", "fa-calendar-times"),
        ]

        


class StatsAPIView(View):
    """
    API pour récupérer les statistiques dynamiques du Dashboard.
    
    Cette vue fournit des points d'API pour alimenter les graphiques et visualisations
    qui nécessitent des données actualisées ou filtrées dynamiquement.
    """
    
    def get(self, request, *args, **kwargs):
        """
        Traite les requêtes GET pour récupérer différentes statistiques.
        
        Args:
            request: Requête HTTP
            *args, **kwargs: Arguments supplémentaires
            
        Returns:
            JsonResponse: Réponse JSON avec les données demandées
        """
        action = request.GET.get('action')
        logger.debug(f"StatsAPIView: Action demandée: {action}")
        
        try:
            if action == 'formations_par_statut':
                return self.formations_par_statut()
            elif action == 'evolution_formations':
                return self.evolution_formations(request)
            elif action == 'formations_par_type':
                return self.formations_par_type()
            else:
                logger.warning(f"StatsAPIView: Action non reconnue: {action}")
                return JsonResponse({'error': 'Action non reconnue'}, status=400)
        except Exception as e:
            logger.error(f"StatsAPIView: Erreur lors du traitement de l'action {action}: {str(e)}", exc_info=True)
            return JsonResponse({'error': f'Erreur serveur: {str(e)}'}, status=500)

    def formations_par_statut(self):
        """
        Renvoie le nombre de formations par statut avec leur taux moyen d'occupation.
        
        Returns:
            JsonResponse: Statistiques des formations par statut
        """
        statuts = Statut.objects.annotate(
            nb_formations=Count('formations'),
            taux_moyen=Coalesce(
                Avg(
                    100.0 * (F('formations__inscrits_crif') + F('formations__inscrits_mp')) /
                    Coalesce(F('formations__prevus_crif') + F('formations__prevus_mp'), Value(1))
                ),
                Value(0.0),
                output_field=FloatField()
            )
        ).values('nom', 'nb_formations', 'taux_moyen', 'couleur')
        
        logger.debug(f"StatsAPIView: {statuts.count()} statuts récupérés")
        return JsonResponse({'statuts': list(statuts)})

    def formations_par_type(self):
        """
        Renvoie le nombre de formations par type d'offre.
        
        Returns:
            JsonResponse: Statistiques des formations par type d'offre
        """
        types = TypeOffre.objects.annotate(
            nb_formations=Count('formations'),
            nb_inscrits=Sum(F('formations__inscrits_crif') + F('formations__inscrits_mp')),
            nb_prevus=Sum(F('formations__prevus_crif') + F('formations__prevus_mp'))
        ).values('nom', 'autre', 'nb_formations', 'nb_inscrits', 'nb_prevus', 'couleur')
        
        # Traitement des types personnalisés (Autre)
        types_list = []
        for t in types:
            if t['nom'] == TypeOffre.AUTRE and t['autre']:
                t['nom_display'] = t['autre']
            else:
                # Récupérer le display name depuis les choices
                for code, label in TypeOffre.TYPE_OFFRE_CHOICES:
                    if code == t['nom']:
                        t['nom_display'] = label
                        break
                else:
                    t['nom_display'] = t['nom']
            
            # Sécurisation des valeurs None
            t['nb_inscrits'] = t['nb_inscrits'] or 0
            t['nb_prevus'] = t['nb_prevus'] or 0
            
            types_list.append(t)
        
        logger.debug(f"StatsAPIView: {len(types_list)} types d'offre récupérés")
        return JsonResponse({'types': types_list})

    def evolution_formations(self, request):
        """
        Renvoie l'évolution du nombre de formations et d'inscrits par période.
        
        Args:
            request: Requête HTTP avec paramètres de filtrage
            
        Returns:
            JsonResponse: Données d'évolution temporelle
        """
        date_limite = timezone.now().date() - timedelta(days=365)
        periode = request.GET.get('periode', 'mois')
        
        # Récupérer l'historique des formations
        query = HistoriqueFormation.objects.filter(
            created_at__gte=date_limite
        ).select_related('formation')
        
        # Définir comment obtenir la période selon le choix
        result = {}
        for historique in query:
            created_at = historique.created_at
            
            # Détermination de la clé pour regrouper par période
            if periode == 'semaine':
                # Obtenir année et semaine
                year, week_num, _ = created_at.isocalendar()
                key = f"{year}-{week_num:02d}"
                label = f"Sem {week_num}, {year}"
            elif periode == 'annee':
                # Obtenir année
                year = created_at.year
                key = str(year)
                label = str(year)
            else:  # mois par défaut
                # Obtenir année et mois
                year = created_at.year
                month = created_at.month
                key = f"{year}-{month:02d}"
                label = f"{month:02d}/{year}"
            
            # Initialisation de l'entrée dans le dictionnaire de résultats
            if key not in result:
                result[key] = {
                    'periode_evolution': key,
                    'label': label,
                    'nb_formations': 0,
                    'nb_inscrits': 0,
                    'total_candidats': 0,
                    'total_entretiens': 0,
                    'taux_saturation': 0,
                    'taux_transformation': 0,
                    'count': 0  # Pour calculer des moyennes
                }
            
            # Incrémenter les compteurs
            result[key]['nb_formations'] += 1
            
            # Calcul des statistiques d'inscription
            inscrits_total = 0
            candidats = 0
            entretiens = 0
            
            # Récupération des inscrits depuis l'historique ou la formation
            if hasattr(historique, 'inscrits_total') and historique.inscrits_total is not None:
                inscrits_total = historique.inscrits_total
            elif historique.formation:
                inscrits_total = (
                    getattr(historique.formation, 'inscrits_crif', 0) or 0 +
                    getattr(historique.formation, 'inscrits_mp', 0) or 0
                )
            
            result[key]['nb_inscrits'] += inscrits_total
            
            # Récupération des candidats et entretiens
            if historique.formation:
                candidats = getattr(historique.formation, 'nombre_candidats', 0) or 0
                entretiens = getattr(historique.formation, 'nombre_entretiens', 0) or 0
                result[key]['total_candidats'] += candidats
                result[key]['total_entretiens'] += entretiens
            
            # Calcul du taux de saturation
            if hasattr(historique, 'saturation') and historique.saturation is not None:
                result[key]['taux_saturation'] += historique.saturation
                result[key]['count'] += 1
            elif historique.formation:
                # Calcul à partir des données de la formation
                prevus_total = (
                    getattr(historique.formation, 'prevus_crif', 0) or 0 +
                    getattr(historique.formation, 'prevus_mp', 0) or 0
                )
                if prevus_total > 0:
                    saturation = (inscrits_total / prevus_total) * 100
                    result[key]['taux_saturation'] += saturation
                    result[key]['count'] += 1
            
            # Calcul du taux de transformation
            if candidats > 0 and inscrits_total > 0:
                transformation = (inscrits_total / candidats) * 100
                result[key]['taux_transformation'] += transformation
                # Pas besoin d'incrémenter count car déjà fait pour la saturation
        
        # Calcul des moyennes et préparation du résultat final
        evolution_list = []
        for key, data in result.items():
            if data['count'] > 0:
                data['taux_saturation'] = round(data['taux_saturation'] / data['count'], 1)
                data['taux_transformation'] = round(data['taux_transformation'] / data['count'], 1)
            del data['count']  # Suppression du compteur technique
            evolution_list.append(data)
        
        # Tri par période
        evolution_list.sort(key=lambda x: x['periode_evolution'])
        
        logger.debug(f"StatsAPIView: {len(evolution_list)} périodes d'évolution trouvées pour '{periode}'")
        return JsonResponse({'evolution': evolution_list})