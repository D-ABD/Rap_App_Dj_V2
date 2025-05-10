from django.db import models, transaction
from django.utils import timezone
from django.db.models import Sum, F, Q, Avg, Count
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse
from django.utils.functional import cached_property
from datetime import date, timedelta

from .base import BaseModel
from .centres import Centre

import logging
logger = logging.getLogger(__name__)

# ----------------------------------------------------
# Signaux déplacés dans un fichier signals/
# ----------------------------------------------------


# Constantes pour l'affichage des noms de mois
NOMS_MOIS = {
    1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
    5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
    9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
}

# Constantes pour les noms d'ateliers
NOMS_ATELIERS = {
    "AT1": "Atelier 1",
    "AT2": "Atelier 2",
    "AT3": "Atelier 3",
    "AT4": "Atelier 4",
    "AT5": "Atelier 5",
    "AT6": "Atelier 6",
    "AT_Autre": "Autre atelier"
}

# Constantes pour les départements
NUM_DEPARTEMENTS = {
    "75": "75 - Paris",
    "77": "77 - Seine-et-Marne",
    "78": "78 - Yvelines",
    "91": "91 - Essonne",
    "92": "92 - Hauts-de-Seine",
    "93": "93 - Seine-Saint-Denis",
    "94": "94 - Val-de-Marne",
    "95": "95 - Val-d'Oise"
}


class SemaineManager(models.Manager):
    """
    Manager personnalisé pour le modèle Semaine.
    Fournit des méthodes utilitaires pour les requêtes courantes.
    """
    
    def semaine_courante(self, centre=None):
        """
        Récupère la semaine en cours, éventuellement filtrée par centre.
        
        Args:
            centre (Centre, optional): Centre à filtrer
            
        Returns:
            Semaine: La semaine courante ou None
        """
        today = date.today()
        queryset = self.filter(
            date_debut_semaine__lte=today,
            date_fin_semaine__gte=today
        )
        
        if centre:
            queryset = queryset.filter(centre=centre)
            
        return queryset.first()
    
    def par_centre_et_annee(self, centre, annee):
        """
        Récupère toutes les semaines d'un centre pour une année donnée.
        
        Args:
            centre (Centre): Centre concerné
            annee (int): Année à filtrer
            
        Returns:
            QuerySet: Semaines du centre pour l'année
        """
        return self.filter(centre=centre, annee=annee).order_by('numero_semaine')
    
    def par_mois(self, annee, mois, centre=None):
        """
        Récupère les semaines d'un mois donné.
        
        Args:
            annee (int): Année concernée
            mois (int): Mois (1-12)
            centre (Centre, optional): Centre à filtrer
            
        Returns:
            QuerySet: Semaines du mois
        """
        queryset = self.filter(annee=annee, mois=mois)
        
        if centre:
            queryset = queryset.filter(centre=centre)
            
        return queryset.order_by('numero_semaine')
    
    def avec_stats(self):
        """
        Ajoute des statistiques calculées aux semaines.
        
        Returns:
            QuerySet: Semaines avec statistiques
        """
        return self.annotate(
            taux_adhesion_calc=models.Case(
                models.When(
                    nombre_presents_ic__gt=0,
                    then=100 * F('nombre_adhesions') / F('nombre_presents_ic')
                ),
                default=0,
                output_field=models.FloatField()
            ),
            taux_transformation_calc=models.Case(
                models.When(
                    nombre_prescriptions__gt=0,
                    then=100 * F('nombre_adhesions') / F('nombre_prescriptions')
                ),
                default=0,
                output_field=models.FloatField()
            ),
            pourcentage_objectif_calc=models.Case(
                models.When(
                    objectif_hebdo_prepa__gt=0,
                    then=100 * F('nombre_adhesions') / F('objectif_hebdo_prepa')
                ),
                default=0,
                output_field=models.FloatField()
            )
        )
    
    def create_for_week(self, centre, date_start, **kwargs):
        """
        Crée une nouvelle semaine débutant à une date donnée.
        
        Args:
            centre (Centre): Centre concerné
            date_start (date): Date de début de semaine
            **kwargs: Attributs supplémentaires
            
        Returns:
            Semaine: Instance créée
        """
        # Calcul de la date de fin (par défaut +6 jours)
        date_end = date_start + timedelta(days=6)
        
        # Détermination du numéro de semaine
        week_number = date_start.isocalendar()[1]
        year = date_start.year
        month = date_start.month
        
        # Création de la semaine
        return self.create(
            centre=centre,
            date_debut_semaine=date_start,
            date_fin_semaine=date_end,
            numero_semaine=week_number,
            annee=year,
            mois=month,
            **kwargs
        )


