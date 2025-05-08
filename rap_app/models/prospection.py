import logging
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.urls import reverse

from .base import BaseModel
from .formations import Formation
from .partenaires import Partenaire

logger = logging.getLogger(__name__)

# Choix standards
PROSPECTION_STATUS_CHOICES = [
    ('a_faire', 'À faire'),
    ('en_cours', 'En cours'),
    ('a_relancer', 'À relancer'),
    ('acceptee', 'Acceptée'),
    ('refusee', 'Refusée'),
    ('annulee', 'Annulée'),
    ('non_renseigne', 'Non renseigné'),
]

PROSPECTION_OBJECTIF_CHOICES = [
    ('prise_contact', 'Prise de contact'),
    ('rendez_vous', 'Obtenir un rendez-vous'),
    ('presentation_offre', 'Présentation d’une offre'),
    ('contrat', 'Signer un contrat'),
    ('partenariat', 'Établir un partenariat'),
    ('autre', 'Autre'),
]

PROSPECTION_MOTIF_CHOICES = [
    ('POEI', 'POEI'),
    ('apprentissage', 'Apprentissage'),
    ('VAE', 'VAE'),
    ('partenariat', 'Établir un partenariat'),
    ('autre', 'Autre'),
]

MOYEN_CONTACT_CHOICES = [
    ('email', 'Email'),
    ('telephone', 'Téléphone'),
    ('visite', 'Visite'),
    ('reseaux', 'Réseaux sociaux'),
]

TYPE_CONTACT_CHOICES = [
    ('premier_contact', 'Premier contact'),
    ('relance', 'Relance'),
]

