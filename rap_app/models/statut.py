import logging
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import post_delete
from django.urls import reverse

from django.dispatch import receiver
from django.utils.html import format_html
from .base import BaseModel

# Logger configuré pour les statuts
logger = logging.getLogger("application.statut")


def get_default_color(statut_nom):
    """
    Retourne une couleur prédéfinie selon le type de statut.
    """
    COULEURS_PREDEFINIES = {
        'non_defini': "#FFEB3B",             # Jaune
        'recrutement_en_cours': "#4CAF50",   # Vert
        'formation_en_cours': "#2196F3",     # Bleu
        'formation_a_annuler': "#FF9800",    # Orange
        'formation_a_repousser': "#FFEB3B",  # Jaune
        'formation_annulee': "#F44336",      # Rouge
        'pleine': "#9C27B0",                 # Violet
        'quasi_pleine': "#3F51B5",           # Indigo
        'autre': "#795548",                  # Marron
    }
    return COULEURS_PREDEFINIES.get(statut_nom, "#607D8B")  # Bleu-gris par défaut


class Statut(BaseModel):
    """
    🔵 Modèle représentant les statuts possibles d’une formation.
    """

    # Choix de statuts
    NON_DEFINI = 'non_defini'
    RECRUTEMENT_EN_COURS = 'recrutement_en_cours'
    FORMATION_EN_COURS = 'formation_en_cours'
    FORMATION_A_ANNULER = 'formation_a_annuler'
    FORMATION_A_REPOUSSER = 'formation_a_repousser'
    FORMATION_ANNULEE = 'formation_annulee'
    PLEINE = 'pleine'
    QUASI_PLEINE = 'quasi_pleine'
    AUTRE = 'autre'

    STATUT_CHOICES = [
        (NON_DEFINI, 'Non défini'),
        (RECRUTEMENT_EN_COURS, 'Recrutement en cours'),
        (FORMATION_EN_COURS, 'Formation en cours'),
        (FORMATION_A_ANNULER, 'Formation à annuler'),
        (FORMATION_A_REPOUSSER, 'Formation à repousser'),
        (FORMATION_ANNULEE, 'Formation annulée'),
        (PLEINE, 'Pleine'),
        (QUASI_PLEINE, 'Quasi-pleine'),
        (AUTRE, 'Autre'),
    ]

    nom = models.CharField(
        max_length=100,
        choices=STATUT_CHOICES,
        verbose_name="Nom du statut"
    )

    couleur = models.CharField(
        max_length=7,
        blank=True,
        verbose_name="Couleur",
        help_text="Couleur hexadécimale (#RRGGBB)."
    )

    description_autre = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Description personnalisée"
    )

    def clean(self):
        """
        ✅ Validation personnalisée :
        - Vérifie `description_autre` si le statut est 'autre'
        - Vérifie le format couleur si fourni
        """
        if self.nom == self.AUTRE and not self.description_autre:
            raise ValidationError({
                'description_autre': "Le champ 'description personnalisée' est requis pour le statut 'Autre'."
            })

        if self.couleur and (not self.couleur.startswith('#') or len(self.couleur) != 7):
            raise ValidationError({
                'couleur': "La couleur doit être au format hexadécimal (#RRGGBB)."
            })

    def get_nom_display(self):
        """
        Affiche le libellé du statut. Si 'Autre', retourne la description personnalisée.
        """
        if self.nom == self.AUTRE and self.description_autre:
            return self.description_autre
        return dict(self.STATUT_CHOICES).get(self.nom, self.nom)

    def get_badge_html(self):
        """
        Génère un badge HTML avec la couleur associée.
        """
        return format_html(
            '<span class="badge" style="background-color:{}; color:white; padding: 3px 8px; border-radius: 5px;">{}</span>',
            self.couleur,
            self.get_nom_display()
        )

    def save(self, *args, **kwargs):
        """
        🔁 Sauvegarde du statut :
        - Applique une couleur par défaut si vide
        - Journalise création ou modification
        """
        is_new = self.pk is None

        if not self.couleur:
            self.couleur = get_default_color(self.nom)

        self.full_clean()
        super().save(*args, **kwargs)

        if is_new:
            logger.info(f"🟢 Nouveau statut créé : {self.get_nom_display()} ({self.couleur})")
        else:
            logger.info(f"📝 Statut modifié : {self.get_nom_display()} ({self.couleur})")

    def __str__(self):
        """
        Représentation textuelle du modèle.
        """
        return self.get_nom_display()
    
    def get_absolute_url(self):
        return reverse("statut-detail", kwargs={"pk": self.pk})

    class Meta:
        verbose_name = "Statut"
        verbose_name_plural = "Statuts"
        ordering = ['nom']


# 🔴 Signal pour journaliser la suppression d’un statut
@receiver(post_delete, sender=Statut)
def log_statut_deleted(sender, instance, **kwargs):
    logger.warning(f"❌ Statut supprimé : {instance.get_nom_display()} ({instance.couleur})")

