# rap_app_project/rap_app/models/declic.py
from datetime import date
from typing import Optional, Dict, Any 

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import localdate

from .base import BaseModel
from .centres import Centre


# -------------------------------------------------------------------
# 📊 ACTIVITÉS DÉCLIC : uniquement ateliers (1 → 6 + autre)
# -------------------------------------------------------------------
class Declic(BaseModel):
    """
    Activité Déclic : uniquement ateliers thématiques (IC supprimée).
    """

    class TypeDeclic(models.TextChoices):
        ATELIER1 = "atelier_1", _("Atelier 1")
        ATELIER2 = "atelier_2", _("Atelier 2")
        ATELIER3 = "atelier_3", _("Atelier 3")
        ATELIER4 = "atelier_4", _("Atelier 4")
        ATELIER5 = "atelier_5", _("Atelier 5")
        ATELIER6 = "atelier_6", _("Atelier 6")
        AUTRE = "autre", _("Autre activité Déclic")

    type_declic = models.CharField(max_length=40, choices=TypeDeclic.choices)
    date_declic = models.DateField(_("Date"))

    centre = models.ForeignKey(
        Centre,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="declics",
        verbose_name=_("Centre de formation"),
    )

    # --- Ateliers uniquement ---
    nb_inscrits_declic = models.PositiveIntegerField(default=0)
    nb_presents_declic = models.PositiveIntegerField(default=0)
    nb_absents_declic = models.PositiveIntegerField(default=0)

    commentaire = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-date_declic", "-id"]

    def __str__(self):
        return f"{self.get_type_declic_display()} – {self.date_declic:%d/%m/%Y}"

    # -------------------------------------------------------------------
    # 🔄 Save automatique (absents ateliers)
    # -------------------------------------------------------------------
    def save(self, *args, user=None, **kwargs):
        self.nb_absents_declic = max(
            0, self.nb_inscrits_declic - self.nb_presents_declic
        )

        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user

        super().save(*args, **kwargs)

    # -------------------------------------------------------------------
    # 📊 Statistiques ateliers
    # -------------------------------------------------------------------
    @property
    def taux_presence_declic(self):
        """% de présence aux ateliers"""
        return (
            round((self.nb_presents_declic / self.nb_inscrits_declic) * 100, 1)
            if self.nb_inscrits_declic
            else 0
        )

    # -------------------------------------------------------------------
    # 🎯 Objectifs annuels — uniquement ateliers
    # -------------------------------------------------------------------
    @property
    def objectif_annuel(self):
        return ObjectifDeclic.get_objectif(self.centre, self.date_declic)

    @property
    def taux_atteinte_annuel(self):
        """Ateliers (1→6 + autre), sans IC"""
        if not self.objectif_annuel or not self.centre:
            return 0

        realise = (
            Declic.objects.filter(
                centre=self.centre,
                date_declic__year=self.date_declic.year,
            )
            .aggregate(total=models.Sum("nb_presents_declic"))["total"]
            or 0
        )
        return round((realise / self.objectif_annuel) * 100, 1)

    @property
    def reste_a_faire(self):
        if not self.objectif_annuel or not self.centre:
            return 0

        realise = (
            Declic.objects.filter(
                centre=self.centre,
                date_declic__year=self.date_declic.year,
            )
            .aggregate(total=models.Sum("nb_presents_declic"))["total"]
            or 0
        )
        return max(self.objectif_annuel - realise, 0)

    # -------------------------------------------------------------------
    # 👥 Totaux d’accueil — ateliers uniquement
    # -------------------------------------------------------------------
    @classmethod
    def total_accueillis(cls, annee=None, centre=None, departement=None):
        annee = annee or localdate().year

        qs = cls.objects.filter(date_declic__year=annee)

        if centre:
            qs = qs.filter(centre=centre)

        if departement:
            qs = [d for d in qs if d.centre and d.centre.departement == departement]
            return sum(d.nb_presents_declic for d in qs)

        return qs.aggregate(total=models.Sum("nb_presents_declic"))["total"] or 0


