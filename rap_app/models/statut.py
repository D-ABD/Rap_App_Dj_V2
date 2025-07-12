import logging
import re
from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse

from django.utils.html import format_html
from .base import BaseModel

# Logger configuré pour les statuts
logger = logging.getLogger("application.statut")

# ----------------------------------------------------
# Signaux déplacés dans un fichier signals/
# ----------------------------------------------------



def get_default_color(statut_nom):
    """
    Retourne une couleur prédéfinie selon le type de statut.
    
    Args:
        statut_nom (str): Le nom du statut (clé dans STATUT_CHOICES)
        
    Returns:
        str: Code couleur hexadécimal correspondant au statut
    """
    COULEURS_PREDEFINIES = {
        'non_defini': "#080807",             # Jaune
        'recrutement_en_cours': "#0A54F4",   # Vert
        'formation_en_cours': "#110452",     # Bleu
        'formation_a_annuler': "#FD570A",    # Orange
        'formation_a_repousser': "#D6C424",  # Jaune
        'formation_annulee': "#922119",      # Rouge
        'pleine': "#00980F",                 # Violet
        'quasi_pleine': "#04758C",           # Indigo
        'autre': "#7B8386",                  # Marron
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
        verbose_name="Nom du statut",
        help_text="Identifiant du statut parmi les choix prédéfinis"
    )

    couleur = models.CharField(
        max_length=7,
        blank=True,
        verbose_name="Couleur",
        help_text="Couleur hexadécimale (#RRGGBB) pour l'affichage visuel"
    )

    description_autre = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Description personnalisée",
        help_text="Description détaillée requise quand le statut est 'Autre'"
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
        📋 Affiche le libellé du statut. Si 'Autre', retourne la description personnalisée.
        
        Returns:
            str: Le libellé du statut à afficher
        """
        if self.nom == self.AUTRE and self.description_autre:
            return self.description_autre
        return dict(self.STATUT_CHOICES).get(self.nom, self.nom)

    def get_badge_html(self):
        """
        🏷️ Génère un badge HTML avec la couleur associée et un texte contrasté.
        
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
    
    def to_csv_row(self) -> list[str]:
        """
        📤 Convertit le statut en ligne pour export CSV.

        Returns:
            list: Valeurs ordonnées correspondant aux en-têtes CSV
        """
        return [
            self.pk,
            self.get_nom_display(),
            self.nom,
            self.couleur,
            self.description_autre or '',
            self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else '',
            self.created_by.username if self.created_by else 'Système',
        ]
    
    @classmethod
    def get_csv_fields(cls) -> list[str]:
        """
        Décrit les champs exportables dans un fichier CSV.

        Returns:
            list: Liste des noms de champs pour export
        """
        return ['id', 'libelle', 'nom', 'couleur', 'description_autre', 'created_at', 'updated_at', 'created_by']

    @classmethod
    def get_csv_headers(cls) -> list[str]:
        """
        Noms lisibles à afficher en première ligne du CSV.

        Returns:
            list: Entêtes de colonnes CSV
        """
        return ['ID', 'Libellé affiché', 'Nom interne', 'Couleur', 'Description personnalisée', 'Créé le', 'Modifié le', 'Créé par']

    def save(self, *args, **kwargs):
        """
        🔁 Sauvegarde du statut :
        - Applique une couleur par défaut si vide
        - Journalise création ou modification
        - Gère la traçabilité utilisateur via BaseModel (user dans kwargs)
        
        Args:
            *args: Arguments positionnels
            **kwargs: Arguments nommés (user, skip_validation)
        """
        is_new = self.pk is None
        user = kwargs.pop('user', None)
        skip_validation = kwargs.pop('skip_validation', False)

        if user:
            self._user = user  # transmis à BaseModel

        if not self.couleur:
            self.couleur = get_default_color(self.nom)

        # ✅ Appliquer la validation seulement si non ignorée
        if not skip_validation:
            self.full_clean()

        super().save(*args, user=user, skip_validation=skip_validation, **kwargs)

        logger.info(
            f"{'🟢 Nouveau statut' if is_new else '📝 Statut modifié'} : "
            f"{self.get_nom_display()} ({self.couleur})"
        )
        
    def invalidate_caches(self):
        """
        🔄 Invalide les caches associés à ce statut.
        """
        super().invalidate_caches()
        
        # Invalider les caches spécifiques aux statuts
        from django.core.cache import cache
        cache_keys = [
            f"statut_{self.pk}",
            f"statut_liste",
            f"statut_{self.nom}"
        ]
        
        for key in cache_keys:
            cache.delete(key)

    def __str__(self):
        """
        🔁 Représentation textuelle du modèle.
        
        Returns:
            str: Le libellé du statut
        """
        return self.get_nom_display()
    
    def __repr__(self):
        """
        📝 Représentation technique pour le débogage.
        
        Returns:
            str: Format technique détaillé
        """
        return f"<Statut(id={self.pk}, nom='{self.nom}', couleur='{self.couleur}')>"
    
    
    def to_serializable_dict(self, exclude=None):
        """
        📦 Retourne un dictionnaire sérialisable du statut.
        
        Args:
            exclude (list[str], optional): Liste de champs à exclure
            
        Returns:
            dict: Données sérialisables du statut
        """
        exclude = exclude or []
        data = super().to_serializable_dict(exclude)
        
        # Ajouter des données spécifiques au statut
        data.update({
            'libelle': self.get_nom_display(),
            'badge_html': self.get_badge_html(),
        })
        
        return data

    class Meta:
        verbose_name = "Statut"
        verbose_name_plural = "Statuts"
        ordering = ['nom']
        indexes = [
            models.Index(fields=['nom'], name='statut_nom_idx'),
            models.Index(fields=['couleur'], name='statut_couleur_idx'),
        ]

# Note: Le signal post_delete devrait être déplacé dans un fichier signals.py