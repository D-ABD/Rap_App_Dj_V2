from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import BaseModel
from .candidat import Candidat


class AtelierTRE(BaseModel):
    """
    🧑‍🏫 Atelier TRE collectif (CV, entretien, prospection, etc.)
    Plusieurs candidats peuvent y être inscrits avec indication de présence.
    """
    class TypeAtelier(models.TextChoices):
        ATELIER_1 = "atelier_1", _("Atelier 1 - CV et lettre de motivation")
        ATELIER_2 = "atelier_2", _("Atelier 2 - Simulation entretien")
        ATELIER_3 = "atelier_3", _("Atelier 3 - Prospection entreprise")
        ATELIER_4 = "atelier_4", _("Atelier 4 - Réseaux sociaux pro")
        ATELIER_5 = "atelier_5", _("Atelier 5 - Posture professionnelle")
        ATELIER_6 = "atelier_6", _("Atelier 6 - Bilan et plan d’action")
        AUTRE = "autre", _("Autre")

    type_atelier = models.CharField(
        max_length=30,
        choices=TypeAtelier.choices,
        verbose_name=_("Type d’atelier"),
        help_text=_("Type d’atelier collectif")
    )

    date = models.DateField(
        verbose_name=_("Date de l'atelier"),
        help_text=_("Date à laquelle l'atelier a eu lieu")
    )



    remarque = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Remarques globales"),
        help_text=_("Commentaires ou contexte de l’atelier")
    )

    candidats = models.ManyToManyField(
        Candidat,
        through="ParticipationAtelierTRE",
        related_name="ateliers_tre_collectifs",
        verbose_name=_("Candidats inscrits"),
        help_text=_("Candidats ayant participé à cet atelier")
    )

    class Meta:
        verbose_name = _("Atelier TRE")
        verbose_name_plural = _("Ateliers TRE")
        ordering = ['-date',                                ]
        unique_together = ('type_atelier', 'date')

    def __str__(self):
        label = self.get_type_atelier_display()
        date_str = self.date.strftime('%d/%m/%Y')
        return f"{label} - {date_str}"

    @property
    def nb_participants_prevus(self) -> int:
        return self.participationateliertre_set.count()

    @property
    def nb_participants_presents(self) -> int:
        return self.participationateliertre_set.filter(present=True).count()

class ParticipationAtelierTRE(models.Model):
    candidat = models.ForeignKey(Candidat, on_delete=models.CASCADE, related_name="participations_ateliers" )
    ateliertre = models.ForeignKey(AtelierTRE, on_delete=models.CASCADE)
    present = models.BooleanField(default=False, verbose_name=_("Présent ?"))

    commentaire_individuel = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Commentaire"),
        help_text=_("Remarques ou observations individuelles")
    )

    class Meta:
        unique_together = ('candidat', 'ateliertre')
        verbose_name = _("Participation à un atelier TRE")
        verbose_name_plural = _("Participations à des ateliers TRE")

    def __str__(self):
        statut = _("présent") if self.present else _("absent")
        return f"{self.candidat} - {self.ateliertre} ({statut})"
