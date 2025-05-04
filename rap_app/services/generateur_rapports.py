import time
from django.db.models import Count, Sum, F, Q
import logging

from ..models.rapports import Rapport
from ..models import Formation

logger = logging.getLogger(__name__)

class GenerateurRapport:
    """Service de génération des différents types de rapports."""

    def generer_rapport(type_rapport, date_debut, date_fin, **kwargs):
        debut_generation = time.time()
        logger.info(f"📊 Génération du rapport {type_rapport} ({date_debut} → {date_fin})")

        rapport = Rapport(
            nom=f"Rapport {dict(Rapport.TYPE_CHOICES).get(type_rapport, 'Inconnu')} du {date_debut} au {date_fin}",
            type_rapport=type_rapport,
            date_debut=date_debut,
            date_fin=date_fin,
            **{k: v for k, v in kwargs.items() if k in ['centre', 'type_offre', 'statut', 'format', 'utilisateur', 'periode']}
        )

        try:
            generateur = getattr(GenerateurRapport, f"_generer_{type_rapport}", None)
            if not generateur:
                logger.error(f"❌ Aucun générateur trouvé pour {type_rapport}")
                return None

            rapport.donnees = generateur(date_debut, date_fin, **kwargs)

            rapport.temps_generation = time.time() - debut_generation
            rapport.save()
            logger.info(f"✅ Rapport {rapport.nom} généré et sauvegardé en {rapport.temps_generation:.2f}s")

        except Exception as e:
            logger.error(f"❌ Erreur lors de la génération du rapport {type_rapport} : {str(e)}")
            return None

        return rapport
    
    @staticmethod
    def _generer_occupation(date_debut, date_fin, **kwargs):
        """Génère un rapport d'occupation des formations."""
        formations = Formation.objects.filter(
            Q(start_date__gte=date_debut, start_date__lte=date_fin) | 
            Q(end_date__gte=date_debut, end_date__lte=date_fin) |
            Q(start_date__isnull=True, end_date__gte=date_debut)
        )
        
        if 'centre' in kwargs and kwargs['centre']:
            formations = formations.filter(centre=kwargs['centre'])
        if 'type_offre' in kwargs and kwargs['type_offre']:
            formations = formations.filter(type_offre=kwargs['type_offre'])
        if 'statut' in kwargs and kwargs['statut']:
            formations = formations.filter(statut=kwargs['statut'])

        formations = formations.annotate(
            places_totales=F('prevus_crif') + F('prevus_mp'),
            inscrits_totaux=F('inscrits_crif') + F('inscrits_mp'),
            taux_remplissage=100 * (F('inscrits_crif') + F('inscrits_mp')) / (F('prevus_crif') + F('prevus_mp'))
        )

        stats = formations.aggregate(
            total_formations=Count('id'),
            total_places=Sum(F('prevus_crif') + F('prevus_mp')),
            total_inscrits=Sum(F('inscrits_crif') + F('inscrits_mp')),
        )

        stats['taux_moyen'] = (stats['total_inscrits'] / stats['total_places']) * 100 if stats['total_places'] else 0

        formations_data = [{
            'id': f.id,
            'nom': f.nom,
            'centre': f.centre.nom,
            'type_offre': f.type_offre.get_nom_display(),
            'statut': f.statut.get_nom_display(),
            'places_totales': f.places_totales,
            'inscrits_totaux': f.inscrits_totaux,
            'taux_remplissage': round(f.taux_remplissage, 2)
        } for f in formations]

        return {
            'statistiques': stats,
            'formations': formations_data
        }
