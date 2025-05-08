from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal, InvalidOperation
from django.db.models import Sum, Count, Case, When, F, Q
from django.utils import timezone
from django.core.exceptions import ValidationError
import logging
from django.db import transaction

from .centres import Centre
from .base import BaseModel 
# Configuration du logger
logger = logging.getLogger("application.vae")

from datetime import date

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
            models.Index(fields=['annee', 'mois']),  # Pour les analyses transversales
            models.Index(fields=['centre', 'annee', 'mois']),  # Existant - à conserver
        ]

    def clean(self):
        """
        Validation des contraintes sur les champs.
        
        Vérifie que le mois est compris entre 1 et 12.
        """
        super().clean()
        if self.mois < 1 or self.mois > 12:
            raise ValidationError({
                'mois': _("Le mois doit être compris entre 1 et 12.")
            })

    def get_periode_display(self):
        """
        Retourne une représentation textuelle de la période.
        
        Returns:
            str: Mois et année formatés (ex: "Janvier 2024")
        """
        return f"{self.get_mois_display()} {self.annee}"

class SuiviJury(BaseModel, PeriodeMixin):
    """
    Modèle pour le suivi des jurys par centre, par mois et par année.
    
    Ce modèle permet de suivre les objectifs et réalisations des jurys
    pour chaque centre, sur une base mensuelle.
    
    Attributes:
        objectif_jury: Nombre de jurys à réaliser (objectif mensuel)
        jurys_realises: Nombre de jurys effectivement réalisés
        pourcentage_mensuel: Pourcentage d'atteinte de l'objectif (calculé automatiquement)
    """
    objectif_jury = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Objectif jury"),
        help_text=_("Nombre de jurys à réaliser pour le mois")
    )
    jurys_realises = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Jurys réalisés"),
        help_text=_("Nombre de jurys effectivement réalisés ce mois")
    )
    pourcentage_mensuel = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False,
        verbose_name=_("Pourcentage mensuel"),
        help_text=_("Pourcentage d'atteinte de l'objectif mensuel (calculé automatiquement)")
    )

    def get_absolute_url(self):
        """
        Retourne l'URL absolue de détail pour cet objet.
        
        Returns:
            str: URL de détail de l'instance
        """
        return reverse("suivijury-detail", kwargs={"pk": self.pk})
    
    def to_serializable_dict(self):
        """
        Retourne un dictionnaire des données de l'instance pour une sérialisation simple.
        
        Returns:
            dict: Données sérialisées
        """
        return {
            "id": self.id,
            "centre_id": self.centre_id,
            "centre_nom": str(self.centre),
            "annee": self.annee,
            "mois": self.mois,
            "mois_libelle": self.get_mois_display(),
            "periode": self.get_periode_display(),
        }



    def get_objectif_auto(self):
        """
        Retourne l'objectif de jury à utiliser pour les calculs.
        
        Utilise l'objectif spécifique s'il est défini, sinon l'objectif
        mensuel standard du centre.
        
        Returns:
            int: L'objectif de jury à utiliser
        """
        if self.objectif_jury and self.objectif_jury > 0:
            return self.objectif_jury
        return self.centre.objectif_mensuel_jury or 0

    def get_pourcentage_atteinte(self):
        """
        Calcule dynamiquement le pourcentage d'atteinte de l'objectif.
        
        Cette méthode recalcule le pourcentage à la volée, contrairement
        à la propriété pourcentage_atteinte qui retourne la valeur stockée.
        
        Returns:
            float: Pourcentage d'atteinte arrondi à une décimale
        """
        objectif = self.get_objectif_auto()
        if objectif > 0:
            return round((self.jurys_realises or 0) / objectif * 100, 1)
        return 0

    class Meta(PeriodeMixin.Meta):
        unique_together = ('centre', 'annee', 'mois')
        verbose_name = _("Suivi des jurys")
        verbose_name_plural = _("Suivis des jurys")
        indexes = PeriodeMixin.Meta.indexes + [
            models.Index(fields=['pourcentage_mensuel']),
            models.Index(fields=['objectif_jury', 'jurys_realises']),
        ]
    
    def __str__(self):
        """
        Représentation textuelle de l'instance.
        
        Returns:
            str: Description du suivi avec centre, mois et année
        """
        return f"Jurys {self.centre} - {self.get_mois_display()} {self.annee}"
    

    def save(self, *args, **kwargs):
        """
        Sauvegarde atomique du suivi jury avec calcul du pourcentage et journalisation.
        
        Args:
            *args: Arguments positionnels
            **kwargs: Arguments nommés pouvant contenir :
                - user: Utilisateur effectuant l'action
                - skip_validation: Booléen pour sauter la validation
        """
        try:
            with transaction.atomic():
                # Calcul du pourcentage avec gestion des erreurs
                try:
                    if self.objectif_jury > 0:
                        self.pourcentage_mensuel = Decimal(self.jurys_realises) / Decimal(self.objectif_jury) * 100
                        self.pourcentage_mensuel = self.pourcentage_mensuel.quantize(Decimal('0.01'))
                    else:
                        self.pourcentage_mensuel = Decimal('0.00')
                except (ZeroDivisionError, InvalidOperation) as e:
                    logger.error(f"Erreur calcul pourcentage jury {self}: {str(e)}")
                    self.pourcentage_mensuel = Decimal('0.00')

                is_new = self.pk is None
                user = kwargs.pop("user", None)

                # Journalisation avant sauvegarde
                log_msg = f"{'Création' if is_new else 'Mise à jour'} suivi jury {self}"
                if user:
                    log_msg += f" par {user.username}"
                logger.info(log_msg)

                # Validation optionnelle
                if not kwargs.pop('skip_validation', False):
                    self.full_clean()

                # Sauvegarde parentale
                super().save(*args, user=user, **kwargs)

                # Post-save logging
                logger.debug(f"Suivi jury {self.pk} sauvegardé avec succès")

        except Exception as e:
            logger.critical(
                f"Échec sauvegarde suivi jury {getattr(self, 'pk', 'Nouveau')} | "
                f"Centre: {getattr(self.centre, 'pk', None)} | "
                f"Erreur: {str(e)}",
                exc_info=True
            )
            raise  # Re-lève l'exception pour ne pas masquer l'erreur


    def ecart(self):
        """
        Calcule l'écart entre les jurys réalisés et l'objectif.
        
        Returns:
            int: Différence entre jurys réalisés et objectif (peut être négatif)
        """
        return self.jurys_realises - self.objectif_jury
    
    @property
    def pourcentage_atteinte(self):
        """
        Propriété qui retourne le pourcentage d'atteinte stocké.
        
        Cette propriété retourne la valeur calculée et stockée lors de la
        sauvegarde, par opposition à get_pourcentage_atteinte() qui recalcule.
        
        Returns:
            Decimal: Pourcentage d'atteinte stocké
        """
        return self.pourcentage_mensuel
        
    @property
    def serializable_data(self):
        """
        Retourne un dictionnaire des données du suivi pour sérialisation.
        
        Returns:
            dict: Données du suivi formatées pour sérialisation
        """
        return {
            'id': self.id,
            'centre_id': self.centre_id,
            'centre_nom': str(self.centre),
            'annee': self.annee,
            'mois': self.mois,
            'mois_libelle': self.get_mois_display(),
            'periode': self.get_periode_display(),
            'objectif_jury': self.objectif_jury,
            'jurys_realises': self.jurys_realises,
            'ecart': self.ecart(),
            'pourcentage_atteinte': float(self.pourcentage_atteinte),
            'objectif_auto': self.get_objectif_auto(),
        }

