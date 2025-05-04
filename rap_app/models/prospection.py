import logging
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from ..models.formations import Formation
from .company import Company

# Configuration du logger
logger = logging.getLogger(__name__)

# ✅ Statuts possibles pour une prospection
PROSPECTION_STATUS_CHOICES = [
    ('a_faire', 'À faire'),
    ('en_cours', 'En cours'),
    ('a_relancer', 'À relancer'),
    ('acceptee', 'Acceptée'),
    ('refusee', 'Refusée'),
    ('annulee', 'Annulée'),
    ('non_renseigne', 'Non renseigné'),
]

# ✅ Objectifs de prospection
PROSPECTION_OBJECTIF_CHOICES = [
    ('prise_contact', 'Prise de contact'),
    ('rendez_vous', 'Obtenir un rendez-vous'),
    ('presentation_offre', 'Présentation d’une offre'),
    ('contrat', 'Signer un contrat'),
    ('partenariat', 'Établir un partenariat'),
    ('autre', 'Autre'),
]

# ✅ Motifs pour lesquels on fait la prospection
PROSPECTION_MOTIF_CHOICES = [
    ('POEI', 'POEI'),
    ('apprentissage', 'Apprentissage'),
    ('VAE', 'VAE'),
    ('partenariat', 'Établir un partenariat'),
    ('autre', 'Autre'),
]

# ✅ Moyens de contact
MOYEN_CONTACT_CHOICES = [
    ('email', 'Email'),
    ('telephone', 'Téléphone'),
    ('visite', 'Visite'),
    ('reseaux', 'Réseaux sociaux'),
]


# ===============================
# 🔵 Modèle principal : Prospection
# ===============================
class Prospection(models.Model):
    """
    Modèle représentant une activité de prospection commerciale.
    Ce modèle permet de suivre les actions commerciales auprès des entreprises,
    avec un suivi détaillé du statut, des objectifs et des résultats.
    """

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="prospections",
        verbose_name="Entreprise",
        help_text="Entreprise ciblée par cette prospection"
    )
    formation = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="prospections",
        verbose_name="Formation en lien",
        help_text="Formation associée à cette prospection (facultatif)"
    )
    date_prospection = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de la prospection",
        help_text="Date à laquelle la prospection a été initiée"
    )
    motif = models.CharField(
        max_length=30,
        choices=PROSPECTION_MOTIF_CHOICES,
        default='prise_contact',
        verbose_name="Motif de la prospection",
        help_text="Raison principale de cette prospection"
    )
    statut = models.CharField(
        max_length=20,
        choices=PROSPECTION_STATUS_CHOICES,
        default='a_faire',
        verbose_name="Statut de la prospection",
        help_text="État actuel de la prospection"
    )
    objectif = models.CharField(
        max_length=30,
        choices=PROSPECTION_OBJECTIF_CHOICES,
        default='prise_contact',
        verbose_name="Objectif de la prospection",
        help_text="But visé par cette prospection"
    )
    commentaire = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaires de la prospection",
        help_text="Notes et observations sur la prospection"
    )
    responsable = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Responsable de la prospection",
        help_text="Personne en charge de cette prospection"
    )

    class Meta:
        verbose_name = "Suivi de la prospection"
        verbose_name_plural = "Suivis des prospections"
        ordering = ['-date_prospection']
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['date_prospection']),
            models.Index(fields=['company']),
            models.Index(fields=['formation']),
            models.Index(fields=['responsable']),
        ]

    def __str__(self):
        """
        Représentation textuelle de la prospection.
        """
        return f"{self.company.name} - {self.formation.nom if self.formation else 'Sans formation'} - {self.get_statut_display()} - {self.get_objectif_display()}"

    def clean(self): 
        """
        Validation personnalisée pour les prospections.
        """
        super().clean()

        # Vérifier que la date de prospection n'est pas dans le futur
        if self.date_prospection > timezone.now():
            logger.error(f"Erreur de validation : La date de prospection {self.date_prospection} est dans le futur.")
            raise ValidationError("La date de prospection ne peut pas être dans le futur.")

        # Vérifier la cohérence du statut et de l'objectif
        if self.statut == 'acceptee' and self.objectif != 'contrat':
            logger.warning(
                f"Prospection {self.id} : Statut 'Acceptée' mais objectif n'est pas 'Contrat'. "
                f"Objectif actuel : {self.get_objectif_display()}"
            )
            raise ValidationError("Une prospection acceptée doit avoir pour objectif la signature d'un contrat.")

    def save(self, *args, **kwargs):
        """
        Personnalisation de la sauvegarde pour historiser les changements.
        """
        is_new = self.pk is None
        old_prospection = None

        # ⚠️ Si la prospection existe déjà, on récupère l'ancienne version pour détecter les changements
        if not is_new:
            try:
                old_prospection = Prospection.objects.get(pk=self.pk)
            except Prospection.DoesNotExist:
                logger.error(f"Prospection {self.pk} introuvable lors de la mise à jour.")
                pass

        # 💾 On sauvegarde d'abord la prospection
        super().save(*args, **kwargs)

        # Journalisation de la création ou de la mise à jour
        if is_new:
            logger.info(
                f"Nouvelle prospection créée : ID {self.id}, Entreprise {self.company.name}, "
                f"Formation {self.formation.nom if self.formation else 'Aucune'}, "
                f"Statut {self.get_statut_display()}, Objectif {self.get_objectif_display()}"
            )
        else:
            logger.info(
                f"Prospection mise à jour : ID {self.id}, Entreprise {self.company.name}, "
                f"Statut {self.get_statut_display()}, Objectif {self.get_objectif_display()}"
            )

        # 🕓 Ensuite, on vérifie s'il y a des changements à historiser
        if old_prospection:
            changement_statut = old_prospection.statut != self.statut
            changement_objectif = old_prospection.objectif != self.objectif
            changement_commentaire = old_prospection.commentaire != self.commentaire

            if changement_statut or changement_objectif or changement_commentaire:
                # 📚 Création d'un enregistrement d'historique
                HistoriqueProspection.objects.create(
                    prospection=self,
                    ancien_statut=old_prospection.statut,
                    nouveau_statut=self.statut,
                    modifie_par=self.responsable,
                    commentaire=self.commentaire or "",
                    resultat=(
                        f"Objectif modifié : {old_prospection.get_objectif_display()} → {self.get_objectif_display()}"
                        if changement_objectif else ""
                    ),
                    prochain_contact=timezone.now().date() + timezone.timedelta(days=7),  # ⏳ J+7 pour relancer
                )
                logger.info(
                    f"Historique créé pour la prospection {self.id} : "
                    f"Statut {old_prospection.get_statut_display()} → {self.get_statut_display()}, "
                    f"Objectif {old_prospection.get_objectif_display()} → {self.get_objectif_display()}"
                )


