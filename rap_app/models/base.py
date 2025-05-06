import logging
from django.db import models
from django.utils.timezone import now
from django.conf import settings

logger = logging.getLogger(__name__)

class BaseModel(models.Model):
    """
    Modèle de base abstrait pour tous les modèles métiers de l'application.

    Fournit :
    - Un suivi temporel avec `created_at` et `updated_at`
    - Le tracking utilisateur (`created_by`, `updated_by`)
    - Une gestion propre du champ `updated_at` (mise à jour uniquement si nécessaire)
    - Un système de logging optionnel (désactivable via settings.ENABLE_MODEL_LOGGING)
    
    À utiliser en classe parente dans tous les modèles personnalisés.
    """

    created_at = models.DateTimeField(
        default=now,
        editable=False,
        verbose_name="Date de création",
        help_text="Date et heure de création de l'enregistrement"
    )

    updated_at = models.DateTimeField(
        default=now,
        verbose_name="Date de mise à jour",
        help_text="Date et heure de la dernière modification"
    )

    created_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    null=True,
    blank=True,
    editable=False,
    on_delete=models.SET_NULL,
    related_name="%(class)s_created",
    verbose_name="Créé par",
    help_text="Utilisateur ayant créé l'enregistrement"
    )

    updated_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    null=True,
    blank=True,
    on_delete=models.SET_NULL,
    related_name="%(class)s_updated",
    verbose_name="Modifié par",
    help_text="Dernier utilisateur ayant modifié l'enregistrement"
)

    class Meta:
        abstract = True
        ordering = ['-created_at']
        get_latest_by = 'created_at'
        verbose_name = "Objet générique"
        verbose_name_plural = "Objets génériques"

    def __str__(self):
        """
        Retourne une représentation textuelle générique de l'objet.
        """
        return f"{self.__class__.__name__} #{self.pk}"

    def save(self, *args, **kwargs):
        """
        Sauvegarde l'objet avec logique métier :
        - Assigne created_by / updated_by si un `user` est passé dans les kwargs
        - Met à jour updated_at uniquement si des champs ont réellement changé
        - Active un logging conditionnel basé sur settings.ENABLE_MODEL_LOGGING
        """
        user = kwargs.pop('user', None)
        is_new = self.pk is None
        has_changed = True

        # Comparaison avec l’état précédent si existant
        if not is_new:
            try:
                old = type(self).objects.get(pk=self.pk)
                has_changed = any(
                    getattr(old, field.name) != getattr(self, field.name)
                    for field in self._meta.fields
                    if field.name not in ('updated_at', 'created_at', 'updated_by')
                )
            except type(self).DoesNotExist:
                has_changed = True

        # Affectation des utilisateurs
        if is_new and user:
            self.created_by = user
        if user:
            self.updated_by = user

        # updated_at seulement si l'objet a changé
        if has_changed:
            self.updated_at = now()

        # Logging conditionnel
        if getattr(settings, 'ENABLE_MODEL_LOGGING', settings.DEBUG):
            action = "Création" if is_new else "Mise à jour"
            logger.debug(f"{action} de {self.__class__.__name__}")

        super().save(*args, **kwargs)

        if getattr(settings, 'ENABLE_MODEL_LOGGING', settings.DEBUG):
            logger.debug(f"{self.__class__.__name__} #{self.pk} sauvegardé avec succès")