class Prospection(BaseModel):
    """
    🔍 Représente une prospection commerciale vers un partenaire.
    Permet de suivre l’objectif, le motif, le type de contact, le statut et les commentaires associés.
    """

    partenaire = models.ForeignKey(
        Partenaire, on_delete=models.CASCADE, related_name="prospections",
        verbose_name="Partenaire", help_text="Partenaire concerné"
    )
    formation = models.ForeignKey(
        Formation, on_delete=models.CASCADE, null=True, blank=True,
        related_name="prospections", verbose_name="Formation", help_text="Formation liée"
    )
    date_prospection = models.DateTimeField(default=timezone.now)
    type_contact = models.CharField(
        max_length=20,
        choices=TYPE_CONTACT_CHOICES,
        default='premier_contact',
        verbose_name="Type de contact",
        help_text="Indique s’il s’agit d’un premier contact ou d’une relance"
    )
    motif = models.CharField(max_length=30, choices=PROSPECTION_MOTIF_CHOICES)
    statut = models.CharField(max_length=20, choices=PROSPECTION_STATUS_CHOICES, default='a_faire')
    objectif = models.CharField(max_length=30, choices=PROSPECTION_OBJECTIF_CHOICES, default='prise_contact')
    commentaire = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Suivi de prospection"
        verbose_name_plural = "Suivis de prospections"
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
        return f"{self.partenaire.nom} - {formation} - {self.get_statut_display()} ({auteur})"

    def clean(self):
        if self.date_prospection > timezone.now():
            raise ValidationError("La date de prospection ne peut pas être dans le futur.")
        if self.statut == 'acceptee' and self.objectif != 'contrat':
            raise ValidationError("Une prospection acceptée doit viser la signature d'un contrat.")

    def save(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        is_new = self.pk is None
        original = None if is_new else Prospection.objects.filter(pk=self.pk).first()

        if user:
            self._user = user

        with transaction.atomic():
            super().save(*args, **kwargs)
            logger.info(f"{'Création' if is_new else 'Mise à jour'} prospection #{self.pk}")

            if is_new:
                HistoriqueProspection.objects.create(
                    prospection=self,
                    ancien_statut='non_renseigne',
                    nouveau_statut=self.statut,
                    type_contact=self.type_contact,
                    commentaire=self.commentaire or "",
                    resultat=f"Objectif initial : {self.get_objectif_display()}",
                    prochain_contact=timezone.now().date() + timezone.timedelta(days=7),
                    moyen_contact=None
                )
            elif original and (
                original.statut != self.statut or
                original.objectif != self.objectif or
                original.commentaire != self.commentaire
            ):
                HistoriqueProspection.objects.create(
                    prospection=self,
                    ancien_statut=original.statut,
                    nouveau_statut=self.statut,
                    modifie_par=user or self.updated_by or self.created_by,
                    commentaire=self.commentaire or "",
                    resultat=(
                        f"Objectif modifié : {original.get_objectif_display()} → {self.get_objectif_display()}"
                        if original.objectif != self.objectif else ""
                    ),
                    prochain_contact=timezone.now().date() + timezone.timedelta(days=7),
                    type_contact=self.type_contact,
                    moyen_contact=None
                )

    def get_absolute_url(self):
        return reverse("prospection-detail", kwargs={"pk": self.pk})

    def to_serializable_dict(self):
        return {
            "id": self.pk,
            "partenaire": str(self.partenaire),
            "formation": self.formation.nom if self.formation else None,
            "date": self.date_prospection.strftime('%Y-%m-%d %H:%M'),
            "type_contact": self.get_type_contact_display(),
            "statut": self.get_statut_display(),
            "objectif": self.get_objectif_display(),
            "motif": self.get_motif_display(),
            "commentaire": self.commentaire,
        }

class HistoriqueProspection(BaseModel):
    """
    🕓 Historique des modifications d'une prospection.
    Enregistre les changements de statut, d’objectif, de commentaires, et de date de relance.
    """

    prospection = models.ForeignKey(
        Prospection, on_delete=models.CASCADE, related_name="historiques"
    )
    date_modification = models.DateTimeField(auto_now_add=True)
    ancien_statut = models.CharField(max_length=20, choices=PROSPECTION_STATUS_CHOICES)
    nouveau_statut = models.CharField(max_length=20, choices=PROSPECTION_STATUS_CHOICES)
    type_contact = models.CharField(
        max_length=20,
        choices=TYPE_CONTACT_CHOICES,
        default='premier_contact',
        verbose_name="Type de contact"
    )
    commentaire = models.TextField(blank=True, null=True)
    resultat = models.TextField(blank=True, null=True)
    prochain_contact = models.DateField(blank=True, null=True)
    moyen_contact = models.CharField(max_length=50, choices=MOYEN_CONTACT_CHOICES, blank=True, null=True)

    class Meta:
        verbose_name = "Historique de prospection"
        verbose_name_plural = "Historiques de prospections"
        ordering = ['-date_modification']
        indexes = [
            models.Index(fields=['prospection']),
            models.Index(fields=['date_modification']),
            models.Index(fields=['prochain_contact']),
        ]

    def __str__(self):
        return f"{self.date_modification.strftime('%d/%m/%Y')} - {self.get_nouveau_statut_display()}"

    def clean(self):
        if self.prochain_contact and self.prochain_contact < timezone.now().date():
            raise ValidationError("La date de relance doit être dans le futur.")

    def save(self, *args, **kwargs):
            """
            💾 Sauvegarde avec validation et transaction sécurisée.
            """
            with transaction.atomic():
                super().save(*args, **kwargs)
            logger.info(f"🕓 Historique enregistré pour prospection {self.prospection.pk}")
            
    def get_absolute_url(self):
        return reverse("historiqueprospection-detail", kwargs={"pk": self.pk})

    def to_serializable_dict(self):
        return {
            "id": self.pk,
            "prospection_id": self.prospection_id,
            "type_contact": self.get_type_contact_display(),
            "ancien_statut": self.get_ancien_statut_display(),
            "nouveau_statut": self.get_nouveau_statut_display(),
            "commentaire": self.commentaire,
            "resultat": self.resultat,
            "prochain_contact": self.prochain_contact.isoformat() if self.prochain_contact else None,
            "date_modification": self.date_modification.strftime('%Y-%m-%d %H:%M'),
        }
