# rap_app_project/rap_app/models/prepa.py
from datetime import date
from typing import Optional, Dict, Any 

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import localdate

from .base import BaseModel
from .centres import Centre

class PrepaQuerySet(models.QuerySet):
    def ateliers(self):
        return self.filter(
            models.Q(type_prepa__startswith="atelier") | models.Q(type_prepa="autre")
        )

    def ic(self):
        return self.filter(type_prepa=Prepa.TypePrepa.INFO_COLLECTIVE)

# -------------------------------------------------------------------
# 📊 ACTIVITÉS PREPA : données réelles (séances, effectifs)
# -------------------------------------------------------------------
class Prepa(BaseModel):
    objects = PrepaQuerySet.as_manager()

    """
    Activité Prépa : Information collective ou ateliers thématiques.

    - Pour les informations collectives :
      * nombre_places_ouvertes : places disponibles pour les prescripteurs
      * nombre_prescriptions   : candidats envoyés par les prescripteurs
      * nb_presents_info       : candidats présents à la séance
      * nb_absents_info        : candidats absents à la séance
      * nb_adhesions           : candidats qui adhèrent au dispositif

    - Pour les ateliers Prépa :
      * nb_inscrits_prepa      : participants inscrits
      * nb_presents_prepa      : présents à l’atelier
      * nb_absents_prepa       : absents à l’atelier
    """

    class TypePrepa(models.TextChoices):

        INFO_COLLECTIVE = "info_collective", _("Information collective")
        ATELIER1 = "atelier_1", _("Atelier 1")
        ATELIER2 = "atelier_2", _("Atelier 2")
        ATELIER3 = "atelier_3", _("Atelier 3")
        ATELIER4 = "atelier_4", _("Atelier 4")
        ATELIER5 = "atelier_5", _("Atelier 5")
        ATELIER6 = "atelier_6", _("Atelier 6")
        AUTRE = "autre", _("Autre activité Prépa")

    type_prepa = models.CharField(max_length=40, choices=TypePrepa.choices, verbose_name=_("Type d’activité"))
    date_prepa = models.DateField(_("Date"), help_text=_("Date de la séance ou de la semaine concernée"))

    centre = models.ForeignKey(
        Centre,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prepas",
        verbose_name=_("Centre de formation"),
    )

    # --- Données Information Collective ---
    nombre_places_ouvertes = models.PositiveIntegerField(default=0, verbose_name=_("Places ouvertes (IC)"))
    nombre_prescriptions = models.PositiveIntegerField(default=0, verbose_name=_("Prescriptions (IC)"))
    nb_presents_info = models.PositiveIntegerField(default=0, verbose_name=_("Présents (IC)"))
    nb_absents_info = models.PositiveIntegerField(default=0, verbose_name=_("Absents (IC)"))
    nb_adhesions = models.PositiveIntegerField(default=0, verbose_name=_("Adhésions (IC)"))

    # --- Données Ateliers Prépa ---
    nb_inscrits_prepa = models.PositiveIntegerField(default=0, verbose_name=_("Inscrits (Atelier)"))
    nb_presents_prepa = models.PositiveIntegerField(default=0, verbose_name=_("Présents (Atelier)"))
    nb_absents_prepa = models.PositiveIntegerField(default=0, verbose_name=_("Absents (Atelier)"))

    commentaire = models.TextField(blank=True, null=True, verbose_name=_("Commentaire / notes"))

    class Meta:
        verbose_name = _("Séance Prépa")
        verbose_name_plural = _("Séances Prépa")
        ordering = ["-date_prepa", "-id"]
        indexes = [
            models.Index(fields=["centre"]),
            models.Index(fields=["date_prepa"]),
            models.Index(fields=["type_prepa"]),
        ]

    def __str__(self):
        return f"{self.get_type_prepa_display()} – {self.date_prepa:%d/%m/%Y}"

    # -------------------------------------------------------------------
    # 🔄 Sauvegarde automatique
    # -------------------------------------------------------------------
    def save(self, *args, user=None, **kwargs):
        """Met automatiquement à jour les absents et renseigne created_by / updated_by."""
        self.nb_absents_prepa = max(0, self.nb_inscrits_prepa - self.nb_presents_prepa)
        self.nb_absents_info = max(0, self.nombre_prescriptions - self.nb_presents_info)

        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user

        super().save(*args, **kwargs)

    # -------------------------------------------------------------------
    # 📈 Taux pour Information collective
    # -------------------------------------------------------------------
    @property
    def taux_prescription(self):
        return round((self.nombre_prescriptions / self.nombre_places_ouvertes) * 100, 1) if self.nombre_places_ouvertes else 0

    @property
    def taux_presence_info(self):
        return round((self.nb_presents_info / self.nombre_prescriptions) * 100, 1) if self.nombre_prescriptions else 0

    @property
    def taux_adhesion(self):
        return round((self.nb_adhesions / self.nb_presents_info) * 100, 1) if self.nb_presents_info else 0

    # -------------------------------------------------------------------
    # 📊 Taux pour ateliers Prépa
    # -------------------------------------------------------------------
    @property
    def taux_presence_prepa(self):
        return round((self.nb_presents_prepa / self.nb_inscrits_prepa) * 100, 1) if self.nb_inscrits_prepa else 0

    # -------------------------------------------------------------------
    # 🎯 Objectifs dynamiques (annuels)
    # -------------------------------------------------------------------
    @property
    def objectif_annuel(self):
        return ObjectifPrepa.get_objectif(self.centre, self.date_prepa)

    @property
    def taux_atteinte_annuel(self):
        """
        Taux d’atteinte de l’objectif du centre pour l’année courante,
        basé sur les présents à l’Atelier 1.
        """
        if not self.objectif_annuel or not self.centre:
            return 0

        realise = (
            Prepa.objects.filter(
                centre=self.centre,
                date_prepa__year=self.date_prepa.year,
                type_prepa=self.TypePrepa.ATELIER1,
            ).aggregate(total=models.Sum("nb_presents_prepa"))["total"]
            or 0
        )

        return round((realise / self.objectif_annuel) * 100, 1) if self.objectif_annuel else 0

    @property
    def reste_a_faire(self):
        """
        Objectif restant pour l’année courante,
        basé sur l’Atelier 1 (entrées effectives dans le dispositif).
        """
        if not self.objectif_annuel or not self.centre:
            return 0

        realise = (
            Prepa.objects.filter(
                centre=self.centre,
                date_prepa__year=self.date_prepa.year,
                type_prepa=self.TypePrepa.ATELIER1,
            ).aggregate(total=models.Sum("nb_presents_prepa"))["total"]
            or 0
        )

        return max(self.objectif_annuel - realise, 0)

    # -------------------------------------------------------------------
    # 📉 Rétention de parcours (Atelier1 → Atelier6)
    # -------------------------------------------------------------------
    @classmethod
    def taux_retention(cls, centre, annee):
        debut = (
            cls.objects.filter(centre=centre, type_prepa=cls.TypePrepa.ATELIER1, date_prepa__year=annee)
            .aggregate(total=models.Sum("nb_presents_prepa"))["total"]
            or 0
        )
        fin = (
            cls.objects.filter(centre=centre, type_prepa=cls.TypePrepa.ATELIER6, date_prepa__year=annee)
            .aggregate(total=models.Sum("nb_presents_prepa"))["total"]
            or 0
        )
        return round((fin / debut) * 100, 1) if debut else 0

    # -------------------------------------------------------------------
    # 👥 Totaux d’accueillis (présents)
    # -------------------------------------------------------------------
    @classmethod
    def total_accueillis(cls, annee: Optional[int] = None, centre=None, departement=None) -> int:
        """
        Total des personnes effectivement accueillies dans le dispositif Prépa
        (référence = présents à l’Atelier 1)
        """
        annee = annee or localdate().year
        qs = cls.objects.filter(
            date_prepa__year=annee,
            type_prepa=cls.TypePrepa.ATELIER1
        )

        if centre:
            qs = qs.filter(centre=centre)
        if departement:
            qs = [d for d in qs if d.centre and d.centre.departement == departement]
            return sum(d.nb_presents_prepa for d in qs)

        total = qs.aggregate(total=models.Sum("nb_presents_prepa"))["total"] or 0
        return total

    @classmethod
    def accueillis_par_centre(cls, annee: Optional[int] = None) -> Dict[str, int]:
        """
        Total des personnes effectivement accueillies (Atelier 1) par centre.
        """
        annee = annee or localdate().year
        data = {}
        for centre in Centre.objects.all():
            total = cls.total_accueillis(annee=annee, centre=centre)
            data[getattr(centre, "nom", str(centre))] = total
        return data

    @classmethod
    def accueillis_par_departement(cls, annee: Optional[int] = None) -> Dict[str, int]:
        """
        Total des personnes effectivement accueillies (Atelier 1) par département.
        """
        annee = annee or localdate().year
        data: Dict[str, int] = {}
        for centre in Centre.objects.all():
            dep = getattr(centre, "departement", None)
            if not dep:
                continue
            total = cls.total_accueillis(annee=annee, departement=dep)
            data[dep] = data.get(dep, 0) + total
        return dict(sorted(data.items()))

    # -------------------------------------------------------------------
    # 🎯 Reste à faire
    # -------------------------------------------------------------------
    @classmethod
    def reste_a_faire_centre(cls, annee: Optional[int] = None) -> Dict[str, int]:
        """
        Reste à faire par centre, basé sur Atelier 1.
        """
        annee = annee or localdate().year
        data = {}
        for obj in ObjectifPrepa.objects.filter(annee=annee):
            realise = cls.total_accueillis(annee=annee, centre=obj.centre)
            reste = max(obj.valeur_objectif - realise, 0)
            data[getattr(obj.centre, "nom", str(obj.centre))] = reste
        return data

    @classmethod
    def reste_a_faire_departement(cls, annee: Optional[int] = None) -> Dict[str, int]:
        """
        Reste à faire par département, basé sur Atelier 1.
        """
        annee = annee or localdate().year
        data: Dict[str, int] = {}
        for obj in ObjectifPrepa.objects.filter(annee=annee).select_related("centre"):
            dep = getattr(obj.centre, "departement", None)
            if not dep:
                continue
            realise_dep = cls.total_accueillis(annee=annee, departement=dep)
            data[dep] = data.get(dep, 0) + max(obj.valeur_objectif - realise_dep, 0)
        return dict(sorted(data.items()))

    @classmethod
    def reste_a_faire_total(cls, annee: Optional[int] = None) -> int:
        annee = annee or localdate().year
        objectif_total = ObjectifPrepa.objects.filter(annee=annee).aggregate(total=models.Sum("valeur_objectif"))["total"] or 0
        realise_total = cls.total_accueillis(annee=annee)
        return max(objectif_total - realise_total, 0)

    # -------------------------------------------------------------------
    # 🧾 Synthèse globale
    # -------------------------------------------------------------------
    @classmethod
    def synthese_objectifs(cls, annee: Optional[int] = None) -> Dict[str, Any]:
        annee = annee or localdate().year
        objectif_total = ObjectifPrepa.objects.filter(annee=annee).aggregate(
            total=models.Sum("valeur_objectif")
        )["total"] or 0

        # ✅ Réalisé = personnes présentes à Atelier 1
        realise_total = (
            cls.objects.filter(
                date_prepa__year=annee,
                type_prepa=cls.TypePrepa.ATELIER1
            ).aggregate(total=models.Sum("nb_presents_prepa"))["total"]
            or 0
        )

        taux_atteinte = round((realise_total / objectif_total) * 100, 1) if objectif_total else 0

        return {
            "annee": annee,
            "objectif_total": objectif_total,
            "realise_total": realise_total,
            "taux_atteinte_total": taux_atteinte,
            "reste_a_faire_total": max(objectif_total - realise_total, 0),
            "par_centre": cls.reste_a_faire_centre(annee),
            "par_departement": cls.reste_a_faire_departement(annee),
        }

    @classmethod
    def ateliers_filtered(cls, **filters):
        return cls.objects.ateliers().filter(**filters)


    @classmethod
    def ic_filtered(cls, **filters):
        return cls.objects.ic().filter(**filters)
            
