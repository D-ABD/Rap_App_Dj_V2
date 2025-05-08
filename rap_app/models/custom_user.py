import logging
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.timezone import now

logger = logging.getLogger("application.customuser")


class CustomUser(AbstractUser):
    """
    👤 Modèle utilisateur personnalisé basé sur AbstractUser.

    Remplace le modèle utilisateur par défaut de Django.
    Utilise l'email comme identifiant unique.
    Ajoute des champs métier utiles :
    - Téléphone, avatar, biographie
    - Rôle d'accès avec permissions spécifiques
    """

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

    # Rôles personnalisés
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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

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
        🧪 Validation personnalisée :
        - Vérifie le format du numéro de téléphone
        - S'assure que seul un superuser peut avoir le rôle 'superadmin'
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
        💾 Sauvegarde personnalisée :
        - Normalise le numéro de téléphone
        - Journalise la création ou mise à jour
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
        """🔁 Représentation textuelle de l'utilisateur."""
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        """
        📛 Nom complet de l'utilisateur.

        Returns:
            str: Prénom + Nom ou username/email
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username or self.email

    def avatar_url(self):
        """
        🖼️ Retourne l'URL de l'avatar ou une image par défaut.
        """
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return '/static/images/default_avatar.png'

    def get_absolute_url(self):
        """
        🔗 URL absolue vers le détail de l'utilisateur (API ou interface).

        Returns:
            str: URL de détail
        """
        return reverse("user-detail", kwargs={"pk": self.pk})

    def to_serializable_dict(self):
        """
        📦 Alias de serializable_data pour compatibilité.

        Returns:
            dict: Données sérialisables
        """
        return self.serializable_data

    @property
    def serializable_data(self):
        """
        📦 Représentation sérialisable de l'utilisateur.

        Returns:
            dict: Données de l'utilisateur prêtes pour une API
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

    # 🔐 Helpers de rôle
    def is_admin(self):
        return self.role in [self.ROLE_ADMIN, self.ROLE_SUPERADMIN]

    def is_staff_or_admin(self):
        return self.role in [self.ROLE_STAFF, self.ROLE_ADMIN, self.ROLE_SUPERADMIN]

    def is_stagiaire(self):
        return self.role == self.ROLE_STAGIAIRE

    def is_superadmin(self):
        return self.role == self.ROLE_SUPERADMIN

    def is_staff_custom(self):
        return self.role == self.ROLE_STAFF

    def is_test(self):
        return self.role == self.ROLE_TEST
