import logging
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone

logger = logging.getLogger("rap_app.customuser")


# ============================================================
# 👥 CustomUserManager
# ============================================================
class CustomUserManager(BaseUserManager):
    """Manager personnalisé pour le modèle CustomUser."""

    @property
    def has_valid_consent(self):
        return bool(self.consent_rgpd and self.consent_date)

    def create_user(self, email, username=None, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
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
        """Filtre par rôle (chaîne ou iterable)."""
        if isinstance(role, (list, tuple, set)):
            roles = [str(r).lower().strip() for r in role]
            return self.filter(role__in=roles)
        return self.filter(role=str(role).lower().strip())

    def admins(self):
        return self.filter(role__in=[CustomUser.ROLE_ADMIN, CustomUser.ROLE_SUPERADMIN])

    def create_user_with_role(self, email, username, password, role=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire.")

        if role and not any(role == r[0] for r in CustomUser.ROLE_CHOICES):
            raise ValueError(f"Rôle invalide : {role}")

        extra_fields.setdefault(
            "is_staff",
            role in [
                CustomUser.ROLE_ADMIN,
                CustomUser.ROLE_SUPERADMIN,
                CustomUser.ROLE_STAFF,
                CustomUser.ROLE_STAFF_READ,
                CustomUser.ROLE_PREPA_STAFF,
                CustomUser.ROLE_DECLIC_STAFF,
            ],
        )
        extra_fields.setdefault("is_superuser", role == CustomUser.ROLE_SUPERADMIN)

        if role:
            extra_fields["role"] = role

        return self.create_user(email, username, password, **extra_fields)


# ============================================================
# 👤 CustomUser
# ============================================================
class CustomUser(AbstractUser):
    """Modèle utilisateur avec rôles et centres."""

    # ----- Consentement RGPD -----
    consent_rgpd = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)

    # ----- Rôles -----
    ROLE_SUPERADMIN = "superadmin"
    ROLE_ADMIN = "admin"
    ROLE_STAGIAIRE = "stagiaire"
    ROLE_STAFF = "staff"
    ROLE_STAFF_READ = "staff_read"
    ROLE_PREPA_STAFF = "prepa_staff"
    ROLE_DECLIC_STAFF = "declic_staff"
    ROLE_CANDIDAT = "candidat"
    ROLE_CANDIDAT_USER = "candidatuser"
    ROLE_TEST = "test"

    ROLE_CHOICES = [
        (ROLE_SUPERADMIN, "Super administrateur"),
        (ROLE_ADMIN, "Administrateur"),
        (ROLE_STAFF, "Membre du staff"),
        (ROLE_STAFF_READ, "Staff lecture seule"),
        (ROLE_PREPA_STAFF, "Staff PrépaComp"),
        (ROLE_DECLIC_STAFF, "Staff Déclic"),
        (ROLE_STAGIAIRE, "Stagiaire"),
        (ROLE_CANDIDAT, "Candidat"),
        (ROLE_CANDIDAT_USER, "Candidat validé"),
        (ROLE_TEST, "Test"),
    ]

    # 🔹 Regroupements de rôles
    STAFF_ROLES = {
        ROLE_SUPERADMIN,
        ROLE_ADMIN,
        ROLE_STAFF,
        ROLE_STAFF_READ,
        ROLE_PREPA_STAFF,
        ROLE_DECLIC_STAFF,
    }
    CANDIDATE_ROLES = {ROLE_STAGIAIRE, ROLE_CANDIDAT, ROLE_CANDIDAT_USER}

    # ----- Champs -----
    email = models.EmailField(
        unique=True,
        verbose_name="Adresse email",
        help_text="Adresse utilisée pour la connexion.",
        error_messages={"unique": "Un utilisateur avec cette adresse email existe déjà."},
    )

    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True, verbose_name="Avatar")
    bio = models.TextField(blank=True, verbose_name="Biographie")

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STAGIAIRE,
        db_index=True,
        verbose_name="Rôle",
    )

    centres = models.ManyToManyField(
        "Centre",
        related_name="users",
        blank=True,
        verbose_name="Centres autorisés",
        help_text="Limite la visibilité des données pour ce membre du staff.",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    objects = CustomUserManager()

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["role"], name="customuser_role_idx"),
            models.Index(fields=["email"], name="customuser_email_idx"),
            models.Index(fields=["is_active"], name="customuser_active_idx"),
        ]

    # ============================================================
    # 🧼 Nettoyage
    # ============================================================
    def clean(self):
        super().clean()
        if self.phone:
            phone_cleaned = self.phone.replace("+", "").replace(" ", "").replace("-", "")
            if not phone_cleaned.isdigit():
                raise ValidationError(
                    {"phone": "Le numéro de téléphone ne doit contenir que des chiffres, espaces ou '+'."}
                )

        if self.role:
            self.role = self.role.lower().strip()

        if self.role == self.ROLE_SUPERADMIN and not self.is_superuser:
            raise ValidationError({"role": "Seul un superuser peut avoir le rôle 'Super administrateur'."})

        if self.email:
            self.email = self.email.lower().strip()

    # ============================================================
    # 💾 Sauvegarde (mise à jour auto des flags)
    # ============================================================
    def save(self, *args, _skip_candidate_sync: bool = False, **kwargs):
        """
        Sauvegarde personnalisée pour CustomUser :
        - Met à jour automatiquement is_staff / is_superuser selon le rôle.
        - Enregistre la date de consentement RGPD.
        - Normalise les champs texte.
        - ✅ _skip_candidate_sync : empêche la synchro User↔Candidat dans les signaux.
        """
        is_new = self.pk is None

        # 🔹 Flag pour les signaux (lu par les receivers)
        self._skip_candidate_sync = _skip_candidate_sync

        # 🔹 Consentement RGPD
        if self.consent_rgpd and not self.consent_date:
            self.consent_date = timezone.now()

        # 🔹 Normalisation
        if self.email:
            self.email = self.email.strip().lower()
        if self.role:
            self.role = self.role.strip().lower()
        if self.phone:
            self.phone = " ".join(self.phone.split())

        # ========================================================
        # 🔐 Règles automatiques pour is_staff / is_superuser
        # ========================================================
        if self.role == self.ROLE_SUPERADMIN:
            # Accès total à tout l'admin Django
            self.is_superuser = True
            self.is_staff = True

        elif self.role == self.ROLE_ADMIN:
            # Admin : accès complet à l’interface admin, mais pas superuser
            self.is_superuser = False
            self.is_staff = True

        elif self.role in {
            self.ROLE_STAFF,
            self.ROLE_STAFF_READ,
            self.ROLE_PREPA_STAFF,
            self.ROLE_DECLIC_STAFF,
        }:
            # Staff / Déclic / Prépa → PAS d'accès à /admin/
            self.is_superuser = False
            self.is_staff = False

        elif self.role in self.CANDIDATE_ROLES or self.role == self.ROLE_TEST:
            # Candidats / stagiaires / test → pas d'accès staff
            self.is_superuser = False
            self.is_staff = False

        else:
            # Rôle inconnu → verrouillage total
            self.is_superuser = False
            self.is_staff = False

        # ========================================================
        # ✅ Validation et sauvegarde
        # ========================================================
        try:
            self.full_clean()
        except ValidationError as e:
            logger.error(f"Erreur de validation pour {self.email}: {e}")
            raise

        # ========================================================
        # ✅ Validation et sauvegarde
        # ========================================================
        try:
            self.full_clean()
        except ValidationError as e:
            logger.error(f"Erreur de validation pour {self.email}: {e}")
            raise

        # 🚫 Supprimer le flag avant l'appel à super().save()
        kwargs.pop("_skip_candidate_sync", None)

        # 🧩 Sauvegarde réelle
        super().save(*args, **kwargs)

        # 🧹 Nettoyage du flag temporaire (évite qu'il traîne en mémoire)
        if hasattr(self, "_skip_candidate_sync"):
            delattr(self, "_skip_candidate_sync")

        # 🧾 Logging clair
        action = "créé" if is_new else "mis à jour"
        logger.info(f"✅ Utilisateur {action} : {self.email} (rôle : {self.get_role_display()})")



    # ============================================================
    # 🔧 Helpers et affichage
    # ============================================================
    def __str__(self):
        return self.username or self.email

    def __repr__(self):
        return f"<CustomUser id={self.pk} role='{self.role}'>"

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username or self.email

    @property
    def full_name(self):
        return self.get_full_name()

    def avatar_url(self):
        return self.avatar.url if self.avatar and hasattr(self.avatar, "url") else "/static/images/default_avatar.png"

    # ============================================================
    # 🔍 Helpers rôles
    # ============================================================
    def is_superadmin(self): return self.role == self.ROLE_SUPERADMIN or self.is_superuser
    def is_admin(self): return self.role == self.ROLE_ADMIN or self.is_superadmin()
    def is_staff_role(self): return self.role == self.ROLE_STAFF
    def is_staff_read(self): return self.role == self.ROLE_STAFF_READ
    def is_declic_staff(self): return self.role == self.ROLE_DECLIC_STAFF
    def is_prepa_staff(self): return self.role == self.ROLE_PREPA_STAFF
    def is_candidat(self): return self.role == self.ROLE_CANDIDAT
    def is_candidatuser(self): return self.role == self.ROLE_CANDIDAT_USER
    def is_stagiaire(self): return self.role == self.ROLE_STAGIAIRE
    def is_candidat_or_stagiaire(self): return self.role in self.CANDIDATE_ROLES
    def has_role(self, *roles): return self.role in roles

    # ============================================================
    # 🔍 Centres (portée)
    # ============================================================
    def get_centre_ids(self):
        return list(self.centres.values_list("id", flat=True))
    
    @property
    def staff_centre_ids(self):
        """
        Retourne la liste des IDs de centres visibles par cet utilisateur
        selon son rôle (staff, staff_read, prepa_staff, declic_staff, admin...).
        """
        if self.role in {
            self.ROLE_SUPERADMIN,
            self.ROLE_ADMIN,
            self.ROLE_STAFF,
            self.ROLE_STAFF_READ,
            self.ROLE_PREPA_STAFF,
            self.ROLE_DECLIC_STAFF,
        }:
            return list(self.centres.values_list("id", flat=True))
        return []


    @property
    def centre(self):
        try:
            if self.centres.exists():
                return self.centres.first()
            if hasattr(self, "candidat_associe") and self.candidat_associe.formation:
                return self.candidat_associe.formation.centre
        except Exception:
            return None
        return None

    def has_centre_access(self, centre_id):
        if self.is_superuser or self.is_admin():
            return True
        if self.is_staff:
            return self.centres.filter(id=centre_id).exists()
        return False


    def has_module_perms(self, app_label):
        """
        Django utilise cette méthode pour déterminer si l'utilisateur
        peut accéder à un module de l'admin (par exemple 'auth', 'users', etc.)
        """
        return self.role in {self.ROLE_ADMIN, self.ROLE_SUPERADMIN}

    def has_perm(self, perm, obj=None):
        """
        Surcharge complémentaire : limite les permissions globales.
        """
        # Les superadmins ont toujours tout accès
        if self.is_superuser or self.role == self.ROLE_SUPERADMIN:
            return True

        # Les admins peuvent gérer les modules
        if self.role == self.ROLE_ADMIN:
            return True

        # Tous les autres (staff, declic_staff, etc.) : aucun accès admin
        return False