# -------------------------------------------------------------------
# 🎯 OBJECTIFS PREPA – par centre (annuel)
# -------------------------------------------------------------------
class ObjectifPrepa(BaseModel):
    """Objectifs Prépa : objectifs annuels par centre."""

    centre = models.ForeignKey(
        Centre,
        on_delete=models.CASCADE,
        related_name="objectifs_prepa",
        verbose_name=_("Centre de formation"),
    )
    departement = models.CharField(
        max_length=3,
        blank=True,
        null=True,
        verbose_name=_("Département"),
    )
    annee = models.PositiveIntegerField(verbose_name=_("Année"))
    valeur_objectif = models.PositiveIntegerField(verbose_name=_("Objectif annuel (personnes)"))
    commentaire = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Objectif Prépa (centre)")
        verbose_name_plural = _("Objectifs Prépa (centres)")
        ordering = ["-annee"]
        constraints = [
            models.UniqueConstraint(fields=["centre", "annee"], name="uniq_objectif_prepa_centre_annee")
        ]
        indexes = [models.Index(fields=["centre", "annee"])]

    def __str__(self):
        base = str(self.centre)
        if self.departement:
            base += f" ({self.departement})"
        return f"{base} – {self.annee}"

    # -------------------------------------------------------------------
    # 🔹 Données réelles issues de Prepa (INFO + ATELIERS)
    # -------------------------------------------------------------------
    @property
    def data_prepa(self) -> Dict[str, int]:
        """
        Retourne un agrégat de toutes les données Prépa du centre pour l’année donnée :
        - infos collectives : places, prescriptions, présents, adhésions
        - ateliers : inscrits, présents, absents
        """
        if hasattr(self, "_data_prepa_cache"):
            return self._data_prepa_cache

        # --- Information collective ---
        agg_info = (
            Prepa.objects.filter(
                centre=self.centre,
                date_prepa__year=self.annee,
                type_prepa=Prepa.TypePrepa.INFO_COLLECTIVE,
            ).aggregate(
                total_places=models.Sum("nombre_places_ouvertes"),
                total_prescriptions=models.Sum("nombre_prescriptions"),
                total_presents_info=models.Sum("nb_presents_info"),
                total_adhesions=models.Sum("nb_adhesions"),
            )
            or {}
        )

        # --- Ateliers Prépa ---
        agg_ateliers = (
            Prepa.objects.filter(
                centre=self.centre,
                date_prepa__year=self.annee,
                type_prepa__startswith="atelier",
            ).aggregate(
                total_inscrits=models.Sum("nb_inscrits_prepa"),
                total_presents=models.Sum("nb_presents_prepa"),
                total_absents=models.Sum("nb_absents_prepa"),
                total_atelier1=models.Sum(
                    models.Case(
                        models.When(type_prepa=Prepa.TypePrepa.ATELIER1, then="nb_presents_prepa"),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                total_atelier6=models.Sum(
                    models.Case(
                        models.When(type_prepa=Prepa.TypePrepa.ATELIER6, then="nb_presents_prepa"),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
            )
            or {}
        )

        self._data_prepa_cache = {
            # Info collective
            "places": agg_info.get("total_places") or 0,
            "prescriptions": agg_info.get("total_prescriptions") or 0,
            "presents_info": agg_info.get("total_presents_info") or 0,
            "adhesions": agg_info.get("total_adhesions") or 0,
            # Ateliers
            "inscrits": agg_ateliers.get("total_inscrits") or 0,
            "presents": agg_ateliers.get("total_presents") or 0,
            "absents": agg_ateliers.get("total_absents") or 0,
            "atelier1": agg_ateliers.get("total_atelier1") or 0,
            "atelier6": agg_ateliers.get("total_atelier6") or 0,
        }
        return self._data_prepa_cache

    # -------------------------------------------------------------------
    # 🔹 Ratios et taux
    # -------------------------------------------------------------------
    def _ratio(self, num, den):
        return round((num / den) * 100, 1) if den else 0

    @property
    def taux_prescription(self):
        """% de remplissage des places ouvertes"""
        return self._ratio(self.data_prepa["prescriptions"], self.data_prepa["places"])

    @property
    def taux_presence_info(self):
        """% de présents parmi les prescrits à l'information collective"""
        return self._ratio(self.data_prepa["presents_info"], self.data_prepa["prescriptions"])

    @property
    def taux_adhesion(self):
        """% d'adhésions parmi les présents à l'information collective"""
        return self._ratio(self.data_prepa["adhesions"], self.data_prepa["presents_info"])

    @property
    def taux_presence_ateliers(self):
        """% de présence globale sur tous les ateliers"""
        return self._ratio(self.data_prepa["presents"], self.data_prepa["inscrits"])

    @property
    def taux_atteinte(self):
        """% de l’objectif atteint — basé sur les entrées Atelier 1"""
        return self._ratio(self.data_prepa["atelier1"], self.valeur_objectif)

    @property
    def reste_a_faire(self):
        """Objectif restant (objectif - entrées Atelier 1)"""
        return max(self.valeur_objectif - self.data_prepa["atelier1"], 0)

    # -------------------------------------------------------------------
    # 🔹 Synthèse globale (pour API / exports)
    # -------------------------------------------------------------------
    def synthese_globale(self) -> Dict[str, Any]:
        """
        Données agrégées cohérentes avec le front actuel.
        On garde les mêmes clés pour compatibilité.
        """
        return {
            "objectif_id": self.id,
            "centre_id": getattr(self.centre, "id", None),
            "centre": getattr(self.centre, "nom", str(self.centre)),
            "annee": self.annee,
            "objectif": self.valeur_objectif,

            # --- Réalisations ---
            "realise": self.data_prepa["atelier1"],  # ✅ entrées effectives
            "adhesions": self.data_prepa["adhesions"],
            "absents": self.data_prepa["absents"],

            # --- Taux (compatibles avec le front) ---
            "taux_prescription": self.taux_prescription,
            "taux_presence": self.taux_presence_info,     # info collective
            "taux_adhesion": self.taux_adhesion,
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
