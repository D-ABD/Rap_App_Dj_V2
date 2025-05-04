from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db.models import Sum, Count, Case, When, F, Q
from django.utils import timezone
from .centres import Centre

class PeriodeMixin(models.Model):
    """
    Classe abstraite pour les éléments liés à une période (mois/année) et un centre.
    """
    MOIS_CHOICES = [
        (1, _("Janvier")), (2, _("Février")), (3, _("Mars")), (4, _("Avril")),
        (5, _("Mai")), (6, _("Juin")), (7, _("Juillet")), (8, _("Août")),
        (9, _("Septembre")), (10, _("Octobre")), (11, _("Novembre")), (12, _("Décembre")),
    ]
    
    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE,
        verbose_name=_("Centre")
    )
    annee = models.PositiveIntegerField(
        validators=[MinValueValidator(2000)],
        verbose_name=_("Année")
    )
    mois = models.PositiveSmallIntegerField(
        choices=MOIS_CHOICES,
        verbose_name=_("Mois")
    )
    
    class Meta:
        abstract = True
        ordering = ['annee', 'mois', 'centre']
        indexes = [
            models.Index(fields=['centre', 'annee', 'mois']),
        ]

class SuiviJury(PeriodeMixin):
    """
    Modèle pour le suivi des jurys par centre, par mois et par année.
    """
    objectif_jury = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Objectif jury")
    )
    jurys_realises = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Jurys réalisés")
    )
    pourcentage_mensuel = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False,
        verbose_name=_("Pourcentage mensuel")
    )

    def get_objectif_auto(self):
        if self.objectif_jury and self.objectif_jury > 0:
            return self.objectif_jury
        return self.centre.objectif_mensuel_jury or 0

    def get_pourcentage_atteinte(self):
        objectif = self.get_objectif_auto()
        if objectif > 0:
            return round((self.jurys_realises or 0) / objectif * 100, 1)
        return 0

    class Meta(PeriodeMixin.Meta):
        unique_together = ('centre', 'annee', 'mois')
        verbose_name = _("Suivi des jurys")
        verbose_name_plural = _("Suivis des jurys")
    
    def __str__(self):
        return f"Jurys {self.centre} - {self.get_mois_display()} {self.annee}"
    
    def save(self, *args, **kwargs):
        """Calcule le pourcentage avant la sauvegarde"""
        if self.objectif_jury > 0:
            self.pourcentage_mensuel = round(Decimal(self.jurys_realises) / Decimal(self.objectif_jury) * 100, 2)
        else:
            self.pourcentage_mensuel = Decimal('0.00')
        super().save(*args, **kwargs)
    
    def ecart(self):
        """Calcule l'écart entre les jurys réalisés et l'objectif"""
        return self.jurys_realises - self.objectif_jury
    
    @property
    def pourcentage_atteinte(self):
        """
        Calcule le pourcentage d'atteinte de l'objectif.
        Retourne le pourcentage stocké, qui est calculé à la sauvegarde.
        """
        return self.pourcentage_mensuel

# Nouveau modèle pour les VAE individuelles
class VAE(models.Model):
    """
    Modèle représentant une VAE individuelle avec son statut.
    """
    STATUT_CHOICES = [
        ('info', _("Demande d'informations")),
        ('dossier', _("Dossier en cours")),
        ('attente_financement', _("En attente de financement")),
        ('accompagnement', _("Accompagnement en cours")),
        ('jury', _("En attente de jury")),
        ('terminee', _("VAE terminée")),
        ('abandonnee', _("VAE abandonnée")),
    ]

    
    
    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE,
        related_name='vaes',
        verbose_name=_("Centre")
    )
    
    # Informations générales
    reference = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name=_("Référence")
    )
    
    # Date configurable manuellement (et non par défaut la date du jour)
    date_creation = models.DateField(
        verbose_name=_("Date de création"),
        help_text=_("Date à laquelle la VAE a été créée, pas nécessairement aujourd'hui")
    )
    
    # Date de saisie dans le système
    date_saisie = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de saisie dans le système")
    )
    
    # Statut actuel
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='info',
        verbose_name=_("Statut")
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de dernière modification")
    )
    
    # Champs optionnels (à compléter selon vos besoins)
    commentaire = models.TextField(
        blank=True,
        verbose_name=_("Commentaire")
    )
    
    class Meta:
        verbose_name = _("VAE")
        verbose_name_plural = _("VAEs")
        ordering = ['-date_creation', 'centre']
        indexes = [
            models.Index(fields=['centre', 'statut']),
            models.Index(fields=['date_creation']),
        ]
    
    def __str__(self):
        return f"VAE {self.reference or self.id} - {self.get_statut_display()}"
    
    def save(self, *args, **kwargs):
        # Si c'est une nouvelle VAE sans date de création spécifiée, utiliser la date du jour
        if not self.date_creation:
            self.date_creation = timezone.now().date()
            
        # Générer une référence automatique si non fournie
        if not self.reference:
            self.reference = f"VAE-{self.date_creation.strftime('%Y%m%d')}-{self.centre.id}"
            
        super().save(*args, **kwargs)
    
    @property
    def annee_creation(self):
        return self.date_creation.year
    
    @property
    def mois_creation(self):
        return self.date_creation.month

    @classmethod
    def get_count_by_statut(cls, centre=None, annee=None, mois=None):
        """
        Retourne le nombre de VAE par statut pour les filtres donnés
        """
        queryset = cls.objects.all()
        
        if centre:
            queryset = queryset.filter(centre=centre)
        
        if annee:
            queryset = queryset.filter(date_creation__year=annee)
        
        if mois:
            queryset = queryset.filter(date_creation__month=mois)
        
        result = {}
        for statut, label in cls.STATUT_CHOICES:
            result[statut] = queryset.filter(statut=statut).count()
        
        # Ajouter des totaux utiles
        result['total'] = queryset.count()
        result['en_cours'] = queryset.exclude(statut__in=['terminee', 'abandonnee']).count()
        
        return result


