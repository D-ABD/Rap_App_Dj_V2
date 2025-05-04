from django.db import models, transaction
from django.utils import timezone
from django.db.models import Sum
from datetime import date

from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ..models.centres import Centre 

import logging
logger = logging.getLogger(__name__)

# Constante pour l'affichage des noms de mois
NOMS_MOIS = {
    1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
    5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
    9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
}

NOMS_ATELIERS = {
    "AT1": "Atelier 1",
    "AT2": "Atelier 2",
    "AT3": "Atelier 3",
    "AT4": "Atelier 4",
    "AT5": "Atelier 5",
    "AT6": "Atelier 6",
    "AT_Autre": "Autre atelier"
}

NUM_DEPARTEMENTS = {
    "75": "75",
    "77": "77",
    "78": "78",
    "91": "91",
    "92": "92",
    "93": "93",
    "94": "94",
    "95": "95"

}

class Semaine(models.Model):
    """Centres et périodes"""
    centre = models.ForeignKey(Centre, on_delete=models.CASCADE, null=True, blank=True)
    annee = models.PositiveIntegerField()
    mois = models.PositiveIntegerField()
    numero_semaine = models.PositiveIntegerField()
    date_debut_semaine = models.DateField()
    date_fin_semaine = models.DateField()

    """Objectifs"""
    objectif_annuel_prepa = models.PositiveIntegerField(default=0)
    objectif_mensuel_prepa = models.PositiveIntegerField(default=0)
    objectif_hebdo_prepa = models.PositiveIntegerField(default=0)

    """Remplissage"""
    nombre_places_ouvertes = models.PositiveIntegerField(default=0)
    nombre_prescriptions = models.PositiveIntegerField(default=0)
    nombre_presents_ic = models.PositiveIntegerField(default=0)
    nombre_adhesions = models.PositiveIntegerField(default=0)

    """Départements"""
    departements = models.JSONField(default=dict, blank=True, null=True)

    """Ateliers"""
    nombre_par_atelier = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        ordering = ['-date_debut_semaine']
        unique_together = ['numero_semaine', 'annee', 'centre']
        verbose_name = "Semaine"
        verbose_name_plural = "Semaines"

    def __str__(self):
        centre_nom = self.centre.nom if self.centre else "Sans centre"
        return f"Semaine {self.numero_semaine} ({self.date_debut_semaine} au {self.date_fin_semaine}) - {centre_nom}"

    def taux_adhesion(self):
        """
        Calcule le taux d'adhésion (rapport entre le nombre d'adhésions et le nombre de présents)
        """
        return (self.nombre_adhesions / self.nombre_presents_ic) * 100 if self.nombre_presents_ic else 0

    def taux_transformation(self):
        return (self.nombre_adhesions / self.nombre_presents_ic) * 100 if self.nombre_presents_ic else 0

    def pourcentage_objectif(self):
        return (self.nombre_adhesions / self.objectif_hebdo_prepa) * 100 if self.objectif_hebdo_prepa else 0

    def total_adhesions_departement(self, code_dept):
        return self.departements.get(code_dept, 0) if self.departements else 0

    def total_par_atelier(self, nom_atelier):
        return self.nombre_par_atelier.get(nom_atelier, 0) if self.nombre_par_atelier else 0

    def nom_mois(self):
        return NOMS_MOIS.get(self.mois, f"Mois {self.mois}")

    @classmethod
    def creer_semaines_annee(cls, centre, annee):
        """
        Crée toutes les semaines de l'année pour un centre donné
        """
        from datetime import timedelta

        # Trouve le lundi de la première semaine de l'année
        premier_janvier = date(annee, 1, 1)
        premier_lundi = premier_janvier - timedelta(days=premier_janvier.weekday()) \
            if premier_janvier.weekday() != 0 else premier_janvier

        semaine_debut = premier_lundi
        nb_semaines_crees = 0

        while semaine_debut.year <= annee:
            semaine_fin = semaine_debut + timedelta(days=6)
            semaine_num = semaine_debut.isocalendar()[1]
            mois = semaine_debut.month

            # Si la semaine dépasse l'année, on arrête
            if semaine_debut.year > annee:
                break

            # Empêche les doublons
            _, created = cls.objects.get_or_create(
                centre=centre,
                annee=annee,
                numero_semaine=semaine_num,
                defaults={
                    'mois': mois,
                    'date_debut_semaine': semaine_debut,
                    'date_fin_semaine': semaine_fin,
                }
            )
            if created:
                nb_semaines_crees += 1

            # Passe à la semaine suivante
            semaine_debut += timedelta(days=7)

        return nb_semaines_crees
    
    @classmethod
    def creer_semaine_courante(cls, centre):
        """
        Crée ou récupère la semaine courante pour un centre donné
        """
        from datetime import datetime
        
        # Obtenir la date courante et son numéro de semaine ISO
        date_courante = datetime.now().date()
        annee, semaine, _ = date_courante.isocalendar()
        
        # Trouver le lundi et le dimanche de la semaine courante
        lundi = date_courante - timedelta(days=date_courante.weekday())
        dimanche = lundi + timedelta(days=6)
        
        # Essayer de récupérer la semaine existante, sinon la créer
        try:
            return cls.objects.get(
                centre=centre,
                annee=annee,
                numero_semaine=semaine
            )
        except cls.DoesNotExist:
            return cls.objects.create(
                centre=centre,
                annee=annee,
                mois=lundi.month,
                numero_semaine=semaine,
                date_debut_semaine=lundi,
                date_fin_semaine=dimanche
            )
    
    @classmethod
    def stats_globales_par_atelier(cls, annee):
        """
        Calcule le total par type d'atelier pour toutes les semaines de l'année donnée
        """
        stats = {code: 0 for code in NOMS_ATELIERS.keys()}
        
        semaines = cls.objects.filter(annee=annee).values_list('nombre_par_atelier', flat=True)
        
        for semaine_data in semaines:
            if semaine_data:
                for code, valeur in semaine_data.items():
                    if code in stats:
                        stats[code] += valeur
        
        # Transforme en liste lisible (ex. pour un template)
        resultats = [
            {
                "code": code,
                "nom": NOMS_ATELIERS.get(code, code),
                "total": total
            }
            for code, total in stats.items()
        ]
        
        return sorted(resultats, key=lambda x: x['nom'])
    
    @property
    def ateliers_nommés(self):
        if not self.nombre_par_atelier:
            return []
        return [
            {
                "code": code,
                "nom": NOMS_ATELIERS.get(code, code),
                "valeur": valeur
            }
            for code, valeur in self.nombre_par_atelier.items()
        ]

    def total_par_atelier(self, code):
        return self.nombre_par_atelier.get(code, 0) if self.nombre_par_atelier else 0


