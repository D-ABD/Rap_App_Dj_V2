import logging
from django.db import models
from django.utils.timezone import now
from django.conf import settings
from django.forms.models import model_to_dict

logger = logging.getLogger(__name__)

class BaseModel(models.Model):
    """
    🔧 Modèle de base abstrait pour tous les modèles métiers de l'application.

    Fournit automatiquement :
    - ⏱️ Suivi des dates de création/modification (`created_at`, `updated_at`)
    - 👤 Suivi des utilisateurs (`created_by`, `updated_by`)
    - 💡 Mise à jour intelligente de `updated_at` uniquement en cas de changement réel
    - 📓 Logging détaillé (conditionnel via `settings.ENABLE_MODEL_LOGGING`)
    - 🔄 Méthodes utilitaires pour la sérialisation et le suivi des modifications

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
    class Meta:
        abstract = True
        ordering = ['-created_at']
        get_latest_by = 'created_at'
        verbose_name = "Objet générique"
        verbose_name_plural = "Objets génériques"

    def __str__(self):
        """
        🔁 Représentation textuelle par défaut de l'objet.

        Returns:
            str: Format générique du type `NomClasse #id`
        """
        return f"{self.__class__.__name__} #{self.pk}"
    

    def clean(self):
        """Validation métier générique (à surcharger dans les sous-modèles)."""
        pass

    def get_absolute_url(self):
        """À surcharger pour retourner l'URL de détail de l'objet."""
        raise NotImplementedError("get_absolute_url() doit être implémenté dans les sous-modèles.")


    def get_changed_fields(self):
        """
        🔍 Identifie les champs modifiés entre l'ancienne et la nouvelle version de l'objet.

        Returns:
            dict: Dictionnaire au format {champ: (ancienne_valeur, nouvelle_valeur)}.
                  Exclut les champs d'audit (`created_at`, `updated_at`, etc.).
        """
        if not self.pk:
            return {}
        try:
            old = type(self).objects.get(pk=self.pk)
            old_data = model_to_dict(old)
            new_data = model_to_dict(self)
            return {
                k: (old_data[k], new_data[k])
                for k in old_data
                if k not in ('created_at', 'updated_at', 'created_by', 'updated_by')
                and old_data[k] != new_data[k]
            }
        except type(self).DoesNotExist:
            return {}

    def save_with_user(self, user, **kwargs):
        """
        💾 Variante simplifiée de `save()` avec passage explicite de l'utilisateur.

        Args:
            user (User): L'utilisateur effectuant l'action.
            **kwargs: Autres arguments pour `save()`.

        Returns:
            None
        """
        return self.save(user=user, **kwargs)

    def save(self, *args, **kwargs):
        """
        💾 Surcharge de la méthode `save()` :
        - Affecte `created_by` et `updated_by` si `user` est fourni.
        - Met à jour `updated_at` uniquement si des champs ont changé.
        - Journalise les actions si `settings.ENABLE_MODEL_LOGGING` est activé.

        Args:
            user (User, optional): Utilisateur ayant initié la modification.
            *args: Paramètres positionnels.
            **kwargs: Paramètres nommés, y compris `user`.
        """
        user = kwargs.pop('user', None)
        is_new = self.pk is None
        has_changed = True
        changed_fields = {}

        if not is_new:
            try:
                old = type(self).objects.get(pk=self.pk)
                old_data = model_to_dict(old)
                new_data = model_to_dict(self)
                changed_fields = {
                    k: (old_data[k], new_data[k])
                    for k in old_data
                    if k not in ('created_at', 'updated_at', 'created_by', 'updated_by')
                    and old_data[k] != new_data[k]
                }
                has_changed = bool(changed_fields)
            except type(self).DoesNotExist:
                has_changed = True

        if is_new and user and not self.created_by:
            self.created_by = user
        if user:
            self.updated_by = user


        if getattr(settings, 'ENABLE_MODEL_LOGGING', settings.DEBUG):
            action = "Création" if is_new else "Mise à jour"
            logger.debug(f"{action} de {self.__class__.__name__} (user={user})")
            if changed_fields:
                logger.debug(f"Changements détectés : {changed_fields}")

        super().save(*args, **kwargs)

        if getattr(settings, 'ENABLE_MODEL_LOGGING', settings.DEBUG):
            logger.debug(f"{self.__class__.__name__} #{self.pk} sauvegardé avec succès.")

    def to_serializable_dict(self, exclude=None):
        """
        📦 Retourne un dictionnaire sérialisable de l'objet.

        Args:
            exclude (list[str], optional): Liste de champs à exclure de la sortie.

        Returns:
            dict: Données sérialisables de l'objet.
        """
        exclude = exclude or []
        return {
            k: v
            for k, v in model_to_dict(self).items()
            if k not in exclude
        }

    @classmethod
    def get_verbose_name(cls):
        """
        🔠 Retourne le nom verbose défini dans les métadonnées du modèle.

        Returns:
            str: Nom humanisé du modèle.
        """
        return cls._meta.verbose_name