class Semaine(BaseModel):
    """
    Semaine de suivi d'un centre de formation (objectifs et résultats hebdo).
    
    Ce modèle permet de suivre les objectifs et résultats hebdomadaires
    d'un centre de formation, avec des statistiques par département et par atelier.
    
    Attributs:
        centre (Centre): Centre de formation concerné
        annee (int): Année de la semaine
        mois (int): Mois de la semaine (1-12)
        numero_semaine (int): Numéro de la semaine dans l'année
        date_debut_semaine (date): Date de début de la semaine
        date_fin_semaine (date): Date de fin de la semaine
        objectif_annuel_prepa (int): Objectif annuel de préparation
        objectif_mensuel_prepa (int): Objectif mensuel de préparation
        objectif_hebdo_prepa (int): Objectif hebdomadaire de préparation
        nombre_places_ouvertes (int): Nombre de places disponibles
        nombre_prescriptions (int): Nombre de prescriptions reçues
        nombre_presents_ic (int): Nombre de personnes présentes en IC
        nombre_adhesions (int): Nombre d'adhésions réalisées
        departements (dict): Répartition des adhésions par département
        nombre_par_atelier (dict): Répartition par type d'atelier
        
    Propriétés:
        is_courante (bool): Indique si c'est la semaine en cours
        ateliers_nommés (list): Liste des ateliers avec leurs noms
        
    Méthodes:
        taux_adhesion: Calcule le taux d'adhésion
        taux_transformation: Calcule le taux de transformation
        pourcentage_objectif: Calcule le taux de réalisation de l'objectif
    """
    
    # Constantes pour la validation
    MAX_OBJECTIF = 9999
    
    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name="semaines", 
        verbose_name=_("Centre de formation"),
        help_text=_("Centre auquel cette semaine est rattachée")
    )
    
    annee = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Année"),
        help_text=_("Année de la semaine")
    )
    
    mois = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Mois"),
        help_text=_("Mois de la semaine (1-12)")
    )
    
    numero_semaine = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Numéro de semaine"),
        help_text=_("Numéro de la semaine dans l'année")
    )
    
    date_debut_semaine = models.DateField(
        verbose_name=_("Date de début"),
        help_text=_("Premier jour de la semaine")
    )
    
    date_fin_semaine = models.DateField(
        verbose_name=_("Date de fin"),
        help_text=_("Dernier jour de la semaine")
    )

    objectif_annuel_prepa = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Objectif annuel"),
        help_text=_("Objectif annuel de préparation")
    )
    
    objectif_mensuel_prepa = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Objectif mensuel"),
        help_text=_("Objectif mensuel de préparation")
    )
    
    objectif_hebdo_prepa = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Objectif hebdomadaire"),
        help_text=_("Objectif hebdomadaire de préparation")
    )

    nombre_places_ouvertes = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Places ouvertes"),
        help_text=_("Nombre de places ouvertes pour la semaine")
    )
    
    nombre_prescriptions = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Prescriptions"),
        help_text=_("Nombre de prescriptions reçues")
    )
    
    nombre_presents_ic = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Présents IC"),
        help_text=_("Nombre de personnes présentes en information collective")
    )
    
    nombre_adhesions = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Adhésions"),
        help_text=_("Nombre d'adhésions réalisées")
    )

    departements = models.JSONField(
        default=dict, 
        blank=True, 
        null=True,
        verbose_name=_("Répartition par département"),
        help_text=_("Nombre d'adhésions par département (format JSON)")
    )
    
    nombre_par_atelier = models.JSONField(
        default=dict, 
        blank=True, 
        null=True,
        verbose_name=_("Répartition par atelier"),
        help_text=_("Nombre de participants par atelier (format JSON)")
    )
    
    # Managers
    objects = models.Manager()
    custom = SemaineManager()

    class Meta:
        ordering = ['-date_debut_semaine']
        unique_together = ['numero_semaine', 'annee', 'centre']
        indexes = [
            models.Index(fields=['annee', 'mois'], name='semaine_annee_mois_idx'),
            models.Index(fields=['centre', 'annee'], name='semaine_centre_annee_idx'),
            models.Index(fields=['date_debut_semaine'], name='semaine_debut_idx'),
            models.Index(fields=['date_fin_semaine'], name='semaine_fin_idx'),
            models.Index(fields=['numero_semaine'], name='semaine_numero_idx'),
        ]
        verbose_name = _("Semaine")
        verbose_name_plural = _("Semaines")
        constraints = [
            models.CheckConstraint(
                check=Q(date_debut_semaine__lte=F('date_fin_semaine')),
                name='semaine_dates_coherentes'
            )
        ]

    def __str__(self):
        centre_nom = self.centre.nom if self.centre else _("Sans centre")
        return f"Semaine {self.numero_semaine} ({self.date_debut_semaine} à {self.date_fin_semaine}) - {centre_nom}"
        
    def __repr__(self):
        """Représentation technique pour le débogage."""
        return f"<Semaine(id={self.pk}, num={self.numero_semaine}, annee={self.annee}, centre_id={self.centre_id if self.centre else None})>"

    def clean(self):
        """
        Validation des données avant sauvegarde.
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        super().clean()
        
        # Validation des dates
        if self.date_debut_semaine and self.date_fin_semaine:
            if self.date_debut_semaine > self.date_fin_semaine:
                raise ValidationError({
                    'date_fin_semaine': _("La date de fin doit être postérieure à la date de début.")
                })
                
            # Vérification que la semaine ne dépasse pas 7 jours
            delta = (self.date_fin_semaine - self.date_debut_semaine).days
            if delta > 6:
                raise ValidationError({
                    'date_fin_semaine': _("La durée d'une semaine ne peut pas dépasser 7 jours.")
                })
        
        # Validation des objectifs
        if self.objectif_hebdo_prepa > self.MAX_OBJECTIF:
            raise ValidationError({
                'objectif_hebdo_prepa': _(f"L'objectif hebdomadaire ne peut pas dépasser {self.MAX_OBJECTIF}.")
            })
            
        # Validation des adhésions par rapport aux présents
        if self.nombre_adhesions > self.nombre_presents_ic and self.nombre_presents_ic > 0:
            raise ValidationError({
                'nombre_adhesions': _("Le nombre d'adhésions ne peut pas être supérieur au nombre de présents.")
            })
            
        # Validation du JSON des départements
        if self.departements:
            if not isinstance(self.departements, dict):
                raise ValidationError({
                    'departements': _("La répartition par département doit être un dictionnaire.")
                })
                
            # Vérification que tous les codes sont valides
            for code in self.departements.keys():
                if code not in NUM_DEPARTEMENTS:
                    raise ValidationError({
                        'departements': _(f"Le code département '{code}' n'est pas valide.")
                    })
                    
            # Vérification que la somme correspond au total d'adhésions
            somme = sum(self.departements.values())
            if somme != self.nombre_adhesions:
                raise ValidationError({
                    'departements': _(f"La somme des adhésions par département ({somme}) ne correspond pas au total ({self.nombre_adhesions}).")
                })
                
        # Validation du JSON des ateliers
        if self.nombre_par_atelier:
            if not isinstance(self.nombre_par_atelier, dict):
                raise ValidationError({
                    'nombre_par_atelier': _("La répartition par atelier doit être un dictionnaire.")
                })

    def taux_adhesion(self) -> float:
        """
        Taux d'adhésion = adhésions / présents IC.
        
        Returns:
            float: Pourcentage d'adhésion
        """
        return (self.nombre_adhesions / self.nombre_presents_ic) * 100 if self.nombre_presents_ic else 0

    def taux_transformation(self) -> float:
        """
        Taux de transformation = adhésions / prescriptions.
        
        Returns:
            float: Pourcentage de transformation
        """
        return (self.nombre_adhesions / self.nombre_prescriptions) * 100 if self.nombre_prescriptions else 0

    def pourcentage_objectif(self) -> float:
        """
        Taux de réalisation de l'objectif hebdomadaire.
        
        Returns:
            float: Pourcentage de réalisation
        """
        return (self.nombre_adhesions / self.objectif_hebdo_prepa) * 100 if self.objectif_hebdo_prepa else 0

    def total_adhesions_departement(self, code_dept: str) -> int:
        """
        Retourne le total d'adhésions pour un département donné.
        
        Args:
            code_dept (str): Code du département
            
        Returns:
            int: Nombre d'adhésions pour ce département
        """
        return self.departements.get(code_dept, 0) if self.departements else 0

    def total_par_atelier(self, code_atelier: str) -> int:
        """
        Retourne le total par atelier.
        
        Args:
            code_atelier (str): Code de l'atelier
            
        Returns:
            int: Nombre de participants pour cet atelier
        """
        return self.nombre_par_atelier.get(code_atelier, 0) if self.nombre_par_atelier else 0

    def nom_mois(self) -> str:
        """
        Retourne le nom du mois (français).
        
        Returns:
            str: Nom du mois
        """
        return NOMS_MOIS.get(self.mois, f"Mois {self.mois}")

    @property
    def ateliers_nommés(self) -> list[dict]:
        """
        Liste nommée des ateliers.
        
        Returns:
            list: Liste de dictionnaires {code, nom, valeur}
        """
        return [
            {"code": code, "nom": NOMS_ATELIERS.get(code, code), "valeur": valeur}
            for code, valeur in (self.nombre_par_atelier or {}).items()
        ]

    @property
    def is_courante(self) -> bool:
        """
        Retourne True si cette semaine est la semaine actuelle.
        
        Returns:
            bool: True si semaine courante
        """
        today = date.today()
        return self.date_debut_semaine <= today <= self.date_fin_semaine
        
    @property
    def departements_nommés(self) -> list[dict]:
        """
        Liste nommée des départements.
        
        Returns:
            list: Liste de dictionnaires {code, nom, valeur}
        """
        return [
            {"code": code, "nom": NUM_DEPARTEMENTS.get(code, code), "valeur": valeur}
            for code, valeur in (self.departements or {}).items()
        ]
        
    @property
    def semaine_precedente(self):
        """
        Récupère la semaine précédente pour le même centre.
        
        Returns:
            Semaine: Semaine précédente ou None
        """
        if not self.date_debut_semaine or not self.centre:
            return None
            
        date_precedente = self.date_debut_semaine - timedelta(days=7)
        return Semaine.objects.filter(
            centre=self.centre,
            date_debut_semaine=date_precedente
        ).first()
        
    @property
    def semaine_suivante(self):
        """
        Récupère la semaine suivante pour le même centre.
        
        Returns:
            Semaine: Semaine suivante ou None
        """
        if not self.date_fin_semaine or not self.centre:
            return None
            
        date_suivante = self.date_fin_semaine + timedelta(days=1)
        return Semaine.objects.filter(
            centre=self.centre,
            date_debut_semaine=date_suivante
        ).first()
        
    @cached_property
    def ecart_objectif(self):
        """
        Écart entre le nombre d'adhésions et l'objectif hebdomadaire.
        
        Returns:
            int: Écart (négatif si objectif non atteint)
        """
        return self.nombre_adhesions - self.objectif_hebdo_prepa

    def save(self, *args, **kwargs):
        """
        Sauvegarde la semaine dans une transaction atomique.
        
        Args:
            *args: Arguments positionnels
            **kwargs: Arguments nommés
        """
        # Validation avant sauvegarde
        self.full_clean()
        
        with transaction.atomic():
            is_new = self.pk is None
            
            # Si nouvelle semaine, mettre à jour les objectifs depuis PrepaCompGlobal
            if is_new and self.centre:
                try:
                    prepa_global = PrepaCompGlobal.objects.filter(
                        centre=self.centre,
                        annee=self.annee
                    ).first()
                    
                    if prepa_global:
                        self.objectif_annuel_prepa = prepa_global.objectif_annuel_prepa
                        self.objectif_hebdo_prepa = prepa_global.objectif_hebdomadaire_prepa
                        logger.debug(f"Objectifs récupérés de PrepaCompGlobal: annuel={self.objectif_annuel_prepa}, hebdo={self.objectif_hebdo_prepa}")
                except Exception as e:
                    logger.warning(f"Erreur lors de la récupération des objectifs depuis PrepaCompGlobal: {e}")
            
            # Sauvegarde
            super().save(*args, **kwargs)
            
            # Mise à jour du PrepaCompGlobal si nécessaire
            if self.centre:
                self.update_prepa_global()
                
        logger.info(f"✅ Semaine enregistrée : {self} (#{self.pk})")
        
    def update_prepa_global(self):
        """
        Met à jour les statistiques globales dans PrepaCompGlobal.
        
        Cette méthode recalcule les totaux dans PrepaCompGlobal
        après modification d'une semaine.
        """
        try:
            # Récupération ou création de l'objet PrepaCompGlobal pour ce centre et cette année
            global_obj, created = PrepaCompGlobal.objects.get_or_create(
                centre=self.centre,
                annee=self.annee,
                defaults={
                    'objectif_annuel_prepa': self.objectif_annuel_prepa,
                    'objectif_hebdomadaire_prepa': self.objectif_hebdo_prepa,
                }
            )
            
            # Calcul des totaux pour l'année
            semaines = Semaine.objects.filter(centre=self.centre, annee=self.annee)
            
            global_obj.adhesions = semaines.aggregate(Sum('nombre_adhesions'))['nombre_adhesions__sum'] or 0
            global_obj.total_presents = semaines.aggregate(Sum('nombre_presents_ic'))['nombre_presents_ic__sum'] or 0
            global_obj.total_prescriptions = semaines.aggregate(Sum('nombre_prescriptions'))['nombre_prescriptions__sum'] or 0
            global_obj.total_places_ouvertes = semaines.aggregate(Sum('nombre_places_ouvertes'))['nombre_places_ouvertes__sum'] or 0
            
            # Si c'est un nouvel objet, utiliser les objectifs de cette semaine
            if created:
                logger.info(f"Création d'un nouvel objet PrepaCompGlobal pour {self.centre.nom} - {self.annee}")
            
            # Sauvegarde
            global_obj.save()
            logger.debug(f"PrepaCompGlobal mis à jour pour {self.centre.nom} - {self.annee}: {global_obj.adhesions} adhésions")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de PrepaCompGlobal: {e}", exc_info=True)

    def to_serializable_dict(self) -> dict:
        """
        Dictionnaire pour affichage/API.
        
        Returns:
            dict: Données sérialisables
        """
        return {
            "id": self.pk,
            "centre": {
                "id": self.centre.pk if self.centre else None,
                "nom": self.centre.nom if self.centre else None
            },
            "annee": self.annee,
            "mois": self.mois,
            "nom_mois": self.nom_mois(),
            "numero_semaine": self.numero_semaine,
            "date_debut": self.date_debut_semaine.isoformat(),
            "date_fin": self.date_fin_semaine.isoformat(),
            "objectifs": {
                "annuel": self.objectif_annuel_prepa,
                "mensuel": self.objectif_mensuel_prepa,
                "hebdomadaire": self.objectif_hebdo_prepa
            },
            "adhesions": self.nombre_adhesions,
            "presents_ic": self.nombre_presents_ic,
            "prescriptions": self.nombre_prescriptions,
            "places_ouvertes": self.nombre_places_ouvertes,
            "taux_adhesion": round(self.taux_adhesion(), 1),
            "taux_transformation": round(self.taux_transformation(), 1),
            "pourcentage_objectif": round(self.pourcentage_objectif(), 1),
            "ecart_objectif": self.ecart_objectif,
            "departements": self.departements or {},
            "departements_nommes": self.departements_nommés,
            "ateliers": self.ateliers_nommés,
            "is_courante": self.is_courante,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
    @classmethod
    def create_for_week(cls, centre, date_start, **kwargs):
        """
        Méthode de classe pour créer une semaine pour une date donnée.
        
        Args:
            centre (Centre): Centre concerné
            date_start (date): Date de début de semaine
            **kwargs: Attributs supplémentaires
            
        Returns:
            Semaine: Instance créée
        """
        return cls.custom.create_for_week(centre, date_start, **kwargs)
        
    @classmethod
    def get_or_create_current_week(cls, centre):
        """
        Récupère ou crée la semaine courante pour un centre.
        
        Args:
            centre (Centre): Centre concerné
            
        Returns:
            tuple: (Semaine, created)
        """
        today = date.today()
        # Calcul du premier jour de la semaine (lundi)
        start_of_week = today - timedelta(days=today.weekday())
        
        try:
            # Recherche d'une semaine existante
            semaine = cls.objects.get(
                centre=centre,
                date_debut_semaine__lte=today,
                date_fin_semaine__gte=today
            )
            return semaine, False
        except cls.DoesNotExist:
            # Création d'une nouvelle semaine
            semaine = cls.create_for_week(
                centre=centre,
                date_start=start_of_week
            )
            return semaine, True


class PrepaCompGlobalManager(models.Manager):
    """
    Manager personnalisé pour le modèle PrepaCompGlobal.
    """
    
    def par_annee(self, annee):
        """
        Récupère tous les objets pour une année donnée.
        
        Args:
            annee (int): Année à filtrer
            
        Returns:
            QuerySet: Objets de l'année
        """
        return self.filter(annee=annee).order_by('centre__nom')
    
    def par_centre(self, centre):
        """
        Récupère tous les objets pour un centre donné.
        
        Args:
            centre (Centre): Centre à filtrer
            
        Returns:
            QuerySet: Objets du centre
        """
        return self.filter(centre=centre).order_by('-annee')
    
    def annee_courante(self):
        """
        Récupère les objets de l'année en cours.
        
        Returns:
            QuerySet: Objets de l'année courante
        """
        annee_courante = date.today().year
        return self.filter(annee=annee_courante)
    
    def avec_taux(self):
        """
        Ajoute des annotations pour les taux calculés.
        
        Returns:
            QuerySet: Objets avec taux calculés
        """
        return self.annotate(
            taux_transformation_calc=models.Case(
                models.When(
                    total_presents__gt=0,
                    then=100 * F('adhesions') / F('total_presents')
                ),
                default=0,
                output_field=models.FloatField()
            ),
            taux_objectif_annee_calc=models.Case(
                models.When(
                    objectif_annuel_prepa__gt=0,
                    then=100 * F('adhesions') / F('objectif_annuel_prepa')
                ),
                default=0,
                output_field=models.FloatField()
            )
        )


class PrepaCompGlobal(BaseModel):
    """
    Données agrégées par centre et par année pour PrépaComp.
    
    Ce modèle stocke les statistiques globales annuelles pour un centre,
    incluant les objectifs et les résultats cumulés de toutes les semaines.
    
    Attributs:
        centre (Centre): Centre concerné
        annee (int): Année concernée
        total_candidats (int): Nombre total de candidats
        total_prescriptions (int): Nombre total de prescriptions
        adhesions (int): Nombre total d'adhésions
        total_presents (int): Nombre total de présents
        total_places_ouvertes (int): Nombre total de places ouvertes
        objectif_annuel_prepa (int): Objectif annuel de préparation
        objectif_hebdomadaire_prepa (int): Objectif hebdomadaire de préparation
        objectif_annuel_jury (int): Objectif annuel pour les jurys
        objectif_mensuel_jury (int): Objectif mensuel pour les jurys
        
    Propriétés:
        taux_transformation (float): Pourcentage d'adhésions par rapport aux présents
        taux_objectif_annee (float): Pourcentage de réalisation de l'objectif annuel
        
    Méthodes:
        to_serializable_dict: Représentation API/export
        recalculate_from_semaines: Recalcule les totaux à partir des semaines
    """
    
    # Constantes pour la validation
    MAX_OBJECTIF = 9999
    ANNEE_MIN = 2020
    ANNEE_MAX = 2100

    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name="prepa_globaux", 
        verbose_name=_("Centre"),
        help_text=_("Centre auquel ces statistiques sont rattachées")
    )
    
    from datetime import date

    def default_annee():
        return date.today().year

    annee = models.PositiveIntegerField(
        default=default_annee,
        verbose_name=_("Année"),
        help_text=_("Année concernée")
    )

    total_candidats = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total candidats"),
        help_text=_("Nombre total de candidats pour l'année")
    )
    
    total_prescriptions = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total prescriptions"),
        help_text=_("Nombre total de prescriptions pour l'année")
    )
    
    adhesions = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Adhésions"),
        help_text=_("Nombre total d'adhésions pour l'année")
    )
    
    total_presents = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total présents"),
        help_text=_("Nombre total de personnes présentes en IC pour l'année")
    )
    
    total_places_ouvertes = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total places ouvertes"),
        help_text=_("Nombre total de places ouvertes pour l'année")
    )

    objectif_annuel_prepa = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Objectif annuel prépa"),
        help_text=_("Objectif annuel de préparation")
    )
    
    objectif_hebdomadaire_prepa = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Objectif hebdomadaire prépa"),
        help_text=_("Objectif hebdomadaire de préparation")
    )
    
    objectif_annuel_jury = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Objectif annuel jury"),
        help_text=_("Objectif annuel pour les jurys")
    )
    
    objectif_mensuel_jury = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Objectif mensuel jury"),
        help_text=_("Objectif mensuel pour les jurys")
    )
    
    # Managers
    objects = models.Manager()
    custom = PrepaCompGlobalManager()

    class Meta:
        verbose_name = _("Bilan global PrépaComp")
        verbose_name_plural = _("Bilans globaux PrépaComp")
        ordering = ['-annee']
        unique_together = ['centre', 'annee']
        indexes = [
            models.Index(fields=['centre', 'annee'], name='prepaglobal_centre_annee_idx'),
            models.Index(fields=['annee'], name='prepaglobal_annee_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(annee__gte=2020) & Q(annee__lte=2100),
                name='prepaglobal_annee_valide'
            )
        ]

    def __str__(self):
        """Représentation textuelle de l'objet."""
        return f"{self.centre.nom if self.centre else _('Global')} - {self.annee}"
        
    def __repr__(self):
        """Représentation technique pour le débogage."""
        return f"<PrepaCompGlobal(id={self.pk}, centre_id={self.centre_id if self.centre else None}, annee={self.annee})>"

    def clean(self):
        """
        Valide la cohérence des objectifs hebdo / annuels.
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        super().clean()
        
        # Validation des objectifs
        if self.objectif_hebdomadaire_prepa and self.objectif_annuel_prepa:
            if self.objectif_hebdomadaire_prepa * 52 < self.objectif_annuel_prepa:
                raise ValidationError({
                    'objectif_hebdomadaire_prepa': _("Objectif hebdomadaire trop bas pour atteindre l'objectif annuel.")
                })
                
        # Validation de l'année
        if self.annee < self.ANNEE_MIN or self.annee > self.ANNEE_MAX:
            raise ValidationError({
                'annee': _(f"L'année doit être comprise entre {self.ANNEE_MIN} et {self.ANNEE_MAX}.")
            })
            
        # Validation des adhésions
        if self.adhesions > self.total_presents and self.total_presents > 0:
            raise ValidationError({
                'adhesions': _("Le nombre d'adhésions ne peut pas être supérieur au nombre de présents.")
            })

    def get_periode_display(self):
        return f"{self.date_debut_semaine.strftime('%d/%m/%Y')} – {self.date_fin_semaine.strftime('%d/%m/%Y')}"
                

    def taux_transformation(self) -> float:
        """
        Taux de transformation = adhésions / présents.
        
        Returns:
            float: Pourcentage de transformation
        """
        return (self.adhesions / self.total_presents) * 100 if self.total_presents else 0

    def taux_adhesion(self) -> float:
        """
        Alias pour cohérence avec Semaine.
        
        Returns:
            float: Même valeur que taux_transformation
        """
        return self.taux_transformation()

    def taux_objectif_annee(self) -> float:
        """
        Taux de réalisation de l'objectif annuel.
        
        Returns:
            float: Pourcentage de réalisation
        """
        return (self.adhesions / self.objectif_annuel_prepa) * 100 if self.objectif_annuel_prepa else 0
        
        
    @property
    def objectif_restant(self) -> int:
        """
        Nombre d'adhésions restantes pour atteindre l'objectif annuel.
        
        Returns:
            int: Nombre d'adhésions à réaliser
        """
        return max(0, self.objectif_annuel_prepa - self.adhesions)
        
    @property
    def semaines_restantes(self) -> int:
        """
        Nombre de semaines restantes dans l'année.
        
        Returns:
            int: Nombre de semaines
        """
        today = date.today()
        
        # Si l'année est déjà passée, retourner 0
        if self.annee < today.year:
            return 0
            
        # Si l'année est future, retourner 52
        if self.annee > today.year:
            return 52
            
        # Pour l'année en cours, calculer les semaines restantes
        current_week = today.isocalendar()[1]
        return max(0, 52 - current_week)
        
    @property
    def adhesions_hebdo_necessaires(self) -> float:
        """
        Nombre d'adhésions hebdomadaires nécessaires pour atteindre l'objectif annuel.
        
        Returns:
            float: Nombre d'adhésions par semaine nécessaire
        """
        if self.semaines_restantes <= 0:
            return 0
            
        return self.objectif_restant / self.semaines_restantes if self.semaines_restantes > 0 else 0
        
    @cached_property
    def moyenne_hebdomadaire(self) -> float:
        """
        Moyenne hebdomadaire des adhésions réalisées.
        
        Returns:
            float: Moyenne hebdomadaire
        """
        if self.centre:
            semaines_count = Semaine.objects.filter(
                centre=self.centre,
                annee=self.annee
            ).count()
            
            return self.adhesions / semaines_count if semaines_count > 0 else 0
        return 0

    def save(self, *args, **kwargs):
        """
        Sauvegarde l'objet dans une transaction atomique.
        
        Args:
            *args: Arguments positionnels
            **kwargs: Arguments nommés
        """
        # Validation des données
        self.full_clean()
        
        with transaction.atomic():
            super().save(*args, **kwargs)
            
        logger.info(f"✅ PrepaCompGlobal enregistré : {self} (#{self.pk})")
        
    def recalculate_from_semaines(self):
        """
        Recalcule les totaux à partir des semaines existantes.
        
        Cette méthode permet de rafraîchir les données globales
        en sommant les données de toutes les semaines de l'année.
        
        Returns:
            bool: True si mise à jour effectuée
        """
        if not self.centre:
            logger.warning("Impossible de recalculer PrepaCompGlobal sans centre associé")
            return False
            
        try:
            with transaction.atomic():
                # Récupération de toutes les semaines pour ce centre et cette année
                semaines = Semaine.objects.filter(
                    centre=self.centre,
                    annee=self.annee
                )
                
                if not semaines.exists():
                    logger.warning(f"Aucune semaine trouvée pour {self.centre.nom} en {self.annee}")
                    return False
                
                # Calcul des totaux
                aggregation = semaines.aggregate(
                    total_adhesions=Sum('nombre_adhesions'),
                    total_presents=Sum('nombre_presents_ic'),
                    total_prescriptions=Sum('nombre_prescriptions'),
                    total_places=Sum('nombre_places_ouvertes')
                )
                
                # Mise à jour des champs
                self.adhesions = aggregation['total_adhesions'] or 0
                self.total_presents = aggregation['total_presents'] or 0
                self.total_prescriptions = aggregation['total_prescriptions'] or 0
                self.total_places_ouvertes = aggregation['total_places'] or 0
                
                # Sauvegarde sans validation (déjà validé)
                super().save(update_fields=[
                    'adhesions', 'total_presents', 'total_prescriptions', 'total_places_ouvertes'
                ])
                
                logger.info(f"Recalcul effectué pour {self}: {self.adhesions} adhésions")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors du recalcul de PrepaCompGlobal: {e}", exc_info=True)
            return False

    def to_serializable_dict(self) -> dict:
        """
        Dictionnaire pour usage API/export.
        
        Returns:
            dict: Données sérialisables
        """
        return {
            "id": self.pk,
            "centre": {
                "id": self.centre.pk if self.centre else None,
                "nom": self.centre.nom if self.centre else None
            },
            "annee": self.annee,
            "adhesions": self.adhesions,
            "presents": self.total_presents,
            "taux_transformation": round(self.taux_transformation(), 1),
            "taux_objectif_annee": round(self.taux_objectif_annee(), 1),
            "objectif_annuel_prepa": self.objectif_annuel_prepa,
            "objectif_hebdo": self.objectif_hebdomadaire_prepa,
            "prescriptions": self.total_prescriptions,
            "places_ouvertes": self.total_places_ouvertes,
            "objectif_restant": self.objectif_restant,
            "semaines_restantes": self.semaines_restantes,
            "adhesions_hebdo_necessaires": round(self.adhesions_hebdo_necessaires, 1),
            "moyenne_hebdomadaire": round(self.moyenne_hebdomadaire, 1),
            "objectif_jury": {
                "annuel": self.objectif_annuel_jury,
                "mensuel": self.objectif_mensuel_jury
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
    @classmethod
    def create_for_centre_and_year(cls, centre, annee, **kwargs):
        """
        Crée un nouvel objet PrepaCompGlobal pour un centre et une année.
        
        Cette méthode vérifie d'abord si un objet existe déjà.
        
        Args:
            centre (Centre): Centre concerné
            annee (int): Année concernée
            **kwargs: Attributs supplémentaires
            
        Returns:
            tuple: (PrepaCompGlobal, created)
        """
        return cls.objects.get_or_create(
            centre=centre,
            annee=annee,
            defaults=kwargs
        )
        
    @classmethod
    def get_for_all_centres(cls, annee=None):
        """
        Récupère les données pour tous les centres pour une année donnée.
        
        Args:
            annee (int, optional): Année, par défaut l'année en cours
            
        Returns:
            QuerySet: Objets PrepaCompGlobal pour tous les centres
        """
        annee = annee or date.today().year
        
        # Récupération de tous les centres
        all_centres = Centre.objects.all()
        
        # Création des objets manquants
        for centre in all_centres:
            cls.create_for_centre_and_year(centre, annee)
            
        # Retour des objets avec statistiques
        return cls.custom.par_annee(annee).select_related('centre')