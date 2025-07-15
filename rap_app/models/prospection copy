import logging
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.db.models import Q, F, Count
from django.utils.functional import cached_property
from django.db.models.functions import Now

from .base import BaseModel
from .formations import Formation
from .partenaires import Partenaire

logger = logging.getLogger(__name__)

# ----------------------------------------------------
# Signaux déplacés dans un fichier signals/
# ----------------------------------------------------


# Choix standards pour les modèles de prospection
from django.utils.translation import gettext_lazy as _

class ProspectionChoices:
    """
    Classe regroupant les choix standards pour les modèles de prospection.
    Facilite la réutilisation et la maintenance des choix.
    """

    # Statuts de prospection
    STATUT_A_FAIRE = 'a_faire'
    STATUT_EN_COURS = 'en_cours'
    STATUT_A_RELANCER = 'a_relancer'
    STATUT_ACCEPTEE = 'acceptee'
    STATUT_REFUSEE = 'refusee'
    STATUT_ANNULEE = 'annulee'
    STATUT_NON_RENSEIGNE = 'non_renseigne'

    PROSPECTION_STATUS_CHOICES = [
        (STATUT_A_FAIRE, _('À faire')),
        (STATUT_EN_COURS, _('En cours')),
        (STATUT_A_RELANCER, _('À relancer')),
        (STATUT_ACCEPTEE, _('Acceptée')),
        (STATUT_REFUSEE, _('Refusée')),
        (STATUT_ANNULEE, _('Annulée')),
        (STATUT_NON_RENSEIGNE, _('Non renseigné')),
    ]

    # Objectifs de prospection
    OBJECTIF_PRISE_CONTACT = 'prise_contact'
    OBJECTIF_RENDEZ_VOUS = 'rendez_vous'
    OBJECTIF_PRESENTATION = 'presentation_offre'
    OBJECTIF_CONTRAT = 'contrat'
    OBJECTIF_PARTENARIAT = 'partenariat'
    OBJECTIF_AUTRE = 'autre'

    PROSPECTION_OBJECTIF_CHOICES = [
        (OBJECTIF_PRISE_CONTACT, _('Prise de contact')),
        (OBJECTIF_RENDEZ_VOUS, _('Obtenir un rendez-vous')),
        (OBJECTIF_PRESENTATION, _("Présentation d'une offre")),
        (OBJECTIF_CONTRAT, _('Signer un contrat')),
        (OBJECTIF_PARTENARIAT, _('Établir un partenariat')),
        (OBJECTIF_AUTRE, _('Autre')),
    ]

    # Motifs de prospection
    MOTIF_POEI = 'POEI'
    MOTIF_APPRENTISSAGE = 'apprentissage'
    MOTIF_VAE = 'VAE'
    MOTIF_PARTENARIAT = 'partenariat'
    MOTIF_AUTRE = 'autre'
    
    PROSPECTION_MOTIF_CHOICES = [
        (MOTIF_POEI, _('POEI')),
        (MOTIF_APPRENTISSAGE, _('Apprentissage')),
        (MOTIF_VAE, _('VAE')),
        (MOTIF_PARTENARIAT, _('Établir un partenariat')),
        (MOTIF_AUTRE, _('Autre')),
    ]
    
    # Moyens de contact
    MOYEN_EMAIL = 'email'
    MOYEN_TELEPHONE = 'telephone'
    MOYEN_VISITE = 'visite'
    MOYEN_RESEAUX = 'reseaux'
    
    MOYEN_CONTACT_CHOICES = [
        (MOYEN_EMAIL, _('Email')),
        (MOYEN_TELEPHONE, _('Téléphone')),
        (MOYEN_VISITE, _('Visite')),
        (MOYEN_RESEAUX, _('Réseaux sociaux')),
    ]
    
    # Types de contact
    TYPE_PREMIER_CONTACT = 'premier_contact'
    TYPE_RELANCE = 'relance'
    
    TYPE_CONTACT_CHOICES = [
        (TYPE_PREMIER_CONTACT, _('Premier contact')),
        (TYPE_RELANCE, _('Relance')),
    ]
    
    @classmethod
    def get_statut_labels(cls):
        """
        Retourne un dictionnaire des labels de statut.
        
        Returns:
            dict: Dictionnaire {code: label} des statuts
        """
        return dict(cls.PROSPECTION_STATUS_CHOICES)
    
    @classmethod
    def get_objectifs_labels(cls):
        """
        Retourne un dictionnaire des labels d'objectif.
        
        Returns:
            dict: Dictionnaire {code: label} des objectifs
        """
        return dict(cls.PROSPECTION_OBJECTIF_CHOICES)


