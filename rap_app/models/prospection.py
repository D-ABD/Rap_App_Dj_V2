import logging
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Q, F, Count
from django.utils.functional import cached_property
from django.db.models.functions import Now
from django.db.models import Subquery, OuterRef, Max

from .base import BaseModel
from .formations import Formation
from .partenaires import Partenaire
from .prospection_choices import ProspectionChoices
logger = logging.getLogger(__name__)

# Constantes globales
MAX_TYPE_LENGTH = 20
MAX_STATUT_LENGTH = 20
MAX_MOTIF_LENGTH = 30
MAX_OBJECTIF_LENGTH = 30
MAX_MOYEN_LENGTH = 50

class ProspectionManager(models.Manager):
    def actives(self):
        return self.exclude(statut__in=[
            ProspectionChoices.STATUT_REFUSEE,
            ProspectionChoices.STATUT_ANNULEE
        ])

    def a_relancer(self, date=None):
        date = date or timezone.now().date()
        derniers_historiques = HistoriqueProspection.objects.filter(
            prospection=OuterRef('pk')
        ).order_by('-date_modification')[:1]
        return self.filter(
            statut=ProspectionChoices.STATUT_A_RELANCER
        ).annotate(
            prochain_contact=Subquery(derniers_historiques.values('prochain_contact'))
        ).filter(
            prochain_contact__lte=date
        )

    def par_partenaire(self, partenaire_id):
        return self.filter(partenaire_id=partenaire_id).select_related('formation')

    def par_formation(self, formation_id):
        return self.filter(formation_id=formation_id).select_related('partenaire')

    def par_statut(self, statut):
        return self.filter(statut=statut)

    def statistiques_par_statut(self):
        stats = self.values('statut').annotate(
            count=Count('id')
        ).order_by('statut')
        resultat = {}
        labels = ProspectionChoices.get_statut_labels()
        for stat in stats:
            code = stat['statut']
            resultat[code] = {
                'label': labels.get(code, code),
                'count': stat['count']
            }
        return resultat

