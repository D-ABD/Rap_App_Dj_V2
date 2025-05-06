from django.db import models, transaction
from django.utils import timezone
from django.db.models import Sum
from datetime import date

from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from .base import BaseModel

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

class Semaine(BaseModel):
    """
    Modèle représentant une semaine de suivi pour un centre de formation.
    
    Ce modèle permet de suivre les statistiques hebdomadaires de présence, 
    d'adhésion et de répartition par atelier et par département pour chaque centre.
    
    Pour la sérialisation, ce modèle est important car:
    - Il contient des données de suivi temporel (semaine/mois/année)
    - Il a des relations avec le modèle Centre
    - Il possède des champs JSON pour les statistiques détaillées
    - Il inclut des méthodes de calcul pour les taux et pourcentages
    
    Relations:
    - Lié à un centre (ForeignKey vers Centre)
    
    Fonctionnalités principales:
    - Suivi hebdomadaire des objectifs et résultats par centre
    - Répartition des participants par atelier et département
    - Calcul des taux d'adhésion et de transformation
    """
    
    # Centres et périodes
    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name="Centre de formation",
        help_text="Centre auquel cette semaine est rattachée"
    )
    annee = models.PositiveIntegerField(
        verbose_name="Année",
        help_text="Année concernée (ex: 2023)"
    )
    mois = models.PositiveIntegerField(
        verbose_name="Mois",
        help_text="Numéro du mois (1-12)"
    )
    numero_semaine = models.PositiveIntegerField(
        verbose_name="Numéro de semaine",
        help_text="Numéro de la semaine dans l'année (1-53)"
    )
    date_debut_semaine = models.DateField(
        verbose_name="Date de début",
        help_text="Premier jour de la semaine (lundi)"
    )
    date_fin_semaine = models.DateField(
        verbose_name="Date de fin",
        help_text="Dernier jour de la semaine (dimanche)"
    )

    # Objectifs
    objectif_annuel_prepa = models.PositiveIntegerField(
        default=0,
        verbose_name="Objectif annuel prépa",
        help_text="Objectif annuel pour la préparation aux compétences"
    )
    objectif_mensuel_prepa = models.PositiveIntegerField(
        default=0,
        verbose_name="Objectif mensuel prépa",
        help_text="Objectif mensuel pour la préparation aux compétences"
    )
    objectif_hebdo_prepa = models.PositiveIntegerField(
        default=0,
        verbose_name="Objectif hebdomadaire prépa",
        help_text="Objectif hebdomadaire pour la préparation aux compétences"
    )

    # Remplissage
    nombre_places_ouvertes = models.PositiveIntegerField(
        default=0,
        verbose_name="Places ouvertes",
        help_text="Nombre de places disponibles pour la semaine"
    )
    nombre_prescriptions = models.PositiveIntegerField(
        default=0,
        verbose_name="Prescriptions",
        help_text="Nombre de prescriptions reçues pour la semaine"
    )
    nombre_presents_ic = models.PositiveIntegerField(
        default=0,
        verbose_name="Présents IC",
        help_text="Nombre de personnes présentes pour l'Information Collective"
    )
    nombre_adhesions = models.PositiveIntegerField(
        default=0,
        verbose_name="Adhésions",
        help_text="Nombre d'adhésions cette semaine"
    )

    # Départements
    departements = models.JSONField(
        default=dict, 
        blank=True, 
        null=True,
        verbose_name="Répartition par département",
        help_text="Dictionnaire avec codes départements comme clés et nombres comme valeurs"
    )

    # Ateliers
    nombre_par_atelier = models.JSONField(
        default=dict, 
        blank=True, 
        null=True,
        verbose_name="Répartition par atelier",
        help_text="Dictionnaire avec codes ateliers comme clés et nombres comme valeurs"
    )

    class Meta:
        ordering = ['-date_debut_semaine']
        unique_together = ['numero_semaine', 'annee', 'centre']
        verbose_name = "Semaine"
        verbose_name_plural = "Semaines"
        indexes = [
            models.Index(fields=['annee', 'mois']),
            models.Index(fields=['centre', 'annee']),
            models.Index(fields=['date_debut_semaine']),
        ]

    def __str__(self):
        """
        Représentation textuelle de la semaine.
        
        Returns:
            str: Description de la semaine avec période et centre
        """
        centre_nom = self.centre.nom if self.centre else "Sans centre"
        return f"Semaine {self.numero_semaine} ({self.date_debut_semaine} au {self.date_fin_semaine}) - {centre_nom}"

    def taux_adhesion(self) -> float:
        """
        Calcule le taux d'adhésion (rapport entre le nombre d'adhésions et le nombre de présents).
        
        Returns:
            float: Pourcentage d'adhésion (0-100)
        """
        return (self.nombre_adhesions / self.nombre_presents_ic) * 100 if self.nombre_presents_ic else 0

    def taux_transformation(self) -> float:
        """
        Calcule le taux de transformation (rapport entre adhésions et présents).
        Dans ce contexte, identique au taux d'adhésion.
        
        Returns:
            float: Pourcentage de transformation (0-100)
        """
        return self.taux_adhesion()  # Réutilisation de la méthode taux_adhesion


    def pourcentage_objectif(self) -> float:
        """
        Calcule le pourcentage de réalisation de l'objectif hebdomadaire.
        
        Returns:
            float: Pourcentage de réalisation (0-100+)
        """
        return (self.nombre_adhesions / self.objectif_hebdo_prepa) * 100 if self.objectif_hebdo_prepa else 0

    def total_adhesions_departement(self, code_dept: str) -> int:
        """
        Retourne le nombre d'adhésions pour un département spécifique.
        
        Args:
            code_dept (str): Code du département (ex: "75", "93")
            
        Returns:
            int: Nombre d'adhésions pour ce département
        """
        return self.departements.get(code_dept, 0) if self.departements else 0

    def total_par_atelier(self, code_atelier):
        """
        Retourne le nombre de participants pour un atelier donné.
        
        Args:
            code_atelier (str): Code de l'atelier (ex: "AT1", "AT2", etc.)
            
        Returns:
            int: Nombre de participants, 0 si l'atelier n'existe pas
        """
        return self.nombre_par_atelier.get(code_atelier, 0) if self.nombre_par_atelier else 0

    def nom_mois(self):
        """
        Retourne le nom du mois en français.
        
        Returns:
            str: Nom du mois correspondant au numéro de mois de la semaine
        """
        return NOMS_MOIS.get(self.mois, f"Mois {self.mois}")

    @property
    def ateliers_nommés(self) -> list[dict]:
        """
        Retourne la liste des ateliers avec leurs noms et valeurs.
        Utile pour la sérialisation et l'affichage.
        
        Returns:
            list: Liste des ateliers au format [{"code": code, "nom": nom, "valeur": valeur}, ...]
        """
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

    @classmethod
    def creer_semaines_annee(cls, centre, annee: int) -> int:
        """
        Crée toutes les semaines de l'année pour un centre donné.
        
        Cette méthode initialise automatiquement les enregistrements de semaines
        pour un centre et une année spécifiques. Utile pour la préparation des données.
        
        Args:
            centre (Centre): Centre pour lequel créer les semaines
            annee (int): Année concernée
            
        Returns:
            int: Nombre de semaines créées
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
        Crée ou récupère la semaine courante pour un centre donné.
        
        Utile pour initialiser rapidement la semaine en cours.
        
        Args:
            centre (Centre): Centre pour lequel créer/récupérer la semaine
            
        Returns:
            Semaine: Instance de la semaine courante
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
    def stats_globales_par_atelier(cls, annee: int) -> list[dict]:
        """
        Calcule le total par type d'atelier pour toutes les semaines de l'année donnée.
        
        Cette méthode agrège les données de tous les centres pour l'année spécifiée.
        
        Args:
            annee (int): Année pour laquelle calculer les statistiques
            
        Returns:
            list: Liste des statistiques par atelier (avec code, nom et total)
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
    def is_courante(self) -> bool:
        """
        Détermine si cette semaine correspond à la semaine courante.
        
        Utile pour l'interface utilisateur (badges "Semaine en cours") 
        et pour les rapports dynamiques.
        
        Returns:
            bool: True si cette semaine est la semaine courante, False sinon
        """
        from datetime import date
        
        # Obtenir la date du jour
        aujourdhui = date.today()
        
        # Vérifier si la date du jour est comprise entre le début et la fin de la semaine
        return self.date_debut_semaine <= aujourdhui <= self.date_fin_semaine

