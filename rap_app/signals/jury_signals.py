import logging
import sys
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps

from ..models.jury import SuiviJury
from ..models.logs import LogUtilisateur

logger = logging.getLogger("rap_app.jury")


def skip_during_migrations():
    return not apps.ready or "migrate" in sys.argv or "makemigrations" in sys.argv


# ==============================
# 👩‍⚖️ SuiviJury : log d'activité
# ==============================

@receiver(post_save, sender=SuiviJury)
def log_suivijury_save(sender, instance, created, **kwargs):
    if skip_during_migrations():
        return

    try:
        LogUtilisateur.log_action(
            instance=instance,
            action="Création" if created else "Mise à jour",
            user=instance.updated_by or instance.created_by,
            details=(
                f"Suivi jury pour {instance.centre} – {instance.get_periode_display()} "
                f"({instance.jurys_realises}/{instance.get_objectif_auto()} jurys)"
            ),
        )
        if hasattr(instance, "invalidate_caches"):
            instance.invalidate_caches()
    except Exception as e:
        logger.warning(
            f"[Signal] Échec journalisation SuiviJury #{instance.pk} : {e}",
            exc_info=True,
        )
