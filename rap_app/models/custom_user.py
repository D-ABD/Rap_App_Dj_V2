import logging
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import now

logger = logging.getLogger("application.customuser")

 
class CustomUser(AbstractUser):
    """
    Utilisateur personnalisé combinant les champs de User et UserProfile.
    
    Remplace le modèle utilisateur standard de Django.
    Utilise l’email comme identifiant unique et intègre des champs supplémentaires :
    téléphone, avatar, biographie, rôle.
    """

    # Utiliser l'email comme identifiant principal
    email = models.EmailField(
        unique=True,
        verbose_name="Adresse email",
        help_text="Adresse email utilisée pour la connexion"
    )

    phone = models.CharField(
        max_length=20,
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

    # Définition des rôles personnalisés
    ROLE_SUPERADMIN = 'superadmin'
    ROLE_ADMIN = 'admin'
    ROLE_STAGIAIRE = 'stagiaire'
    ROLE_STAFF = 'staff'
    ROLE_TEST = 'test'

    ROLE_CHOICES = [
        (ROLE_SUPERADMIN, "Super administrateur"),
        (ROLE_ADMIN, "Administrateur"),
        (ROLE_STAGIAIRE, "Stagiaire"),
        (ROLE_STAFF, "Membre du staff"),
        (ROLE_TEST, "Test"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STAGIAIRE,
        verbose_name="Rôle",
        help_text="Rôle ou niveau d'accès de l'utilisateur"
    )

    # Configuration du modèle personnalisé
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Peut aussi contenir ['first_name', 'last_name'] si besoin

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['email']),
        ]
        ordering = ['-date_joined']

    def clean(self):
        """
        Validation personnalisée :
        - Format du numéro de téléphone
        - Restrictions sur le rôle superadmin
        """
        super().clean()

        if self.phone and not self.phone.replace('+', '').replace(' ', '').isdigit():
            raise ValidationError({
                'phone': "Le numéro de téléphone ne doit contenir que des chiffres, des espaces et éventuellement un '+'"
            })

        if self.role == self.ROLE_SUPERADMIN and not self.is_superuser:
            raise ValidationError({
                'role': "Seul un superuser peut avoir le rôle 'Super administrateur'"
            })

    def save(self, *args, **kwargs):
        """
        Sauvegarde personnalisée :
        - Normalisation du téléphone
        - Logging
        """
        is_new = self.pk is None

        if self.phone:
            self.phone = ' '.join(self.phone.split())

        self.full_clean()
        super().save(*args, **kwargs)

        if is_new:
            logger.info(f"Utilisateur créé : {self.email} avec rôle {self.get_role_display()}")
        else:
            logger.info(f"Utilisateur mis à jour : {self.email}")

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username or self.email

    def avatar_url(self):
        """
        Retourne l'URL de l'avatar ou une image par défaut.
        """
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return '/static/images/default_avatar.png'

    @property
    def serializable_data(self):
        """
        Retourne un dictionnaire prêt pour la sérialisation API.
        """
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'phone': self.phone,
            'avatar_url': self.avatar_url(),
            'bio': self.bio,
            'role': self.role,
            'role_display': self.get_role_display(),
            'date_joined': self.date_joined,
            'is_active': self.is_active,
            'is_staff': self.is_staff,
            'is_superuser': self.is_superuser,
        }

    # Helpers pour les rôles
    def is_admin(self): return self.role in [self.ROLE_ADMIN, self.ROLE_SUPERADMIN]
    def is_staff_or_admin(self): return self.role in [self.ROLE_STAFF, self.ROLE_ADMIN, self.ROLE_SUPERADMIN]
    def is_stagiaire(self): return self.role == self.ROLE_STAGIAIRE
    def is_superadmin(self): return self.role == self.ROLE_SUPERADMIN
    def is_staff_custom(self): return self.role == self.ROLE_STAFF
    def is_test(self): return self.role == self.ROLE_TEST