# ===============================
# 🔵 Historique des changements
# ===============================
class HistoriqueProspection(models.Model):
    """
    Modèle pour enregistrer l'historique des changements d'une prospection.
    Ce modèle permet de suivre l'évolution d'une prospection dans le temps,
    en enregistrant les modifications de statut, les commentaires,
    et les dates de prochain contact.
    """

    prospection = models.ForeignKey(
        Prospection,
        on_delete=models.CASCADE,
        related_name="historiques",
        verbose_name="Prospection",
        help_text="Prospection concernée par cet historique"
    )
    date_modification = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de modification",
        help_text="Date à laquelle cette modification a été enregistrée"
    )
    ancien_statut = models.CharField(
        max_length=20,
        choices=PROSPECTION_STATUS_CHOICES,
        verbose_name="Ancien statut",
        help_text="Statut avant la modification"
    )
    nouveau_statut = models.CharField(
        max_length=20,
        choices=PROSPECTION_STATUS_CHOICES,
        verbose_name="Nouveau statut",
        help_text="Nouveau statut après la modification"
    )
    commentaire = models.TextField(
        null=True,
        blank=True,
        verbose_name="Commentaire",
        help_text="Commentaire associé à cette modification"
    )
    modifie_par = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Modifié par",
        help_text="Utilisateur ayant effectué cette modification"
    )
    prochain_contact = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de relance",
        help_text="Date à laquelle un suivi devrait être effectué"
    )
    resultat = models.TextField(
        null=True,
        blank=True,
        verbose_name="Résultat ou retour de la prospection",
        help_text="Information sur le résultat de cette étape de prospection"
    )
    moyen_contact = models.CharField(
        max_length=50,
        choices=MOYEN_CONTACT_CHOICES,
        null=True,
        blank=True,
        verbose_name="Moyen de contact",
        help_text="Moyen utilisé pour ce contact"
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
        """
        Représentation textuelle de l'historique.
        """
        date_str = self.date_modification.strftime("%d/%m/%Y %H:%M")
        return f"{date_str} - {self.prospection.company.name} - {self.get_nouveau_statut_display()}"

    def save(self, *args, **kwargs):
        """
        Personnalisation de la sauvegarde pour journaliser l'historique.
        """
        super().save(*args, **kwargs)
        logger.info(
            f"Historique enregistré pour la prospection {self.prospection.id} : "
            f"Statut {self.ancien_statut} → {self.nouveau_statut}, "
            f"Modifié par {self.modifie_par.username if self.modifie_par else 'N/A'}"
        )