class ProspectionManager(models.Manager):
    """
    Manager personnalisé pour le modèle Prospection.
    Fournit des méthodes utilitaires pour les requêtes courantes.
    """
    
    def actives(self):
        """
        Retourne uniquement les prospections actives (non refusées/annulées).
        
        Returns:
            QuerySet: Prospections actives
        """
        return self.exclude(statut__in=[
            ProspectionChoices.STATUT_REFUSEE,
            ProspectionChoices.STATUT_ANNULEE
        ])
    
    def a_relancer(self, date=None):
        """
        Retourne les prospections à relancer.
        
        Args:
            date (date, optional): Date de référence, aujourd'hui par défaut
            
        Returns:
            QuerySet: Prospections à relancer
        """
        date = date or timezone.now().date()
        
        # Récupérer les derniers historiques pour chaque prospection
        derniers_historiques = HistoriqueProspection.objects.filter(
            prospection=models.OuterRef('pk')
        ).order_by('-date_modification')[:1]
        
        # Annoter avec la date du prochain contact
        return self.filter(
            statut=ProspectionChoices.STATUT_A_RELANCER
        ).annotate(
            prochain_contact=models.Subquery(
                derniers_historiques.values('prochain_contact')
            )
        ).filter(
            prochain_contact__lte=date
        )
    
    def par_partenaire(self, partenaire_id):
        """
        Filtre les prospections par partenaire.
        
        Args:
            partenaire_id (int): ID du partenaire
            
        Returns:
            QuerySet: Prospections du partenaire
        """
        return self.filter(partenaire_id=partenaire_id).select_related('formation')
    
    def par_formation(self, formation_id):
        """
        Filtre les prospections par formation.
        
        Args:
            formation_id (int): ID de la formation
            
        Returns:
            QuerySet: Prospections liées à la formation
        """
        return self.filter(formation_id=formation_id).select_related('partenaire')
    
    def par_statut(self, statut):
        """
        Filtre les prospections par statut.
        
        Args:
            statut (str): Code du statut
            
        Returns:
            QuerySet: Prospections ayant ce statut
        """
        return self.filter(statut=statut)
    
    def statistiques_par_statut(self):
        """
        Calcule des statistiques de prospection par statut.
        
        Returns:
            dict: Statistiques par statut
        """
        stats = self.values('statut').annotate(
            count=Count('id')
        ).order_by('statut')
        
        # Conversion en dictionnaire {statut: count}
        resultat = {}
        statut_labels = ProspectionChoices.get_statut_labels()
        
        for stat in stats:
            code = stat['statut']
            label = statut_labels.get(code, code)
            resultat[code] = {
                'label': label,
                'count': stat['count']
            }
            
        return resultat


