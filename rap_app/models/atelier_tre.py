# models/atelier_tre.py
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.db.models import Exists, OuterRef, Count, Q
from django.db.models import QuerySet

from .base import BaseModel
from .centres import Centre
from .candidat import Candidat


class AtelierTRE(BaseModel):
    class TypeAtelier(models.TextChoices):
        ATELIER_1 = "atelier_1", _("Atelier 1 - Exploration et positionnement")
        ATELIER_2 = "atelier_2", _("Atelier 2 - CV et lettre de motivation")
        ATELIER_3 = "atelier_3", _("Atelier 3 - Simulation entretien")
        ATELIER_4 = "atelier_4", _("Atelier 4 - Prospection entreprise")
        ATELIER_5 = "atelier_5", _("Atelier 5 - Réseaux sociaux pro")
        ATELIER_6 = "atelier_6", _("Atelier 6 - Posture professionnelle")
        ATELIER_7 = "atelier_7", _("Atelier 7 - Bilan et plan d’action")
        AUTRE     = "autre",     _("Autre")

    type_atelier = models.CharField(
        max_length=30,
        choices=TypeAtelier.choices,
        verbose_name=_("Type d’atelier"),
        help_text=_("Type d’atelier collectif"),
    )

    # ✅ réintroduction (tolérante)
    date_atelier = models.DateTimeField(
        _("Date de l'atelier"),
        null=True, blank=True,
        help_text=_("Date/heure de l’atelier"),
    )

    centre = models.ForeignKey(
        Centre,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="ateliers_tre",
        verbose_name=_("Centre de formation"),
        help_text=_("Centre où se déroule la formation"),
    )

    candidats = models.ManyToManyField(
        Candidat,
        related_name="ateliers_tre",
        blank=True,
        verbose_name=_("Candidats inscrits"),
        help_text=_("Candidats liés à cet atelier"),
    )

    class Meta:
        verbose_name = _("Atelier TRE")
        verbose_name_plural = _("Ateliers TRE")
        ordering = ["-date_atelier", "-id"]  # si null → tri secondaire par id
        indexes = [
            models.Index(fields=["type_atelier"], name="idx_ateliertre_type"),
            models.Index(fields=["centre"], name="idx_ateliertre_centre"),
            models.Index(fields=["date_atelier"], name="idx_ateliertre_date"),
        ]

    def __str__(self):
        label = self.get_type_atelier_display()
        if self.date_atelier:
            return f"{label} – {self.date_atelier:%d/%m/%Y %H:%M}"
        return label

    @property
    def nb_inscrits(self) -> int:
        return self.candidats.count()

    @staticmethod
    def annotate_candidats_with_atelier_flags(qs: QuerySet) -> QuerySet:
        """
        Annoter un QuerySet de Candidat avec :
        - has_<type>   : bool (au moins un atelier de ce type)
        - count_<type> : int  (nombre d'ateliers de ce type)
        Et conserver un alias 'count_atelier_autre' pour compat front/sérializer.
        """
        annotations = {}
        for key, _label in AtelierTRE.TypeAtelier.choices:
            # ex: has_atelier_1, has_autre…
            annotations[f"has_{key}"] = Exists(
                AtelierTRE.objects.filter(type_atelier=key, candidats=OuterRef("pk"))
            )
            # ex: count_atelier_1, count_autre…
            annotations[f"count_{key}"] = Count(
                "ateliers_tre",
                filter=Q(ateliers_tre__type_atelier=key),
                distinct=True,
            )

        # ✅ alias pour compatibilité (le front/sérializer lit count_atelier_autre)
        if "count_autre" in annotations:
            annotations["count_atelier_autre"] = annotations["count_autre"]

        return qs.annotate(**annotations)
    

class PresenceStatut(models.TextChoices):
    PRESENT = "present", "Présent"
    ABSENT = "absent", "Absent"
    EXCUSE = "excuse", "Excusé"
    INCONNU = "inconnu", "Non renseigné"  


class AtelierTREPresence(BaseModel):
    """
    Une ligne par (atelier, candidat) pour enregistrer la présence.
    Ne casse pas la M2M existante `AtelierTRE.candidats`.
    """
    atelier = models.ForeignKey(
        "AtelierTRE", on_delete=models.CASCADE,
        related_name="presences", verbose_name=_("Atelier")
    )
    candidat = models.ForeignKey(
        Candidat, on_delete=models.CASCADE,
        related_name="presences_ateliers", verbose_name=_("Candidat")
    )
    statut = models.CharField(
        max_length=15, choices=PresenceStatut.choices,
        default=PresenceStatut.INCONNU, verbose_name=_("Statut de présence")
    )
    commentaire = models.TextField(blank=True, null=True, verbose_name=_("Commentaire"))

    class Meta:
        verbose_name = _("Présence à un atelier")
        verbose_name_plural = _("Présences à des ateliers")
        constraints = [
            models.UniqueConstraint(
                fields=["atelier", "candidat"],
                name="uniq_presence_atelier_candidat",
            )
        ]

    def __str__(self):
        return f"{self.atelier_id} / {self.candidat_id} → {self.get_statut_display()}"

# Helpers optionnels sur AtelierTRE (mets-les dans la classe AtelierTRE si tu veux)
def ateliertre_set_presence(self, candidat: Candidat, statut: str, commentaire: str | None = None, user=None):
    """
    Upsert de présence pour un candidat donné.
    À copier comme méthode d'instance d'AtelierTRE si souhaité.
    """
    with transaction.atomic():
        obj, _ = AtelierTREPresence.objects.get_or_create(
            atelier=self, candidat=candidat,
            defaults={"statut": statut, "commentaire": commentaire},
        )
        obj.statut = statut
        if commentaire is not None:
            obj.commentaire = commentaire
        try:
            obj.save(user=user)
        except TypeError:
            obj.save()
        return obj

# si tu veux l’avoir sur le modèle directement :
AtelierTRE.set_presence = ateliertre_set_presence  # monkey patch pratique
