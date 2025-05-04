from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model
import logging

# Configuration du logger pour enregistrer les actions (création, modification)
logger = logging.getLogger(__name__)

# Regex pour valider un numéro de téléphone français
phone_regex = RegexValidator(
    regex=r'^(0[1-9]\d{8})$|^(?:\+33|0033)[1-9]\d{8}$',
    message="Entrez un numéro de téléphone français valide commençant par 01, 02, ..., 06 ou 07."
)

# Regex pour valider un code postal à 5 chiffres
zip_code_regex = RegexValidator(
    regex=r'^[0-9]{5}$',
    message="Le code postal doit être composé de 5 chiffres."
)

# Regex pour s'assurer que l'URL commence par http:// ou https://
url_regex = RegexValidator(
    regex=r'^(http|https)://',
    message="L'URL doit commencer par http:// ou https://"
)

# Liste des types d'action qu'une entreprise peut proposer
CHOICES_TYPE_OF_ACTION = [
    ('recrutement_emploi', 'Recrutement - Emploi'),
    ('recrutement_stage', 'Recrutement - Stage'),
    ('recrutement_apprentissage', 'Recrutement - Apprentissage'),
    ('presentation_metier_entreprise', 'Présentation de métier(s)/entreprise'),
    ('visite_entreprise', "Visite de l'entreprise"),
    ('coaching', 'Coaching'),
    ('autre', 'Autre'),
    ('partenariat', 'Partenariat'),
    ('non_definie', 'Non définie')
]

# Réseaux sociaux possibles pour une entreprise
CHOICES_SOCIAL_NETWORK = [
    ("facebook", "Facebook"),
    ("twitter", "Twitter"),
    ("instagram", "Instagram"),
    ("linkedin", "LinkedIn"),
    ("tiktok", "TikTok"),
]

# Récupère le modèle utilisateur personnalisé si défini
User = get_user_model()

