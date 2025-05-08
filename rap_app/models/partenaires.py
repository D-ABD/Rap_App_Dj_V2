from django.db import models
from django.core.validators import RegexValidator
from django.utils.text import slugify
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
import logging
from .base import BaseModel
logger = logging.getLogger("application.partenaires")

# Validators
phone_regex = RegexValidator(
    regex=r'^(0[1-9]\d{8})$|^(?:\+33|0033)[1-9]\d{8}$',
    message="Entrez un numéro de téléphone français valide."
)

zip_code_regex = RegexValidator(
    regex=r'^[0-9]{5}$',
    message="Le code postal doit être composé de 5 chiffres."
)

url_regex = RegexValidator(
    regex=r'^(http|https)://',
    message="L'URL doit commencer par http:// ou https://"
)

CHOICES_TYPE_OF_ACTION = [
    ('recrutement_emploi', 'Recrutement - Emploi'),
    ('recrutement_stage', 'Recrutement - Stage'),
    ('recrutement_apprentissage', 'Recrutement - Apprentissage'),
    ('presentation_metier_entreprise', 'Présentation métier/entreprise'),
    ('visite_entreprise', "Visite d'entreprise"),
    ('coaching', 'Coaching'),
    ('autre', 'Autre'),
    ('partenariat', 'Partenariat'),
    ('non_definie', 'Non définie')
]

TYPE_CHOICES = [
    ("entreprise", "Entreprise"),
    ("partenaire", "Partenaire institutionnel"),
    ("personne", "Personne physique"),
]

class Partenaire(BaseModel):
    """
    Modèle représentant une entité externe liée à l'organisation :
    - une entreprise,
    - un partenaire institutionnel,
    - ou une personne physique.

    Ce modèle regroupe les informations générales, de contact, web et d'activité,
    en lien avec les prospections commerciales.
    """

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default="partenaire",
        verbose_name="Type de partenaire",
        help_text="Définit s'il s'agit d'une entreprise, d'un partenaire ou d'une personne physique"
    )

    nom = models.CharField(max_length=255, unique=True, verbose_name="Nom")
    secteur_activite = models.CharField(max_length=255, blank=True, null=True, verbose_name="Secteur d'activité")

    # Localisation
    street_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="Adresse")
    zip_code = models.CharField(max_length=5, blank=True, null=True, validators=[zip_code_regex], verbose_name="Code postal")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ville")
    country = models.CharField(max_length=100, blank=True, null=True, default="France", verbose_name="Pays")

    # Contact
    contact_nom = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nom du contact")
    contact_poste = models.CharField(max_length=255, blank=True, null=True, verbose_name="Poste du contact")
    contact_telephone = models.CharField(max_length=20, blank=True, null=True, validators=[phone_regex], verbose_name="Téléphone")
    contact_email = models.EmailField(blank=True, null=True, verbose_name="Email")

    # Web
    website = models.URLField(blank=True, null=True, validators=[url_regex], verbose_name="Site web")
    social_network_url = models.URLField(blank=True, null=True, verbose_name="Réseau social")

    # Détails
    actions = models.CharField(max_length=50, blank=True, null=True, choices=CHOICES_TYPE_OF_ACTION, verbose_name="Type d'action")
    action_description = models.TextField(blank=True, null=True, verbose_name="Description de l'action")
    description = models.TextField(blank=True, null=True, verbose_name="Description générale")

    # Slug & métadonnées
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Slug",
        help_text="Identifiant URL unique généré automatiquement à partir du nom"
    )
    class Meta:
        verbose_name = "Partenaire"
        verbose_name_plural = "Partenaires"
        ordering = ['nom']
        indexes = [
            models.Index(fields=['nom']),
            models.Index(fields=['secteur_activite']),
            models.Index(fields=['slug']),
            models.Index(fields=['zip_code']),
            models.Index(fields=['type']),
        ]

    def __str__(self) -> str:
        """
        Représentation textuelle de l'entité.

        Returns:
            str: Nom et type formatés (ex. "ACME Corp (Entreprise)")
        """
        return f"{self.nom} ({self.get_type_display()})"

    def save(self, *args, **kwargs):
        """
        Sauvegarde personnalisée :
        - Génère un slug unique automatiquement
        - Normalise l'email et l'URL du site web
        - Journalise la création ou la modification
        - Transmet `user` à BaseModel via `self._user`
        """
        user = kwargs.pop('user', None)
        is_new = self.pk is None

        # Génération du slug si nécessaire
        if not self.slug:
            base_slug = slugify(self.nom)
            slug = base_slug
            counter = 1
            while Partenaire.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # Normalisation email et URL
        if self.contact_email:
            self.contact_email = self.contact_email.lower().strip()

        if self.website and not self.website.startswith(('http://', 'https://')):
            self.website = f"https://{self.website}"

        # Transmission de l'utilisateur à BaseModel
        if user:
            self._user = user

        super().save(*args, **kwargs)

        logger.info(f"{'Création' if is_new else 'Modification'} du partenaire : {self.nom}")

    def get_absolute_url(self) -> str:
        """
        Retourne l'URL de détail du partenaire (pour l'admin ou les vues publiques).

        Returns:
            str: URL vers la vue de détail du partenaire
        """
        return reverse('partenaire-detail', kwargs={'pk': self.pk})

    def get_full_address(self) -> str:
        """
        Retourne l'adresse complète formatée (rue, code postal, ville, pays).

        Returns:
            str: Adresse lisible ou "Adresse non spécifiée"
        """
        parts = [self.street_name, f"{self.zip_code or ''} {self.city or ''}".strip(), self.country]
        return ", ".join(filter(None, parts)) or "Adresse non spécifiée"

    def get_contact_info(self) -> str:
        """
        Retourne une chaîne formatée contenant les infos de contact.

        Returns:
            str: Détails du contact ou "Aucun contact"
        """
        parts = [self.contact_nom, f"({self.contact_poste})" if self.contact_poste else None, self.contact_email, self.contact_telephone]
        return " - ".join(filter(None, parts)) or "Aucun contact"

    def has_contact_info(self) -> bool:
        """
        Vérifie si le partenaire possède au moins une info de contact.

        Returns:
            bool: True si nom, téléphone ou email est renseigné
        """
        return any([self.contact_nom, self.contact_telephone, self.contact_email])

    def get_prospections_info(self, with_list: bool = False) -> dict:
        """
        Retourne les informations sur les prospections liées à ce partenaire.

        Args:
            with_list (bool): Si True, inclut également la liste des objets Prospection.

        Returns:
            dict: Un dictionnaire contenant :
                - 'count': nombre total de prospections associées
                - 'prospections' (facultatif): liste des objets (si with_list est True)
        """
        queryset = self.prospections.all().order_by('-date_prospection')
        info = {
            "count": queryset.count()
        }
        if with_list:
            info["prospections"] = queryset
        return info
