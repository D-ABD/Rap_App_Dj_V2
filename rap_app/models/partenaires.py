from django.db import models
from django.core.validators import RegexValidator
from django.utils.text import slugify
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Count, Q

import logging
from .base import BaseModel

logger = logging.getLogger("application.partenaires")

# ─────────────────────────────────────────────────────────────────────
# Validators
# ─────────────────────────────────────────────────────────────────────
phone_regex = RegexValidator(
    regex=r'^(0[1-9]\d{8})$|^(?:\+33|0033)[1-9]\d{8}$',
    message=_("Entrez un numéro de téléphone français valide.")
)

zip_code_regex = RegexValidator(
    regex=r'^[0-9]{5}$',
    message=_("Le code postal doit être composé de 5 chiffres.")
)

url_regex = RegexValidator(
    regex=r'^(http|https)://',
    message=_("L'URL doit commencer par http:// ou https://")
)


# ─────────────────────────────────────────────────────────────────────
# Manager
# ─────────────────────────────────────────────────────────────────────
class PartenaireManager(models.Manager):
    """
    Manager personnalisé pour le modèle Partenaire.
    Fournit des méthodes utilitaires pour les requêtes courantes.
    """

    def entreprises(self):
        return self.filter(type=Partenaire.TYPE_ENTREPRISE)

    def institutionnels(self):
        return self.filter(type=Partenaire.TYPE_INSTITUTIONNEL)

    def personnes(self):
        return self.filter(type=Partenaire.TYPE_PERSONNE)

    def avec_contact(self):
        return self.filter(
            Q(contact_nom__isnull=False) |
            Q(contact_email__isnull=False) |
            Q(contact_telephone__isnull=False)
        ).exclude(
            Q(contact_nom__exact='') &
            Q(contact_email__exact='') &
            Q(contact_telephone__exact='')
        )

    def par_secteur(self, secteur):
        return self.filter(secteur_activite__icontains=secteur)

    def recherche(self, query):
        if not query:
            return self.all()
        return self.filter(
            Q(nom__icontains=query) |
            Q(secteur_activite__icontains=query) |
            Q(contact_nom__icontains=query) |
            Q(description__icontains=query) |
            Q(city__icontains=query)
        )

    def avec_statistiques(self):
        """
        Ajoute des statistiques aux partenaires.
        - nb_prospections : total de prospections liées
        - nb_formations : total de formations distinctes liées via appairages et/ou prospections
        """
        return self.annotate(
            nb_prospections=Count('prospections', distinct=True),
            nb_formations=(
                Count('appairages__formation', filter=Q(appairages__formation__isnull=False), distinct=True)
                + Count('prospections__formation', filter=Q(prospections__formation__isnull=False), distinct=True)
            ),
        )


