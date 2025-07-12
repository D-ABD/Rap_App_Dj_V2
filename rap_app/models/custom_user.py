import logging
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.utils.functional import cached_property
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.base_user import BaseUserManager

logger = logging.getLogger("rap_app.customuser")


class CustomUserManager(BaseUserManager):
    """
    Manager personnalisé pour le modèle CustomUser.
    Fournit des méthodes utilitaires pour les requêtes courantes.
    """
    
    def create_user(self, email, username=None, password=None, **extra_fields):
        """
        Crée et retourne un utilisateur avec un email et mot de passe.
        """
        if not email:
            raise ValueError()
        email = self.normalize_email(email)
        user = self.model(email=email, username=username or email.split('@')[0], **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username=None, password=None, **extra_fields):
        """
        Crée et retourne un superutilisateur avec tous les droits.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", CustomUser.ROLE_SUPERADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Le superutilisateur doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Le superutilisateur doit avoir is_superuser=True.")
        return self.create_user(email, username, password, **extra_fields)    
    def active(self):
        """
        Retourne uniquement les utilisateurs actifs.
        
        Returns:
            QuerySet: Utilisateurs actifs
        """
        return self.filter(is_active=True)
    
    def by_role(self, role):
        """
        Filtre les utilisateurs par rôle.
        
        Args:
            role (str): Un des rôles définis dans CustomUser.ROLE_CHOICES
            
        Returns:
            QuerySet: Utilisateurs ayant le rôle spécifié
        """
        return self.filter(role=role)
    
    def admins(self):
        """
        Retourne tous les utilisateurs administrateurs.
        
        Returns:
            QuerySet: Tous les administrateurs et super-administrateurs
        """
        return self.filter(role__in=[CustomUser.ROLE_ADMIN, CustomUser.ROLE_SUPERADMIN])
    
    def create_user_with_role(self, email, username, password, role=None, **extra_fields):
        """
        Crée un nouvel utilisateur avec un rôle spécifique.
        
        Args:
            email (str): Email de l'utilisateur (obligatoire)
            username (str): Nom d'utilisateur
            password (str): Mot de passe
            role (str, optional): Rôle à assigner
            **extra_fields: Champs supplémentaires
            
        Returns:
            CustomUser: Nouvel utilisateur créé
        """
        if not email:
            raise ValueError("L'adresse email est obligatoire")
            
        if role and not any(role == r[0] for r in CustomUser.ROLE_CHOICES):
            raise ValueError(f"Rôle invalide: {role}")
            
        extra_fields.setdefault('is_staff', role in [CustomUser.ROLE_ADMIN, CustomUser.ROLE_SUPERADMIN, CustomUser.ROLE_STAFF])
        extra_fields.setdefault('is_superuser', role == CustomUser.ROLE_SUPERADMIN)
        
        if role:
            extra_fields['role'] = role
            
        return self.create_user(email, username, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    👤 Modèle utilisateur personnalisé basé sur AbstractUser.

    Remplace le modèle utilisateur par défaut de Django.
    Utilise l'email comme identifiant unique.
    
    Attributs:
        email (str): Adresse email, utilisée comme identifiant de connexion
        phone (str): Numéro de téléphone (optionnel)
        avatar (ImageField): Image de profil (optionnel)
        bio (str): Biographie ou texte de présentation (optionnel)
        role (str): Rôle ou niveau d'accès de l'utilisateur
        
    Propriétés:
        full_name (str): Nom complet (prénom + nom)
        serializable_data (dict): Données sérialisables pour API
        
    Méthodes:
        is_admin(): Vérifie si l'utilisateur est administrateur
        is_staff_or_admin(): Vérifie si l'utilisateur est staff ou admin
        avatar_url(): Retourne l'URL de l'avatar
    """

    # Constantes pour les rôles
    ROLE_SUPERADMIN = 'superadmin'
    ROLE_ADMIN = 'admin'
    ROLE_STAGIAIRE = 'stagiaire'
    ROLE_STAFF = 'staff'
    ROLE_TEST = 'test'
    ROLE_CANDIDAT = 'candidat'
    ROLE_CANDIDAT_USER = 'candidatuser'

    ROLE_CHOICES = [
        (ROLE_SUPERADMIN, "Super administrateur"),
        (ROLE_ADMIN, "Administrateur"),
        (ROLE_STAGIAIRE, "Stagiaire"),
        (ROLE_STAFF, "Membre du staff"),
        (ROLE_TEST, "Test"),
        (ROLE_CANDIDAT, "candidat"),
        (ROLE_CANDIDAT_USER, "Candidat validé"), 
    ]
    
    # Constantes pour validation
    PHONE_MAX_LENGTH = 20
    USERNAME_VALIDATOR = UnicodeUsernameValidator()

    # Champs personnalisés
    email = models.EmailField(
        unique=True,
        verbose_name="Adresse email",
        help_text="Adresse email utilisée pour la connexion",
        error_messages={
            'unique': "Un utilisateur avec cette adresse email existe déjà."
        }
    )

    phone = models.CharField(
        max_length=PHONE_MAX_LENGTH,
        blank=True,
        verbose_name="Téléphone",
        help_text="Numéro de téléphone de l'utilisateur"
    )

    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name="Avatar",
        help_text="Image de profil de l'utilisateur"
    )

    bio = models.TextField(
        blank=True,
        verbose_name="Biographie",
        help_text="Texte de présentation ou informations supplémentaires"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STAGIAIRE,
        verbose_name="Rôle",
        help_text="Rôle ou niveau d'accès de l'utilisateur",
        db_index=True
    )
    
    # Paramètres d'authentification
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    # Managers
    objects = CustomUserManager()

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        indexes = [
            models.Index(fields=['role'], name='customuser_role_idx'),
            models.Index(fields=['email'], name='customuser_email_idx'),
            models.Index(fields=['is_active'], name='customuser_active_idx'),
        ]
        ordering = ['-date_joined']
        permissions = [
            ("can_view_all_users", "Peut voir tous les utilisateurs"),
            ("can_export_users", "Peut exporter les données utilisateurs"),
        ]



    def clean(self):
        """
        🧪 Validation personnalisée :
        - Vérifie le format du numéro de téléphone
        - S'assure que seul un superuser peut avoir le rôle 'superadmin'
        - Normalise l'email (lowercase) et le rôle (lowercase + strip)
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        super().clean()

        # Validation du téléphone
        if self.phone:
            phone_cleaned = self.phone.replace('+', '').replace(' ', '').replace('-', '')
            if not phone_cleaned.isdigit():
                raise ValidationError({
                    'phone': "Le numéro de téléphone ne doit contenir que des chiffres, des espaces, un '+' ou des tirets"
                })

        # Normalisation du rôle
        if self.role:
            self.role = self.role.lower().strip()

        # Validation du rôle superadmin
        if self.role == self.ROLE_SUPERADMIN and not self.is_superuser:
            raise ValidationError({
                'role': "Seul un superuser peut avoir le rôle 'Super administrateur'"
            })

        # Normalisation de l'email
        if self.email:
            self.email = self.email.lower().strip()

    def is_candidat(self):
        return self.role == self.ROLE_CANDIDAT
    

    def save(self, *args, **kwargs):
        """
        💾 Sauvegarde personnalisée :
        - Normalise l'email, le téléphone et le rôle
        - Met à jour les flags is_staff/is_superuser selon le rôle
        - Effectue la validation
        - Journalise la création ou mise à jour
        """
        is_new = self.pk is None

        # ✅ Normalisation de l'email
        if self.email:
            self.email = self.email.strip().lower()

        # ✅ Normalisation du rôle
        if self.role:
            self.role = self.role.strip().lower()

        # ✅ Normalisation du téléphone
        if self.phone:
            self.phone = ' '.join(self.phone.split())

        # 🔁 Synchronisation des flags selon le rôle
        if self.role == self.ROLE_SUPERADMIN:
            self.is_superuser = True
            self.is_staff = True
        elif self.role in [self.ROLE_ADMIN, self.ROLE_STAFF]:
            self.is_staff = True

        # ✅ Validation avant sauvegarde
        try:
            self.full_clean()
        except ValidationError as e:
            logger.error(f"Erreur de validation pour l'utilisateur {self.email}: {e}")
            raise

        # ✅ Sauvegarde réelle
        super().save(*args, **kwargs)

        # 📝 Journalisation
        if is_new:
            logger.info(f"✅ Utilisateur créé : {self.email} avec rôle {self.get_role_display()}")
        else:
            logger.info(f"🔄 Utilisateur mis à jour : {self.email}")

    def __str__(self):
        """🔁 Représentation textuelle de l'utilisateur."""
        return self.username
        
    def __repr__(self):
        """Représentation technique pour le débogage."""
        return f"<CustomUser(id={self.pk}, email='{self.email}', role='{self.role}')>"

    def get_full_name(self):
        """
        📛 Nom complet de l'utilisateur.

        Returns:
            str: Prénom + Nom ou username/email
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username or self.email
        
    @property
    def full_name(self):
        """
        Alias de get_full_name pour utilisation comme propriété.
        
        Returns:
            str: Nom complet de l'utilisateur
        """
        return self.get_full_name()

    def avatar_url(self):
        """
        🖼️ Retourne l'URL de l'avatar ou une image par défaut.
        
        Returns:
            str: URL de l'avatar ou image par défaut
        """
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return '/static/images/default_avatar.png'

        


    def to_serializable_dict(self, include_sensitive=False):
        """
        📦 Retourne une représentation sérialisable de l'utilisateur.
        
        Args:
            include_sensitive (bool): Si True, inclut des données plus sensibles
            
        Returns:
            dict: Données sérialisables
        """
        base_data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'avatar_url': self.avatar_url(),
            'role': self.role,
            'role_display': self.get_role_display(),
            'date_joined': self.date_joined.isoformat() if self.date_joined else None,
            'is_active': self.is_active,
        }
        
        # Ajouter les données optionnelles selon le niveau d'accès
        if include_sensitive:
            base_data.update({
                'phone': self.phone,
                'bio': self.bio,
                'is_staff': self.is_staff,
                'is_superuser': self.is_superuser,
                'last_login': self.last_login.isoformat() if self.last_login else None,
            })
            
        return base_data

    @property
    def serializable_data(self):
        """
        📦 Propriété pour la rétrocompatibilité.
        Équivalent à to_serializable_dict(include_sensitive=True).

        Returns:
            dict: Données de l'utilisateur prêtes pour une API
        """
        return self.to_serializable_dict(include_sensitive=True)
        
    @cached_property
    def permissions_list(self):
        """
        🔐 Liste des permissions de l'utilisateur.
        Mise en cache pour optimiser les performances.
        
        Returns:
            list: Liste des codenames de permission
        """
        if self.is_superuser:
            from django.contrib.auth.models import Permission
            return list(Permission.objects.values_list('codename', flat=True))
            
        return list(self.user_permissions.values_list('codename', flat=True))

    # 🔐 Helpers de rôle - avec validation stricte des types
    def is_admin(self):
        """
        Vérifie si l'utilisateur a un rôle d'administrateur.
        
        Returns:
            bool: True si admin ou superadmin
        """
        return self.role in [self.ROLE_ADMIN, self.ROLE_SUPERADMIN]

    def is_staff_or_admin(self):
        """
        Vérifie si l'utilisateur est staff ou administrateur.
        
        Returns:
            bool: True si staff, admin ou superadmin
        """
        return self.role in [self.ROLE_STAFF, self.ROLE_ADMIN, self.ROLE_SUPERADMIN]

    def is_stagiaire(self):
        """
        Vérifie si l'utilisateur est un stagiaire.
        
        Returns:
            bool: True si stagiaire
        """
        return self.role == self.ROLE_STAGIAIRE

    def is_superadmin(self):
        """
        Vérifie si l'utilisateur est super-administrateur.
        
        Returns:
            bool: True si superadmin
        """
        return self.role == self.ROLE_SUPERADMIN

    def is_staff_custom(self):
        """
        Vérifie si l'utilisateur est membre du staff.
        
        Returns:
            bool: True si staff
        """
        return self.role == self.ROLE_STAFF
    
    def is_candidat(self):
        return self.role == self.ROLE_CANDIDAT
    
    def is_candidatuser(self):
        return self.role == self.ROLE_CANDIDAT_USER

    def is_test(self):
        """
        Vérifie si c'est un compte de test.
        
        Returns:
            bool: True si compte test
        """
        return self.role == self.ROLE_TEST
        
    def has_module_access(self, module_name):
        """
        Vérifie si l'utilisateur a accès à un module spécifique.
        À implémenter selon vos besoins métier.
        
        Args:
            module_name (str): Nom du module à vérifier
            
        Returns:
            bool: True si l'utilisateur a accès
        """
        # Exemple - à adapter selon votre logique d'accès
        if self.is_superadmin():
            return True
            
        # Implémentez votre logique d'accès aux modules ici
        module_access = {
            'admin': [self.ROLE_ADMIN, self.ROLE_SUPERADMIN],
            'reporting': [self.ROLE_ADMIN, self.ROLE_SUPERADMIN, self.ROLE_STAFF],
            'formation': [self.ROLE_ADMIN, self.ROLE_SUPERADMIN, self.ROLE_STAFF, self.ROLE_STAGIAIRE],
        }
        
        return module_name in module_access and self.role in module_access[module_name]
        
    @classmethod
    def get_role_choices_display(cls):
        """
        Retourne un dictionnaire des rôles et leurs labels.
        Utile pour les formulaires ou l'API.
        
        Returns:
            dict: Dictionnaire {code_role: label}
        """
        return dict(cls.ROLE_CHOICES)
        
    @classmethod
    def get_csv_fields(cls):
        """
        Définit les champs à inclure dans un export CSV.
        
        Returns:
            list: Liste des noms de champs
        """
        return [
            'id', 'email', 'username', 'first_name', 'last_name', 
            'role', 'date_joined', 'is_active'
        ]
        
    @classmethod
    def get_csv_headers(cls):
        """
        Définit les en-têtes pour un export CSV.
        
        Returns:
            list: Liste des en-têtes de colonnes
        """
        return [
            'ID', 'Email', 'Nom d\'utilisateur', 'Prénom', 'Nom',
            'Rôle', 'Date d\'inscription', 'Actif'
        ]