from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone
from ..models.centres import Centre

class PrepaCompGlobal(BaseModel):
    """
    Bilan global annuel PrépaComp pour un centre de formation.

    Ce modèle permet de suivre les statistiques annuelles et les objectifs
    pour la préparation aux compétences et les jurys, avec des agrégations 
    sur les candidatures, les présences, les adhésions et les places ouvertes.

    Il remplace les objectifs stockés auparavant dans le modèle Centre.
    """

    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name="Centre de formation",
        help_text="Centre auquel ce bilan est rattaché"
    )

    annee = models.PositiveIntegerField(
        verbose_name="Année",
        help_text="Année concernée par ce bilan"
    )

    # Totaux suivis
    total_candidats = models.PositiveIntegerField(
        default=0,
        verbose_name="Total candidats",
        help_text="Nombre total de candidats sur l'année"
    )

    total_prescriptions = models.PositiveIntegerField(
        default=0,
        verbose_name="Total prescriptions",
        help_text="Nombre total de prescriptions sur l'année"
    )

    adhesions = models.PositiveIntegerField(
        default=0,
        verbose_name="Adhésions",
        help_text="Nombre total d'adhésions sur l'année"
    )

    total_presents = models.PositiveIntegerField(
        default=0,
        verbose_name="Total présents",
        help_text="Nombre total de personnes présentes sur l'année"
    )

    total_places_ouvertes = models.PositiveIntegerField(
        default=0,
        verbose_name="Total places ouvertes",
        help_text="Nombre total de places ouvertes sur l'année"
    )

    # 🎯 Objectifs prépa
    objectif_annuel_prepa = models.PositiveIntegerField(
        default=0,
        verbose_name="Objectif annuel prépa",
        help_text="Objectif annuel d'adhésions pour la préparation aux compétences"
    )

    objectif_hebdomadaire_prepa = models.PositiveIntegerField(
        default=0,
        verbose_name="Objectif hebdomadaire prépa",
        help_text="Objectif hebdomadaire d'adhésions pour la prépa compétences"
    )

    # 🎯 Objectifs jury
    objectif_annuel_jury = models.PositiveIntegerField(
        default=0,
        verbose_name="Objectif annuel jury",
        help_text="Objectif annuel pour les jurys"
    )

    objectif_mensuel_jury = models.PositiveIntegerField(
        default=0,
        verbose_name="Objectif mensuel jury",
        help_text="Objectif mensuel pour les jurys"
    )

    class Meta:
        unique_together = ['centre', 'annee']
        verbose_name = "Bilan global PrépaComp"
        verbose_name_plural = "Bilans globaux PrépaComp"
        indexes = [
            models.Index(fields=['centre', 'annee']),
            models.Index(fields=['annee']),
        ]

    def __str__(self):
        centre_nom = self.centre.nom if self.centre else 'Global'
        return f"Bilan {self.annee} - {centre_nom}"

    def clean(self):
        """
        Validation métier :
        - Vérifie que les objectifs hebdo sont cohérents avec l’annuel
        """
        if self.objectif_hebdomadaire_prepa and self.objectif_annuel_prepa:
            max_possible = self.objectif_hebdomadaire_prepa * 52
            if max_possible < self.objectif_annuel_prepa:
                raise ValidationError({
                    'objectif_annuel_prepa': "L'objectif hebdomadaire est trop faible pour atteindre l'objectif annuel."
                })

    def taux_transformation(self) -> float:
        """
        Taux de transformation annuel (adhésions / présents).
        """
        return (self.adhesions / self.total_presents) * 100 if self.total_presents else 0

    def taux_objectif_annee(self) -> float:
        """
        Pourcentage de réalisation de l’objectif annuel prépa.
        """
        return (self.adhesions / self.objectif_annuel_prepa) * 100 if self.objectif_annuel_prepa else 0

    @classmethod
    def objectif_annuel_global(cls) -> int:
        """
        Total des objectifs annuels prépa tous centres confondus.
        """
        return cls.objects.aggregate(total=Sum('objectif_annuel_prepa'))['total'] or 0

    @classmethod
    def objectif_hebdo_global(cls, annee: int) -> int:
        """
        Total des objectifs hebdomadaires prépa pour l’année donnée.
        """
        return cls.objects.filter(annee=annee).aggregate(
            total=Sum('objectif_hebdomadaire_prepa')
        )['total'] or 0
    
    @classmethod
    def objectifs_par_centre(cls, annee: int) -> list[dict]:
        """
        Retourne les objectifs annuels, mensuels et hebdomadaires par centre.
        
        Cette méthode calcule et compare les objectifs définis avec les résultats
        réels pour chaque centre.
        
        Args:
            annee (int): Année pour laquelle calculer les objectifs
            
        Returns:
            list: Liste des statistiques d'objectifs par centre
        """
        centres = Centre.objects.all()
        resultats = []
        
        for centre in centres:
            try:
                prepa = PrepaCompGlobal.objects.get(centre=centre, annee=annee)
            except PrepaCompGlobal.DoesNotExist:
                prepa = None

            objectif_annuel = prepa.objectif_annuel_prepa if prepa else 0
            objectif_hebdo = prepa.objectif_hebdomadaire_prepa if prepa else 0

            
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
    def stats_par_mois(cls, annee: int, centre=None) -> list[dict]:
        """
        Retourne les statistiques mensuelles pour l'année donnée.
        
        Cette méthode calcule les métriques clés par mois, avec un niveau
        de détail important sur les objectifs et les taux.
        
        Args:
            annee (int): Année pour laquelle calculer les statistiques
            centre (Centre, optional): Centre spécifique à filtrer, ou None pour tous
            
        Returns:
            list: Liste des statistiques mensuelles avec métriques détaillées
        """
        stats_mois = []
        
        # Base de la requête
        base_query = Semaine.objects.filter(annee=annee)
        if centre:
            base_query = base_query.filter(centre=centre)
        
        # Récupérer l'objectif hebdomadaire du centre
        objectif_hebdo = 0
        if centre:
            try:
                prepa = PrepaCompGlobal.objects.get(centre=centre, annee=annee)
                objectif_hebdo = prepa.objectif_hebdomadaire_prepa
            except PrepaCompGlobal.DoesNotExist:
                objectif_hebdo = 0

        
        # Grouper par mois et calculer les totaux
        for mois in range(1, 13):
            # Calculer le nombre de semaines dans le mois
            semaines_du_mois = base_query.filter(mois=mois).count()
            # Utilisation de 4 semaines par défaut si aucune semaine n'est trouvée dans le mois
            nb_semaines = semaines_du_mois if semaines_du_mois > 0 else 4  # Par défaut
            
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