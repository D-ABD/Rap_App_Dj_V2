from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError
import logging
from datetime import date

from .centres import Centre
from .base import BaseModel 

# Configuration du logger
logger = logging.getLogger("application.vae")


# ----------------------------------------------------
# Signaux déplacés dans un fichier signals/
# ----------------------------------------------------


class PeriodeMixin(models.Model):
    """
    📅 Classe abstraite pour les éléments liés à une période (mois/année) et un centre.
    """
    MOIS_CHOICES = [
        (1, _("Janvier")), (2, _("Février")), (3, _("Mars")), (4, _("Avril")),
        (5, _("Mai")), (6, _("Juin")), (7, _("Juillet")), (8, _("Août")),
        (9, _("Septembre")), (10, _("Octobre")), (11, _("Novembre")), (12, _("Décembre")),
    ]

    centre = models.ForeignKey(
        Centre,
        on_delete=models.CASCADE,
        verbose_name=_("Centre"),
        help_text=_("Centre associé à cet enregistrement")
    )
    annee = models.PositiveIntegerField(
        default=date.today().year,
        validators=[MinValueValidator(2000)],
        verbose_name=_("Année"),
        help_text=_("Année au format YYYY (ex: 2024)")
    )
    mois = models.PositiveSmallIntegerField(
        default=date.today().month,
        choices=MOIS_CHOICES,
        verbose_name=_("Mois"),
        help_text=_("Mois de l'année (1-12)")
    )

    class Meta:
        abstract = True
        ordering = ['annee', 'mois', 'centre']
        indexes = [
            models.Index(fields=['annee', 'mois'], name='periode_idx'),
            models.Index(fields=['centre', 'annee', 'mois'], name='cent_periode_idx'),
        ]

    def clean(self):
        """🔍 Validation du mois."""
        super().clean()
        if self.mois < 1 or self.mois > 12:
            raise ValidationError({'mois': _("Le mois doit être compris entre 1 et 12.")})

    def get_periode_display(self):
        """📋 Affichage humain de la période."""
        return f"{self.get_mois_display()} {self.annee}"


# ====================================================
#  VAE & Historique des statuts
# ====================================================

class VAE(BaseModel):
    STATUT_CHOICES = [
        ('info', _("Demande d'informations")),
        ('dossier', _("Dossier en cours")),
        ('attente_financement', _("En attente de financement")),
        ('accompagnement', _("Accompagnement en cours")),
        ('jury', _("En attente de jury")),
        ('terminee', _("VAE terminée")),
        ('abandonnee', _("VAE abandonnée")),
    ]
    STATUTS_EN_COURS = ['info', 'dossier', 'attente_financement', 'accompagnement', 'jury']
    STATUTS_TERMINES = ['terminee', 'abandonnee']

    centre = models.ForeignKey(
        Centre,
        on_delete=models.CASCADE,
        related_name='vaes',
        verbose_name=_("Centre"),
        help_text=_("Centre responsable de cette VAE")
    )
    reference = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Référence"),
        help_text=_("Référence unique de la VAE (générée automatiquement si vide)")
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='info',
        verbose_name=_("Statut"),
        help_text=_("Statut actuel de la VAE")
    )
    commentaire = models.TextField(
        blank=True,
        verbose_name=_("Commentaire"),
        help_text=_("Notes ou informations supplémentaires sur cette VAE")
    )

    class Meta:
        verbose_name = _("VAE")
        verbose_name_plural = _("VAEs")
        ordering = ['-created_at', 'centre']
        indexes = [
            models.Index(fields=['statut'], name='vae_statut_idx'),
            models.Index(fields=['created_at'], name='vae_created_idx'),
            models.Index(fields=['reference'], name='vae_reference_idx'),
            models.Index(fields=['centre', 'statut'], name='vae_centre_statut_idx'),
            models.Index(fields=['centre', 'created_at'], name='vae_centre_created_idx'),
        ]

    def __str__(self):
        return f"VAE {self.reference or self.id} - {self.get_statut_display()}"

    def __repr__(self):
        return f"<VAE(id={self.pk}, ref='{self.reference}', statut='{self.statut}')>"

    def save(self, *args, **kwargs):
        skip_validation = kwargs.pop('skip_validation', False)
        user = kwargs.pop("user", None)
        is_new = self.pk is None

        if not self.created_at:
            self.created_at = timezone.now()

        if not self.reference:
            prefix = "VAE"
            date_str = self.created_at.strftime('%Y%m%d')
            centre_id = self.centre.id if self.centre_id else "000"
            existing_refs = VAE.objects.filter(
                reference__startswith=f"{prefix}-{date_str}-{centre_id}"
            ).count()
            self.reference = f"{prefix}-{date_str}-{centre_id}-{existing_refs + 1:03d}"

        if not skip_validation:
            self.full_clean()

        if is_new:
            logger.info(f"🆕 Création VAE {self.reference} pour centre {self.centre}")
        else:
            logger.info(f"✏️ Mise à jour VAE {self.reference} - Statut: {self.get_statut_display()}")

        super().save(*args, user=user, **kwargs)

    def changer_statut(self, nouveau_statut, date_effet=None, commentaire="", user=None):
        if nouveau_statut not in dict(self.STATUT_CHOICES):
            raise ValidationError(f"Statut invalide: {nouveau_statut}")

        date_effet = date_effet or timezone.now().date()
        self.statut = nouveau_statut
        self.save(user=user)

        HistoriqueStatutVAE.objects.create(
            vae=self,
            statut=nouveau_statut,
            date_changement_effectif=date_effet,
            commentaire=commentaire
        )

    def is_en_cours(self):
        return self.statut in self.STATUTS_EN_COURS

    def is_terminee(self):
        return self.statut in self.STATUTS_TERMINES

    def dernier_changement_statut(self):
        return self.historique_statuts.order_by(
            '-date_changement_effectif', '-created_at'
        ).first()

    def duree_statut_actuel(self):
        dernier_changement = self.dernier_changement_statut()
        if dernier_changement:
            return (timezone.now().date() - dernier_changement.date_changement_effectif).days
        return self.duree_jours

    @property
    def annee_creation(self):
        return self.created_at.year

    @property
    def mois_creation(self):
        return self.created_at.month

    @property
    def duree_jours(self):
        return (timezone.now().date() - self.created_at.date()).days

    def to_csv_row(self):
        return [
            self.id,
            self.reference,
            self.centre.nom if self.centre else '',
            self.get_statut_display(),
            self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            self.commentaire,
            self.duree_jours,
            self.is_en_cours(),
            self.is_terminee(),
            self.dernier_changement_statut().get_statut_display()
            if self.dernier_changement_statut() else '',
            self.duree_statut_actuel(),
        ]

    def to_serializable_dict(self, exclude=None):
        exclude = exclude or []
        data = super().to_serializable_dict(exclude)
        dernier_changement = self.dernier_changement_statut()
        data.update({
            'reference': self.reference,
            'centre_id': self.centre_id,
            'centre_nom': str(self.centre),
            'statut': self.statut,
            'statut_libelle': self.get_statut_display(),
            'commentaire': self.commentaire,
            'duree_jours': self.duree_jours,
            'is_en_cours': self.is_en_cours(),
            'is_terminee': self.is_terminee(),
            'dernier_changement_statut': {
                'date': dernier_changement.date_changement_effectif.isoformat()
                if dernier_changement else None,
                'statut': dernier_changement.statut if dernier_changement else None,
                'statut_libelle': (
                    dernier_changement.get_statut_display()
                    if dernier_changement else None
                ),
            } if dernier_changement else None,
            'duree_statut_actuel': self.duree_statut_actuel(),
        })
        return data

    def clean(self):
        super().clean()
        if self.reference and not self.reference.startswith('VAE-'):
            raise ValidationError({'reference': "La référence doit commencer par 'VAE-'"})
        