class Prospection(BaseModel):
    """
    🔍 Représente une prospection commerciale vers un partenaire.
    
    Ce modèle permet de suivre les démarches commerciales avec des partenaires,
    incluant l'objectif, le motif, le type de contact, le statut et les commentaires.
    
    Attributs:
        partenaire (Partenaire): Partenaire concerné par la prospection
        formation (Formation, optional): Formation liée à la prospection
        date_prospection (datetime): Date et heure de la prospection
        type_contact (str): Type de contact (premier ou relance)
        motif (str): Motif de la prospection
        statut (str): Statut actuel de la prospection
        objectif (str): Objectif visé par la prospection
        commentaire (str): Commentaire ou notes sur la prospection
        
    Propriétés:
        is_active (bool): Indique si la prospection est active
        prochain_contact (date): Date prévue pour le prochain contact
        historique_recent (QuerySet): Historique récent de la prospection
        
    Méthodes:
        to_serializable_dict: Représentation sérialisable pour API
        creer_historique: Crée une entrée d'historique pour la prospection
    """
    
    # Constantes pour les limites de champs
    MAX_TYPE_LENGTH = 20
    MAX_STATUT_LENGTH = 20
    MAX_MOTIF_LENGTH = 30
    MAX_OBJECTIF_LENGTH = 30

    # === Relations ===
    partenaire = models.ForeignKey(
        Partenaire, 
        on_delete=models.CASCADE, 
        related_name="prospections",
        verbose_name=_("Partenaire"), 
        help_text=_("Partenaire concerné par cette prospection")
    )
    
    formation = models.ForeignKey(
        Formation, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name="prospections", 
        verbose_name=_("Formation"), 
        help_text=_("Formation associée à cette prospection (optionnel)")
    )

    # === Champs principaux ===
    date_prospection = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Date de prospection"),
        help_text=_("Date et heure de la prospection")
    )
    
    type_contact = models.CharField(
        max_length=MAX_TYPE_LENGTH,
        choices=ProspectionChoices.TYPE_CONTACT_CHOICES,
        default=ProspectionChoices.TYPE_PREMIER_CONTACT,
        verbose_name=_("Type de contact"),
        help_text=_("Indique s'il s'agit d'un premier contact ou d'une relance")
    )
    
    motif = models.CharField(
        max_length=MAX_MOTIF_LENGTH, 
        choices=ProspectionChoices.PROSPECTION_MOTIF_CHOICES,
        verbose_name=_("Motif"),
        help_text=_("Motif principal de la prospection")
    )
    
    statut = models.CharField(
        max_length=MAX_STATUT_LENGTH, 
        choices=ProspectionChoices.PROSPECTION_STATUS_CHOICES, 
        default=ProspectionChoices.STATUT_A_FAIRE,
        verbose_name=_("Statut"),
        help_text=_("État actuel de la prospection")
    )
    
    objectif = models.CharField(
        max_length=MAX_OBJECTIF_LENGTH, 
        choices=ProspectionChoices.PROSPECTION_OBJECTIF_CHOICES, 
        default=ProspectionChoices.OBJECTIF_PRISE_CONTACT,
        verbose_name=_("Objectif"),
        help_text=_("Objectif visé par cette prospection")
    )
    
    commentaire = models.TextField(
        blank=True, 
        null=True,
        verbose_name=_("Commentaire"),
        help_text=_("Notes ou commentaires sur cette prospection")
    )
    
    # === Managers ===
    objects = models.Manager()
    custom = ProspectionManager()

    class Meta:
        verbose_name = _("Suivi de prospection")
        verbose_name_plural = _("Suivis de prospections")
        ordering = ['-date_prospection']
        indexes = [
            models.Index(fields=['statut'], name='prosp_statut_idx'),
            models.Index(fields=['date_prospection'], name='prosp_date_idx'),
            models.Index(fields=['partenaire'], name='prosp_partenaire_idx'),
            models.Index(fields=['formation'], name='prosp_formation_idx'),
            models.Index(fields=['created_by'], name='prosp_createdby_idx'),
            models.Index(fields=['motif'], name='prosp_motif_idx'),
            models.Index(fields=['objectif'], name='prosp_objectif_idx'),
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
        """Représentation textuelle de la prospection."""
        formation = self.formation.nom if self.formation else _("Sans formation")
        auteur = self.created_by.username if self.created_by else _("Anonyme")
        return f"{self.partenaire.nom} - {formation} - {self.get_statut_display()} ({auteur})"
        
    def __repr__(self):
        """Représentation technique pour le débogage."""
        return f"<Prospection(id={self.pk}, partenaire='{self.partenaire.nom if self.partenaire else None}', statut='{self.statut}')>"

    def clean(self):
        """
        Validation des données avant sauvegarde.
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        super().clean()
        
        # Validation de la date (pas dans le futur)
        if self.date_prospection > timezone.now():
            raise ValidationError({
                'date_prospection': _("La date de prospection ne peut pas être dans le futur.")
            })
            
        # Validation pour les prospections acceptées
        if self.statut == ProspectionChoices.STATUT_ACCEPTEE and self.objectif != ProspectionChoices.OBJECTIF_CONTRAT:
            raise ValidationError({
                'statut': _("Une prospection acceptée doit viser la signature d'un contrat."),
                'objectif': _("L'objectif doit être la signature d'un contrat pour une prospection acceptée.")
            })
            
        # Validation du commentaire pour certains statuts
        if self.statut in [ProspectionChoices.STATUT_REFUSEE, ProspectionChoices.STATUT_ANNULEE] and not self.commentaire:
            raise ValidationError({
                'commentaire': _("Un commentaire est obligatoire pour les prospections refusées ou annulées.")
            })

    def save(self, *args, **kwargs):
        """
        Sauvegarde la prospection et crée un historique si nécessaire.
        
        Args:
            *args: Arguments positionnels
            **kwargs: Arguments nommés, notamment user et skip_history
        """
        user = kwargs.pop("user", None)
        skip_history = kwargs.pop("skip_history", False)  # Option pour désactiver l'historique
        
        is_new = self.pk is None
        original = None if is_new else Prospection.objects.filter(pk=self.pk).first()

        if user:
            self._user = user

        # Validation des données
        self.full_clean()

        with transaction.atomic():
            # Sauvegarde
            super().save(*args, **kwargs)
            logger.info(f"{'Création' if is_new else 'Mise à jour'} prospection #{self.pk} - {self.partenaire.nom}")

            # Création d'une entrée dans l'historique si nécessaire
            if not skip_history:
                if is_new:
                    # Historique pour une nouvelle prospection
                    self.creer_historique(
                        ancien_statut=ProspectionChoices.STATUT_NON_RENSEIGNE,
                        nouveau_statut=self.statut,
                        type_contact=self.type_contact,
                        commentaire=self.commentaire or "",
                        resultat=f"Objectif initial : {self.get_objectif_display()}",
                        user=user
                    )
                elif original and (
                    original.statut != self.statut or
                    original.objectif != self.objectif or
                    original.commentaire != self.commentaire
                ):
                    # Historique pour une modification
                    self.creer_historique(
                        ancien_statut=original.statut,
                        nouveau_statut=self.statut,
                        type_contact=self.type_contact,
                        commentaire=self.commentaire or "",
                        resultat=(
                            f"Objectif modifié : {original.get_objectif_display()} → {self.get_objectif_display()}"
                            if original.objectif != self.objectif else ""
                        ),
                        user=user or self.updated_by or self.created_by
                    )        
   
   
   
    def creer_historique(self, ancien_statut, nouveau_statut, type_contact, commentaire="", 
                         resultat="", moyen_contact=None, user=None, prochain_contact=None):
        """
        Crée une entrée d'historique pour cette prospection.
        
        Args:
            ancien_statut (str): Statut avant modification
            nouveau_statut (str): Statut après modification
            type_contact (str): Type de contact
            commentaire (str): Commentaire explicatif
            resultat (str): Résultat de l'action
            moyen_contact (str): Moyen de contact utilisé
            user (User): Utilisateur ayant effectué la modification
            prochain_contact (date): Date prévue pour le prochain contact
            
        Returns:
            HistoriqueProspection: Instance créée
        """
        # Calcul de la date du prochain contact (par défaut 7 jours)
        if prochain_contact is None:
            # Si statut "à relancer", prochain contact dans 7 jours
            if nouveau_statut == ProspectionChoices.STATUT_A_RELANCER:
                prochain_contact = timezone.now().date() + timezone.timedelta(days=7)
            # Si statut "en cours", prochain contact dans 14 jours
            elif nouveau_statut == ProspectionChoices.STATUT_EN_COURS:
                prochain_contact = timezone.now().date() + timezone.timedelta(days=14)
                
        # Création de l'historique
        historique = HistoriqueProspection.objects.create(
            prospection=self,
            ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut,
            type_contact=type_contact,
            commentaire=commentaire,
            resultat=resultat,
            prochain_contact=prochain_contact,
            moyen_contact=moyen_contact,
            created_by=user
        )
        
        logger.debug(f"Historique créé pour prospection #{self.pk}: {ancien_statut} → {nouveau_statut}")
        return historique

    @classmethod
    def add_to_formation(cls, formation, partenaire: Partenaire, user, **kwargs) -> "Prospection":
        """
        Crée une prospection liée à une formation et journalise l'action.

        Args:
            formation (Formation): Formation concernée
            partenaire (Partenaire): Partenaire ciblé
            user (User): Utilisateur initiant la création
            **kwargs: Champs additionnels (objectif, statut, etc.)

        Returns:
            Prospection: Instance de prospection créée
        """
        from .formations import HistoriqueFormation  # import local pour éviter conflit
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



    def to_serializable_dict(self):
        """
        Convertit la prospection en dictionnaire sérialisable pour API.
        
        Returns:
            dict: Données sérialisables
        """
        return {
            "id": self.pk,
            "partenaire": {
                "id": self.partenaire.pk,
                "nom": str(self.partenaire)
            },
            "formation": {
                "id": self.formation.pk if self.formation else None,
                "nom": self.formation.nom if self.formation else None
            },
            "date": self.date_prospection.strftime('%Y-%m-%d %H:%M'),
            "type_contact": self.get_type_contact_display(),
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
        
    @property
    def is_active(self):
        """
        Indique si la prospection est active (non refusée/annulée).
        
        Returns:
            bool: True si active
        """
        return self.statut not in [
            ProspectionChoices.STATUT_REFUSEE,
            ProspectionChoices.STATUT_ANNULEE
        ]
        
    @cached_property
    def prochain_contact(self):
        """
        Retourne la date du prochain contact prévue.
        
        Returns:
            date: Date du prochain contact ou None
        """
        # Récupération du dernier historique
        historique = HistoriqueProspection.objects.filter(
            prospection=self
        ).order_by('-date_modification').first()
        
        # Si historique trouvé et date de prochain contact définie
        if historique and historique.prochain_contact:
            return historique.prochain_contact
            
        return None
        
    @property
    def historique_recent(self):
        """
        Retourne l'historique récent de la prospection.
        
        Returns:
            QuerySet: Historique limité aux 5 dernières entrées
        """
        return self.historiques.all().order_by('-date_modification')[:5]
    
    @property
    def relance_necessaire(self):
        """
        Indique si une relance est nécessaire selon la date prévue.
        
        Returns:
            bool: True si relance nécessaire
        """
        if not self.is_active or not self.prochain_contact:
            return False
            
        return self.statut == ProspectionChoices.STATUT_A_RELANCER and self.prochain_contact <= timezone.now().date()
        
    @classmethod
    def get_stats_par_statut(cls, formation=None):
        """
        Retourne des statistiques de prospection par statut.
        
        Args:
            formation (Formation, optional): Filtrer par formation
            
        Returns:
            dict: Statistiques par statut
        """
        # Base de la requête
        queryset = cls.objects.all()
        
        # Filtrage par formation si spécifiée
        if formation:
            queryset = queryset.filter(formation=formation)
            
        # Calcul des statistiques
        return queryset.custom.statistiques_par_statut()


class HistoriqueProspectionManager(models.Manager):
    """
    Manager personnalisé pour le modèle HistoriqueProspection.
    """
    
    def a_relancer_cette_semaine(self):
        """
        Retourne les historiques avec relance prévue cette semaine.
        
        Returns:
            QuerySet: Historiques avec relance cette semaine
        """
        today = timezone.now().date()
        start_of_week = today - timezone.timedelta(days=today.weekday())
        end_of_week = start_of_week + timezone.timedelta(days=6)
        
        return self.filter(
            prochain_contact__gte=start_of_week,
            prochain_contact__lte=end_of_week
        ).select_related('prospection', 'prospection__partenaire')
    
    def derniers_par_prospection(self):
        """
        Retourne les derniers historiques pour chaque prospection.
        
        Returns:
            QuerySet: Derniers historiques par prospection
        """
        # Sous-requête pour trouver la date de modification maximale par prospection
        last_dates = self.values('prospection').annotate(
            max_date=models.Max('date_modification')
        ).values('prospection', 'max_date')
        
        # Liste des derniers historiques
        result = []
        
        for item in last_dates:
            historique = self.filter(
                prospection_id=item['prospection'],
                date_modification=item['max_date']
            ).first()
            
            if historique:
                result.append(historique.pk)
                
        return self.filter(pk__in=result)


class HistoriqueProspection(BaseModel):
    """
    🕓 Historique des modifications d'une prospection.
    
    Ce modèle enregistre les changements de statut, d'objectif, de commentaires,
    et de date de relance pour une prospection.
    
    Attributs:
        prospection (Prospection): Prospection concernée
        date_modification (datetime): Date et heure de la modification
        ancien_statut (str): Statut avant modification
        nouveau_statut (str): Statut après modification
        type_contact (str): Type de contact
        commentaire (str): Commentaire explicatif
        resultat (str): Résultat de l'action
        prochain_contact (date): Date prévue pour le prochain contact
        moyen_contact (str): Moyen de contact utilisé
        
    Propriétés:
        est_recent (bool): Indique si l'historique est récent
        jours_avant_relance (int): Nombre de jours avant la relance
        
    Méthodes:
        to_serializable_dict: Représentation API
    """
    
    # Constantes pour les limites de champs
    MAX_STATUT_LENGTH = 20
    MAX_TYPE_LENGTH = 20
    MAX_MOYEN_LENGTH = 50

    prospection = models.ForeignKey(
        Prospection, 
        on_delete=models.CASCADE, 
        related_name="historiques",
        verbose_name=_("Prospection"),
        help_text=_("Prospection concernée par cet historique")
    )
    
    date_modification = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de modification"),
        help_text=_("Date et heure de la modification")
    )
    
    ancien_statut = models.CharField(
        max_length=MAX_STATUT_LENGTH, 
        choices=ProspectionChoices.PROSPECTION_STATUS_CHOICES,
        verbose_name=_("Ancien statut"),
        help_text=_("Statut avant la modification")
    )
    
    nouveau_statut = models.CharField(
        max_length=MAX_STATUT_LENGTH, 
        choices=ProspectionChoices.PROSPECTION_STATUS_CHOICES,
        verbose_name=_("Nouveau statut"),
        help_text=_("Statut après la modification")
    )
    
    type_contact = models.CharField(
        max_length=MAX_TYPE_LENGTH,
        choices=ProspectionChoices.TYPE_CONTACT_CHOICES,
        default=ProspectionChoices.TYPE_PREMIER_CONTACT,
        verbose_name=_("Type de contact"),
        help_text=_("Type de contact utilisé")
    )
    
    commentaire = models.TextField(
        blank=True, 
        null=True,
        verbose_name=_("Commentaire"),
        help_text=_("Commentaire ou note sur la modification")
    )
    
    resultat = models.TextField(
        blank=True, 
        null=True,
        verbose_name=_("Résultat"),
        help_text=_("Résultat ou conséquence de l'action")
    )
    
    prochain_contact = models.DateField(
        blank=True, 
        null=True,
        verbose_name=_("Prochain contact"),
        help_text=_("Date prévue pour le prochain contact")
    )
    
    moyen_contact = models.CharField(
        max_length=MAX_MOYEN_LENGTH, 
        choices=ProspectionChoices.MOYEN_CONTACT_CHOICES, 
        blank=True, 
        null=True,
        verbose_name=_("Moyen de contact"),
        help_text=_("Moyen de communication utilisé")
    )
    
    # Managers
    objects = models.Manager()
    custom = HistoriqueProspectionManager()

    class Meta:
        verbose_name = _("Historique de prospection")
        verbose_name_plural = _("Historiques de prospections")
        ordering = ['-date_modification']
        indexes = [
            models.Index(fields=['prospection'], name='histprosp_prosp_idx'),
            models.Index(fields=['date_modification'], name='histprosp_date_idx'),
            models.Index(fields=['prochain_contact'], name='histprosp_next_idx'),
            models.Index(fields=['nouveau_statut'], name='histprosp_statut_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(prochain_contact__isnull=True) | Q(prochain_contact__gte=Now()),
                name='histprosp_prochain_contact_futur'
            )
        ]

    def __str__(self):
        """Représentation textuelle de l'historique."""
        return f"{self.date_modification.strftime('%d/%m/%Y')} - {self.get_nouveau_statut_display()}"
        
    def __repr__(self):
        """Représentation technique pour le débogage."""
        return f"<HistoriqueProspection(id={self.pk}, prospection_id={self.prospection_id}, statut='{self.nouveau_statut}')>"

    def clean(self):
        """
        Validation des données avant sauvegarde.
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        super().clean()
        
        # Validation de la date de prochain contact
        if self.prochain_contact and self.prochain_contact < timezone.now().date():
            raise ValidationError({
                'prochain_contact': _("La date de relance doit être dans le futur.")
            })
            
        # Vérification de la cohérence des statuts
        if self.ancien_statut == self.nouveau_statut:
            # Autorisé pour les commentaires supplémentaires, mais générer un avertissement
            logger.warning(f"Historique créé sans changement de statut pour prospection #{self.prospection_id}")

    def save(self, *args, **kwargs):
        """
        Sauvegarde avec validation et transaction sécurisée.
        
        Args:
            *args: Arguments positionnels
            **kwargs: Arguments nommés
        """
        # Validation des données
        self.full_clean()
        
        with transaction.atomic():
            # Sauvegarde
            super().save(*args, **kwargs)
            
            # Mise à jour du statut de la prospection si nécessaire
            prospection = self.prospection
            if prospection.statut != self.nouveau_statut:
                prospection.statut = self.nouveau_statut
                prospection.save(update_fields=['statut'], skip_history=True)
                
        logger.info(f"🕓 Historique enregistré pour prospection {self.prospection.pk}: {self.ancien_statut} → {self.nouveau_statut}")
            

    def to_serializable_dict(self):
        """
        Convertit l'historique en dictionnaire sérialisable pour API.
        
        Returns:
            dict: Données sérialisables
        """
        return {
            "id": self.pk,
            "prospection_id": self.prospection_id,
            "prospection": {
                "id": self.prospection_id,
                "partenaire": str(self.prospection.partenaire) if self.prospection.partenaire else None
            },
            "type_contact": self.get_type_contact_display(),
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
        """
        Indique si l'historique est récent (moins de 7 jours).
        
        Returns:
            bool: True si récent
        """
        return (timezone.now().date() - self.date_modification.date()).days <= 7
        
    @property
    def jours_avant_relance(self):
        """
        Calcule le nombre de jours avant la relance.
        
        Returns:
            int: Nombre de jours ou -1 si pas de prochain contact
        """
        if not self.prochain_contact:
            return -1
            
        today = timezone.now().date()
        delta = (self.prochain_contact - today).days
        return max(0, delta)
        
    @property
    def relance_urgente(self):
        """
        Indique si la relance est urgente (moins de 2 jours).
        
        Returns:
            bool: True si urgente
        """
        return 0 <= self.jours_avant_relance <= 2
        
    @property
    def statut_avec_icone(self):
        """
        Retourne le statut avec une icône adaptée.
        
        Returns:
            tuple: (statut, icone, classe_css)
        """
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
        """
        Retourne les relances à venir dans les prochains jours.
        
        Args:
            jours (int): Nombre de jours à considérer
            
        Returns:
            QuerySet: Historiques avec relance prévue
        """
        today = timezone.now().date()
        date_limite = today + timezone.timedelta(days=jours)
        
        return cls.objects.filter(
            prochain_contact__gte=today,
            prochain_contact__lte=date_limite,
            prospection__statut=ProspectionChoices.STATUT_A_RELANCER
        ).select_related(
            'prospection', 
            'prospection__partenaire'
        ).order_by('prochain_contact') 