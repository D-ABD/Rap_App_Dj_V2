# models/rapports.py
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from ..models.formations import Formation
from .base import BaseModel

class Rapport(BaseModel):
    """
    Modèle représentant un rapport généré par le système.
    Les rapports peuvent être générés automatiquement ou manuellement.
    """
    TYPE_OCCUPATION = 'occupation'
    TYPE_CENTRE = 'centre'
    TYPE_STATUT = 'statut'
    TYPE_EVENEMENT = 'evenement'
    TYPE_RECRUTEMENT = 'recrutement'
    TYPE_PARTENAIRE = 'partenaire'
    TYPE_REPARTITION = 'repartition'
    TYPE_PERIODIQUE = 'periodique'
    TYPE_ANNUEL = 'annuel'
    TYPE_UTILISATEUR = 'utilisateur'
    
    TYPE_CHOICES = [
        (TYPE_OCCUPATION, 'Rapport d\'occupation des formations'),
        (TYPE_CENTRE, 'Rapport de performance par centre'),
        (TYPE_STATUT, 'Rapport de suivi des statuts'),
        (TYPE_EVENEMENT, 'Rapport d\'efficacité des événements'),
        (TYPE_RECRUTEMENT, 'Rapport de suivi du recrutement'),
        (TYPE_PARTENAIRE, 'Rapport d\'activité des partenaires'),
        (TYPE_REPARTITION, 'Rapport de répartition des partenaires'),
        (TYPE_PERIODIQUE, 'Rapport périodique'),
        (TYPE_ANNUEL, 'Rapport annuel consolidé'),
        (TYPE_UTILISATEUR, 'Rapport d\'activité utilisateurs'),
    ]
    
    PERIODE_QUOTIDIEN = 'quotidien'
    PERIODE_HEBDOMADAIRE = 'hebdomadaire'
    PERIODE_MENSUEL = 'mensuel'
    PERIODE_TRIMESTRIEL = 'trimestriel'
    PERIODE_ANNUEL = 'annuel'
    PERIODE_PERSONNALISE = 'personnalise'
    
    PERIODE_CHOICES = [
        (PERIODE_QUOTIDIEN, 'Quotidien'),
        (PERIODE_HEBDOMADAIRE, 'Hebdomadaire'),
        (PERIODE_MENSUEL, 'Mensuel'),
        (PERIODE_TRIMESTRIEL, 'Trimestriel'),
        (PERIODE_ANNUEL, 'Annuel'),
        (PERIODE_PERSONNALISE, 'Période personnalisée'),
    ]
    
    FORMAT_PDF = 'pdf'
    FORMAT_EXCEL = 'excel'
    FORMAT_CSV = 'csv'
    FORMAT_HTML = 'html'
    
    FORMAT_CHOICES = [
        (FORMAT_PDF, 'PDF'),
        (FORMAT_EXCEL, 'Excel'),
        (FORMAT_CSV, 'CSV'),
        (FORMAT_HTML, 'HTML'),
    ]
    
    nom = models.CharField(max_length=255, verbose_name="Nom du rapport")
    type_rapport = models.CharField(max_length=50, choices=TYPE_CHOICES, verbose_name="Type de rapport")
    periode = models.CharField(max_length=50, choices=PERIODE_CHOICES, verbose_name="Périodicité")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default=FORMAT_HTML, verbose_name="Format")
    
    # Filtres optionnels
    centre = models.ForeignKey('Centre', null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Centre")
    type_offre = models.ForeignKey('TypeOffre', null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Type d'offre")
    statut = models.ForeignKey('Statut', null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Statut")
    formation = models.ForeignKey('Formation', null=True, blank=True, on_delete=models.CASCADE, related_name="rapports")
    # Données du rapport
    donnees = models.JSONField(default=dict, verbose_name="Données du rapport")
    
    # Métadonnées
    temps_generation = models.FloatField(null=True, blank=True, verbose_name="Temps de génération (s)")
    
    class Meta:
        verbose_name = "Rapport"
        verbose_name_plural = "Rapports"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['date_debut', 'date_fin']),
            models.Index(fields=['type_rapport']),
            models.Index(fields=['format']),
            models.Index(fields=['centre']),
            models.Index(fields=['formation']),
        ]

        
    def __str__(self):
        return f"{self.nom} - {self.get_type_rapport_display()} ({self.date_debut} à {self.date_fin})"
    
    def clean(self):
        """
        🔎 Validation des dates de début et de fin du rapport :
        - La date de début ne peut pas être après la date de fin.
        - La période couverte doit respecter les contraintes de la périodicité.
        """
        super().clean()
        errors = {}

        if self.date_debut and self.date_fin:
            if self.date_debut > self.date_fin:
                errors['date_debut'] = "La date de début ne peut pas être postérieure à la date de fin."
                errors['date_fin'] = "La date de fin ne peut pas précéder la date de début."

            delta = (self.date_fin - self.date_debut).days

            # Contraintes selon la périodicité
            max_days = {
                self.PERIODE_QUOTIDIEN: 1,
                self.PERIODE_HEBDOMADAIRE: 7,
                self.PERIODE_MENSUEL: 31,
                self.PERIODE_TRIMESTRIEL: 93,
                self.PERIODE_ANNUEL: 366,
            }

            if self.periode != self.PERIODE_PERSONNALISE:
                max_allowed = max_days.get(self.periode, None)
                if max_allowed is not None and delta > max_allowed:
                    errors['date_fin'] = f"La période sélectionnée ne doit pas dépasser {max_allowed} jour(s)."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        💾 Sauvegarde du rapport avec journalisation de l'action via logger.
        Transmet également l'utilisateur au modèle de base si fourni.
        """
        user = kwargs.pop("user", None)
        is_new = self.pk is None

        if user:
            self._user = user  # transmis à BaseModel

        super().save(*args, **kwargs)

        import logging
        logger = logging.getLogger("application.rapports")

        action = "créé" if is_new else "modifié"
        user_info = f" par {user.get_full_name() or user.username}" if user else ""
        logger.info(f"[Rapport] Rapport {action} : {self.nom} ({self.get_type_rapport_display()}){user_info}")