class VAE(BaseModel):
    """
    Modèle représentant une VAE individuelle avec son statut.
    
    Ce modèle permet de suivre l'évolution d'une Validation des Acquis de l'Expérience
    à travers différents statuts, depuis la demande d'information jusqu'à sa complétion
    ou son abandon.
    
    Attributes:
        centre: Centre responsable de cette VAE
        reference: Référence unique de la VAE
        created_at: Date à laquelle la VAE a été créée
        date_saisie: Date à laquelle la VAE a été enregistrée dans le système
        statut: Statut actuel de la VAE
        date_modification: Date de dernière modification
        commentaire: Notes supplémentaires sur la VAE
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
    
    # Statuts considérés comme "en cours"
    STATUTS_EN_COURS = ['info', 'dossier', 'attente_financement', 'accompagnement', 'jury']
    
    # Statuts considérés comme "terminés" (positivement ou négativement)
    STATUTS_TERMINES = ['terminee', 'abandonnee']
    
    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE,
        related_name='vaes',
        verbose_name=_("Centre"),
        help_text=_("Centre responsable de cette VAE")
    )
    
    # Informations générales
    reference = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name=_("Référence"),
        help_text=_("Référence unique de la VAE (générée automatiquement si vide)")
    )
    


    
    # Statut actuel
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='info',
        verbose_name=_("Statut"),
        help_text=_("Statut actuel de la VAE")
    )

    
    # Champs optionnels (à compléter selon vos besoins)
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
            models.Index(fields=['statut']),  # Très important pour le filtrage
            models.Index(fields=['created_at']),  # Existant - à conserver
            models.Index(fields=['reference']),  # Existant - à conserver
            models.Index(fields=['centre', 'statut']),  # Existant - à conserver
            models.Index(fields=['centre', 'created_at']),  # Nouveau pour les analyses temporelles
        ]
    
    def __str__(self):
        """
        Représentation textuelle de la VAE.
        
        Returns:
            str: Identification de la VAE avec sa référence et son statut
        """
        return f"VAE {self.reference or self.id} - {self.get_statut_display()}"

    
    def save(self, *args, **kwargs):
        """
        Personnalisation de la sauvegarde pour générer la référence automatiquement
        et journaliser l'action.

        Args:
            *args: Arguments positionnels
            **kwargs: Arguments nommés, dont 'user' et 'skip_validation' optionnels
        """
        skip_validation = kwargs.pop('skip_validation', False)
        user = kwargs.pop("user", None)
        is_new = self.pk is None

        # Date de création explicite si non renseignée
        if not self.created_at:
            self.created_at = timezone.now()

        # Référence automatique
        if not self.reference:
            prefix = "VAE"
            date_str = self.created_at.strftime('%Y%m%d')
            centre_id = self.centre.id if self.centre_id else "000"
            existing_refs = VAE.objects.filter(reference__startswith=f"{prefix}-{date_str}-{centre_id}").count()
            self.reference = f"{prefix}-{date_str}-{centre_id}-{existing_refs + 1:03d}"

        # Validation facultative
        if not skip_validation:
            self.full_clean()

        # Journalisation
        if is_new:
            logger.info(f"🆕 Création VAE {self.reference} pour centre {self.centre}")
        else:
            logger.info(f"✏️ Mise à jour VAE {self.reference} - Statut: {self.get_statut_display()}")

        # Sauvegarde réelle
        super().save(*args, user=user, **kwargs)
    
    @property
    def annee_creation(self):
        """
        Retourne l'année de création de la VAE.
        
        Returns:
            int: Année de création
        """
        return self.created_at.year
    
    @property
    def mois_creation(self):
        """
        Retourne le mois de création de la VAE.
        
        Returns:
            int: Mois de création (1-12)
        """
        return self.created_at.month
        
    @property
    def duree_jours(self):
        """
        Calcule la durée en jours depuis la création de la VAE.
        
        Returns:
            int: Nombre de jours écoulés depuis la création
        """
        today = timezone.now().date()
        return (today - self.created_at).days
        
    def is_en_cours(self):
        """
        Vérifie si la VAE est en cours (non terminée ou abandonnée).
        
        Returns:
            bool: True si la VAE est en cours, False sinon
        """
        return self.statut in self.STATUTS_EN_COURS
        
    def is_terminee(self):
        """
        Vérifie si la VAE est terminée ou abandonnée.
        
        Returns:
            bool: True si la VAE est terminée ou abandonnée, False sinon
        """
        return self.statut in self.STATUTS_TERMINES
        
    def dernier_changement_statut(self):
        """
        Retourne le dernier changement de statut de cette VAE.
        
        Returns:
            HistoriqueStatutVAE: Dernier historique de statut, ou None si aucun
        """
        return self.historique_statuts.order_by('-date_changement_effectif', '-created_at').first()
        
    def duree_statut_actuel(self):
        """
        Calcule la durée (en jours) depuis le dernier changement de statut.
        
        Returns:
            int: Nombre de jours écoulés depuis le dernier changement de statut
        """
        dernier_changement = self.dernier_changement_statut()
        if dernier_changement:
            today = timezone.now().date()
            return (today - dernier_changement.date_changement_effectif).days
        return self.duree_jours

    @classmethod
    def get_count_by_statut_optimized(cls, centre=None, annee=None, mois=None):
        """
        Version optimisée avec annotation
        """
        queryset = cls.objects.all()
        
        if centre:
            queryset = queryset.filter(centre=centre)
        if annee:
            queryset = queryset.filter(created_at__year=annee)
        if mois:
            queryset = queryset.filter(created_at__month=mois)
        
        return queryset.aggregate(
            total=Count('id'),
            en_cours=Count(Case(When(statut__in=cls.STATUTS_EN_COURS, then=1))),
            terminees=Count(Case(When(statut='terminee', then=1))),
            abandonnees=Count(Case(When(statut='abandonnee', then=1))),
            **{statut: Count(Case(When(statut=statut, then=1))) for statut, _ in cls.STATUT_CHOICES}
        )
    
    # Ajouter une méthode pour le changement de statut contrôlé
    def changer_statut(self, nouveau_statut, date_effet=None, commentaire="", user=None):
        """
        Change le statut de manière contrôlée avec historique
        """
        if nouveau_statut not in dict(self.STATUT_CHOICES):
            raise ValidationError(f"Statut invalide: {nouveau_statut}")
        
        date_effet = date_effet or timezone.now().date()
        self.statut = nouveau_statut
        self.save(user=user)
        
        # Création de l'historique
        HistoriqueStatutVAE.objects.create(
            vae=self,
            statut=nouveau_statut,
            date_changement_effectif=date_effet,
            commentaire=commentaire
        )
                
    @property
    def serializable_data(self):
        """
        Retourne un dictionnaire des données de la VAE pour sérialisation.
        
        Returns:
            dict: Données de la VAE formatées pour sérialisation
        """
        dernier_changement = self.dernier_changement_statut()
        
        return {
            'id': self.id,
            'reference': self.reference,
            'centre_id': self.centre_id,
            'centre_nom': str(self.centre),
            'created_at': self.created_at.isoformat(),
            'statut': self.statut,
            'statut_libelle': self.get_statut_display(),
            'date_modification': self.date_modification.isoformat(),
            'commentaire': self.commentaire,
            'duree_jours': self.duree_jours,
            'is_en_cours': self.is_en_cours(),
            'is_terminee': self.is_terminee(),
            'dernier_changement_statut': {
                'date': dernier_changement.date_changement_effectif.isoformat() if dernier_changement else None,
                'statut': dernier_changement.statut if dernier_changement else None,
                'statut_libelle': dernier_changement.get_statut_display() if dernier_changement else None,
            } if dernier_changement else None,
            'duree_statut_actuel': self.duree_statut_actuel(),
        }

    def clean(self):
        """Validation supplémentaire"""
        super().clean()
        
        # Validation de la référence
        if self.reference and not self.reference.startswith('VAE-'):
            raise ValidationError({'reference': "La référence doit commencer par 'VAE-'"})
        
        # Validation des dates
        if hasattr(self, 'date_modification') and self.date_modification:
            if self.date_modification < self.created_at:
                raise ValidationError({
                    'date_modification': "La date de modification ne peut pas être antérieure à la création"
                })

class HistoriqueStatutVAE(BaseModel, PeriodeMixin):
    """
    Modèle pour suivre l'historique des changements de statut d'une VAE.
    
    Ce modèle enregistre chaque changement de statut d'une VAE, permettant
    ainsi de suivre son évolution dans le temps et de calculer des statistiques
    sur les durées des différentes étapes.
    
    Attributes:
        vae: La VAE concernée par ce changement de statut
        statut: Le nouveau statut
        date_changement_effectif: Date à laquelle le changement a eu lieu
        commentaire: Notes supplémentaires sur ce changement
    """
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
    
    # Date configurable manuellement pour le changement de statut
    date_changement_effectif = models.DateField(
        verbose_name=_("Date effective du changement"),
        help_text=_("Date à laquelle le changement de statut a eu lieu (pas nécessairement aujourd'hui)")
    )
    

    commentaire = models.TextField(
        blank=True,
        verbose_name=_("Commentaire"),
        help_text=_("Notes ou informations supplémentaires sur ce changement de statut")
    )
    
    class Meta:
        verbose_name = _("Historique de statut VAE")
        verbose_name_plural = _("Historiques de statuts VAE")
        ordering = ['-date_changement_effectif', '-created_at']
        indexes = [
            models.Index(fields=['vae', 'statut']),  # Existant - à conserver
            models.Index(fields=['date_changement_effectif']),  # Existant - à conserver
            models.Index(fields=['vae', 'date_changement_effectif']),  # Nouveau pour le suivi chronologique
        ]
    
    def __str__(self):
        """
        Représentation textuelle de l'historique de statut.
        
        Returns:
            str: Description du changement de statut avec la VAE et la date
        """
        return f"{self.vae} - {self.get_statut_display()} le {self.date_changement_effectif.strftime('%d/%m/%Y')}"
        
    def clean(self):
        """
        Validation des contraintes sur les champs.
        
        Vérifie notamment que la date du changement n'est pas dans le futur et
        qu'elle n'est pas antérieure à la date de création de la VAE.
        """
        super().clean()
        
        if self.date_changement_effectif and self.date_changement_effectif > timezone.now().date():
            raise ValidationError({
                'date_changement_effectif': _("La date du changement ne peut pas être dans le futur.")
            })
            
        if hasattr(self, 'vae') and self.vae and self.vae.created_at:
            if self.date_changement_effectif < self.vae.created_at:
                raise ValidationError({
                    'date_changement_effectif': _("La date du changement ne peut pas être antérieure à la date de création de la VAE.")
                })
                
    def save(self, *args, **kwargs):
        """
        Personnalisation de la sauvegarde.
        
        Args:
            *args, **kwargs: Arguments à passer à la méthode save() de base
            
        Kwargs:
            skip_validation (bool): Si True, ignore la validation complète
        """
        skip_validation = kwargs.pop('skip_validation', False)
        is_new = self.pk is None
        
        # Validation complète sauf si désactivée
        if not skip_validation:
            self.full_clean()
        
        # Journalisation
        if is_new:
            logger.info(f"Nouveau statut enregistré pour {self.vae}: {self.get_statut_display()} le {self.date_changement_effectif}")
            
        super().save(*args, **kwargs)
        
    @property
    def serializable_data(self):
        """
        Retourne un dictionnaire des données de l'historique pour sérialisation.
        
        Returns:
            dict: Données de l'historique formatées pour sérialisation
        """
        return {
            'id': self.id,
            'vae_id': self.vae_id,
            'vae_reference': self.vae.reference,
            'statut': self.statut,
            'statut_libelle': self.get_statut_display(),
            'date_changement_effectif': self.date_changement_effectif.isoformat(),
            'commentaire': self.commentaire,
        }


# Signal pour enregistrer l'historique des changements de statut
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

@receiver(pre_save, sender=VAE)
def track_vae_status_change(sender, instance, **kwargs):
    """
    Suit les changements de statut des VAE et les enregistre dans l'historique.
    
    Ce signal est déclenché avant la sauvegarde d'une VAE et prépare les données
    nécessaires pour créer une entrée d'historique si le statut a changé.
    
    Args:
        sender: Le modèle qui a envoyé le signal (VAE)
        instance: L'instance du modèle qui va être sauvegardée
        **kwargs: Arguments supplémentaires
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
    Crée une entrée dans l'historique après la sauvegarde d'une VAE.
    
    Ce signal est déclenché après la sauvegarde d'une VAE et crée une entrée
    d'historique si le statut a changé ou si c'est une nouvelle VAE.
    
    Args:
        sender: Le modèle qui a envoyé le signal (VAE)
        instance: L'instance du modèle qui a été sauvegardée
        created: Booléen indiquant si un nouvel objet a été créé
        **kwargs: Arguments supplémentaires
    """
    # Si c'est une nouvelle VAE, créer la première entrée d'historique
    if created:
        historique = HistoriqueStatutVAE.objects.create(
            vae=instance,
            statut=instance.statut,
            date_changement_effectif=instance.created_at,  # Utiliser la date de création de la VAE
            commentaire=f"Création de la VAE avec statut initial : {instance.get_statut_display()}"
        )
        logger.info(f"Historique initial créé pour nouvelle VAE {instance.reference or instance.id}: {historique}")
    # Si le statut a changé, créer une entrée d'historique
    elif hasattr(instance, '_status_changed') and instance._status_changed:
        historique = HistoriqueStatutVAE.objects.create(
            vae=instance,
            statut=instance.statut,
            date_changement_effectif=timezone.now().date(),  # Par défaut aujourd'hui, mais peut être modifié après
            commentaire=f"Changement de statut : {dict(VAE.STATUT_CHOICES).get(instance._old_status)} → {instance.get_statut_display()}"
        )
        logger.info(f"Nouvel historique créé pour changement de statut VAE {instance.reference}: {historique}")