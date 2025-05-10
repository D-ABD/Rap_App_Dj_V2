import logging
import sys
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps

from ..models.types_offre import TypeOffre
from ..models.logs import LogUtilisateur

logger = logging.getLogger("rap_app.typeoffre")


def skip_during_migrations() -> bool:
    """
    Ignore les signaux durant les migrations.
    """
    return not apps.ready or 'migrate' in sys.argv or 'makemigrations' in sys.argv


@receiver(post_save, sender=TypeOffre)
def log_type_offre_save(sender, instance, created, **kwargs):
    """
    📄 Log utilisateur et serveur pour la création ou modification d'un TypeOffre.
    """
    if skip_during_migrations():
        return

    try:
        action = "Création" if created else "Mise à jour"
        user = getattr(instance, '_user', None)

        # Log utilisateur
        LogUtilisateur.log_action(
            instance=instance,
            action=action,
            user=user,
            details=f"{action} du type d'offre : {instance.nom}"
        )

        # Log technique
        logger.info(f"[Signal] {action} du type d'offre #{instance.pk} : {instance.nom}")

    except Exception as e:
        logger.warning(f"[Signal] Échec log utilisateur pour TypeOffre #{instance.pk} : {e}", exc_info=True)


@receiver(post_delete, sender=TypeOffre)
def log_type_offre_delete(sender, instance, **kwargs):
    """
    🗑️ Log utilisateur et serveur pour la suppression d’un TypeOffre.
    """
    if skip_during_migrations():
        return

    try:
        user = getattr(instance, '_user', None)

        LogUtilisateur.log_action(
            instance=instance,
            action="Suppression",
            user=user,
            details=f"Suppression du type d'offre : {instance.nom} (ID: {instance.pk})"
        )

        logger.warning(f"[Signal] Suppression du type d'offre #{instance.pk} : {instance.nom}")

    except Exception as e:
        logger.error(f"[Signal] Échec log suppression TypeOffre #{instance.pk} : {e}", exc_info=True)