class Prospection(BaseModel):
    partenaire = models.ForeignKey(
        Partenaire, on_delete=models.CASCADE, related_name="prospections",
        verbose_name=_("Partenaire")
    )
    formation = models.ForeignKey(
        Formation, on_delete=models.CASCADE, null=True, blank=True,
        related_name="prospections", verbose_name=_("Formation")
    )
    date_prospection = models.DateTimeField(default=timezone.now, verbose_name=_("Date de prospection"))
    type_prospection = models.CharField(
        max_length=MAX_TYPE_LENGTH, choices=ProspectionChoices.TYPE_PROSPECTION_CHOICES,
        default=ProspectionChoices.TYPE_PREMIER_CONTACT, verbose_name=_("Type de prospection")
    )
    motif = models.CharField(
        max_length=MAX_MOTIF_LENGTH, choices=ProspectionChoices.PROSPECTION_MOTIF_CHOICES,
        verbose_name=_("Motif")
    )
    statut = models.CharField(
        max_length=MAX_STATUT_LENGTH, choices=ProspectionChoices.PROSPECTION_STATUS_CHOICES,
        default=ProspectionChoices.STATUT_A_FAIRE, verbose_name=_("Statut")
    )
    objectif = models.CharField(
        max_length=MAX_OBJECTIF_LENGTH, choices=ProspectionChoices.PROSPECTION_OBJECTIF_CHOICES,
        default=ProspectionChoices.OBJECTIF_PRISE_CONTACT, verbose_name=_("Objectif")
    )
    commentaire = models.TextField(blank=True, null=True, verbose_name=_("Commentaire"))

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
            models.Index(fields=['motif']),
            models.Index(fields=['objectif']),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(date_prospection__lte=Now()),
                name='prosp_date_not_future'
            ),
            models.CheckConstraint(
                check=~(Q(statut=ProspectionChoices.STATUT_ACCEPTEE) & ~Q(objectif=ProspectionChoices.OBJECTIF_CONTRAT)),
                name='prosp_acceptee_contrat'
            )
        ]

    def __str__(self):
        formation = self.formation.nom if self.formation else _("Sans formation")
        auteur = self.created_by.username if self.created_by else _("Anonyme")
        return f"{self.partenaire.nom} - {formation} - {self.get_statut_display()} ({auteur})"

    def clean(self):
        super().clean()
        if self.date_prospection > timezone.now():
            raise ValidationError({'date_prospection': _("La date de prospection ne peut pas être dans le futur.")})
        if self.statut == ProspectionChoices.STATUT_ACCEPTEE and self.objectif != ProspectionChoices.OBJECTIF_CONTRAT:
            raise ValidationError({
                'statut': _("Une prospection acceptée doit viser la signature d'un contrat."),
                'objectif': _("L'objectif doit être 'contrat'.")
            })
        if self.statut in [ProspectionChoices.STATUT_REFUSEE, ProspectionChoices.STATUT_ANNULEE] and not self.commentaire:
            raise ValidationError({
                'commentaire': _("Un commentaire est obligatoire pour les prospections refusées ou annulées.")
            })


    def save(self, *args, **kwargs):
        is_new = self.pk is None
        changements: dict[str, tuple[str, str]] = {}
        user = getattr(self, "updated_by", None) or getattr(self, "created_by", None)

        # Liste des champs à surveiller (modifiables et pertinents)
        champs_suivis = [
            "statut",
            "type_prospection",
            "objectif",
            "motif",
            "commentaire",
            "formation_id",
            "partenaire_id",
        ]

        if not is_new:
            try:
                ancien_obj = Prospection.objects.get(pk=self.pk)
                for champ in champs_suivis:
                    old_val = getattr(ancien_obj, champ)
                    new_val = getattr(self, champ)
                    if old_val != new_val:
                        changements[champ] = (old_val, new_val)
            except Prospection.DoesNotExist:
                pass

        # Sauvegarde normale
        super().save(*args, **kwargs)

        if changements:
            log_msg = f"[Prospection #{self.pk}] Modifications détectées par {user or 'inconnu'} :"
            for champ, (ancien, nouveau) in changements.items():
                log_msg += f"\n  - {champ}: « {ancien} » → « {nouveau} »"
            logger.info(log_msg)

            # Création de l'historique seulement si le statut a changé
            ancien_statut = changements.get("statut", (self.statut,))[0]
            
            self.creer_historique(
                    ancien_statut=ancien_statut,
                    nouveau_statut=self.statut,
                    type_prospection=self.type_prospection,
                    commentaire=self.commentaire or "",
                    resultat="",
                    moyen_contact=None,
                    user=user,
                    prochain_contact=self.prochain_contact,
                )

    @property
    def is_active(self):
        return self.statut not in [
            ProspectionChoices.STATUT_REFUSEE,
            ProspectionChoices.STATUT_ANNULEE
        ]

    @cached_property
    def prochain_contact(self):
        historique = self.historiques.order_by('-date_modification').first()
        return historique.prochain_contact if historique else None

    @property
    def relance_necessaire(self):
        return self.statut == ProspectionChoices.STATUT_A_RELANCER and \
               self.prochain_contact and self.prochain_contact <= timezone.now().date()

    @property
    def historique_recent(self):
        return self.historiques.all().order_by('-date_modification')[:5]

    def creer_historique(self, ancien_statut, nouveau_statut, type_prospection, commentaire="", 
                         resultat="", moyen_contact=None, user=None, prochain_contact=None):
        if not prochain_contact:
            if nouveau_statut == ProspectionChoices.STATUT_A_RELANCER:
                prochain_contact = timezone.now().date() + timezone.timedelta(days=7)
            elif nouveau_statut == ProspectionChoices.STATUT_EN_COURS:
                prochain_contact = timezone.now().date() + timezone.timedelta(days=14)

        return HistoriqueProspection.objects.create(
            prospection=self,
            ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut,
            type_prospection=type_prospection,
            commentaire=commentaire,
            resultat=resultat,
            prochain_contact=prochain_contact,
            moyen_contact=moyen_contact,
            created_by=user
        )

    def to_serializable_dict(self):
        return {
            "id": self.pk,
            "partenaire": {"id": self.partenaire.pk, "nom": str(self.partenaire)},
            "formation": {
                "id": self.formation.pk if self.formation else None,
                "nom": self.formation.nom if self.formation else None
            },
            "date": self.date_prospection.strftime('%Y-%m-%d %H:%M'),
            "type_prospection": self.get_type_prospection_display(),
            "statut": self.get_statut_display(),
            "objectif": self.get_objectif_display(),
            "motif": self.get_motif_display(),
            "commentaire": self.commentaire,
            "prochain_contact": self.prochain_contact.isoformat() if self.prochain_contact else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": str(self.created_by) if self.created_by else None,
        }

    @classmethod
    def add_to_formation(cls, formation, partenaire: Partenaire, user, **kwargs):
        from .formations import HistoriqueFormation
        prospection = cls.objects.create(
            formation=formation,
            partenaire=partenaire,
            created_by=user,
            **kwargs
        )
        HistoriqueFormation.objects.create(
            formation=formation,
            champ_modifie="prospection",
            nouvelle_valeur=f"{partenaire.nom} ({kwargs.get('statut')})",
            commentaire=f"Ajout d'une prospection pour le partenaire « {partenaire.nom} »",
            created_by=user,
            action=HistoriqueFormation.ActionType.AJOUT
        )
        return prospection

class HistoriqueProspectionManager(models.Manager):
    def a_relancer_cette_semaine(self):
        today = timezone.now().date()
        start = today - timezone.timedelta(days=today.weekday())
        end = start + timezone.timedelta(days=6)
        return self.filter(
            prochain_contact__gte=start,
            prochain_contact__lte=end
        ).select_related('prospection', 'prospection__partenaire')

    def derniers_par_prospection(self):
        subquery = self.filter(
            prospection=OuterRef('prospection')
        ).order_by('-date_modification').values('id')[:1]
        return self.filter(id__in=Subquery(subquery))


