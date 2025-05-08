import logging
import re
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
    
    Args:
        statut_nom (str): Le nom du statut (clé dans STATUT_CHOICES)
        
    Returns:
        str: Code couleur hexadécimal correspondant au statut
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


def calculer_couleur_texte(couleur_fond):
    """
    Calcule si le texte doit être noir ou blanc en fonction de la luminosité de la couleur de fond.
    
    Args:
        couleur_fond (str): Code hexadécimal de la couleur de fond (#RRGGBB)
        
    Returns:
        str: "#000000" (noir) ou "#FFFFFF" (blanc) selon la luminosité
    """
    # Extraire les composants RGB
    r = int(couleur_fond[1:3], 16)
    g = int(couleur_fond[3:5], 16)
    b = int(couleur_fond[5:7], 16)
    
    # Calculer la luminosité (formule standard)
    luminosite = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    
    # Si luminosité > 0.5, le fond est clair, donc texte noir
    return "#000000" if luminosite > 0.5 else "#FFFFFF"


class Statut(BaseModel):
    """
    🔵 Modèle représentant les statuts possibles d'une formation.
    
    Ce modèle stocke les différents états qu'une formation peut avoir,
    avec des couleurs associées pour l'affichage visuel.
    
    Attributes:
        nom (str): L'identifiant du statut (choix prédéfini)
        couleur (str): Code couleur hexadécimal (#RRGGBB)
        description_autre (str): Description personnalisée pour le statut 'autre'
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
        - Vérifie le format couleur si fourni (format et caractères valides)
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        if self.nom == self.AUTRE and not self.description_autre:
            raise ValidationError({
                'description_autre': "Le champ 'description personnalisée' est requis pour le statut 'Autre'."
            })

        if self.couleur:
            # Vérification améliorée avec regex pour le format hexadécimal
            if not re.match(r'^#[0-9A-Fa-f]{6}$', self.couleur):
                raise ValidationError({
                    'couleur': "La couleur doit être au format hexadécimal valide (#RRGGBB)."
                })

    def get_nom_display(self):
        """
        Affiche le libellé du statut. Si 'Autre', retourne la description personnalisée.
        
        Returns:
            str: Le libellé du statut à afficher
        """
        if self.nom == self.AUTRE and self.description_autre:
            return self.description_autre
        return dict(self.STATUT_CHOICES).get(self.nom, self.nom)

    def get_badge_html(self):
        """
        Génère un badge HTML avec la couleur associée et un texte contrasté.
        
        Le texte sera en noir ou blanc selon la luminosité de la couleur de fond
        pour garantir une meilleure accessibilité.
        
        Returns:
            SafeString: Code HTML formaté pour l'affichage du badge
        """
        couleur_texte = calculer_couleur_texte(self.couleur)
        return format_html(
            '<span class="badge" style="background-color:{}; color:{}; padding: 3px 8px; border-radius: 5px;">{}</span>',
            self.couleur,
            couleur_texte,
            self.get_nom_display()
        )

    def save(self, *args, **kwargs):
        """
        🔁 Sauvegarde du statut :
        - Applique une couleur par défaut si vide
        - Journalise création ou modification
        - Gère la traçabilité utilisateur via BaseModel (user dans kwargs)
        """
        is_new = self.pk is None
        user = kwargs.pop('user', None)
        if user:
            self._user = user  # transmis à BaseModel

        if not self.couleur:
            self.couleur = get_default_color(self.nom)

        # Possibilité de désactiver la validation complète avec skip_validation=True
        if not kwargs.pop('skip_validation', False):
            self.full_clean()

        super().save(*args, **kwargs)

        logger.info(
            f"{'🟢 Nouveau statut' if is_new else '📝 Statut modifié'} : "
            f"{self.get_nom_display()} ({self.couleur})"
        )

    def __str__(self):
        """
        Représentation textuelle du modèle.
        
        Returns:
            str: Le libellé du statut
        """
        return self.get_nom_display()
    
    def get_absolute_url(self):
        """
        Retourne l'URL pour accéder à la vue détaillée de ce statut.
        
        Returns:
            str: URL absolue vers la page de détail du statut
        """
        return reverse("statut-detail", kwargs={"pk": self.pk})
    
    @property
    def serializable_data(self):
        """
        Retourne un dictionnaire des données du statut pour sérialisation.
        
        Cette propriété facilite la création de serializers DRF.
        
        Returns:
            dict: Données du statut formatées pour sérialisation
        """
        return {
            'id': self.id,
            'nom': self.nom,
            'libelle': self.get_nom_display(),
            'couleur': self.couleur,
            'description_autre': self.description_autre,
        }

    class Meta:
        verbose_name = "Statut"
        verbose_name_plural = "Statuts"
        ordering = ['nom']
        indexes = [
            models.Index(fields=['nom']),
            models.Index(fields=['couleur']),
        ]



# 🔴 Signal pour journaliser la suppression d'un statut
@receiver(post_delete, sender=Statut)
def log_statut_deleted(sender, instance, **kwargs):
    """
    Signal déclenché lors de la suppression d'un statut.
    Journalise l'information de suppression.
    
    Args:
        sender: Le modèle qui a envoyé le signal
        instance: L'instance du modèle qui a été supprimée
        **kwargs: Arguments supplémentaires
    """
    logger.warning(f"❌ Statut supprimé : {instance.get_nom_display()} ({instance.couleur})")