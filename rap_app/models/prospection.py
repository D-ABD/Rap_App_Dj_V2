# models/prospection.py

import logging
from datetime import timedelta

from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Q, Count, Subquery, OuterRef
from django.db.models.functions import Now
from django.conf import settings

from .base import BaseModel
from .partenaires import Partenaire
from .prospection_choices import ProspectionChoices

logger = logging.getLogger(__name__)

# Constantes de longueur
MAX_TYPE_LENGTH = 20
MAX_STATUT_LENGTH = 20
MAX_MOTIF_LENGTH = 30
MAX_OBJECTIF_LENGTH = 30
MAX_MOYEN_LENGTH = 50


class ProspectionManager(models.Manager):
    def actives(self):
        return self.exclude(
            statut__in=[
                ProspectionChoices.STATUT_REFUSEE,
                ProspectionChoices.STATUT_ANNULEE,
            ]
        )

    def a_relancer(self, date=None):
        date = date or timezone.now().date()
        return (
            self.actives()
            .filter(relance_prevue__isnull=False, relance_prevue__lte=date)
        )

    def par_partenaire(self, partenaire_id):
        return self.filter(partenaire_id=partenaire_id).select_related('formation')

    def par_formation(self, formation_id):
        return self.filter(formation_id=formation_id).select_related('partenaire')

    def par_statut(self, statut):
        return self.filter(statut=statut)

    def statistiques_par_statut(self):
        stats = self.values('statut').annotate(count=Count('id')).order_by('statut')
        labels = ProspectionChoices.get_statut_labels()
        return {
            s['statut']: {
                'label': labels.get(s['statut'], s['statut']),
                'count': s['count']
            }
            for s in stats
        }