# Classe pour suivre l'historique des changements de statut
class HistoriqueStatutVAE(models.Model):
    """
    Modèle pour suivre l'historique des changements de statut d'une VAE.
    """
    vae = models.ForeignKey(
        VAE,
        on_delete=models.CASCADE,
        related_name='historique_statuts',
        verbose_name=_("VAE")
    )
    statut = models.CharField(
        max_length=20,
        choices=VAE.STATUT_CHOICES,
        verbose_name=_("Statut")
    )
    
    # Date configurable manuellement pour le changement de statut
    date_changement_effectif = models.DateField(
        verbose_name=_("Date effective du changement"),
        help_text=_("Date à laquelle le changement de statut a eu lieu (pas nécessairement aujourd'hui)")
    )
    
    # Date à laquelle l'enregistrement a été saisi dans le système
    date_saisie = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de saisie dans le système")
    )
    
    commentaire = models.TextField(
        blank=True,
        verbose_name=_("Commentaire")
    )
    
    class Meta:
        verbose_name = _("Historique de statut VAE")
        verbose_name_plural = _("Historiques de statuts VAE")
        ordering = ['-date_changement_effectif', '-date_saisie']
    
    def __str__(self):
        return f"{self.vae} - {self.get_statut_display()} le {self.date_changement_effectif.strftime('%d/%m/%Y')}"


# Signal pour enregistrer l'historique des changements de statut
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

@receiver(pre_save, sender=VAE)
def track_vae_status_change(sender, instance, **kwargs):
    """
    Suit les changements de statut des VAE et les enregistre dans l'historique
    """
    # Si c'est une nouvelle VAE, on ne fait rien pour l'instant
    if instance.pk is None:
        return
    
    try:
        # Récupérer l'ancienne instance pour comparer le statut
        old_instance = VAE.objects.get(pk=instance.pk)
        
        # Si le statut a changé, créer une entrée dans l'historique
        if old_instance.statut != instance.statut:
            # On utilise post_save pour créer l'historique
            instance._status_changed = True
            instance._old_status = old_instance.statut
        else:
            instance._status_changed = False
    except VAE.DoesNotExist:
        # Nouvelle instance, pas d'ancien statut
        instance._status_changed = False


@receiver(post_save, sender=VAE)
def create_vae_status_history(sender, instance, created, **kwargs):
    """
    Crée une entrée dans l'historique après la sauvegarde
    """
    # Si c'est une nouvelle VAE, créer la première entrée d'historique
    if created:
        HistoriqueStatutVAE.objects.create(
            vae=instance,
            statut=instance.statut,
            date_changement_effectif=instance.date_creation,  # Utiliser la date de création de la VAE
            commentaire=f"Création de la VAE avec statut initial : {instance.get_statut_display()}"
        )
    # Si le statut a changé, créer une entrée d'historique
    elif hasattr(instance, '_status_changed') and instance._status_changed:
        HistoriqueStatutVAE.objects.create(
            vae=instance,
            statut=instance.statut,
            date_changement_effectif=timezone.now().date(),  # Par défaut aujourd'hui, mais peut être modifié après
            commentaire=f"Changement de statut : {dict(VAE.STATUT_CHOICES).get(instance._old_status)} → {instance.get_statut_display()}"
        )