import logging
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from django.db.models import Q, F, Avg, Count, Sum

from .base import BaseModel
from .formations import Formation

logger = logging.getLogger("application.evenements")

# ----------------------------------------------------
# Signaux déplacés dans un fichier signals/
# ----------------------------------------------------


class EvenementManager(models.Manager):
    """
    Manager personnalisé pour le modèle Evenement.
    Fournit des méthodes utilitaires pour les requêtes courantes.
    """
    
    def a_venir(self, days=30):
        """
        Retourne les événements à venir dans les prochains jours.
        
        Args:
            days (int): Nombre de jours à considérer
            
        Returns:
            QuerySet: Événements à venir
        """
        today = timezone.now().date()
        limit_date = today + timezone.timedelta(days=days)
        return self.filter(
            event_date__gte=today,
            event_date__lte=limit_date
        ).order_by('event_date')
    
    def passes(self):
        """
        Retourne les événements déjà passés.
        
        Returns:
            QuerySet: Événements passés
        """
        today = timezone.now().date()
        return self.filter(event_date__lt=today).order_by('-event_date')
    
    def aujourd_hui(self):
        """
        Retourne les événements ayant lieu aujourd'hui.
        
        Returns:
            QuerySet: Événements du jour
        """
        today = timezone.now().date()
        return self.filter(event_date=today)
    
    def par_type(self, type_evenement):
        """
        Filtre les événements par type.
        
        Args:
            type_evenement (str): Type d'événement (utiliser les constantes TypeEvenement)
            
        Returns:
            QuerySet: Événements filtrés par type
        """
        return self.filter(type_evenement=type_evenement)
    
    def par_formation(self, formation_id):
        """
        Filtre les événements par formation.
        
        Args:
            formation_id (int): ID de la formation
            
        Returns:
            QuerySet: Événements liés à la formation
        """
        return self.filter(formation_id=formation_id)
    
    def avec_statistiques(self):
        """
        Ajoute des statistiques calculées aux événements.
        
        Returns:
            QuerySet: Événements avec des annotations
        """
        return self.annotate(
            taux_participation=models.Case(
                models.When(
                    participants_prevus__gt=0,
                    then=models.ExpressionWrapper(
                        100 * F('participants_reels') / F('participants_prevus'),
                        output_field=models.FloatField()
                    )
                ),
                default=None,
                output_field=models.FloatField()
            )
        )