class HistoriqueStatutVAE(BaseModel):
    vae = models.ForeignKey(
        VAE,
        on_delete=models.CASCADE,
        related_name='historique_statuts',
        verbose_name=_("VAE"),
        help_text=_("VAE concernée par ce changement de statut")
    )
    statut = models.CharField(
        max_length=20,
        choices=VAE.STATUT_CHOICES,
        verbose_name=_("Statut"),
        help_text=_("Nouveau statut de la VAE")
    )
    date_changement_effectif = models.DateField(
        verbose_name=_("Date effective du changement"),
        help_text=_("Date à laquelle le changement de statut a eu lieu")
    )
    commentaire = models.TextField(
        blank=True,
        verbose_name=_("Commentaire"),
        help_text=_("Notes ou informations supplémentaires")
    )

    class Meta:
        verbose_name = _("Historique de statut VAE")
        verbose_name_plural = _("Historiques de statuts VAE")
        ordering = ['-date_changement_effectif', '-created_at']
        indexes = [
            models.Index(fields=['vae', 'statut'], name='hist_vae_statut_idx'),
            models.Index(fields=['date_changement_effectif'], name='hist_vae_date_idx'),
            models.Index(fields=['vae', 'date_changement_effectif'], name='hist_vae_vae_date_idx'),
        ]

    def __str__(self):
        return f"{self.vae} - {self.get_statut_display()} le {self.date_changement_effectif.strftime('%d/%m/%Y')}"

    def __repr__(self):
        return f"<HistoriqueStatutVAE(id={self.pk}, vae='{self.vae_id}', statut='{self.statut}')>"

    def clean(self):
        super().clean()
        if self.date_changement_effectif > timezone.now().date():
            raise ValidationError({'date_changement_effectif': _("La date du changement ne peut pas être dans le futur.")})
        if self.vae and self.vae.created_at:
            if self.date_changement_effectif < self.vae.created_at.date():
                raise ValidationError({'date_changement_effectif': _("La date du changement ne peut pas être antérieure à la date de création de la VAE.")})

    def save(self, *args, **kwargs):
        skip_validation = kwargs.pop('skip_validation', False)
        user = kwargs.pop("user", None)
        if not skip_validation:
            self.full_clean()
        if self.pk is None:
            logger.info(f"📝 Nouveau statut enregistré pour {self.vae}: {self.get_statut_display()} le {self.date_changement_effectif}")
        super().save(*args, user=user, **kwargs)

    def invalidate_caches(self):
        super().invalidate_caches()
        from django.core.cache import cache
        cache_keys = [
            f"historiquestatut_{self.pk}",
            f"vae_{self.vae_id}_historique",
            f"vae_statuts_{self.vae_id}",
            f"vae_historique_{self.vae.reference}" if self.vae else None
        ]
        for key in cache_keys:
            if key:
                cache.delete(key)

    def to_serializable_dict(self, exclude=None):
        exclude = exclude or []
        data = super().to_serializable_dict(exclude)
        data.update({
            'vae_id': self.vae_id,
            'vae_reference': self.vae.reference if self.vae else None,
            'statut': self.statut,
            'statut_libelle': self.get_statut_display(),
            'date_changement_effectif': self.date_changement_effectif.isoformat(),
            'commentaire': self.commentaire,
        })
        return data
