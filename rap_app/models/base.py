import logging
from django.db import models
from django.utils.timezone import now
from django.conf import settings
from django.forms.models import model_to_dict
from django.core.cache import cache
from django.core.exceptions import FieldError, ValidationError

from ..middleware import get_current_user

logger = logging.getLogger(__name__)


class BaseModel(models.Model):
    """
    🔧 Modèle de base abstrait pour tous les modèles métiers de l'application.

    Fournit automatiquement :
    - ⏱️ Suivi des dates de création/modification (`created_at`, `updated_at`)
    - 👤 Suivi des utilisateurs (`created_by`, `updated_by`)
    - 🔄 Mise à jour intelligente de `updated_at` uniquement en cas de changement réel
    - 📓 Logging détaillé (conditionnel via `settings.ENABLE_MODEL_LOGGING`)
    - 🔄 Méthodes utilitaires pour la sérialisation et le suivi des modifications
    - 🔒 Validations et gestion des erreurs robustes
    - 📊 Optimisations de performance (cache, détection des changements)
    - 🗑️ Champ `is_active` pour la suppression logique

    👉 À hériter dans tous les modèles personnalisés de l'application.
    """

    created_at = models.DateTimeField(
        auto_now_add=True, 
        editable=False, 
        verbose_name="Date de création",
        help_text="Date et heure de création de l'enregistrement"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Date de mise à jour",
        help_text="Date et heure de la dernière modification"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, 
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name="created_%(class)s_set",
        verbose_name="Créé par",
        help_text="Utilisateur ayant créé l'enregistrement"
    )
    
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, 
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_%(class)s_set",
        verbose_name="Modifié par",
        help_text="Dernier utilisateur ayant modifié l'enregistrement"
    )

    is_active = models.BooleanField(
        default=True, 
        verbose_name="Actif",
        help_text="Indique si l'objet est actif ou archivé"
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']
        get_latest_by = 'created_at'
        verbose_name = "Objet de base"
        verbose_name_plural = "Objets de base"
        indexes = [
            models.Index(fields=['is_active'], name='%(app_label)s_%(class)s_active_idx'),
        ]

    def __str__(self):
        """
        🔁 Représentation textuelle par défaut de l'objet.

        Returns:
            str: Format générique du type `NomClasse #id`
        """
        return f"{self.__class__.__name__} #{self.pk}"

    def __repr__(self):
        """
        📝 Représentation technique pour le débogage.
        
        Returns:
            str: Format technique détaillé
        """
        return f"<{self.__class__.__name__}(id={self.pk})>"

    def clean(self):
        """
        🔍 Validation personnalisée à surcharger dans les sous-classes.
        
        Cette méthode est appelée avant la sauvegarde de l'objet pour
        effectuer des validations qui ne peuvent pas être exprimées par
        des contraintes sur les champs individuels.
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        pass

    def validate_unique(self, exclude=None):
        """
        🔍 Surcharge de la validation d'unicité avec des messages d'erreur plus clairs.
        
        Améliore les messages d'erreur en ajoutant le nom verbeux des champs.
        
        Args:
            exclude (list): Champs à exclure de la validation
            
        Raises:
            ValidationError: Si les contraintes d'unicité ne sont pas respectées
        """
        try:
            super().validate_unique(exclude=exclude)
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, msgs in e.message_dict.items():
                    try:
                        field_verbose = self._meta.get_field(field).verbose_name
                        e.message_dict[field] = [f"{field_verbose}: {msg}" for msg in msgs]
                    except Exception:
                        continue
            raise e


    @classmethod
    def get_current_user(cls):
        """
        👤 Récupère l'utilisateur actuel à partir du contexte.
        
        Utilise le middleware ThreadLocal pour récupérer l'utilisateur actuel.
        
        Returns:
            User: L'utilisateur actuellement connecté ou None si non disponible
        """
        try:
            return get_current_user()
        except ImportError:
            logger.debug("Middleware get_current_user() non disponible.")
            return None
        except AttributeError:
            logger.debug("Aucun utilisateur trouvé dans le contexte.")
            return None
        except Exception as e:
            logger.debug(f"Erreur lors de la récupération de l'utilisateur: {str(e)}")
            return None

    def get_changed_fields(self):
        """
        🔍 Retourne les champs modifiés par rapport à la version enregistrée en base.
        
        Compare les valeurs actuelles avec celles en base de données pour
        détecter les modifications sur tous les champs (sauf les champs d'audit).
        
        Returns:
            dict: Dictionnaire au format {champ: (ancienne_valeur, nouvelle_valeur)}
        """
        if not self.pk:
            return {}
        try:
            old = type(self).objects.get(pk=self.pk)
            changes = {}
            for field in self._meta.fields:
                name = field.name
                if name in ('created_at', 'updated_at', 'created_by', 'updated_by'):
                    continue
                old_val = getattr(old, name, None)
                new_val = getattr(self, name, None)
                if old_val != new_val:
                    changes[name] = (old_val, new_val)
            return changes
        except type(self).DoesNotExist:
            return {}

    def log_debug(self, message):
        """
        📓 Journalise un message de débogage si le paramètre `ENABLE_MODEL_LOGGING` est activé.
        
        Args:
            message (str): Message à journaliser
        """
        if getattr(settings, 'ENABLE_MODEL_LOGGING', settings.DEBUG):
            logger.debug(f"[{self.__class__.__name__}] {message}")

    def save(self, *args, **kwargs):
        """
        💾 Sauvegarde l'objet avec gestion automatique des utilisateurs et journalisation.
        
        - Affecte `created_by` et `updated_by` si l'utilisateur est fourni
        - Valide les données avec `clean()` sauf si `skip_validation=True`
        - Journalise les actions si `settings.ENABLE_MODEL_LOGGING` est activé
        - Invalide le cache après la sauvegarde
        """
        user = kwargs.pop('user', None) or self.get_current_user()
        skip_validation = kwargs.pop('skip_validation', False)
        is_new = self.pk is None
        changed_fields = {} if is_new else self.get_changed_fields()

        if is_new and user and not self.created_by:
            self.created_by = user
        if user:
            self.updated_by = user

        try:
            if not skip_validation:
                self.clean()
        except Exception as e:
            model_name = self.__class__.__name__
            logger.error(f"Erreur de validation pour {model_name} (ID: {self.pk or 'nouveau'}): {e}")
            raise

        self.log_debug(f"{'Création' if is_new else 'Mise à jour'} par {user}")
        if changed_fields:
            self.log_debug(f"Changements détectés : {changed_fields}")

        super().save(*args, **kwargs)
        self.invalidate_caches()
        self.log_debug(f"#{self.pk} sauvegardé.")

    def delete(self, *args, **kwargs):
        """
        🗑️ Supprime l'objet avec journalisation et invalidation du cache.
        
        Args:
            *args: Arguments positionnels à transmettre à `models.Model.delete()`
            **kwargs: Arguments nommés pouvant inclure `user` pour l'utilisateur effectuant l'action
            
        Returns:
            tuple: Résultat de la suppression (nombre d'objets supprimés, dict avec détail par type)
        """
        user = kwargs.pop('user', None) or self.get_current_user()
        self.log_debug(f"Suppression de #{self.pk} par {user}")
        self.invalidate_caches()
        result = super().delete(*args, **kwargs)
        self.log_debug(f"#{self.pk} supprimé.")
        return result

    def to_serializable_dict(self, exclude=None):
        """
        📦 Retourne un dictionnaire sérialisable de l'objet.
        
        Convertit toutes les valeurs de l'objet (y compris les relations) 
        en types sérialisables pour JSON ou autre format d'échange.
        
        Args:
            exclude (list): Liste de champs à exclure
            
        Returns:
            dict: Dictionnaire des données sérialisables
        """
        exclude = exclude or []
        data = {}
        
        # Champs simples
        for field in self._meta.fields:
            name = field.name
            if name in exclude:
                continue
            value = getattr(self, name)
            
            # Conversion spécifique selon le type
            if hasattr(value, 'isoformat'):  # Date/datetime
                data[name] = value.isoformat()
            elif hasattr(value, 'url'):  # FileField/ImageField
                data[name] = value.url
            elif isinstance(value, models.Model):  # ForeignKey
                data[name] = {'id': value.pk, 'str': str(value)}
            else:  # Types simples
                data[name] = value

        # Relations many-to-many
        for field in self._meta.many_to_many:
            if field.name in exclude:
                continue
            related_objects = getattr(self, field.name).all()
            data[field.name] = [{'id': obj.pk, 'str': str(obj)} for obj in related_objects]

        return data

    @classmethod
    def get_verbose_name(cls):
        """
        🔠 Retourne le nom verbeux du modèle.
        
        Returns:
            str: Nom verbeux défini dans les métadonnées
        """
        return cls._meta.verbose_name

    @classmethod
    def get_by_id(cls, id, active_only=True):
        """
        🔍 Récupère un objet par son ID avec gestion des erreurs.
        
        Args:
            id: Identifiant de l'objet
            active_only (bool): Si True, ne récupère que les objets actifs
            
        Returns:
            Object: L'instance correspondant à l'ID
            
        Raises:
            ValueError: Si l'ID est vide ou invalide
            DoesNotExist: Si aucun objet ne correspond
        """
        if not id:
            raise ValueError("L'identifiant ne peut pas être vide.")
        try:
            id = int(id)
            qs = cls.objects
            if active_only:
                qs = qs.filter(is_active=True)
            return qs.get(pk=id)
        except (ValueError, TypeError):
            raise ValueError(f"Identifiant invalide : {id}")
        except cls.DoesNotExist:
            logger.warning(f"{cls.__name__} avec ID={id} non trouvé")
            raise

    def invalidate_caches(self):
        """
        🔄 Invalide les caches associés à cet objet.
        
        Cette méthode peut être étendue dans les sous-classes pour
        invalider des caches supplémentaires spécifiques.
        """
        cache.delete(f"{self.__class__.__name__}_{self.pk}")
        cache.delete(f"{self.__class__.__name__}_list")

    @classmethod
    def get_filtered_queryset(cls, **filters):
        """
        🔍 Retourne un queryset filtré avec gestion des erreurs.
        
        Args:
            **filters: Filtres à appliquer au queryset
            
        Returns:
            QuerySet: QuerySet filtré ou vide en cas d'erreur
        """
        try:
            return cls.objects.filter(**filters)
        except (FieldError, ValueError) as e:
            logger.error(f"Erreur de filtrage sur {cls.__name__}: {e}")
            return cls.objects.none()