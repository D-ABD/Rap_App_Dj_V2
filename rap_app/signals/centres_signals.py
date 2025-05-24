import logging
import sys
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.apps import apps

from ..models.centres import Centre
from ..models.logs import LogUtilisateur

# Logger audit uniquement
audit_logger = logging.getLogger('rap_app.audit')


@receiver(post_save, sender=Centre)
def log_centre_save(sender, instance, created, **kwargs):
    """Signal exécuté après la création ou modification d'un centre."""
    if not apps.ready or 'migrate' in sys.argv or 'makemigrations' in sys.argv:
        return

    # Logging application (base de données)
    LogUtilisateur.log_action(
        instance=instance,
        action="création" if created else "modification",
        user=instance.modified_by if hasattr(instance, "modified_by") else None,
        details="Création ou mise à jour d'un centre"
    )

    # Logging audit structuré
    audit_logger.info(
        "Nouveau centre créé" if created else "Centre mis à jour",
        extra={
            'user': 'system',
            'action': 'création' if created else 'modification',
            'object': f"Centre #{instance.pk} - {instance.nom}"
        }
    )


@receiver(pre_delete, sender=Centre)
def log_centre_deleted(sender, instance, **kwargs):
    """Signal exécuté avant la suppression d'un centre."""
    audit_logger.info(
        "Centre supprimé (pré-delete)",
        extra={
            'user': 'system',
            'action': 'suppression',
            'object': f"Centre #{instance.pk} - {instance.nom}"
        }
    )


@receiver(post_delete, sender=Centre)
def invalidate_centre_cache_on_delete(sender, instance, **kwargs):
    """Signal exécuté après suppression pour invalidation du cache."""
    instance.invalidate_caches()