class Prospection(BaseModel):
    """
    Suivi d'une prospection vers un partenaire pour une formation éventuelle.
    Historique automatique de chaque modification de champ important.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prospections_attribuees",
        verbose_name=_("Responsable de la prospection")
    )

    centre = models.ForeignKey(
        'rap_app.Centre',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        related_name='prospections',
        verbose_name='Centre'
    )

    formation = models.ForeignKey(
        'rap_app.Formation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prospections'
    )

    partenaire = models.ForeignKey(
        'rap_app.Partenaire',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prospections'
    )

    date_prospection = models.DateTimeField(
        default=timezone.now, verbose_name=_("Date de prospection")
    )

    # Saisie libre de la date de relance prévue
    relance_prevue = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date de relance prévue"),
        help_text=_("Date de relance saisie par l’utilisateur")
    )

    type_prospection = models.CharField(
        max_length=MAX_TYPE_LENGTH,
        choices=ProspectionChoices.TYPE_PROSPECTION_CHOICES,
        default=ProspectionChoices.TYPE_PREMIER_CONTACT,
        verbose_name=_("Type de prospection")
    )
    motif = models.CharField(
        max_length=MAX_MOTIF_LENGTH,
        choices=ProspectionChoices.PROSPECTION_MOTIF_CHOICES,
        verbose_name=_("Motif")
    )
    statut = models.CharField(
        max_length=MAX_STATUT_LENGTH,
        choices=ProspectionChoices.PROSPECTION_STATUS_CHOICES,
        default=ProspectionChoices.STATUT_A_FAIRE,
        verbose_name=_("Statut")
    )
    objectif = models.CharField(
        max_length=MAX_OBJECTIF_LENGTH,
        choices=ProspectionChoices.PROSPECTION_OBJECTIF_CHOICES,
        default=ProspectionChoices.OBJECTIF_PRISE_CONTACT,
        verbose_name=_("Objectif")
    )
    commentaire = models.TextField(blank=True, null=True, verbose_name=_("Commentaire"))

    # ✅ moyen de contact saisi (écrasé à chaque mise à jour)
    moyen_contact = models.CharField(
        max_length=MAX_MOYEN_LENGTH,
        choices=ProspectionChoices.MOYEN_CONTACT_CHOICES,
        blank=True, null=True,
        verbose_name=_("Moyen de contact")
    )

    objects = models.Manager()
    custom = ProspectionManager()

    class Meta:
        verbose_name = _("Suivi de prospection")
        verbose_name_plural = _("Suivis de prospections")
        ordering = ['-date_prospection']
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['date_prospection']),
            models.Index(fields=['partenaire']),
            models.Index(fields=['formation']),
            models.Index(fields=['created_by']),
            models.Index(fields=['owner']),    # ✅ utile côté filtres
            models.Index(fields=['centre']),   # ✅ utile pour le scope staff
            models.Index(fields=['motif']),
            models.Index(fields=['objectif']),
            models.Index(fields=['moyen_contact']),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(date_prospection__lte=Now()),
                name='prosp_date_not_future'
            ),
            # ❌ contrainte "prosp_acceptee_contrat" retirée
        ]

    def __str__(self):
        formation = self.formation.nom if self.formation else _("Sans formation")
        partenaire_nom = self.partenaire.nom if self.partenaire else _("Sans partenaire")
        auteur = self.created_by.username if self.created_by else _("Anonyme")
        return f"{partenaire_nom} - {formation} - {self.get_statut_display()} ({auteur})"

    # ------------------- validation métier -------------------

    def clean(self):
        super().clean()
        # Si formation présente ET centre fixé, ils doivent correspondre
        if self.formation_id and self.centre_id and self.centre_id != self.formation.centre_id:
            raise ValidationError("Le centre de la prospection doit correspondre au centre de la formation.")

        if self.date_prospection and self.date_prospection > timezone.now():
            raise ValidationError({
                'date_prospection': _("La date de prospection ne peut pas être dans le futur.")
            })

        # ❌ règle applicative "Acceptée ⇒ objectif contrat" retirée

        if (
            self.statut in [ProspectionChoices.STATUT_REFUSEE, ProspectionChoices.STATUT_ANNULEE]
            and not self.commentaire
        ):
            raise ValidationError({
                'commentaire': _("Un commentaire est obligatoire pour un refus ou une annulation.")
            })

    # ------------------- synchro centre -------------------

    def sync_centre(self):
        """
        Ordre de priorité pour déterminer le centre :
        1) formation.centre si formation est renseignée
        2) sinon, default_centre du partenaire si présent
        3) sinon, on laisse tel quel (centre éventuellement saisi explicitement)
        """
        if self.formation_id:
            self.centre_id = self.formation.centre_id
        elif not self.centre_id and self.partenaire_id:
            self.centre_id = getattr(self.partenaire, 'default_centre_id', None)

    # ------------------- persistence -------------------

    def save(self, *args, **kwargs):
        self.sync_centre()

        updated_by   = kwargs.pop('updated_by', None)
        skip_history = kwargs.pop('skip_history', False)

        is_new = self.pk is None
        user = updated_by or getattr(self, 'created_by', None)

        TERMINAUX = {
            ProspectionChoices.STATUT_ACCEPTEE,
            ProspectionChoices.STATUT_REFUSEE,
            ProspectionChoices.STATUT_ANNULEE,
        }

        ancien = None
        if not is_new:
            try:
                # ✅ on charge TOUT ce qu'on compare ensuite
                ancien = (
                    Prospection.objects.only(
                        'statut', 'relance_prevue', 'moyen_contact',
                        'formation_id', 'partenaire_id', 'centre_id',
                        'type_prospection', 'objectif', 'motif', 'commentaire'
                    )
                    .get(pk=self.pk)
                )
            except Prospection.DoesNotExist:
                pass

        old_statut = getattr(ancien, "statut", None)

        # Cohérence statut ↔ relance
        if self.relance_prevue and self.statut not in TERMINAUX:
            self.statut = ProspectionChoices.STATUT_A_RELANCER
        elif not self.relance_prevue and self.statut == ProspectionChoices.STATUT_A_RELANCER:
            self.statut = ProspectionChoices.STATUT_EN_COURS

        # S'assurer que les validations de clean() s'appliquent bien
        self.full_clean()

        # Support update_fields: si statut a changé, forcer sa persistance
        if "update_fields" in kwargs:
            update_fields = set(kwargs.get("update_fields") or [])
            if old_statut is not None and old_statut != self.statut:
                update_fields.add("statut")
            kwargs["update_fields"] = list(update_fields)

        champs_suivis = [
            "statut", "type_prospection", "objectif",
            "motif", "commentaire",
            "formation_id", "partenaire_id", "centre_id",  # ✅ on trace aussi le centre
            "relance_prevue", "moyen_contact",
        ]
        changements: dict[str, tuple] = {}

        if not is_new and ancien is not None:
            for champ in champs_suivis:
                old, new = getattr(ancien, champ, None), getattr(self, champ)
                if old != new:
                    changements[champ] = (old, new)

        super().save(*args, **kwargs)

        if not skip_history and changements:
            username = getattr(user, 'username', None) or 'inconnu'
            logger.info(
                f"[Prospection #{self.pk}] Changements par {username} : "
                + "; ".join(f"{c}: {a}→{b}" for c, (a, b) in changements.items())
            )
            for champ, (old, new) in changements.items():
                self.creer_historique(
                    champ_modifie=champ,
                    ancienne_valeur=str(old),
                    nouvelle_valeur=str(new),
                    ancien_statut=old if champ == "statut" else self.statut,
                    nouveau_statut=new if champ == "statut" else self.statut,
                    type_prospection=self.type_prospection,
                    commentaire=self.commentaire or "",
                    resultat="",
                    moyen_contact=self.moyen_contact if champ == "moyen_contact" else None,
                    user=user,
                    prochain_contact=self.relance_prevue,
                )

    def creer_historique(
        self,
        *,
        champ_modifie: str,
        ancienne_valeur: str | None = None,
        nouvelle_valeur: str | None = None,
        ancien_statut: str | None = None,
        nouveau_statut: str | None = None,
        type_prospection: str | None = None,
        commentaire: str | None = None,
        resultat: str | None = None,
        prochain_contact=None,
        moyen_contact: str | None = None,
        user=None,
    ):
        ancien_statut = ancien_statut or self.statut
        nouveau_statut = nouveau_statut or self.statut
        type_prospection = type_prospection or self.type_prospection

        return HistoriqueProspection.objects.create(
            prospection=self,
            champ_modifie=champ_modifie,
            ancienne_valeur=ancienne_valeur or "",
            nouvelle_valeur=nouvelle_valeur or "",
            ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut,
            type_prospection=type_prospection,
            commentaire=commentaire or "",
            resultat=resultat or "",
            prochain_contact=prochain_contact,
            moyen_contact=moyen_contact or None,
        )

    @property
    def is_active(self):
        return self.statut not in [
            ProspectionChoices.STATUT_REFUSEE,
            ProspectionChoices.STATUT_ANNULEE
        ]

    @property
    def relance_necessaire(self):
        return bool(
            self.is_active and
            self.relance_prevue and
            self.relance_prevue <= timezone.now().date()
        )

    @property
    def historique_recent(self):
        return self.historiques.order_by('-date_modification')[:5]


class HistoriqueProspectionManager(models.Manager):
    """Manager pour filtrer et agréger les historiques de prospection."""

    def a_relancer_cette_semaine(self):
        today = timezone.now().date()
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        return self.filter(
            prochain_contact__range=(start, end)
        ).select_related('prospection', 'prospection__partenaire')

    def derniers_par_prospection(self):
        sub = (
            self.filter(prospection=OuterRef('prospection'))
            .order_by('-date_modification')
            .values('id')[:1]
        )
        return self.filter(id__in=Subquery(sub))


class HistoriqueProspection(BaseModel):
    """
    Trace un changement de champ pour une prospection,
    avec détail du champ modifié, ancienne et nouvelle valeurs,
    ancien/nouveau statut, type de prospection, etc.
    """
    prospection = models.ForeignKey(
        Prospection, on_delete=models.CASCADE,
        related_name="historiques", verbose_name=_("Prospection")
    )
    date_modification = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de modification")
    )

    champ_modifie   = models.CharField(max_length=50, verbose_name=_("Champ modifié"))
    ancienne_valeur = models.TextField(blank=True, null=True, verbose_name=_("Ancienne valeur"))
    nouvelle_valeur = models.TextField(blank=True, null=True, verbose_name=_("Nouvelle valeur"))

    ancien_statut = models.CharField(
        max_length=MAX_STATUT_LENGTH,
        choices=ProspectionChoices.PROSPECTION_STATUS_CHOICES,
        verbose_name=_("Ancien statut")
    )
    nouveau_statut = models.CharField(
        max_length=MAX_STATUT_LENGTH,
        choices=ProspectionChoices.PROSPECTION_STATUS_CHOICES,
        verbose_name=_("Nouveau statut")
    )
    type_prospection = models.CharField(
        max_length=MAX_TYPE_LENGTH,
        choices=ProspectionChoices.TYPE_PROSPECTION_CHOICES,
        default=ProspectionChoices.TYPE_NOUVEAU_PROSPECT,
        verbose_name=_("Type de prospection")
    )
    commentaire      = models.TextField(blank=True, null=True, verbose_name=_("Commentaire"))
    resultat         = models.TextField(blank=True, null=True, verbose_name=_("Résultat"))
    # on garde ce champ côté historique pour tracer les choix saisis à ce moment-là
    prochain_contact = models.DateField(blank=True, null=True, verbose_name=_("Prochain contact"))

    moyen_contact = models.CharField(
        max_length=MAX_MOYEN_LENGTH,
        choices=ProspectionChoices.MOYEN_CONTACT_CHOICES,
        blank=True, null=True, verbose_name=_("Moyen de contact")
    )

    objects = models.Manager()
    custom = HistoriqueProspectionManager()

    class Meta:
        verbose_name = _("Historique de prospection")
        verbose_name_plural = _("Historiques de prospections")
        ordering = ['-date_modification']
        indexes = [
            models.Index(fields=['prospection']),
            models.Index(fields=['date_modification']),
            models.Index(fields=['prochain_contact']),
            models.Index(fields=['nouveau_statut']),
        ]

    def __str__(self):
        return f"{self.date_modification.strftime('%d/%m/%Y')} – {self.get_nouveau_statut_display()}"

    def clean(self):
        super().clean()
        if self.ancien_statut == self.nouveau_statut:
            logger.warning(
                f"Historique sans changement de statut pour prospection #{self.prospection_id}"
            )

    def save(self, *args, **kwargs):
        """
        Persiste l'historique (pas de synchro automatique sur Prospection).
        """
        skip_history = kwargs.pop('skip_history', False)  # réservé si utile plus tard
        self.full_clean()
        with transaction.atomic():
            super().save(*args, **kwargs)

    @property
    def est_recent(self) -> bool:
        return (timezone.now().date() - self.date_modification.date()).days <= 7

    @property
    def jours_avant_relance(self) -> int:
        if not self.prochain_contact:
            return -1
        delta = (self.prochain_contact - timezone.now().date()).days
        return max(0, delta)

    @property
    def relance_urgente(self) -> bool:
        return 0 <= self.jours_avant_relance <= 2

    @classmethod
    def get_relances_a_venir(cls, jours=7):
        today = timezone.now().date()
        limite = today + timedelta(days=jours)
        return (
            cls.objects
            .filter(prochain_contact__range=(today, limite))
            .exclude(prospection__statut__in=[
                ProspectionChoices.STATUT_REFUSEE,
                ProspectionChoices.STATUT_ANNULEE,
            ])
            .select_related('prospection', 'prospection__partenaire')
            .order_by('prochain_contact')
        )
