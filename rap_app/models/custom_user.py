import logging
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone

logger = logging.getLogger("rap_app.customuser")


class CustomUserManager(BaseUserManager):
    """
    Manager personnalisé pour le modèle CustomUser.
    """
    @property
    def has_valid_consent(self):
        """Retourne True si le consentement RGPD est donné et daté."""
        return bool(self.consent_rgpd and self.consent_date)

    def create_user(self, email, username=None, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username or email.split("@")[0], **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", CustomUser.ROLE_SUPERADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Le superutilisateur doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Le superutilisateur doit avoir is_superuser=True.")
        return self.create_user(email, username, password, **extra_fields)

    def active(self):
        return self.filter(is_active=True)

    def by_role(self, role):
        """
        Filtre par rôle. Accepte un str OU un itérable de rôles.
        """
        if isinstance(role, (list, tuple, set)):
            roles = [str(r).lower().strip() for r in role]
            return self.filter(role__in=roles)
        return self.filter(role=str(role).lower().strip())

    def admins(self):
        return self.filter(role__in=[CustomUser.ROLE_ADMIN, CustomUser.ROLE_SUPERADMIN])

    def create_user_with_role(self, email, username, password, role=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire")

        if role and not any(role == r[0] for r in CustomUser.ROLE_CHOICES):
            raise ValueError(f"Rôle invalide: {role}")

        extra_fields.setdefault(
            "is_staff",
            role in [CustomUser.ROLE_ADMIN, CustomUser.ROLE_SUPERADMIN, CustomUser.ROLE_STAFF],
        )
        extra_fields.setdefault("is_superuser", role == CustomUser.ROLE_SUPERADMIN)

        if role:
            extra_fields["role"] = role

        return self.create_user(email, username, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    👤 Modèle utilisateur personnalisé basé sur AbstractUser (email = identifiant).
    """
    # ----- Consetement RGPD -----
    consent_rgpd = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)

    # ----- rôles -----
    ROLE_SUPERADMIN = "superadmin"
    ROLE_ADMIN = "admin"
    ROLE_STAGIAIRE = "stagiaire"
    ROLE_STAFF = "staff"
    ROLE_STAFF_READ = "staff_read"   # ✅ nouveau rôle
    ROLE_TEST = "test"
    ROLE_CANDIDAT = "candidat"
    ROLE_CANDIDAT_USER = "candidatuser"

    ROLE_CHOICES = [
        (ROLE_SUPERADMIN, "Super administrateur"),
        (ROLE_ADMIN, "Administrateur"),
        (ROLE_STAGIAIRE, "Stagiaire"),
        (ROLE_STAFF, "Membre du staff"),
        (ROLE_STAFF_READ, "Staff lecture seule"),  # ✅ affichage lisible
        (ROLE_TEST, "Test"),
        (ROLE_CANDIDAT, "Candidat"),
        (ROLE_CANDIDAT_USER, "Candidat validé"),
    ]

    # ✅ source de vérité “candidat-like”
    CANDIDATE_ROLES = {ROLE_CANDIDAT, ROLE_STAGIAIRE, ROLE_CANDIDAT_USER}

    # ----- constantes validation -----
    PHONE_MAX_LENGTH = 20
    USERNAME_VALIDATOR = UnicodeUsernameValidator()

    # ----- champs personnalisés -----
    email = models.EmailField(
        unique=True,
        verbose_name="Adresse email",
        help_text="Adresse email utilisée pour la connexion",
        error_messages={"unique": "Un utilisateur avec cette adresse email existe déjà."},
    )

    phone = models.CharField(
        max_length=PHONE_MAX_LENGTH,
        blank=True,
        verbose_name="Téléphone",
        help_text="Numéro de téléphone de l'utilisateur",
    )

    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        verbose_name="Avatar",
        help_text="Image de profil de l'utilisateur",
    )

    bio = models.TextField(
        blank=True,
        verbose_name="Biographie",
        help_text="Texte de présentation ou informations supplémentaires",
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STAGIAIRE,
        verbose_name="Rôle",
        help_text="Rôle ou niveau d'accès de l'utilisateur",
        db_index=True,
    )

    # 🔐 Centres autorisés pour les membres du staff (M2M, multi-affectation)
    centres = models.ManyToManyField(
        "Centre",
        related_name="users",
        blank=True,
        verbose_name="Centres autorisés",
        help_text="Limite la visibilité des données pour ce membre du staff.",
    )

    # Auth
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    # Manager
    objects = CustomUserManager()

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        indexes = [
            models.Index(fields=["role"], name="customuser_role_idx"),
            models.Index(fields=["email"], name="customuser_email_idx"),
            models.Index(fields=["is_active"], name="customuser_active_idx"),
        ]
        ordering = ["-date_joined"]
        permissions = [
            ("can_view_all_users", "Peut voir tous les utilisateurs"),
            ("can_export_users", "Peut exporter les données utilisateurs"),
        ]

    # ----- validation -----
    def clean(self):
        super().clean()
        if self.phone:
            phone_cleaned = self.phone.replace("+", "").replace(" ", "").replace("-", "")
            if not phone_cleaned.isdigit():
                raise ValidationError(
                    {"phone": "Le numéro de téléphone ne doit contenir que des chiffres, des espaces, un '+' ou des tirets"}
                )

        if self.role:
            self.role = self.role.lower().strip()

        if self.role == self.ROLE_SUPERADMIN and not self.is_superuser:
            raise ValidationError({"role": "Seul un superuser peut avoir le rôle 'Super administrateur'"})

        if self.email:
            self.email = self.email.lower().strip()

    # ----- sauvegarde -----
    def save(self, *args, **kwargs):
        is_new = self.pk is None
         # ⏱️ Si l'utilisateur vient juste de cocher le consentement RGPD
        if self.consent_rgpd and not self.consent_date:
            self.consent_date = timezone.now()

        if self.email:
            self.email = self.email.strip().lower()
        if self.role:
            self.role = self.role.strip().lower()
        if self.phone:
            self.phone = " ".join(self.phone.split())

        if self.role == self.ROLE_SUPERADMIN:
            self.is_superuser = True
            self.is_staff = True
        elif self.role in [self.ROLE_ADMIN, self.ROLE_STAFF]:
            self.is_staff = True

        try:
            self.full_clean()
        except ValidationError as e:
            logger.error(f"Erreur de validation pour l'utilisateur {self.email}: {e}")
            raise

        super().save(*args, **kwargs)

        if is_new:
            logger.info(f"✅ Utilisateur créé : {self.email} avec rôle {self.get_role_display()}")
        else:
            logger.info(f"🔄 Utilisateur mis à jour : {self.email}")

    # ----- représentation -----
    def __str__(self):
        return self.username

    def __repr__(self):
        return f"<CustomUser(id={self.pk}, email='{self.email}', role='{self.role}')>"

    # ----- helpers d'affichage -----
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username or self.email

    @property
    def full_name(self):
        return self.get_full_name()

    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, "url"):
            return self.avatar.url
        return "/static/images/default_avatar.png"

    # ----- sérialisation -----
    def to_serializable_dict(self, include_sensitive=False):
        base_data = {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.get_full_name(),
            "avatar_url": self.avatar_url(),
            "role": self.role,
            "role_display": self.get_role_display(),
            "date_joined": self.date_joined.isoformat() if self.date_joined else None,
            "is_active": self.is_active,
        }
        if include_sensitive:
            base_data.update(
                {
                    "phone": self.phone,
                    "bio": self.bio,
                    "is_staff": self.is_staff,
                    "is_superuser": self.is_superuser,
                    "last_login": self.last_login.isoformat() if self.last_login else None,
                }
            )
        return base_data

    @property
    def serializable_data(self):
        return self.to_serializable_dict(include_sensitive=True)

    @cached_property
    def permissions_list(self):
        if self.is_superuser:
            from django.contrib.auth.models import Permission
            return list(Permission.objects.values_list("codename", flat=True))
        return list(self.user_permissions.values_list("codename", flat=True))

    # ----- helpers rôle -----
    def is_superadmin(self) -> bool:
        return self.role == self.ROLE_SUPERADMIN or self.is_superuser is True

    def is_admin(self) -> bool:
        return self.role == self.ROLE_ADMIN or self.is_superadmin()

    def is_staff_role(self) -> bool:
        return self.role == self.ROLE_STAFF

    def is_staff_or_admin(self) -> bool:
        return self.is_staff_role() or self.is_admin() or self.is_superadmin()
    
    def is_staff_read(self):
        return self.role == self.ROLE_STAFF_READ

    def is_stagiaire(self):
        return self.role == self.ROLE_STAGIAIRE

    def is_candidat(self):
        return self.role == self.ROLE_CANDIDAT

    def is_candidatuser(self):
        return self.role == self.ROLE_CANDIDAT_USER

    def is_candidat_or_stagiaire(self):
        return (self.role or "").lower() in self.CANDIDATE_ROLES

    def has_role(self, *roles):
        return self.role in roles

    def has_module_access(self, module_name):
        if self.is_superadmin():
            return True
        module_access = {
            "admin": [self.ROLE_ADMIN, self.ROLE_SUPERADMIN],
            "reporting": [self.ROLE_ADMIN, self.ROLE_SUPERADMIN, self.ROLE_STAFF],
            "formation": [self.ROLE_ADMIN, self.ROLE_SUPERADMIN, self.ROLE_STAFF, self.ROLE_STAGIAIRE],
        }
        return module_name in module_access and self.role in module_access[module_name]

    # ----- helpers centres (scope) -----
    def get_centre_ids(self):
        return list(self.centres.values_list("id", flat=True))
    
    @property
    def centre(self):
        """
        🔹 Retourne le centre principal associé à l'utilisateur.
        - Pour un candidat/stagiaire : centre de sa formation.
        - Pour un staff/admin : premier centre de user.centres.
        """
        try:
            if self.centres.exists():
                return self.centres.first()
            if hasattr(self, "candidat_associe") and self.candidat_associe.formation:
                return self.candidat_associe.formation.centre
        except Exception:
            return None
        return None


    def has_centre_access(self, centre_id: int) -> bool:
        if self.is_superuser or self.is_admin():
            return True
        if self.is_staff:
            return self.centres.filter(id=centre_id).exists()
        return False

    @classmethod
    def get_role_choices_display(cls):
        return dict(cls.ROLE_CHOICES)

    @classmethod
    def get_csv_fields(cls):
        return ["id", "email", "username", "first_name", "last_name", "role", "date_joined", "is_active"]

    @classmethod
    def get_csv_headers(cls):
        return [
            "ID", "Email", "Nom d'utilisateur", "Prénom", "Nom", "Rôle", "Date d'inscription", "Actif",
        ]
