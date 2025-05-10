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

# ----------------------------------------------------
# Signaux déplacés dans un fichier signals/
# ----------------------------------------------------


from datetime import date

class PeriodeMixin(models.Model):
    """
    📅 Classe abstraite pour les éléments liés à une période (mois/année) et un centre.
    
    Cette classe fournit les champs et méthodes communs pour tous les modèles
    qui nécessitent un suivi temporel (par mois et année) et un lien avec un centre.
    
    Attributes:
        centre (Centre): Centre associé à l'enregistrement
        annee (int): Année concernée
        mois (int): Mois concerné (1-12)
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
        """
        🔍 Validation des contraintes sur les champs.
        
        Vérifie que le mois est compris entre 1 et 12.
        
        Raises:
            ValidationError: Si le mois n'est pas valide
        """
        super().clean()
        if self.mois < 1 or self.mois > 12:
            raise ValidationError({
                'mois': _("Le mois doit être compris entre 1 et 12.")
            })

    def get_periode_display(self):
        """
        📋 Retourne une représentation textuelle de la période.
        
        Returns:
            str: Mois et année formatés (ex: "Janvier 2024")
        """
        return f"{self.get_mois_display()} {self.annee}"
    
class SuiviJury(BaseModel, PeriodeMixin):
    """
    📊 Modèle pour le suivi des jurys par centre, par mois et par année.
    
    Ce modèle permet de suivre les objectifs et réalisations des jurys
    pour chaque centre, sur une base mensuelle.
    
    Attributes:
        objectif_jury (int): Nombre de jurys à réaliser (objectif mensuel)
        jurys_realises (int): Nombre de jurys effectivement réalisés
        pourcentage_mensuel (Decimal): Pourcentage d'atteinte de l'objectif (calculé automatiquement)
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

    
    def to_serializable_dict(self, exclude=None):
        """
        📦 Retourne un dictionnaire des données de l'instance pour une sérialisation simple.
        
        Args:
            exclude (list[str], optional): Liste de champs à exclure
            
        Returns:
            dict: Données sérialisables du suivi jury
        """
        exclude = exclude or []
        data = super().to_serializable_dict(exclude)
        
        # Ajouter des données spécifiques
        data.update({
            "centre_id": self.centre_id,
            "centre_nom": str(self.centre),
            "annee": self.annee,
            "mois": self.mois,
            "mois_libelle": self.get_mois_display(),
            "periode": self.get_periode_display(),
            "objectif_jury": self.objectif_jury,
            "jurys_realises": self.jurys_realises,
            "ecart": self.ecart(),
            "pourcentage_atteinte": float(self.pourcentage_atteinte),
            "objectif_auto": self.get_objectif_auto(),
        })
        
        return data

    def get_objectif_auto(self):
        """
        🎯 Retourne l'objectif de jury à utiliser pour les calculs.
        
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
        📈 Calcule dynamiquement le pourcentage d'atteinte de l'objectif.
        
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
        # Index pour 'pourcentage_mensuel' retiré
        indexes = PeriodeMixin.Meta.indexes + [
            models.Index(fields=['pourcentage_mensuel'], name='sj_pct_idx'),
            models.Index(fields=['objectif_jury', 'jurys_realises'], name='sj_obj_jr_idx'),
    ]


        
    def __str__(self):
        """
        🔁 Représentation textuelle de l'instance.
        
        Returns:
            str: Description du suivi avec centre, mois et année
        """
        return f"Jurys {self.centre} - {self.get_mois_display()} {self.annee}"
    
    def __repr__(self):
        """
        📝 Représentation technique pour le débogage.
        
        Returns:
            str: Format technique détaillé
        """
        return f"<SuiviJury(id={self.pk}, centre='{self.centre}', periode='{self.get_periode_display()}')>"

    def save(self, *args, **kwargs):
        """
        💾 Sauvegarde atomique du suivi jury avec calcul du pourcentage et journalisation.
        
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

    def invalidate_caches(self):
        """
        🔄 Invalide les caches associés à ce suivi de jury.
        """
        super().invalidate_caches()
        
        # Invalider les caches spécifiques
        from django.core.cache import cache
        cache_keys = [
            f"suivijury_{self.pk}",
            f"suivijury_centre_{self.centre_id}",
            f"suivijury_periode_{self.annee}_{self.mois}",
            f"suivijury_stats_{self.centre_id}_{self.annee}"
        ]
        
        for key in cache_keys:
            cache.delete(key)

    def ecart(self):
        """
        📊 Calcule l'écart entre les jurys réalisés et l'objectif.
        
        Returns:
            int: Différence entre jurys réalisés et objectif (peut être négatif)
        """
        return self.jurys_realises - self.objectif_jury
    
    @property
    def pourcentage_atteinte(self):
        """
        📈 Propriété qui retourne le pourcentage d'atteinte stocké.
        
        Cette propriété retourne la valeur calculée et stockée lors de la
        sauvegarde, par opposition à get_pourcentage_atteinte() qui recalcule.
        
        Returns:
            Decimal: Pourcentage d'atteinte stocké
        """
        return self.pourcentage_mensuel
    
    def to_csv_row(self):
        """
        📤 Retourne une ligne CSV représentant ce suivi de jury.

        Returns:
            list: Valeurs formatées pour une exportation CSV
        """
        return [
            self.id,
            self.centre.nom if self.centre else '',
            self.annee,
            self.mois,
            self.get_mois_display(),
            self.objectif_jury,
            self.jurys_realises,
            self.ecart(),
            float(self.pourcentage_atteinte),
            self.get_objectif_auto(),
        ]
    
