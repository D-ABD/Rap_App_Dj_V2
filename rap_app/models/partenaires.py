from django.db import models
from django.core.validators import RegexValidator
from django.utils.text import slugify
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Count, Q

import logging
from .base import BaseModel

logger = logging.getLogger("application.partenaires")

# ----------------------------------------------------
# Signaux déplacés dans un fichier signals/
# ----------------------------------------------------


# Validators
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


class PartenaireManager(models.Manager):
    """
    Manager personnalisé pour le modèle Partenaire.
    Fournit des méthodes utilitaires pour les requêtes courantes.
    """
    
    def entreprises(self):
        """
        Retourne uniquement les partenaires de type 'entreprise'.
        
        Returns:
            QuerySet: Partenaires de type entreprise
        """
        return self.filter(type=Partenaire.TYPE_ENTREPRISE)
    
    def institutionnels(self):
        """
        Retourne uniquement les partenaires institutionnels.
        
        Returns:
            QuerySet: Partenaires institutionnels
        """
        return self.filter(type=Partenaire.TYPE_INSTITUTIONNEL)
    
    def personnes(self):
        """
        Retourne uniquement les personnes physiques.
        
        Returns:
            QuerySet: Partenaires de type personne
        """
        return self.filter(type=Partenaire.TYPE_PERSONNE)
    
    def avec_contact(self):
        """
        Retourne les partenaires ayant des informations de contact.
        
        Returns:
            QuerySet: Partenaires avec info de contact
        """
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
        """
        Filtre les partenaires par secteur d'activité.
        
        Args:
            secteur (str): Secteur d'activité à rechercher
            
        Returns:
            QuerySet: Partenaires du secteur spécifié
        """
        return self.filter(secteur_activite__icontains=secteur)
    
    def recherche(self, query):
        """
        Recherche des partenaires par texte libre.
        
        Args:
            query (str): Texte à rechercher
            
        Returns:
            QuerySet: Partenaires correspondant à la recherche
        """
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
        
        Returns:
            QuerySet: Partenaires avec annotations
        """
        return self.annotate(
            nb_prospections=Count('prospections'),
            nb_formations=Count('formations')
        )


class Partenaire(BaseModel):
    """
    Modèle représentant une entité externe liée à l'organisation.
    
    Ce modèle peut représenter :
    - une entreprise
    - un partenaire institutionnel
    - ou une personne physique
    
    Il regroupe les informations de contact, de localisation, web et d'activité,
    en lien avec les prospections commerciales.
    
    Attributs:
        type (str): Type d'entité (choix prédéfinis)
        nom (str): Nom de l'entité
        secteur_activite (str): Secteur d'activité
        street_name (str): Adresse postale
        zip_code (str): Code postal
        city (str): Ville
        country (str): Pays
        contact_nom (str): Nom du contact principal
        contact_poste (str): Poste du contact
        contact_telephone (str): Téléphone du contact
        contact_email (str): Email du contact
        website (str): Site web
        social_network_url (str): URL réseau social
        actions (str): Type d'action avec le partenaire
        action_description (str): Description de l'action
        description (str): Description générale
        slug (str): Identifiant URL unique
        
    Propriétés:
        full_address (str): Adresse complète formatée
        contact_info (str): Informations de contact formatées
        has_contact (bool): Indique si des infos de contact existent
        
    Méthodes:
        get_prospections_info: Statistiques sur les prospections
    """
    
    # Constantes pour les types de partenaires
    TYPE_ENTREPRISE = "entreprise"
    TYPE_INSTITUTIONNEL = "partenaire"
    TYPE_PERSONNE = "personne"
    
    # Constantes pour les limites de champs
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
    
    # Choix pour les types de partenaires
    TYPE_CHOICES = [
        (TYPE_ENTREPRISE, _("Entreprise")),
        (TYPE_INSTITUTIONNEL, _("Partenaire institutionnel")),
        (TYPE_PERSONNE, _("Personne physique")),
    ]
    
    # Choix pour les types d'actions
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

    # === Champs de base ===
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

    # === Localisation ===
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

    # === Contact ===
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

    # === Web ===
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

    # === Détails ===
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

    # === Slug & métadonnées ===
    slug = models.SlugField(
        max_length=SLUG_MAX_LENGTH,
        unique=True,
        blank=True,
        null=True,
        verbose_name=_("Slug"),
        help_text=_("Identifiant URL unique généré automatiquement à partir du nom")
    )
    
    # === Managers ===
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

    def __str__(self) -> str:
        """
        Représentation textuelle de l'entité.

        Returns:
            str: Nom et type formatés (ex. "ACME Corp (Entreprise)")
        """
        return f"{self.nom} ({self.get_type_display()})"
        
    def __repr__(self) -> str:
        """
        Représentation technique pour le débogage.
        
        Returns:
            str: Représentation du partenaire pour le débogage
        """
        return f"<Partenaire(id={self.pk}, nom='{self.nom}', type='{self.type}')>"

    def clean(self):
        """
        Validation personnalisée des données.
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        super().clean()
        
        # Validation du nom (obligatoire)
        if not self.nom or not self.nom.strip():
            raise ValidationError({"nom": _("Le nom du partenaire est obligatoire.")})
            
        # Validation de cohérence du code postal et de la ville
        if self.zip_code and not self.city:
            raise ValidationError({"city": _("La ville doit être renseignée si le code postal est fourni.")})
            
        # Validation du site web
        if self.website and not (self.website.startswith('http://') or self.website.startswith('https://')):
            raise ValidationError({"website": _("L'URL doit commencer par http:// ou https://")})
            
        # Validation du réseau social
        if self.social_network_url and not (self.social_network_url.startswith('http://') or self.social_network_url.startswith('https://')):
            raise ValidationError({"social_network_url": _("L'URL doit commencer par http:// ou https://")})

    def save(self, *args, **kwargs):
        """
        Sauvegarde personnalisée :
        - Génère un slug unique automatiquement
        - Normalise l'email et l'URL du site web
        - Journalise la création ou la modification
        - Transmet `user` à BaseModel via `self._user`
        
        Args:
            *args: Arguments positionnels
            **kwargs: Arguments nommés, notamment user
        """
        user = kwargs.pop('user', None)
        is_new = self.pk is None

        # Génération du slug si nécessaire
        if not self.slug:
            base_slug = slugify(self.nom)
            slug = base_slug
            counter = 1
            
            # Vérification de l'unicité du slug
            while Partenaire.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
                
            self.slug = slug

        # Normalisation email et URL
        if self.contact_email:
            self.contact_email = self.contact_email.lower().strip()

        if self.website and not self.website.startswith(('http://', 'https://')):
            self.website = f"https://{self.website}"
            
        if self.social_network_url and not self.social_network_url.startswith(('http://', 'https://')):
            self.social_network_url = f"https://{self.social_network_url}"

        # Transmission de l'utilisateur à BaseModel
        if user:
            self._user = user
            
        # Validation des données
        self.full_clean()

        # Sauvegarde
        super().save(*args, **kwargs)

        # Journalisation
        logger.info(f"{'Création' if is_new else 'Modification'} du partenaire : {self.nom} (ID: {self.pk})")

        
        
    def get_delete_url(self) -> str:
        """
        Retourne l'URL de suppression du partenaire.
        
        Returns:
            str: URL vers la vue de suppression
        """
        return reverse('partenaire-delete', kwargs={'pk': self.pk})

    def get_full_address(self) -> str:
        """
        Retourne l'adresse complète formatée (rue, code postal, ville, pays).

        Returns:
            str: Adresse lisible ou "Adresse non spécifiée"
        """
        parts = [
            self.street_name, 
            f"{self.zip_code or ''} {self.city or ''}".strip(), 
            self.country
        ]
        return ", ".join(filter(None, parts)) or _("Adresse non spécifiée")
        
    @property
    def full_address(self) -> str:
        """
        Propriété pour accéder facilement à l'adresse complète.
        
        Returns:
            str: Adresse complète formatée
        """
        return self.get_full_address()

    def get_contact_info(self) -> str:
        """
        Retourne une chaîne formatée contenant les infos de contact.

        Returns:
            str: Détails du contact ou "Aucun contact"
        """
        parts = [
            self.contact_nom, 
            f"({self.contact_poste})" if self.contact_poste else None, 
            self.contact_email, 
            self.contact_telephone
        ]
        return " - ".join(filter(None, parts)) or _("Aucun contact")
        
    @property
    def contact_info(self) -> str:
        """
        Propriété pour accéder facilement aux informations de contact.
        
        Returns:
            str: Informations de contact formatées
        """
        return self.get_contact_info()

    def has_contact_info(self) -> bool:
        """
        Vérifie si le partenaire possède au moins une info de contact.

        Returns:
            bool: True si nom, téléphone ou email est renseigné
        """
        return any([
            self.contact_nom, 
            self.contact_telephone, 
            self.contact_email
        ])
        
    @property
    def has_contact(self) -> bool:
        """
        Propriété pour vérifier facilement si des infos de contact existent.
        
        Returns:
            bool: True si au moins une info de contact existe
        """
        return self.has_contact_info()
        
    @property
    def has_web_presence(self) -> bool:
        """
        Vérifie si le partenaire a une présence web.
        
        Returns:
            bool: True si site web ou réseau social renseigné
        """
        return bool(self.website or self.social_network_url)
        
    @property
    def has_address(self) -> bool:
        """
        Vérifie si le partenaire a une adresse.
        
        Returns:
            bool: True si au moins un élément d'adresse existe
        """
        return any([
            self.street_name, 
            self.zip_code, 
            self.city
        ])

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
        
    def get_formations_info(self, with_list: bool = False) -> dict:
        """
        Retourne les informations sur les formations liées à ce partenaire.
        
        Args:
            with_list (bool): Si True, inclut la liste des formations
            
        Returns:
            dict: Informations sur les formations associées
        """
        queryset = self.formations.all().order_by('-start_date')
        info = {
            "count": queryset.count()
        }
        if with_list:
            info["formations"] = queryset
        return info
    
    @property
    def nb_appairages(self) -> int:
        return self.appairages.count()

    @property
    def nb_prospections(self) -> int:
        return self.prospections.count()

    @property
    def nb_formations(self) -> int:
        return self.formations.count()
        
    def to_serializable_dict(self, include_relations: bool = False) -> dict:
        """
        Convertit le partenaire en dictionnaire sérialisable pour API.
        
        Args:
            include_relations (bool): Si True, inclut les données liées
            
        Returns:
            dict: Données du partenaire au format JSON
        """
        data = {
            "id": self.pk,
            "nom": self.nom,
            "type": self.type,
            "type_display": self.get_type_display(),
            "secteur_activite": self.secteur_activite,
            "slug": self.slug,
            "contact": {
                "nom": self.contact_nom,
                "poste": self.contact_poste,
                "email": self.contact_email,
                "telephone": self.contact_telephone,
                "formatted": self.get_contact_info(),
                "has_contact": self.has_contact_info()
            },
            "localisation": {
                "adresse": self.street_name,
                "code_postal": self.zip_code,
                "ville": self.city,
                "pays": self.country,
                "adresse_complete": self.get_full_address(),
                "has_address": self.has_address
            },
            "web": {
                "site": self.website,
                "reseau_social": self.social_network_url,
                "has_web": self.has_web_presence
            },
            "actions": {
                "type": self.actions,
                "description": self.action_description,
                "type_display": self.get_actions_display() if self.actions else None
            },
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Ajouter les relations si demandé
        if include_relations:
            data["prospections"] = self.get_prospections_info(with_list=False)
            data["formations"] = self.get_formations_info(with_list=False)
            
        return data
        
    @classmethod
    def get_secteurs_list(cls):
        """
        Récupère la liste des secteurs d'activité distincts.
        
        Returns:
            list: Liste des secteurs d'activité uniques
        """
        return cls.objects.exclude(
            secteur_activite__isnull=True
        ).exclude(
            secteur_activite__exact=''
        ).values_list(
            'secteur_activite', flat=True
        ).distinct().order_by('secteur_activite')