# ─────────────────────────────────────────────────────────────────────
# Model
# ─────────────────────────────────────────────────────────────────────
class Partenaire(BaseModel):
    """
    Entité externe (entreprise/partenaire/personne) liée aux prospections,
    appairages, formations, etc.
    """

    # Types
    TYPE_ENTREPRISE = "entreprise"
    TYPE_INSTITUTIONNEL = "partenaire"
    TYPE_PERSONNE = "personne"

    # Lengths
    NOM_MAX_LENGTH = 255
    SECTEUR_MAX_LENGTH = 255
    STREET_MAX_LENGTH = 200
    ZIP_CODE_LENGTH = 5
    CITY_MAX_LENGTH = 100
    COUNTRY_MAX_LENGTH = 100
    CONTACT_NOM_MAX_LENGTH = 255
    CONTACT_POSTE_MAX_LENGTH = 255
    CONTACT_TEL_MAX_LENGTH = 20
    ACTION_MAX_LENGTH = 50
    SLUG_MAX_LENGTH = 255

    TYPE_CHOICES = [
        (TYPE_ENTREPRISE, _("Entreprise")),
        (TYPE_INSTITUTIONNEL, _("Partenaire institutionnel")),
        (TYPE_PERSONNE, _("Personne physique")),
    ]

    CHOICES_TYPE_OF_ACTION = [
        ('recrutement_emploi', _('Recrutement - Emploi')),
        ('recrutement_stage', _('Recrutement - Stage')),
        ('recrutement_apprentissage', _('Recrutement - Apprentissage')),
        ('presentation_metier_entreprise', _('Présentation métier/entreprise')),
        ('visite_entreprise', _("Visite d'entreprise")),
        ('coaching', _('Coaching')),
        ('partenariat', _('Partenariat')),
        ('autre', _('Autre')),
        ('non_definie', _('Non définie')),
    ]

    # === Champs principaux ===
    default_centre = models.ForeignKey(
        'rap_app.Centre',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='partenaires_default',
        verbose_name='Centre par défaut'
    )

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_INSTITUTIONNEL,
        verbose_name=_("Type de partenaire"),
        help_text=_("Définit s'il s'agit d'une entreprise, d'un partenaire ou d'une personne physique"),
        db_index=True
    )

    nom = models.CharField(
        max_length=NOM_MAX_LENGTH,
        unique=True,
        verbose_name=_("Nom"),
        help_text=_("Nom complet de l'entité")
    )

    secteur_activite = models.CharField(
        max_length=SECTEUR_MAX_LENGTH,
        blank=True,
        null=True,
        verbose_name=_("Secteur d'activité"),
        help_text=_("Domaine d'activité principal")
    )

    # Localisation
    street_name = models.CharField(
        max_length=STREET_MAX_LENGTH,
        blank=True,
        null=True,
        verbose_name=_("Adresse"),
        help_text=_("Adresse postale (rue, numéro)")
    )

    zip_code = models.CharField(
        max_length=ZIP_CODE_LENGTH,
        blank=True,
        null=True,
        validators=[zip_code_regex],
        verbose_name=_("Code postal"),
        help_text=_("Code postal à 5 chiffres")
    )

    city = models.CharField(
        max_length=CITY_MAX_LENGTH,
        blank=True,
        null=True,
        verbose_name=_("Ville"),
        help_text=_("Ville")
    )

    country = models.CharField(
        max_length=COUNTRY_MAX_LENGTH,
        blank=True,
        null=True,
        default="France",
        verbose_name=_("Pays"),
        help_text=_("Pays (France par défaut)")
    )

    # Contact
    contact_nom = models.CharField(
        max_length=CONTACT_NOM_MAX_LENGTH,
        blank=True,
        null=True,
        verbose_name=_("Nom du contact"),
        help_text=_("Nom et prénom du contact principal")
    )

    contact_poste = models.CharField(
        max_length=CONTACT_POSTE_MAX_LENGTH,
        blank=True,
        null=True,
        verbose_name=_("Poste du contact"),
        help_text=_("Fonction occupée par le contact")
    )

    contact_telephone = models.CharField(
        max_length=CONTACT_TEL_MAX_LENGTH,
        blank=True,
        null=True,
        validators=[phone_regex],
        verbose_name=_("Téléphone"),
        help_text=_("Numéro de téléphone au format français")
    )

    contact_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_("Email"),
        help_text=_("Adresse email du contact")
    )

    # Web
    website = models.URLField(
        blank=True,
        null=True,
        validators=[url_regex],
        verbose_name=_("Site web"),
        help_text=_("Site web officiel (http:// ou https://)")
    )

    social_network_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Réseau social"),
        help_text=_("URL d'un profil LinkedIn, Twitter, etc.")
    )

    # Détails
    actions = models.CharField(
        max_length=ACTION_MAX_LENGTH,
        blank=True,
        null=True,
        choices=CHOICES_TYPE_OF_ACTION,
        verbose_name=_("Type d'action"),
        help_text=_("Catégorie principale d'interaction avec ce partenaire")
    )

    action_description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description de l'action"),
        help_text=_("Détails sur les actions menées ou envisagées")
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description générale"),
        help_text=_("Informations générales sur le partenaire")
    )

    # Slug
    slug = models.SlugField(
        max_length=SLUG_MAX_LENGTH,
        unique=True,
        blank=True,
        null=True,
        verbose_name=_("Slug"),
        help_text=_("Identifiant URL unique généré automatiquement à partir du nom")
    )

    # Managers
    objects = models.Manager()
    custom = PartenaireManager()

    class Meta:
        verbose_name = _("Partenaire")
        verbose_name_plural = _("Partenaires")
        ordering = ['nom']
        indexes = [
            models.Index(fields=['nom'], name='partenaire_nom_idx'),
            models.Index(fields=['secteur_activite'], name='partenaire_secteur_idx'),
            models.Index(fields=['slug'], name='partenaire_slug_idx'),
            models.Index(fields=['zip_code'], name='partenaire_cp_idx'),
            models.Index(fields=['type'], name='partenaire_type_idx'),
            models.Index(fields=['actions'], name='partenaire_actions_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=~Q(nom=''),
                name='partenaire_nom_not_empty'
            )
        ]

    # ─────────────────────────────────────────────────────────────
    # Repr
    # ─────────────────────────────────────────────────────────────
    def __str__(self) -> str:
        return f"{self.nom} ({self.get_type_display()})"

    def __repr__(self) -> str:
        return f"<Partenaire(id={self.pk}, nom='{self.nom}', type='{self.type}')>"

    # ─────────────────────────────────────────────────────────────
    # Validation & save
    # ─────────────────────────────────────────────────────────────
    def clean(self):
        super().clean()

        if not self.nom or not self.nom.strip():
            raise ValidationError({"nom": _("Le nom du partenaire est obligatoire.")})

        if self.zip_code and not self.city:
            raise ValidationError({"city": _("La ville doit être renseignée si le code postal est fourni.")})

        if self.website and not (self.website.startswith('http://') or self.website.startswith('https://')):
            raise ValidationError({"website": _("L'URL doit commencer par http:// ou https://")})

        if self.social_network_url and not (self.social_network_url.startswith('http://') or self.social_network_url.startswith('https://')):
            raise ValidationError({"social_network_url": _("L'URL doit commencer par http:// ou https://")})

    def save(self, *args, **kwargs):
        """
        - Génère un slug unique automatiquement
        - Normalise l'email et l'URL du site
        - Journalise création/modification
        - Transmet `user` à BaseModel via `self._user`
        """
        user = kwargs.pop('user', None)
        is_new = self.pk is None

        if not self.slug:
            base_slug = slugify(self.nom)
            slug = base_slug
            counter = 1
            while Partenaire.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        if self.contact_email:
            self.contact_email = self.contact_email.lower().strip()

        if self.website and not self.website.startswith(('http://', 'https://')):
            self.website = f"https://{self.website}"

        if self.social_network_url and not self.social_network_url.startswith(('http://', 'https://')):
            self.social_network_url = f"https://{self.social_network_url}"

        if user:
            self._user = user

        self.full_clean()
        super().save(*args, **kwargs)

        logger.info(f"{'Création' if is_new else 'Modification'} du partenaire : {self.nom} (ID: {self.pk})")

    # ─────────────────────────────────────────────────────────────
    # Formations liées (via appairages et/ou prospections)
    # ─────────────────────────────────────────────────────────────
    def _formations_qs(self):
        """
        QuerySet de formations liées à ce partenaire via appairages et/ou prospections.
        """
        from .formations import Formation
        return Formation.objects.filter(
            Q(appairages__partenaire=self) | Q(prospections__partenaire=self)
        ).distinct()

    def get_formations_info(self, with_list: bool = False) -> dict:
        qs = self._formations_qs().order_by('-start_date')
        info = {"count": qs.count()}
        if with_list:
            info["formations"] = list(qs)
        return info

    @property
    def nb_formations(self) -> int:
        return self._formations_qs().count()

    # ─────────────────────────────────────────────────────────────
    # Divers helpers
    # ─────────────────────────────────────────────────────────────
    def get_delete_url(self) -> str:
        return reverse('partenaire-delete', kwargs={'pk': self.pk})

    def get_full_address(self) -> str:
        parts = [
            self.street_name,
            f"{self.zip_code or ''} {self.city or ''}".strip(),
            self.country
        ]
        return ", ".join(filter(None, parts)) or _("Adresse non spécifiée")

    @property
    def default_centre_nom(self) -> str:
        return getattr(self.default_centre, "nom", "") or ""

    @property
    def full_address(self) -> str:
        return self.get_full_address()

    def get_contact_info(self) -> str:
        parts = [
            self.contact_nom,
            f"({self.contact_poste})" if self.contact_poste else None,
            self.contact_email,
            self.contact_telephone,
        ]
        return " - ".join(filter(None, parts)) or _("Aucun contact")

    @property
    def contact_info(self) -> str:
        return self.get_contact_info()

    def has_contact_info(self) -> bool:
        return any([self.contact_nom, self.contact_telephone, self.contact_email])

    @property
    def has_contact(self) -> bool:
        return self.has_contact_info()

    @property
    def has_web_presence(self) -> bool:
        return bool(self.website or self.social_network_url)

    @property
    def has_address(self) -> bool:
        return any([self.street_name, self.zip_code, self.city])

    def get_prospections_info(self, with_list: bool = False) -> dict:
        queryset = self.prospections.all().order_by('-date_prospection')
        info = {"count": queryset.count()}
        if with_list:
            info["prospections"] = queryset
        return info

    @property
    def nb_appairages(self) -> int:
        return self.appairages.count()

    @property
    def nb_prospections(self) -> int:
        return self.prospections.count()