class HistoriqueProspection(BaseModel):
    prospection = models.ForeignKey(
        "Prospection", on_delete=models.CASCADE,
        related_name="historiques", verbose_name=_("Prospection")
    )
    date_modification = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de modification")
    )
    ancien_statut = models.CharField(
        max_length=MAX_STATUT_LENGTH, choices=ProspectionChoices.PROSPECTION_STATUS_CHOICES
    )
    nouveau_statut = models.CharField(
        max_length=MAX_STATUT_LENGTH, choices=ProspectionChoices.PROSPECTION_STATUS_CHOICES
    )
    type_prospection = models.CharField(
        max_length=MAX_TYPE_LENGTH,
        choices=ProspectionChoices.TYPE_PROSPECTION_CHOICES,
        default=ProspectionChoices.TYPE_NOUVEAU_PROSPECT,
        verbose_name=_("Type de prospection")
    )

    commentaire = models.TextField(blank=True, null=True)
    resultat = models.TextField(blank=True, null=True)
    prochain_contact = models.DateField(blank=True, null=True)
    moyen_contact = models.CharField(
        max_length=MAX_MOYEN_LENGTH, choices=ProspectionChoices.MOYEN_CONTACT_CHOICES,
        blank=True, null=True
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
        constraints = [
            models.CheckConstraint(
                check=Q(prochain_contact__isnull=True) | Q(prochain_contact__gte=Now()),
                name='histprosp_prochain_contact_futur'
            )
        ]

    def __str__(self):
        return f"{self.date_modification.strftime('%d/%m/%Y')} - {self.get_nouveau_statut_display()}"

    def clean(self):
        super().clean()
        if self.prochain_contact and self.prochain_contact < timezone.now().date():
            raise ValidationError({
                'prochain_contact': _("La date de relance doit être dans le futur.")
            })
        if self.ancien_statut == self.nouveau_statut:
            logger.warning(f"Historique sans changement de statut pour prospection #{self.prospection_id}")

    def save(self, *args, **kwargs):
        self.full_clean()
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.prospection.statut != self.nouveau_statut:
                self.prospection.statut = self.nouveau_statut
                self.prospection.save(update_fields=['statut'], skip_history=True)
        logger.info(f"Historique enregistré pour prospection #{self.prospection.pk} : {self.ancien_statut} → {self.nouveau_statut}")

    def to_serializable_dict(self):
        return {
            "id": self.pk,
            "prospection_id": self.prospection_id,
            "prospection": {
                "id": self.prospection_id,
                "partenaire": str(self.prospection.partenaire) if self.prospection.partenaire else None
            },
            "type_prospection": self.get_type_prospection_display(),
            "ancien_statut": self.get_ancien_statut_display(),
            "nouveau_statut": self.get_nouveau_statut_display(),
            "commentaire": self.commentaire,
            "resultat": self.resultat,
            "prochain_contact": self.prochain_contact.isoformat() if self.prochain_contact else None,
            "moyen_contact": self.get_moyen_contact_display() if self.moyen_contact else None,
            "date_modification": self.date_modification.strftime('%Y-%m-%d %H:%M'),
            "created_by": str(self.created_by) if self.created_by else None,
            "jours_avant_relance": self.jours_avant_relance,
            "est_recent": self.est_recent,
        }

    @property
    def est_recent(self):
        return (timezone.now().date() - self.date_modification.date()).days <= 7

    @property
    def jours_avant_relance(self):
        if not self.prochain_contact:
            return -1
        delta = (self.prochain_contact - timezone.now().date()).days
        return max(0, delta)

    @property
    def relance_urgente(self):
        return 0 <= self.jours_avant_relance <= 2

    @property
    def statut_avec_icone(self):
        icones = {
            ProspectionChoices.STATUT_A_FAIRE: ("far fa-circle", "text-secondary"),
            ProspectionChoices.STATUT_EN_COURS: ("fas fa-spinner", "text-primary"),
            ProspectionChoices.STATUT_A_RELANCER: ("fas fa-clock", "text-warning"),
            ProspectionChoices.STATUT_ACCEPTEE: ("fas fa-check", "text-success"),
            ProspectionChoices.STATUT_REFUSEE: ("fas fa-times", "text-danger"),
            ProspectionChoices.STATUT_ANNULEE: ("fas fa-ban", "text-muted"),
            ProspectionChoices.STATUT_NON_RENSEIGNE: ("fas fa-question", "text-secondary"),
        }
        icone, classe = icones.get(self.nouveau_statut, ("fas fa-question", "text-secondary"))
        return (self.get_nouveau_statut_display(), icone, classe)

    @classmethod
    def get_relances_a_venir(cls, jours=7):
        today = timezone.now().date()
        date_limite = today + timezone.timedelta(days=jours)
        return cls.objects.filter(
            prochain_contact__gte=today,
            prochain_contact__lte=date_limite,
            prospection__statut=ProspectionChoices.STATUT_A_RELANCER
        ).select_related('prospection', 'prospection__partenaire').order_by('prochain_contact')
