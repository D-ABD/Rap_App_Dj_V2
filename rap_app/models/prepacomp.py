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
    Semaine de suivi d'un centre de formation (objectifs et résultats hebdo).
    """

    centre = models.ForeignKey(
        Centre, on_delete=models.CASCADE, null=True, blank=True,
        related_name="semaines", verbose_name="Centre de formation"
    )
    annee = models.PositiveIntegerField(default=0)
    mois = models.PositiveIntegerField(default=1)
    numero_semaine = models.PositiveIntegerField(default=1)
    date_debut_semaine = models.DateField()
    date_fin_semaine = models.DateField()

    objectif_annuel_prepa = models.PositiveIntegerField(default=0)
    objectif_mensuel_prepa = models.PositiveIntegerField(default=0)
    objectif_hebdo_prepa = models.PositiveIntegerField(default=0)

    nombre_places_ouvertes = models.PositiveIntegerField(default=0)
    nombre_prescriptions = models.PositiveIntegerField(default=0)
    nombre_presents_ic = models.PositiveIntegerField(default=0)
    nombre_adhesions = models.PositiveIntegerField(default=0)

    departements = models.JSONField(default=dict, blank=True, null=True)
    nombre_par_atelier = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        ordering = ['-date_debut_semaine']
        unique_together = ['numero_semaine', 'annee', 'centre']
        indexes = [
            models.Index(fields=['annee', 'mois']),
            models.Index(fields=['centre', 'annee']),
            models.Index(fields=['date_debut_semaine']),
        ]
        verbose_name = "Semaine"
        verbose_name_plural = "Semaines"

    def __str__(self):
        centre_nom = self.centre.nom if self.centre else "Sans centre"
        return f"Semaine {self.numero_semaine} ({self.date_debut_semaine} à {self.date_fin_semaine}) - {centre_nom}"

    def taux_adhesion(self) -> float:
        """Taux d'adhésion = adhésions / présents IC"""
        return (self.nombre_adhesions / self.nombre_presents_ic) * 100 if self.nombre_presents_ic else 0

    def taux_transformation(self) -> float:
        """Taux de transformation = adhésions / prescriptions"""
        return (self.nombre_adhesions / self.nombre_prescriptions) * 100 if self.nombre_prescriptions else 0

    def pourcentage_objectif(self) -> float:
        """Taux de réalisation de l’objectif hebdomadaire"""
        return (self.nombre_adhesions / self.objectif_hebdo_prepa) * 100 if self.objectif_hebdo_prepa else 0

    def total_adhesions_departement(self, code_dept: str) -> int:
        """Retourne le total d'adhésions pour un département donné"""
        return self.departements.get(code_dept, 0) if self.departements else 0

    def total_par_atelier(self, code_atelier: str) -> int:
        """Retourne le total par atelier"""
        return self.nombre_par_atelier.get(code_atelier, 0) if self.nombre_par_atelier else 0

    def nom_mois(self) -> str:
        """Retourne le nom du mois (français)"""
        return NOMS_MOIS.get(self.mois, f"Mois {self.mois}")

    @property
    def ateliers_nommés(self) -> list[dict]:
        """Liste nommée des ateliers"""
        return [
            {"code": code, "nom": NOMS_ATELIERS.get(code, code), "valeur": valeur}
            for code, valeur in (self.nombre_par_atelier or {}).items()
        ]

    @property
    def is_courante(self) -> bool:
        """Retourne True si cette semaine est la semaine actuelle"""
        today = date.today()
        return self.date_debut_semaine <= today <= self.date_fin_semaine

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
        logger.info(f"✅ Semaine enregistrée : {self}")

    def to_serializable_dict(self) -> dict:
        """Dictionnaire pour affichage/API"""
        return {
            "id": self.pk,
            "centre": self.centre.nom if self.centre else None,
            "annee": self.annee,
            "mois": self.mois,
            "nom_mois": self.nom_mois(),
            "numero_semaine": self.numero_semaine,
            "date_debut": self.date_debut_semaine.isoformat(),
            "date_fin": self.date_fin_semaine.isoformat(),
            "adhesions": self.nombre_adhesions,
            "presents_ic": self.nombre_presents_ic,
            "prescriptions": self.nombre_prescriptions,
            "places_ouvertes": self.nombre_places_ouvertes,
            "taux_adhesion": round(self.taux_adhesion(), 1),
            "taux_transformation": round(self.taux_transformation(), 1),
            "pourcentage_objectif": round(self.pourcentage_objectif(), 1),
            "departements": self.departements or {},
            "ateliers": self.ateliers_nommés,
            "is_courante": self.is_courante,
        }
class PrepaCompGlobal(BaseModel):
    """
    Données agrégées par centre et par année pour PrépaComp.
    """

    centre = models.ForeignKey(
        Centre, on_delete=models.CASCADE, null=True, blank=True,
        related_name="prepa_globaux", verbose_name="Centre"
    )
    annee = models.PositiveIntegerField(default=2024)

    total_candidats = models.PositiveIntegerField(default=0)
    total_prescriptions = models.PositiveIntegerField(default=0)
    adhesions = models.PositiveIntegerField(default=0)
    total_presents = models.PositiveIntegerField(default=0)
    total_places_ouvertes = models.PositiveIntegerField(default=0)

    objectif_annuel_prepa = models.PositiveIntegerField(default=0)
    objectif_hebdomadaire_prepa = models.PositiveIntegerField(default=0)
    objectif_annuel_jury = models.PositiveIntegerField(default=0)
    objectif_mensuel_jury = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Bilan global PrépaComp"
        verbose_name_plural = "Bilans globaux PrépaComp"
        ordering = ['-annee']
        unique_together = ['centre', 'annee']
        indexes = [
            models.Index(fields=['centre', 'annee']),
            models.Index(fields=['annee']),
        ]

    def __str__(self):
        return f"{self.centre.nom if self.centre else 'Global'} - {self.annee}"

    def clean(self):
        """Valide la cohérence des objectifs hebdo / annuels"""
        if self.objectif_hebdomadaire_prepa and self.objectif_annuel_prepa:
            if self.objectif_hebdomadaire_prepa * 52 < self.objectif_annuel_prepa:
                raise ValidationError("Objectif hebdomadaire trop bas pour atteindre l'objectif annuel.")

    def taux_transformation(self) -> float:
        """Taux de transformation = adhésions / présents"""
        return (self.adhesions / self.total_presents) * 100 if self.total_presents else 0

    def taux_adhesion(self) -> float:
        """Alias pour cohérence avec Semaine"""
        return self.taux_transformation()

    def taux_objectif_annee(self) -> float:
        """Taux de réalisation de l’objectif annuel"""
        return (self.adhesions / self.objectif_annuel_prepa) * 100 if self.objectif_annuel_prepa else 0

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
        logger.info(f"✅ PrepaCompGlobal enregistré : {self}")

    def to_serializable_dict(self) -> dict:
        """Dictionnaire pour usage API/export"""
        return {
            "id": self.pk,
            "centre": self.centre.nom if self.centre else None,
            "annee": self.annee,
            "adhesions": self.adhesions,
            "presents": self.total_presents,
            "taux_transformation": round(self.taux_transformation(), 1),
            "taux_objectif_annee": round(self.taux_objectif_annee(), 1),
            "objectif_annuel_prepa": self.objectif_annuel_prepa,
            "objectif_hebdo": self.objectif_hebdomadaire_prepa,
            "prescriptions": self.total_prescriptions,
            "places_ouvertes": self.total_places_ouvertes,
        }
