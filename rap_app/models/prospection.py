import logging
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from ..models.formations import Formation
from .partenaires import Partenaire
from .base import BaseModel  # Assure-toi que BaseModel est bien importé ici

logger = logging.getLogger(__name__)

# Statuts possibles
PROSPECTION_STATUS_CHOICES = [
    ('a_faire', 'À faire'),
    ('en_cours', 'En cours'),
    ('a_relancer', 'À relancer'),
    ('acceptee', 'Acceptée'),
    ('refusee', 'Refusée'),
    ('annulee', 'Annulée'),
    ('non_renseigne', 'Non renseigné'),
]

# Objectifs
PROSPECTION_OBJECTIF_CHOICES = [
    ('prise_contact', 'Prise de contact'),
    ('rendez_vous', 'Obtenir un rendez-vous'),
    ('presentation_offre', 'Présentation d’une offre'),
    ('contrat', 'Signer un contrat'),
    ('partenariat', 'Établir un partenariat'),
    ('autre', 'Autre'),
]

# Motifs
PROSPECTION_MOTIF_CHOICES = [
    ('POEI', 'POEI'),
    ('apprentissage', 'Apprentissage'),
    ('VAE', 'VAE'),
    ('partenariat', 'Établir un partenariat'),
    ('autre', 'Autre'),
]

# Moyens de contact
MOYEN_CONTACT_CHOICES = [
    ('email', 'Email'),
    ('telephone', 'Téléphone'),
    ('visite', 'Visite'),
    ('reseaux', 'Réseaux sociaux'),
]

class Prospection(BaseModel):
    """
    Représente une action commerciale envers un partenaire (entreprise, institution ou personne).
    Permet de suivre le motif, le statut, l’objectif et les commentaires liés à une prospection.
    """

    partenaire = models.ForeignKey(
        Partenaire,
        on_delete=models.CASCADE,
        related_name="prospections",
        verbose_name="Partenaire",
        help_text="Partenaire concerné par cette prospection"
    )

    formation = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="prospections",
        verbose_name="Formation",
        help_text="Formation liée à cette prospection (facultatif)"
    )

    date_prospection = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de prospection",
        help_text="Date à laquelle la prospection a eu lieu"
    )

    motif = models.CharField(
        max_length=30,
        choices=PROSPECTION_MOTIF_CHOICES,
        default='prise_contact',
        verbose_name="Motif",
        help_text="Motif principal de la prospection"
    )

    statut = models.CharField(
        max_length=20,
        choices=PROSPECTION_STATUS_CHOICES,
        default='a_faire',
        verbose_name="Statut",
        help_text="Statut actuel de la prospection"
    )

    objectif = models.CharField(
        max_length=30,
        choices=PROSPECTION_OBJECTIF_CHOICES,
        default='prise_contact',
        verbose_name="Objectif",
        help_text="Objectif visé par la prospection"
    )

    commentaire = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire",
        help_text="Remarques ou suivi concernant la prospection"
    )

    class Meta:
        verbose_name = "Suivi de la prospection"
        verbose_name_plural = "Suivis des prospections"
        ordering = ['-date_prospection']
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['date_prospection']),
            models.Index(fields=['partenaire']),
            models.Index(fields=['formation']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        formation = self.formation.nom if self.formation else "Sans formation"
        auteur = self.created_by.username if self.created_by else "Anonyme"
        return f"{self.partenaire.nom} - {formation} - {self.get_statut_display()} - {self.get_objectif_display()} ({auteur})"

    def clean(self):
        super().clean()

        if self.date_prospection > timezone.now():
            raise ValidationError("La date de prospection ne peut pas être dans le futur.")

        if self.statut == 'acceptee' and self.objectif != 'contrat':
            raise ValidationError("Une prospection acceptée doit avoir pour objectif la signature d'un contrat.")

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old = Prospection.objects.filter(pk=self.pk).first() if not is_new else None

        super().save(*args, **kwargs)

        logger.info(
            f"{'Création' if is_new else 'Mise à jour'} prospection #{self.pk} pour {self.partenaire.nom} "
            f"({self.get_statut_display()} - {self.get_objectif_display()})"
        )

        if old:
            if (
                old.statut != self.statut or
                old.objectif != self.objectif or
                old.commentaire != self.commentaire
            ):
                HistoriqueProspection.objects.create(
                    prospection=self,
                    ancien_statut=old.statut,
                    nouveau_statut=self.statut,
                    modifie_par=self.updated_by or self.created_by,
                    commentaire=self.commentaire or "",
                    resultat=(
                        f"Objectif modifié : {old.get_objectif_display()} → {self.get_objectif_display()}"
                        if old.objectif != self.objectif else ""
                    ),
                    prochain_contact=timezone.now().date() + timezone.timedelta(days=7)
                )
                logger.info(
                    f"📌 Historique créé pour prospection #{self.pk} : "
                    f"{old.get_statut_display()} → {self.get_statut_display()}"
                )

class HistoriqueProspection(models.Model):
    """
    Historique des modifications d'une prospection : changement de statut, objectif, etc.
    Utile pour le suivi temporel et l'audit des actions commerciales.
    """

    prospection = models.ForeignKey(
        Prospection,
        on_delete=models.CASCADE,
        related_name="historiques",
        verbose_name="Prospection",
        help_text="Prospection liée à cet historique"
    )

    date_modification = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date",
        help_text="Date de la modification"
    )

    ancien_statut = models.CharField(
        max_length=20,
        choices=PROSPECTION_STATUS_CHOICES,
        verbose_name="Ancien statut"
    )

    nouveau_statut = models.CharField(
        max_length=20,
        choices=PROSPECTION_STATUS_CHOICES,
        verbose_name="Nouveau statut"
    )

    commentaire = models.TextField(
        null=True,
        blank=True,
        verbose_name="Commentaire",
        help_text="Commentaire éventuel de modification"
    )



    prochain_contact = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de relance"
    )

    resultat = models.TextField(
        null=True,
        blank=True,
        verbose_name="Résultat"
    )

    moyen_contact = models.CharField(
        max_length=50,
        choices=MOYEN_CONTACT_CHOICES,
        null=True,
        blank=True,
        verbose_name="Moyen de contact"
    )

    class Meta:
        ordering = ['-date_modification']
        verbose_name = "Historique de prospection"
        verbose_name_plural = "Historiques de prospection"
        indexes = [
            models.Index(fields=['prospection']),
            models.Index(fields=['date_modification']),
            models.Index(fields=['prochain_contact']),
        ]

    def __str__(self):
        return f"{self.date_modification.strftime('%d/%m/%Y %H:%M')} - {self.prospection.partenaire.nom} - {self.get_nouveau_statut_display()}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        logger.info(
            f"🕓 Historique ajouté pour prospection {self.prospection.id} - "
            f"{self.ancien_statut} → {self.nouveau_statut}"
        )