class PrepaCompGlobal(models.Model):
    """Modèle pour gérer les bilans globaux annuels par centre"""
    centre = models.ForeignKey(Centre, on_delete=models.CASCADE, null=True, blank=True)
    annee = models.PositiveIntegerField()
    total_candidats = models.PositiveIntegerField(default=0)
    total_prescriptions = models.PositiveIntegerField(default=0)
    adhesions = models.PositiveIntegerField(default=0)
    total_presents = models.PositiveIntegerField(default=0)
    total_places_ouvertes = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['centre', 'annee']
        verbose_name = "Bilan global PrépaComp"
        verbose_name_plural = "Bilans globaux PrépaComp"
    
    def __str__(self):
        return f"Bilan {self.annee} - {self.centre.nom}"
    
    @classmethod
    def objectif_annuel_global(cls):
        """Retourne l'objectif annuel global pour tous les centres"""
        return Centre.objects.aggregate(total=Sum('objectif_annuel_prepa'))['total'] or 0
    
    @classmethod
    def objectif_hebdo_global(cls, annee):
        """Retourne l'objectif hebdomadaire global pour l'année donnée"""
        return Centre.objects.aggregate(total=Sum('objectif_hebdomadaire_prepa'))['total'] or 0
    
    @classmethod
    def objectifs_par_centre(cls, annee):
        """Retourne les objectifs annuels, mensuels et hebdomadaires par centre"""
        centres = Centre.objects.all()
        resultats = []
        
        for centre in centres:
            # Objectif défini dans les paramètres du centre
            objectif_annuel = centre.objectif_annuel_prepa or 0
            objectif_hebdo = centre.objectif_hebdomadaire_prepa or 0
            
            # Calcul de l'objectif mensuel (basé sur 4 semaines par mois)
            objectif_mensuel = objectif_hebdo * 4
            
            # Objectif réellement atteint (calculé à partir des semaines)
            adhesions_reelles = Semaine.objects.filter(
                centre=centre, 
                annee=annee
            ).aggregate(total=Sum('nombre_adhesions'))['total'] or 0
            
            # Calcul du pourcentage de réalisation
            pourcentage = 0
            if objectif_annuel > 0:
                pourcentage = (adhesions_reelles / objectif_annuel) * 100
                
            # Calcul du pourcentage de réalisation mensuel
            pourcentage_mensuel = 0
            if objectif_mensuel > 0:
                # Pour simplifier, on utilise le total d'adhésions sur l'année divisé par (nb de mois écoulés * objectif mensuel)
                # Cette logique pourrait être affinée pour une analyse plus précise par mois
                mois_actuel = min(timezone.now().month, 12) if annee == timezone.now().year else 12
                pourcentage_mensuel = (adhesions_reelles / (objectif_mensuel * mois_actuel)) * 100
            
            resultats.append({
                'centre_id': centre.id,
                'centre_nom': centre.nom,
                'objectif_annuel_defini': objectif_annuel,
                'objectif_mensuel': objectif_mensuel,
                'objectif_hebdo': objectif_hebdo,
                'objectif_calculé': adhesions_reelles,
                'pourcentage': pourcentage,
                'pourcentage_mensuel': pourcentage_mensuel,
                'ecart': adhesions_reelles - objectif_annuel,
            })
        
        return resultats
    
    @classmethod
    def stats_par_mois(cls, annee, centre=None):
        """Retourne les statistiques mensuelles pour l'année donnée"""
        stats_mois = []
        
        # Base de la requête
        base_query = Semaine.objects.filter(annee=annee)
        if centre:
            base_query = base_query.filter(centre=centre)
        
        # Grouper par mois et calculer les totaux
        for mois in range(1, 13):
            stats_mensuelles = base_query.filter(mois=mois).aggregate(
                places=Sum('nombre_places_ouvertes'),
                prescriptions=Sum('nombre_prescriptions'),
                presents=Sum('nombre_presents_ic'),
                adhesions=Sum('nombre_adhesions')
            )
            
            # Calculer les taux
            total_presents = stats_mensuelles['presents'] or 0
            total_adhesions = stats_mensuelles['adhesions'] or 0
            
            # Taux de transformation (adhésions / présents)
            taux_transformation = (
                (total_adhesions / total_presents * 100) 
                if total_presents else 0
            )
            
            # Taux d'adhésion (identique au taux de transformation dans ce contexte)
            taux_adhesion = taux_transformation
            
            stats_mois.append({
                'mois_num': mois,
                'mois_nom': NOMS_MOIS[mois],
                'places': stats_mensuelles['places'] or 0,
                'prescriptions': stats_mensuelles['prescriptions'] or 0,
                'presents': total_presents,
                'adhesions': total_adhesions,
                'taux_transformation': round(taux_transformation, 1),
                'taux_adhesion': round(taux_adhesion, 1)
            })
        
        return stats_mois           
    
    """
    Méthodes ajoutées au modèle PrepaCompGlobal pour supporter les templates
    """

    def taux_transformation(self):
        """
        Calcule le taux de transformation (adhésions / présents)
        """
        return (self.adhesions / self.total_presents) * 100 if self.total_presents else 0

    def taux_objectif_annee(self):
        """
        Calcule le pourcentage de réalisation de l'objectif annuel
        """
        if not self.centre.objectif_annuel_prepa:
            return 0
        return (self.adhesions / self.centre.objectif_annuel_prepa) * 100
    @classmethod
    def stats_par_mois(cls, annee, centre=None):
        """Retourne les statistiques mensuelles pour l'année donnée"""
        stats_mois = []
        
        # Base de la requête
        base_query = Semaine.objects.filter(annee=annee)
        if centre:
            base_query = base_query.filter(centre=centre)
        
        # Récupérer l'objectif hebdomadaire du centre
        objectif_hebdo = 0
        if centre:
            objectif_hebdo = centre.objectif_hebdomadaire_prepa or 0
        
        # Grouper par mois et calculer les totaux
        for mois in range(1, 13):
            # Calculer le nombre de semaines dans le mois (approximatif)
            nb_semaines = 4  # Par défaut
            
            # Une méthode plus précise serait de compter les semaines réelles dans le mois
            semaines_du_mois = base_query.filter(mois=mois).count()
            if semaines_du_mois > 0:
                nb_semaines = semaines_du_mois
            
            stats_mensuelles = base_query.filter(mois=mois).aggregate(
                places=Sum('nombre_places_ouvertes'),
                prescriptions=Sum('nombre_prescriptions'),
                presents=Sum('nombre_presents_ic'),
                adhesions=Sum('nombre_adhesions')
            )
            
            # Calculer les taux
            total_presents = stats_mensuelles['presents'] or 0
            total_adhesions = stats_mensuelles['adhesions'] or 0
            
            # Taux de transformation (adhésions / présents)
            taux_transformation = (
                (total_adhesions / total_presents * 100) 
                if total_presents else 0
            )
            
            # Objectifs et atteintes
            objectif_mensuel = objectif_hebdo * nb_semaines
            
            # Calcul des pourcentages d'atteinte
            pourcentage_objectif_hebdo = 0
            if objectif_hebdo > 0:
                pourcentage_objectif_hebdo = (total_adhesions / objectif_hebdo) * 100
                
            pourcentage_objectif_mensuel = 0
            if objectif_mensuel > 0:
                pourcentage_objectif_mensuel = (total_adhesions / objectif_mensuel) * 100
            
            stats_mois.append({
                'mois_num': mois,
                'mois_nom': NOMS_MOIS[mois],
                'places': stats_mensuelles['places'] or 0,
                'prescriptions': stats_mensuelles['prescriptions'] or 0,
                'presents': total_presents,
                'adhesions': total_adhesions,
                'taux_transformation': round(taux_transformation, 1),
                'objectif_hebdo': objectif_hebdo,
                'objectif_mensuel': objectif_mensuel,
                'pourcentage_objectif_hebdo': round(pourcentage_objectif_hebdo, 1),
                'pourcentage_objectif_mensuel': round(pourcentage_objectif_mensuel, 1),
                'nb_semaines': nb_semaines
            })
        
        return stats_mois
    