# -------------------------------------------------------------------
# 🎯 OBJECTIFS DÉCLIC – par centre (annuel)
# -------------------------------------------------------------------
class ObjectifDeclic(BaseModel):
    """Objectifs Déclic : objectifs annuels par centre (ateliers uniquement)."""

    centre = models.ForeignKey(
        Centre,
        on_delete=models.CASCADE,
        related_name="objectifs_declic",
        verbose_name=_("Centre de formation"),
    )
    departement = models.CharField(
        max_length=3,
        blank=True,
        null=True,
        verbose_name=_("Département"),
    )
    annee = models.PositiveIntegerField(verbose_name=_("Année"))
    valeur_objectif = models.PositiveIntegerField(
        verbose_name=_("Objectif annuel (personnes)")
    )
    commentaire = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Objectif Déclic (centre)")
        verbose_name_plural = _("Objectifs Déclic (centres)")
        ordering = ["-annee"]
        constraints = [
            models.UniqueConstraint(
                fields=["centre", "annee"],
                name="uniq_objectif_declic_centre_annee",
            )
        ]
        indexes = [models.Index(fields=["centre", "annee"])]

    def __str__(self):
        base = str(self.centre)
        if self.departement:
            base += f" ({self.departement})"
        return f"{base} – {self.annee}"

    # -------------------------------------------------------------------
    # 🔹 Données réelles issues de Declic (ATELIERS uniquement)
    # -------------------------------------------------------------------
    @property
    def data_declic(self) -> Dict[str, int]:
        """
        Retourne un agrégat de toutes les données Déclic du centre pour l’année donnée :
        - ateliers (1 à 6 + autre) : inscrits, présents, absents
        """
        if hasattr(self, "_data_declic_cache"):
            return self._data_declic_cache

        agg_ateliers = (
            Declic.objects.filter(
                centre=self.centre,
                date_declic__year=self.annee,
            ).aggregate(
                total_inscrits=models.Sum("nb_inscrits_declic"),
                total_presents=models.Sum("nb_presents_declic"),
                total_absents=models.Sum("nb_absents_declic"),
            )
            or {}
        )

        inscrits = agg_ateliers.get("total_inscrits") or 0
        presents = agg_ateliers.get("total_presents") or 0
        absents = agg_ateliers.get("total_absents") or 0

        self._data_declic_cache = {
            "inscrits": inscrits,
            "presents": presents,
            "absents": absents,
            # Alias explicite pour “tous les ateliers”
            "total_ateliers": presents,
        }
        return self._data_declic_cache

    # -------------------------------------------------------------------
    # 🔹 Ratios et taux
    # -------------------------------------------------------------------
    def _ratio(self, num, den):
        return round((num / den) * 100, 1) if den else 0

    @property
    def taux_presence_ateliers(self):
        """% de présence globale sur tous les ateliers (1 à 6 + autre)"""
        return self._ratio(self.data_declic["presents"], self.data_declic["inscrits"])

    @property
    def taux_atteinte(self):
        """% de l’objectif atteint — basé sur l’ensemble des ateliers (1 à 6 + autre)"""
        return self._ratio(self.data_declic["total_ateliers"], self.valeur_objectif)

    @property
    def reste_a_faire(self):
        """Objectif restant (objectif - présents sur l’ensemble des ateliers)"""
        return max(self.valeur_objectif - self.data_declic["total_ateliers"], 0)

    # -------------------------------------------------------------------
    # 🔹 Synthèse globale (pour API / exports)
    # -------------------------------------------------------------------
    def synthese_globale(self) -> Dict[str, Any]:
        """
        Données agrégées cohérentes avec le front actuel (version ateliers only).
        - `realise` = présents sur tous les ateliers (1 à 6 + autre)
        """
        return {
            "objectif_id": self.id,
            "centre_id": getattr(self.centre, "id", None),
            "centre": getattr(self.centre, "nom", str(self.centre)),
            "annee": self.annee,
            "objectif": self.valeur_objectif,

            # --- Réalisations ---
            "realise": self.data_declic["total_ateliers"],
            "absents": self.data_declic["absents"],

            # --- Taux ---
            "taux_presence_ateliers": self.taux_presence_ateliers,
            "taux_atteinte": self.taux_atteinte,

            # --- Reste à faire ---
            "reste_a_faire": self.reste_a_faire,
        }

    # -------------------------------------------------------------------
    # 🔹 Méthodes utilitaires
    # -------------------------------------------------------------------
    @classmethod
    def get_objectif(cls, centre, date):
        """Renvoie la valeur de l’objectif du centre pour l’année donnée."""
        if not centre or not date:
            return 0
        return (
            cls.objects.filter(centre=centre, annee=date.year)
            .values_list("valeur_objectif", flat=True)
            .first()
            or 0
        )

    def save(self, *args, user=None, **kwargs):
        """Enregistrement avec mise à jour du département et des métadonnées utilisateur."""
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user

        centre = getattr(self, "centre", None)
        if centre:
            centre_dept = getattr(centre, "departement", None)
            if centre_dept and self.departement != centre_dept:
                self.departement = centre_dept

        super().save(*args, **kwargs)