class VAE(BaseModel):
    """
    📝 Modèle représentant une VAE individuelle avec son statut.
    
    Ce modèle permet de suivre l'évolution d'une Validation des Acquis de l'Expérience
    à travers différents statuts, depuis la demande d'information jusqu'à sa complétion
    ou son abandon.
    
    Attributes:
        centre (Centre): Centre responsable de cette VAE
        reference (str): Référence unique de la VAE
        created_at (datetime): Date à laquelle la VAE a été créée
        statut (str): Statut actuel de la VAE
        commentaire (str): Notes supplémentaires sur la VAE
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

    # Champs optionnels
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
        """
        🔁 Représentation textuelle de la VAE.
        
        Returns:
            str: Identification de la VAE avec sa référence et son statut
        """
        return f"VAE {self.reference or self.id} - {self.get_statut_display()}"
    
    def __repr__(self):
        """
        📝 Représentation technique pour le débogage.
        
        Returns:
            str: Format technique détaillé
        """
        return f"<VAE(id={self.pk}, ref='{self.reference}', statut='{self.statut}')>"
    
    def save(self, *args, **kwargs):
        """
        💾 Personnalisation de la sauvegarde pour générer la référence automatiquement
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
        
    def invalidate_caches(self):
        """
        🔄 Invalide les caches associés à cette VAE.
        """
        super().invalidate_caches()
        
        # Invalider les caches spécifiques
        from django.core.cache import cache
        cache_keys = [
            f"vae_{self.pk}",
            f"vae_reference_{self.reference}",
            f"vae_centre_{self.centre_id}",
            f"vae_statut_{self.statut}",
            f"vae_stats_{self.centre_id}_{self.annee_creation}"
        ]
        
        for key in cache_keys:
            cache.delete(key)
    
    @property
    def annee_creation(self):
        """
        📅 Retourne l'année de création de la VAE.
        
        Returns:
            int: Année de création
        """
        return self.created_at.year
    
    @property
    def mois_creation(self):
        """
        📅 Retourne le mois de création de la VAE.
        
        Returns:
            int: Mois de création (1-12)
        """
        return self.created_at.month
        
    @property
    def duree_jours(self):
        """
        ⏱️ Calcule la durée en jours depuis la création de la VAE.
        
        Returns:
            int: Nombre de jours écoulés depuis la création
        """
        today = timezone.now().date()
        return (today - self.created_at.date()).days
        
    def is_en_cours(self):
        """
        🔍 Vérifie si la VAE est en cours (non terminée ou abandonnée).
        
        Returns:
            bool: True si la VAE est en cours, False sinon
        """
        return self.statut in self.STATUTS_EN_COURS
        
    def is_terminee(self):
        """
        🔍 Vérifie si la VAE est terminée ou abandonnée.
        
        Returns:
            bool: True si la VAE est terminée ou abandonnée, False sinon
        """
        return self.statut in self.STATUTS_TERMINES
        
    def dernier_changement_statut(self):
        """
        📋 Retourne le dernier changement de statut de cette VAE.
        
        Returns:
            HistoriqueStatutVAE: Dernier historique de statut, ou None si aucun
        """
        return self.historique_statuts.order_by('-date_changement_effectif', '-created_at').first()
        
    def duree_statut_actuel(self):
        """
        ⏱️ Calcule la durée (en jours) depuis le dernier changement de statut.
        
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
        📊 Version optimisée des comptages par statut avec annotation
        
        Args:
            centre (Centre, optional): Centre pour filtrer les résultats
            annee (int, optional): Année pour filtrer les résultats
            mois (int, optional): Mois pour filtrer les résultats
            
        Returns:
            dict: Dictionnaire des comptages par statut
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
    
    def changer_statut(self, nouveau_statut, date_effet=None, commentaire="", user=None):
        """
        📝 Change le statut de manière contrôlée avec historique
        
        Args:
            nouveau_statut (str): Nouveau statut à appliquer
            date_effet (date, optional): Date d'effet du changement
            commentaire (str, optional): Commentaire sur le changement
            user (User, optional): Utilisateur effectuant le changement
            
        Raises:
            ValidationError: Si le statut est invalide
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

    def to_csv_row(self):
        """
        📤 Retourne une ligne CSV représentant cette VAE.

        Returns:
            list: Valeurs formatées pour une exportation CSV
        """
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
            self.dernier_changement_statut().get_statut_display() if self.dernier_changement_statut() else '',
            self.duree_statut_actuel(),
        ]
                
    def to_serializable_dict(self, exclude=None):
        """
        📦 Retourne un dictionnaire sérialisable de la VAE.
        
        Args:
            exclude (list[str], optional): Liste de champs à exclure
            
        Returns:
            dict: Données sérialisables de la VAE
        """
        exclude = exclude or []
        data = super().to_serializable_dict(exclude)
        
        dernier_changement = self.dernier_changement_statut()
        
        # Ajouter des données spécifiques
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
                'date': dernier_changement.date_changement_effectif.isoformat() if dernier_changement else None,
                'statut': dernier_changement.statut if dernier_changement else None,
                'statut_libelle': dernier_changement.get_statut_display() if dernier_changement else None,
            } if dernier_changement else None,
            'duree_statut_actuel': self.duree_statut_actuel(),
        })
        
        return data

    def clean(self):
        """
        🔍 Validation supplémentaire
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        super().clean()

        # Validation de la référence
        if self.reference and not self.reference.startswith('VAE-'):
            raise ValidationError({'reference': "La référence doit commencer par 'VAE-'"})
            
class HistoriqueStatutVAE(BaseModel):
    """
    📜 Modèle pour suivre l'historique des changements de statut d'une VAE.
    
    Ce modèle enregistre chaque changement de statut d'une VAE, permettant
    ainsi de suivre son évolution dans le temps et de calculer des statistiques
    sur les durées des différentes étapes.
    
    Attributes:
        vae (VAE): La VAE concernée par ce changement de statut
        statut (str): Le nouveau statut
        date_changement_effectif (date): Date à laquelle le changement a eu lieu
        commentaire (str): Notes supplémentaires sur ce changement
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
            models.Index(fields=['vae', 'statut'], name='hist_vae_statut_idx'),
            models.Index(fields=['date_changement_effectif'], name='hist_vae_date_idx'),
            models.Index(fields=['vae', 'date_changement_effectif'], name='hist_vae_vae_date_idx'),
        ]
    
    def to_csv_row(self):
        """
        📤 Retourne une ligne CSV représentant cet historique de statut.

        Returns:
            list: Valeurs formatées pour une exportation CSV
        """
        return [
            self.id,
            self.vae.reference if self.vae else '',
            self.get_statut_display(),
            self.date_changement_effectif.strftime('%Y-%m-%d') if self.date_changement_effectif else '',
            self.commentaire,
        ]
    
    def __str__(self):
        """
        🔁 Représentation textuelle de l'historique de statut.
        
        Returns:
            str: Description du changement de statut avec la VAE et la date
        """
        return f"{self.vae} - {self.get_statut_display()} le {self.date_changement_effectif.strftime('%d/%m/%Y')}"
    
    def __repr__(self):
        """
        📝 Représentation technique pour le débogage.
        
        Returns:
            str: Format technique détaillé
        """
        return f"<HistoriqueStatutVAE(id={self.pk}, vae='{self.vae_id}', statut='{self.statut}')>"
        
        
    def clean(self):
        """
        🔍 Validation des contraintes sur les champs.
        
        Vérifie notamment que la date du changement n'est pas dans le futur et
        qu'elle n'est pas antérieure à la date de création de la VAE.
        
        Raises:
            ValidationError: Si les contraintes ne sont pas respectées
        """
        super().clean()
        
        if self.date_changement_effectif and self.date_changement_effectif > timezone.now().date():
            raise ValidationError({
                'date_changement_effectif': _("La date du changement ne peut pas être dans le futur.")
            })
            
        if hasattr(self, 'vae') and self.vae and self.vae.created_at:
            if self.date_changement_effectif < self.vae.created_at.date():
                raise ValidationError({
                    'date_changement_effectif': _("La date du changement ne peut pas être antérieure à la date de création de la VAE.")
                })
                
    def save(self, *args, **kwargs):
        """
        💾 Personnalisation de la sauvegarde.
        
        Args:
            *args: Arguments positionnels
            **kwargs: Arguments nommés pouvant contenir skip_validation (bool)
        """
        skip_validation = kwargs.pop('skip_validation', False)
        is_new = self.pk is None
        user = kwargs.pop("user", None)
        
        # Validation complète sauf si désactivée
        if not skip_validation:
            self.full_clean()
        
        # Journalisation
        if is_new:
            logger.info(f"📝 Nouveau statut enregistré pour {self.vae}: {self.get_statut_display()} le {self.date_changement_effectif}")
            
        super().save(*args, user=user, **kwargs)
        
    def invalidate_caches(self):
        """
        🔄 Invalide les caches associés à cet historique.
        """
        super().invalidate_caches()
        
        # Invalider les caches spécifiques
        from django.core.cache import cache
        cache_keys = [
            f"historiquestatut_{self.pk}",
            f"vae_{self.vae_id}_historique",
            f"vae_statuts_{self.vae_id}",
            f"vae_historique_{self.vae.reference}" if hasattr(self, 'vae') and self.vae else None
        ]
        
        for key in cache_keys:
            if key:  # Éviter les clés None
                cache.delete(key)
        
    def to_serializable_dict(self, exclude=None):
        """
        📦 Retourne un dictionnaire sérialisable de l'historique.
        
        Args:
            exclude (list[str], optional): Liste de champs à exclure
            
        Returns:
            dict: Données sérialisables de l'historique
        """
        exclude = exclude or []
        data = super().to_serializable_dict(exclude)
        
        # Ajouter des données spécifiques
        data.update({
            'vae_id': self.vae_id,
            'vae_reference': self.vae.reference if hasattr(self, 'vae') and self.vae else None,
            'statut': self.statut,
            'statut_libelle': self.get_statut_display(),
            'date_changement_effectif': self.date_changement_effectif.isoformat(),
            'commentaire': self.commentaire,
        })
        
        return data