class Company(models.Model):
    """
    Modèle représentant une entreprise avec ses coordonnées, contacts, site web, secteur, etc.
    """
    # Pour les requêtes : Company.objects.all() utilisera ce manager par défaut
    objects = models.Manager()

    # --- Informations générales ---
    name = models.CharField(
        max_length=100,
        null=True, blank=True,
        verbose_name="Nom",
        help_text="Nom de l'entreprise"
    )

    street_name = models.CharField(
        max_length=200,
        null=True, blank=True,
        verbose_name="Numéro et nom de la rue",
        help_text="Exemple: 123 rue de la République"
    )

    zip_code = models.CharField(
        max_length=5,
        validators=[zip_code_regex],  # Validation du format
        verbose_name="Code postal",
        blank=True, null=True,
        help_text="Code postal à 5 chiffres"
    )

    city = models.CharField(
        max_length=100,
        verbose_name="Ville",
        blank=True, null=True,
        help_text="Ville du siège social"
    )

    country = models.CharField(
        max_length=100,
        default="France",
        verbose_name="Pays",
        blank=True, null=True
    )

    # --- Contact principal ---
    contact_name = models.CharField(
        max_length=255,
        null=True, blank=True,
        verbose_name="Nom du contact",
        help_text="Nom et prénom du contact principal"
    )

    contact_email = models.EmailField(
        null=True, blank=True,
        verbose_name="Adresse email du contact",
        help_text="Email professionnel du contact"
    )

    contact_phone_number = models.CharField(
        max_length=20,
        validators=[phone_regex],  # Validation du numéro
        verbose_name="Numéro de téléphone du contact",
        blank=True, null=True,
        help_text="Format: 06XXXXXXXX ou +33XXXXXXXXX"
    )

    contact_job = models.CharField(
        max_length=255,
        null=True, blank=True,
        verbose_name="Métier du contact",
        help_text="Fonction ou poste du contact"
    )

    # --- Détails supplémentaires ---
    sector_name = models.CharField(
        max_length=200,
        null=True, blank=True,
        verbose_name="Secteur d'activité",
        help_text="Domaine d'activité principal de l'entreprise"
    )

    actions = models.CharField(
        max_length=50,
        null=True, blank=True,
        choices=CHOICES_TYPE_OF_ACTION,
        verbose_name="Actions",
        help_text="Type d'interaction possible avec cette entreprise"
    )

    action_description = models.CharField(
        max_length=5000,
        null=True, blank=True,
        verbose_name="Description de l'action",
        help_text="Détails sur l'action ou l'opportunité"
    )

    website = models.URLField(
        null=True, blank=True,
        validators=[url_regex],
        help_text="Site web de l'entreprise (avec http:// ou https://)"
    )

    social_network_url = models.CharField(
        max_length=200,
        verbose_name="URL du réseau social",
        null=True, blank=True,
        help_text="Lien vers le profil de l'entreprise sur un réseau social"
    )

    # --- Métadonnées ---
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Créé par",
        related_name="companies_created"
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name="Contact créé le"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        null=True, blank=True,
        verbose_name="Date de MAJ"
    )

    class Meta:
        verbose_name = 'entreprise'
        verbose_name_plural = 'entreprises'
        db_table = 'companies'  # Nom de la table dans la base de données
        ordering = ['-created_at']  # Tri par date de création descendante
        indexes = [  # Index pour optimiser les requêtes
            models.Index(fields=['name'], name='company_name_idx'),
            models.Index(fields=['city'], name='company_city_idx'),
            models.Index(fields=['sector_name'], name='company_sector_idx'),
            models.Index(fields=['zip_code'], name='company_zipcode_idx'),
        ]

    def __str__(self):
        # Représentation textuelle de l'entreprise dans l'admin
        return f"{self.name or 'Entreprise sans nom'} ({self.city or 'Ville non spécifiée'}) - {self.sector_name or 'Secteur inconnu'}"

    def get_absolute_url(self):
        # Pour les liens dans les templates : {{ object.get_absolute_url }}
        return reverse('company-detail', kwargs={'pk': self.pk})

    def get_full_address(self):
        """Retourne l'adresse complète formatée pour affichage."""
        parts = []
        if self.street_name:
            parts.append(self.street_name)
        if self.zip_code and self.city:
            parts.append(f"{self.zip_code} {self.city}")
        elif self.city:
            parts.append(self.city)
        if self.country and self.country != "France":
            parts.append(self.country)
        return ", ".join(parts) if parts else "Adresse non spécifiée"

    def get_contact_info(self):
        """Retourne les infos de contact formatées pour affichage."""
        parts = []
        if self.contact_name:
            parts.append(self.contact_name)
        if self.contact_job:
            parts.append(f"({self.contact_job})")
        if self.contact_email:
            parts.append(self.contact_email)
        if self.contact_phone_number:
            parts.append(self.contact_phone_number)
        return " - ".join(parts) if parts else "Aucun contact spécifié"

    def get_prospections_count(self):
        """Retourne le nombre de prospections associées à l'entreprise."""
        return self.prospections.count()

    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save() pour :
        - Nettoyer/normaliser les champs (email, nom)
        - Préfixer automatiquement les URLs si besoin
        - Logger les modifications dans les logs système
        """
        is_new = self.pk is None  # Vérifie si c'est une création

        # Nettoyage de base
        if self.name:
            self.name = self.name.strip()

        if self.contact_email:
            self.contact_email = self.contact_email.lower().strip()

        # Ajoute le préfixe https:// si l'utilisateur l'a oublié
        if self.website and not self.website.startswith(('http://', 'https://')):
            self.website = f"https://{self.website}"

        # Journalisation des modifications
        if is_new:
            logger.info(f"Création d'une nouvelle entreprise: {self.name or 'Sans nom'}")
        else:
            try:
                original = Company.objects.get(pk=self.pk)
                changes = []
                for field in ('name', 'city', 'contact_name', 'contact_email', 'sector_name'):
                    old_value = getattr(original, field)
                    new_value = getattr(self, field)
                    if old_value != new_value:
                        changes.append(f"{field}: '{old_value or 'Non spécifié'}' → '{new_value or 'Non spécifié'}'")
                if changes:
                    logger.info(f"Mise à jour de l'entreprise #{self.pk}: {', '.join(changes)}")
            except Company.DoesNotExist:
                logger.warning(f"Entreprise introuvable lors de la tentative de modification (ID: {self.pk})")

        super().save(*args, **kwargs)  # Appelle la méthode save() originale de Django