class Evenement(BaseModel):
    """
    📅 Modèle représentant un événement lié à une formation (job dating, forum, etc.).
    
    Permet de suivre les types d'événements, leur date, lieu, et le nombre de participants.
    
    Attributs:
        formation (Formation): Formation associée à l'événement (optionnel)
        type_evenement (str): Type d'événement selon les choix prédéfinis
        description_autre (str): Description personnalisée pour le type 'Autre'
        details (str): Détails ou informations supplémentaires
        event_date (date): Date de l'événement
        lieu (str): Lieu où se déroule l'événement
        participants_prevus (int): Nombre de participants attendus
        participants_reels (int): Nombre de participants effectifs
        
    Propriétés:
        status_label (str): Statut textuel (Passé, Aujourd'hui, À venir)
        status_color (str): Classe CSS pour la couleur du statut
        
    Méthodes:
        get_temporal_status(): Calcule le statut temporel (past, today, soon, future)
        get_participation_rate(): Calcule le taux de participation si possible
        to_serializable_dict(): Représentation sérialisable pour API
    """
    
    # Constantes pour les limites de champs
    MAX_TYPE_LENGTH = 100
    MAX_DESC_LENGTH = 255
    MAX_LIEU_LENGTH = 255
    DAYS_SOON = 7  # Nombre de jours pour considérer un événement comme "bientôt"
    
    # ===== Choix de types d'événements =====
    class TypeEvenement(models.TextChoices):
        INFO_PRESENTIEL = 'info_collective_presentiel', _('Information collective présentiel')
        INFO_DISTANCIEL = 'info_collective_distanciel', _('Information collective distanciel')
        JOB_DATING = 'job_dating', _('Job dating')
        EVENEMENT_EMPLOI = 'evenement_emploi', _('Événement emploi')
        FORUM = 'forum', _('Forum')
        JPO = 'jpo', _('Journée Portes Ouvertes')
        AUTRE = 'autre', _('Autre')
    
    # ===== Statuts temporels =====
    class StatutTemporel(models.TextChoices):
        PASSE = 'past', _('Passé')
        AUJOURD_HUI = 'today', _('Aujourd\'hui')
        BIENTOT = 'soon', _('Bientôt')
        FUTUR = 'future', _('À venir')
        INCONNU = 'unknown', _('Inconnu')

    # ===== Champs du modèle =====
    formation = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="evenements",
        verbose_name=_("Formation"),
        help_text=_("Formation associée à l'événement")
    )

    type_evenement = models.CharField(
        max_length=MAX_TYPE_LENGTH,
        choices=TypeEvenement.choices,
        db_index=True,
        verbose_name=_("Type d'événement"),
        help_text=_("Catégorie de l'événement (ex : forum, job dating, etc.)")
    )

    description_autre = models.CharField(
        max_length=MAX_DESC_LENGTH,
        blank=True,
        null=True,
        verbose_name=_("Description personnalisée"),
        help_text=_("Détail du type si 'Autre' est sélectionné")
    )

    details = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Détails complémentaires"),
        help_text=_("Détails ou informations supplémentaires")
    )

    event_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date de l'événement"),
        help_text=_("Date prévue pour l'événement")
    )

    lieu = models.CharField(
        max_length=MAX_LIEU_LENGTH,
        blank=True,
        null=True,
        verbose_name=_("Lieu"),
        help_text=_("Lieu où se déroule l'événement")
    )

    participants_prevus = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Participants prévus"),
        help_text=_("Nombre de personnes attendues")
    )

    participants_reels = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Participants réels"),
        help_text=_("Nombre de participants présents")
    )
    
    # ===== Managers =====
    objects = models.Manager()
    custom = EvenementManager()

    # ===== Meta =====
    class Meta:
        verbose_name = _("Événement")
        verbose_name_plural = _("Événements")
        ordering = ['-event_date']
        indexes = [
            models.Index(fields=['event_date'], name='event_date_idx'),
            models.Index(fields=['type_evenement'], name='event_type_idx'),
            models.Index(fields=['formation'], name='event_formation_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(type_evenement='autre', description_autre__isnull=False) | ~Q(type_evenement='autre'),
                name='autre_needs_description'
            )
        ]

    # ===== Représentation =====
    def __str__(self):
        """Représentation textuelle de l'événement."""
        label = self.description_autre if self.type_evenement == self.TypeEvenement.AUTRE and self.description_autre else self.get_type_evenement_display()
        date_str = self.event_date.strftime('%d/%m/%Y') if self.event_date else "Date inconnue"
        return f"{label} - {date_str} - {self.status_label}"
    
    def __repr__(self):
        """Représentation pour le débogage."""
        return f"<Evenement(id={self.pk}, type='{self.type_evenement}', date='{self.event_date}')>"

    
    def get_edit_url(self):
        """
        🔗 Retourne l'URL de modification de l'événement.
        
        Returns:
            str: URL de la page d'édition
        """
        return reverse("evenement-edit", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        """
        🔗 Retourne l'URL de suppression de l'événement.
        
        Returns:
            str: URL de la page de suppression
        """
        return reverse("evenement-delete", kwargs={"pk": self.pk})

    # ===== Sérialisation =====
    def to_serializable_dict(self):
        """
        📦 Retourne une représentation sérialisable pour API.
        
        Returns:
            dict: Données sérialisables de l'événement
        """
        return {
            "id": self.pk,
            "formation_id": self.formation_id,
            "formation_nom": self.formation.nom if self.formation else None,
            "type_evenement": self.type_evenement,
            "type_evenement_display": self.get_type_evenement_display(),
            "description_autre": self.description_autre,
            "details": self.details,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "event_date_formatted": self.event_date.strftime('%d/%m/%Y') if self.event_date else None,
            "lieu": self.lieu,
            "participants_prevus": self.participants_prevus,
            "participants_reels": self.participants_reels,
            "taux_participation": self.get_participation_rate(),
            "status": self.get_temporal_status(),
            "status_label": self.status_label,
            "status_color": self.status_color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    # ===== Validation =====
    def clean(self):
        """
        Validation des données avant sauvegarde.
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        super().clean()
        
        today = timezone.now().date()
        
        # Validation type "Autre"
        if self.type_evenement == self.TypeEvenement.AUTRE and not self.description_autre:
            raise ValidationError({
                'description_autre': _("Veuillez décrire l'événement de type 'Autre'.")
            })
        
        # Validation de date ancienne (warning uniquement)
        if self.event_date and self.event_date < today - timezone.timedelta(days=365):
            logger.warning(f"Date ancienne pour l'événement #{self.pk} : {self.event_date}")
        
        # Validation participants
        if self.participants_reels is not None and self.participants_prevus:
            if self.participants_reels > self.participants_prevus * 1.5:
                logger.warning(f"Participants réels ({self.participants_reels}) dépassent largement les prévisions ({self.participants_prevus}) pour l'événement #{self.pk}")
                
            if self.participants_reels == 0 and self.get_temporal_status() == self.StatutTemporel.PASSE:
                logger.warning(f"Événement passé #{self.pk} avec 0 participant réel")

    # ===== Sauvegarde =====
    def save(self, *args, **kwargs):
        """
        💾 Sauvegarde l'événement avec nettoyage, validation, et journalisation des modifications.

        - Valide les champs (`full_clean`)
        - Utilise `transaction.atomic` pour la cohérence
        - Logue les différences si modification détectée
        - Permet le suivi utilisateur via `user=...` dans `kwargs`
        
        Args:
            *args: Arguments positionnels
            **kwargs: Arguments nommés, notamment user
        """
        user = kwargs.pop("user", None)
        is_new = self.pk is None
        original = None if is_new else self.__class__.objects.filter(pk=self.pk).first()

        # Validation des données
        self.full_clean()

        with transaction.atomic():
            # Sauvegarde
            super().save(*args, user=user, **kwargs)
            
            # Journalisation
            if is_new:
                logger.info(f"Nouvel événement '{self}' créé (ID: {self.pk}).")
            elif original:
                self._log_changes(original)

    def _log_changes(self, original):
        """
        📝 Enregistre les modifications détectées par comparaison avec l'instance originale.

        Args:
            original (Evenement): Ancienne version de l'objet avant modification.
        """
        # Liste des champs à surveiller
        fields_to_watch = [
            ('type_evenement', 'Type d\'événement'),
            ('event_date', 'Date'),
            ('formation_id', 'Formation'),
            ('lieu', 'Lieu'),
            ('participants_prevus', 'Participants prévus'),
            ('participants_reels', 'Participants réels'),
            ('description_autre', 'Description personnalisée'),
        ]
        
        # Détection des changements
        changes = []
        for field, label in fields_to_watch:
            old_value = getattr(original, field)
            new_value = getattr(self, field)
            
            if old_value != new_value:
                old_display = self._format_field_value(field, old_value)
                new_display = self._format_field_value(field, new_value)
                changes.append(f"{label}: '{old_display}' → '{new_display}'")
        
        # Journalisation si des changements sont détectés
        if changes:
            logger.info(f"Modification de l'événement #{self.pk} : {', '.join(changes)}")
    
    def _format_field_value(self, field_name, value):
        """
        Formate une valeur de champ pour l'affichage dans les logs.
        
        Args:
            field_name (str): Nom du champ
            value: Valeur à formater
            
        Returns:
            str: Valeur formatée
        """
        if value is None:
            return "Non défini"
            
        if field_name == 'event_date' and value:
            return value.strftime('%d/%m/%Y')
            
        if field_name == 'type_evenement':
            return dict(self.TypeEvenement.choices).get(value, value)
            
        if field_name == 'formation_id' and value:
            try:
                formation = Formation.objects.get(pk=value)
                return formation.nom
            except Formation.DoesNotExist:
                return f"Formation #{value}"
                
        return str(value)

    # ===== Status temporel =====
    def get_temporal_status(self, days=None):
        """
        🧭 Retourne le statut temporel de l'événement.
        
        Args:
            days (int, optional): Jours à considérer pour "bientôt"
                Si None, utilise la valeur par défaut DAYS_SOON
        
        Returns:
            str: Statut temporel (past, today, soon, future, unknown)
        """
        days = days or self.DAYS_SOON
        
        if not self.event_date:
            return self.StatutTemporel.INCONNU
            
        today = timezone.now().date()
        
        if self.event_date < today:
            return self.StatutTemporel.PASSE
            
        if self.event_date == today:
            return self.StatutTemporel.AUJOURD_HUI
            
        if self.event_date <= today + timezone.timedelta(days=days):
            return self.StatutTemporel.BIENTOT
            
        return self.StatutTemporel.FUTUR

    @property
    def status_label(self):
        """
        Libellé du statut temporel, adapté pour l'affichage.
        
        Returns:
            str: Libellé du statut (Passé, Aujourd'hui, À venir, etc.)
        """
        return {
            self.StatutTemporel.PASSE: _("Passé"),
            self.StatutTemporel.AUJOURD_HUI: _("Aujourd'hui"),
            self.StatutTemporel.BIENTOT: _("Bientôt"),
            self.StatutTemporel.FUTUR: _("À venir"),
            self.StatutTemporel.INCONNU: _("Date inconnue"),
        }.get(self.get_temporal_status(), _("Inconnu"))

    @property
    def status_color(self):
        """
        Classe CSS pour la couleur du statut.
        
        Returns:
            str: Classe CSS Bootstrap (text-*)
        """
        return {
            self.StatutTemporel.PASSE: "text-secondary",
            self.StatutTemporel.AUJOURD_HUI: "text-danger",
            self.StatutTemporel.BIENTOT: "text-warning",
            self.StatutTemporel.FUTUR: "text-primary",
            self.StatutTemporel.INCONNU: "text-muted",
        }.get(self.get_temporal_status(), "text-muted")
    
    @property
    def status_badge_class(self):
        """
        Classe CSS pour un badge de statut.
        
        Returns:
            str: Classe CSS Bootstrap (badge-*)
        """
        return {
            self.StatutTemporel.PASSE: "badge-secondary",
            self.StatutTemporel.AUJOURD_HUI: "badge-danger",
            self.StatutTemporel.BIENTOT: "badge-warning",
            self.StatutTemporel.FUTUR: "badge-primary",
            self.StatutTemporel.INCONNU: "badge-light",
        }.get(self.get_temporal_status(), "badge-light")
    
    @property
    def is_past(self):
        """
        Indique si l'événement est passé.
        
        Returns:
            bool: True si l'événement est passé
        """
        return self.get_temporal_status() == self.StatutTemporel.PASSE
    
    @property
    def is_today(self):
        """
        Indique si l'événement a lieu aujourd'hui.
        
        Returns:
            bool: True si l'événement est aujourd'hui
        """
        return self.get_temporal_status() == self.StatutTemporel.AUJOURD_HUI
    
    @property
    def is_future(self):
        """
        Indique si l'événement est à venir.
        
        Returns:
            bool: True si l'événement est à venir
        """
        status = self.get_temporal_status()
        return status in [self.StatutTemporel.BIENTOT, self.StatutTemporel.FUTUR]

    # ===== Statistiques =====
    def get_participation_rate(self):
        """
        📊 Calcule le taux de participation si possible.
        
        Returns:
            float: Taux de participation en pourcentage, ou None
        """
        if self.participants_prevus and self.participants_reels is not None and self.participants_prevus > 0:
            return round((self.participants_reels / self.participants_prevus) * 100, 1)
        return None
    
    @property
    def taux_participation(self):
        """Alias pour get_participation_rate."""
        return self.get_participation_rate()
    
    @property
    def taux_participation_formatted(self):
        """
        Taux de participation formaté pour l'affichage.
        
        Returns:
            str: Taux formaté avec % ou "N/A"
        """
        taux = self.get_participation_rate()
        return f"{taux}%" if taux is not None else "N/A"
    
    @cached_property
    def participation_status(self):
        """
        Évalue le niveau de participation.
        
        Returns:
            str: 'success', 'warning', 'danger' ou 'neutral'
        """
        taux = self.get_participation_rate()
        if taux is None:
            return 'neutral'
            
        if taux >= 90:
            return 'success'
        if taux >= 60:
            return 'warning'
        return 'danger'
    
    # ===== Méthodes de classe =====
    @classmethod
    def get_evenements_du_mois(cls, annee=None, mois=None):
        """
        Récupère les événements pour un mois donné.
        
        Args:
            annee (int, optional): Année, par défaut l'année en cours
            mois (int, optional): Mois (1-12), par défaut le mois en cours
            
        Returns:
            QuerySet: Événements du mois spécifié
        """
        today = timezone.now().date()
        annee = annee or today.year
        mois = mois or today.month
        
        return cls.objects.filter(
            event_date__year=annee,
            event_date__month=mois
        ).order_by('event_date')
    
    @classmethod
    def get_stats_by_type(cls, start_date=None, end_date=None):
        """
        Statistiques de participation par type d'événement.
        
        Args:
            start_date (date, optional): Date de début pour le filtre
            end_date (date, optional): Date de fin pour le filtre
            
        Returns:
            dict: Statistiques par type d'événement
        """
        queryset = cls.objects.all()
        
        # Appliquer les filtres de date si fournis
        if start_date:
            queryset = queryset.filter(event_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(event_date__lte=end_date)
        
        # Agrégation par type d'événement
        stats = queryset.values('type_evenement').annotate(
            count=Count('id'),
            total_prevus=Sum('participants_prevus'),
            total_reels=Sum('participants_reels'),
            taux_moyen=Avg(
                models.Case(
                    models.When(
                        participants_prevus__gt=0,
                        then=100 * F('participants_reels') / F('participants_prevus')
                    ),
                    default=None,
                    output_field=models.FloatField()
                )
            )
        ).order_by('-count')
        
        # Conversion en dictionnaire avec libellés
        result = {}
        type_choices = dict(cls.TypeEvenement.choices)
        
        for item in stats:
            type_key = item['type_evenement']
            result[type_key] = {
                'libelle': type_choices.get(type_key, type_key),
                'nombre': item['count'],
                'participants_prevus': item['total_prevus'] or 0,
                'participants_reels': item['total_reels'] or 0,
                'taux_participation': round(item['taux_moyen'], 1) if item['taux_moyen'] else None
            }
        
        return result