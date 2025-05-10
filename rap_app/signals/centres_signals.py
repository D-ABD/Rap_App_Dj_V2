import logging
import sys
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.apps import apps

from ..models.centres import Centre
from ..models.logs import LogUtilisateur

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Centre)
def log_centre_save(sender, instance, created, **kwargs):
    """Signal exécuté après la création ou modification d'un centre."""
    if not apps.ready or 'migrate' in sys.argv or 'makemigrations' in sys.argv:
        return

    # Logging utilisateur
    LogUtilisateur.log_action(
        instance=instance,
        action="création" if created else "modification",
        user=instance.modified_by if hasattr(instance, "modified_by") else None,
        details="Création ou mise à jour d'un centre"
    )

    # Logging console
    if created:
        logger.info(f"[Signal] Nouveau centre créé : {instance.nom}")
    else:
        logger.info(f"[Signal] Centre mis à jour : {instance.nom}")


@receiver(pre_delete, sender=Centre)
def log_centre_deleted(sender, instance, **kwargs):
    """Signal exécuté avant la suppression d'un centre."""
    logger.warning(f"[Signal] Suppression du centre : {instance.nom} (ID: {instance.pk})")


@receiver(post_delete, sender=Centre)
def invalidate_centre_cache_on_delete(sender, instance, **kwargs):
    """Signal exécuté après suppression pour invalidation du cache."""
    instance.invalidate_caches()
