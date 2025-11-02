from datetime import date
from typing import Optional, Dict, Any

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import localdate

from .base import BaseModel
from .centres import Centre


# -------------------------------------------------------------------
# 📊 ACTIVITÉS : données réelles (séances, effectifs)
# -------------------------------------------------------------------
class Prepa2(BaseModel):
    """
    Activité PrépaComp : Information collective ou ateliers thématiques.

    - Pour les informations collectives :
      * nombre_places_ouvertes : places disponibles pour les prescripteurs
      * nombre_prescriptions   : candidats envoyés par les prescripteurs
      * nb_presents_info       : candidats présents à la séance
      * nb_absents_info        : candidats absents à la séance
      * nb_adhesions           : candidats qui adhèrent au dispositif

    - Pour les ateliers :
      * nb_inscrits_atelier    : participants inscrits à l’atelier
      * nb_presents_atelier    : présents à l’atelier
      * nb_absents_atelier     : absents à l’atelier
    """

    class TypePrepa(models.TextChoices):
        INFO_COLLECTIVE = "info_collective", _("Information collective")
        AT1 = "atelier_1", _("Atelier 1")
        AT2 = "atelier_2", _("Atelier 2")
        AT3 = "atelier_3", _("Atelier 3")
        AT4 = "atelier_4", _("Atelier 4")
        AT5 = "atelier_5", _("Atelier 5")
        AT6 = "atelier_6", _("Atelier 6")
        AUTRE = "autre", _("Autre activité PrépaComp")

    type_prepa = models.CharField(max_length=40, choices=TypePrepa.choices, verbose_name=_("Type d’activité"))
    date_prepa = models.DateField(_("Date"), help_text=_("Date de la séance ou de la semaine concernée"))

    centre = models.ForeignKey(
        Centre,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prepas2",
        verbose_name=_("Centre de formation"),
    )

    # --- Données Information Collective ---
    nombre_places_ouvertes = models.PositiveIntegerField(default=0, verbose_name=_("Places ouvertes (IC)"))
    nombre_prescriptions = models.PositiveIntegerField(default=0, verbose_name=_("Prescriptions (IC)"))
    nb_presents_info = models.PositiveIntegerField(default=0, verbose_name=_("Présents (IC)"))
    nb_absents_info = models.PositiveIntegerField(default=0, verbose_name=_("Absents (IC)"))
    nb_adhesions = models.PositiveIntegerField(default=0, verbose_name=_("Adhésions (IC)"))

    # --- Données Ateliers ---
    nb_inscrits_atelier = models.PositiveIntegerField(default=0, verbose_name=_("Inscrits (Atelier)"))
    nb_presents_atelier = models.PositiveIntegerField(default=0, verbose_name=_("Présents (Atelier)"))
    nb_absents_atelier = models.PositiveIntegerField(default=0, verbose_name=_("Absents (Atelier)"))

    commentaire = models.TextField(blank=True, null=True, verbose_name=_("Commentaire / notes"))

    class Meta:
        verbose_name = _("Séance PrépaComp")
        verbose_name_plural = _("Séances PrépaComp")
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
        self.nb_absents_atelier = max(0, self.nb_inscrits_atelier - self.nb_presents_atelier)
        self.nb_absents_info = max(0, self.nombre_prescriptions - self.nb_presents_info)

        # Si l'utilisateur est passé explicitement (depuis admin ou API)
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
        """Prescriptions / places ouvertes (IC)."""
        return round((self.nombre_prescriptions / self.nombre_places_ouvertes) * 100, 1) if self.nombre_places_ouvertes else 0

    @property
    def taux_presence_info(self):
        """Présents / prescriptions (IC)."""
        return round((self.nb_presents_info / self.nombre_prescriptions) * 100, 1) if self.nombre_prescriptions else 0

    @property
    def taux_adhesion(self):
        """Adhésions / présents (IC)."""
        return round((self.nb_adhesions / self.nb_presents_info) * 100, 1) if self.nb_presents_info else 0

    # -------------------------------------------------------------------
    # 📊 Taux pour ateliers
    # -------------------------------------------------------------------
    @property
    def taux_presence_atelier(self):
        """Présents / inscrits (Atelier)."""
        return round((self.nb_presents_atelier / self.nb_inscrits_atelier) * 100, 1) if self.nb_inscrits_atelier else 0

    # -------------------------------------------------------------------
    # 🎯 Objectifs dynamiques (annuels)
    # -------------------------------------------------------------------
    @property
    def objectif_annuel(self):
        return ObjectifPrepa.get_objectif(self.centre, self.date_prepa)

    @property
    def taux_atteinte_annuel(self):
        """Présents IC cumulés / objectif annuel."""
        if not self.objectif_annuel or not self.centre:
            return 0
        cumul_annuel = (
            Prepa2.objects.filter(
                centre=self.centre,
                date_prepa__year=self.date_prepa.year,
                type_prepa=self.TypePrepa.INFO_COLLECTIVE,
            ).aggregate(total=models.Sum("nb_presents_info"))["total"]
            or 0
        )
        return round((cumul_annuel / self.objectif_annuel) * 100, 1)

    @property
    def reste_a_faire(self):
        """Présents IC restants pour atteindre l’objectif annuel."""
        if not self.objectif_annuel or not self.centre:
            return 0
        cumul_annuel = (
            Prepa2.objects.filter(
                centre=self.centre,
                date_prepa__year=self.date_prepa.year,
                type_prepa=self.TypePrepa.INFO_COLLECTIVE,
            ).aggregate(total=models.Sum("nb_presents_info"))["total"]
            or 0
        )
        return max(self.objectif_annuel - cumul_annuel, 0)

    # -------------------------------------------------------------------
    # 📉 Rétention de parcours (AT1 → AT6)
    # -------------------------------------------------------------------
    @classmethod
    def taux_retention(cls, centre, annee):
        """Compare le nombre de présents entre Atelier 1 et Atelier 6."""
        debut = (
            cls.objects.filter(centre=centre, type_prepa=cls.TypePrepa.AT1, date_prepa__year=annee)
            .aggregate(total=models.Sum("nb_presents_atelier"))["total"]
            or 0
        )
        fin = (
            cls.objects.filter(centre=centre, type_prepa=cls.TypePrepa.AT6, date_prepa__year=annee)
            .aggregate(total=models.Sum("nb_presents_atelier"))["total"]
            or 0
        )
        return round((fin / debut) * 100, 1) if debut else 0

    # -------------------------------------------------------------------
    # 👥 Totaux d’accueillis (présents)
    # -------------------------------------------------------------------
    @classmethod
    def total_accueillis(cls, annee: Optional[int] = None, centre=None, departement=None, type_prepa=None) -> int:
        """Total des personnes accueillies selon les filtres."""
        today = localdate()
        annee = annee or today.year
        qs = cls.objects.filter(date_prepa__year=annee)

        if centre:
            qs = qs.filter(centre=centre)
        if departement:
            # Filtrage Python sur la propriété centre.departement
            qs = [p for p in qs if p.centre and p.centre.departement == departement]

            if type_prepa == cls.TypePrepa.INFO_COLLECTIVE:
                total = sum(p.nb_presents_info for p in qs)
            elif type_prepa and type_prepa.startswith("atelier"):
                total = sum(p.nb_presents_atelier for p in qs)
            else:
                total = sum((p.nb_presents_info + p.nb_presents_atelier) for p in qs)

            return total



        if type_prepa == cls.TypePrepa.INFO_COLLECTIVE:
            total = qs.aggregate(total=models.Sum("nb_presents_info"))["total"] or 0
        elif type_prepa and type_prepa.startswith("atelier"):
            total = qs.aggregate(total=models.Sum("nb_presents_atelier"))["total"] or 0
        else:
            total_ic = qs.aggregate(total=models.Sum("nb_presents_info"))["total"] or 0
            total_at = qs.aggregate(total=models.Sum("nb_presents_atelier"))["total"] or 0
            total = total_ic + total_at

        return total

    @classmethod
    def accueillis_par_centre(cls, annee: Optional[int] = None, type_prepa=None) -> Dict[str, int]:
        """Retourne un dictionnaire {centre: total_accueillis}."""
        annee = annee or localdate().year
        data = {}
        for centre in Centre.objects.all():
            data[getattr(centre, "nom", str(centre))] = cls.total_accueillis(annee=annee, centre=centre, type_prepa=type_prepa)
        return data

    @classmethod
    def accueillis_par_departement(cls, annee: Optional[int] = None, type_prepa=None) -> Dict[str, int]:
        """Retourne un dictionnaire {departement: total_accueillis}."""
        annee = annee or localdate().year
        data = {}

        for centre in Centre.objects.all():
            dep = getattr(centre, "departement", None)
            if not dep:
                continue
            total = cls.total_accueillis(annee=annee, departement=dep, type_prepa=type_prepa)
            data[dep] = data.get(dep, 0) + total

        return dict(sorted(data.items()))


    # -------------------------------------------------------------------
    # 🎯 Reste à faire
    # -------------------------------------------------------------------
    @classmethod
    def reste_a_faire_centre(cls, annee: Optional[int] = None) -> Dict[str, int]:
        """Retourne le reste à faire pour chaque centre."""
        annee = annee or localdate().year
        data = {}
        for obj in ObjectifPrepa.objects.filter(annee=annee):
            realise = cls.total_accueillis(annee=annee, centre=obj.centre, type_prepa=cls.TypePrepa.INFO_COLLECTIVE)
            reste = max(obj.valeur_objectif - realise, 0)
            data[getattr(obj.centre, "nom", str(obj.centre))] = reste
        return data

    @classmethod
    def reste_a_faire_departement(cls, annee: Optional[int] = None) -> Dict[str, int]:
        """
        Retourne le reste à faire pour chaque département (somme des centres).
        Utilise la propriété centre.departement dérivée du code postal.
        """
        annee = annee or localdate().year
        data: Dict[str, int] = {}

        # On parcourt tous les objectifs existants
        for obj in ObjectifPrepa.objects.filter(annee=annee).select_related("centre"):
            dep = getattr(obj.centre, "departement", None)
            if not dep:
                continue  # si le code postal est vide, on ignore

            # Récupère le total réalisé dans ce département
            realise_dep = cls.total_accueillis(
                annee=annee,
                departement=dep,
                type_prepa=cls.TypePrepa.INFO_COLLECTIVE,
            )

            # Calcule le total des objectifs du département
            if dep not in data:
                data[dep] = 0
            data[dep] += max(obj.valeur_objectif - realise_dep, 0)

        return dict(sorted(data.items()))

    @classmethod
    def reste_a_faire_total(cls, annee: Optional[int] = None) -> int:
        """Retourne le reste à faire global (tous centres, toutes régions)."""
        annee = annee or localdate().year
        objectif_total = ObjectifPrepa.objects.filter(annee=annee).aggregate(total=models.Sum("valeur_objectif"))["total"] or 0
        realise_total = cls.total_accueillis(annee=annee, type_prepa=cls.TypePrepa.INFO_COLLECTIVE)
        return max(objectif_total - realise_total, 0)

    # -------------------------------------------------------------------
    # 🧾 Synthèse globale
    # -------------------------------------------------------------------
    @classmethod
    def synthese_objectifs(cls, annee: Optional[int] = None) -> Dict[str, Any]:
        """Retourne une synthèse globale : objectifs, réalisés, reste, taux."""
        annee = annee or localdate().year
        objectif_total = ObjectifPrepa.objects.filter(annee=annee).aggregate(total=models.Sum("valeur_objectif"))["total"] or 0
        realise_total = cls.total_accueillis(annee=annee, type_prepa=cls.TypePrepa.INFO_COLLECTIVE)
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


