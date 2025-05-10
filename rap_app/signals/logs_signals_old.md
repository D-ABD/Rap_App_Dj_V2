import logging
import sys
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps
from ..models.logs import LogUtilisateur

logger = logging.getLogger("application.logs")

EXCLUDED_MODELS = [
    'LogEntry', 'Permission', 'Group', 'ContentType', 'Session',
    'LogUtilisateur', 'HistoriqueFormation'
]

EXCLUDED_APPS = ['admin', 'contenttypes', 'sessions', 'auth', 'staticfiles']


def skip_during_migrations() -> bool:
    """⛔ Ignore les signaux durant les migrations."""
    return not apps.ready or 'migrate' in sys.argv or 'makemigrations' in sys.argv


def is_loggable(instance) -> bool:
    """Détermine si l'instance doit être logguée."""
    model_name = instance.__class__.__name__
    app_label = instance._meta.app_label

    if model_name in EXCLUDED_MODELS or app_label in EXCLUDED_APPS:
        return False

    excluded = getattr(settings, 'LOG_EXCLUDED_MODELS', [])
    if model_name in excluded or f"{app_label}.{model_name}" in excluded:
        return False

    return True


def get_user_from_instance_or_kwargs(instance, kwargs):
    """Récupère l'utilisateur depuis les kwargs ou les attributs de l'instance."""
    return (
        kwargs.get('user') or
        getattr(instance, '_user', None) or
        getattr(instance, 'updated_by', None) or
        getattr(instance, 'created_by', None)
    )


@receiver(post_save)
def log_post_save(sender, instance, created, **kwargs):
    """Log les créations ou mises à jour."""
    if skip_during_migrations() or not is_loggable(instance):
        return

    if not getattr(instance, "pk", None):
        return  # Objet non sauvegardé

    action = LogUtilisateur.ACTION_CREATE if created else LogUtilisateur.ACTION_UPDATE
    user = get_user_from_instance_or_kwargs(instance, kwargs)

    if created:
        details = f"Création de {sender.__name__} #{instance.pk}"
    elif hasattr(instance, 'get_changed_fields') and callable(instance.get_changed_fields):
        changed = instance.get_changed_fields()
        details = f"Champs modifiés : {', '.join(changed.keys())}" if changed else "Aucune modification détectée"
    else:
        details = f"Modification de {sender.__name__} #{instance.pk}"

    try:
        LogUtilisateur.log_action(
            instance=instance,
            action=action,
            user=user,
            details=details
        )
    except Exception as e:
        logger.error(f"❌ Erreur log {action} {sender.__name__} #{instance.pk} : {e}", exc_info=True)
        if settings.DEBUG:
            print(f"[log_post_save] Erreur : {e}")


@receiver(post_delete)
def log_post_delete(sender, instance, **kwargs):
    """Log les suppressions d'objet."""
    if skip_during_migrations() or not is_loggable(instance):
        return

    if not getattr(instance, "pk", None):
        return

    user = get_user_from_instance_or_kwargs(instance, kwargs)
    details = f"Suppression de {sender.__name__} #{instance.pk} : {instance}"

    try:
        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_DELETE,
            user=user,
            details=details
        )
    except Exception as e:
        logger.error(f"❌ Erreur log suppression {sender.__name__} #{instance.pk} : {e}", exc_info=True)
        if settings.DEBUG:
            print(f"[log_post_delete] Erreur : {e}")