# -------------------------------------------------------------------
# 🎯 OBJECTIFS – par centre uniquement (annuel)
# -------------------------------------------------------------------
class ObjectifPrepa(BaseModel):
    """Objectifs PrépaComp : objectifs annuels par centre."""

    centre = models.ForeignKey(
        Centre,
        on_delete=models.CASCADE,
        related_name="objectifs_prepa",
        verbose_name=_("Centre de formation"),
    )
    departement = models.CharField(max_length=3, blank=True, null=True, verbose_name=_("Département"))
    annee = models.PositiveIntegerField(verbose_name=_("Année"))
    valeur_objectif = models.PositiveIntegerField(verbose_name=_("Objectif annuel (personnes)"))
    commentaire = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Objectif PrépaComp (centre)")
        verbose_name_plural = _("Objectifs PrépaComp (centres)")
        ordering = ["-annee"]
        constraints = [models.UniqueConstraint(fields=["centre", "annee"], name="uniq_objectif_centre_annee")]

    def __str__(self):
        base = str(self.centre)
        if self.departement:
            base += f" ({self.departement})"
        return f"{base} – {self.annee}"

    # -------------------------------------------------------------------
    # 📊 Données agrégées
    # -------------------------------------------------------------------
    @property
    def data_prepa(self) -> Dict[str, int]:
        """Retourne les agrégats pour ce centre et cette année (IC uniquement)."""
        if hasattr(self, "_data_prepa_cache"):
            return self._data_prepa_cache

        agg = (
            Prepa2.objects.filter(
                centre=self.centre,
                date_prepa__year=self.annee,
                type_prepa=Prepa2.TypePrepa.INFO_COLLECTIVE,
            ).aggregate(
                total_places=models.Sum("nombre_places_ouvertes"),
                total_prescriptions=models.Sum("nombre_prescriptions"),
                total_presents=models.Sum("nb_presents_info"),
                total_adhesions=models.Sum("nb_adhesions"),
            )
            or {}
        )
        self._data_prepa_cache = {
            "places": agg.get("total_places") or 0,
            "prescriptions": agg.get("total_prescriptions") or 0,
            "presents": agg.get("total_presents") or 0,
            "adhesions": agg.get("total_adhesions") or 0,
        }
        return self._data_prepa_cache

    @property
    def taux_prescription(self):
        return round((self.data_prepa["prescriptions"] / self.data_prepa["places"]) * 100, 1) if self.data_prepa["places"] else 0

    @property
    def taux_presence(self):
        return round((self.data_prepa["presents"] / self.data_prepa["prescriptions"]) * 100, 1) if self.data_prepa["prescriptions"] else 0

    @property
    def taux_adhesion(self):
        return round((self.data_prepa["adhesions"] / self.data_prepa["presents"]) * 100, 1) if self.data_prepa["presents"] else 0

    @property
    def taux_atteinte(self):
        return round((self.data_prepa["presents"] / self.valeur_objectif) * 100, 1) if self.valeur_objectif else 0

    @property
    def reste_a_faire(self):
        return max(self.valeur_objectif - self.data_prepa["presents"], 0)

    def synthese_globale(self) -> Dict[str, Any]:
        """Retourne les indicateurs principaux sous forme de dictionnaire."""
        return {
            "centre": getattr(self.centre, "nom", str(self.centre)),
            "annee": self.annee,
            "objectif": self.valeur_objectif,
            "realise": self.data_prepa["presents"],
            "adhesions": self.data_prepa["adhesions"],
            "taux_prescription": self.taux_prescription,
            "taux_presence": self.taux_presence,
            "taux_adhesion": self.taux_adhesion,
            "taux_atteinte": self.taux_atteinte,
            "reste_a_faire": self.reste_a_faire,
        }

    @classmethod
    def get_objectif(cls, centre, date):
        """Retourne l'objectif annuel pour un centre et une date donnée."""
        if not centre or not date:
            return None
        return (
            cls.objects.filter(centre=centre, annee=date.year)
            .values_list("valeur_objectif", flat=True)
            .first()
        )
        
    def save(self, *args, user=None, **kwargs):
        """
        Sauvegarde l'objectif en renseignant automatiquement le créateur / modificateur.
        """
        # Attribution automatique du user
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user

        # Copie du département depuis le centre si absent
        centre = getattr(self, "centre", None)
        if centre and not self.departement and getattr(centre, "departement", None):
            self.departement = centre.departement

        super().save(*args, **kwargs)

