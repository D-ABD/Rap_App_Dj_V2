import os
import logging
from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver

from ..models.documents import Document
from ..models.logs import LogUtilisateur

logger = logging.getLogger("application.documents")


@receiver(post_delete, sender=Document)
def log_and_cleanup_document(sender, instance, **kwargs):
    """
    🔁 Signal exécuté après la suppression d'un document :
    - Enregistre un log utilisateur
    - Supprime physiquement le fichier associé
    """
    user = instance.created_by if hasattr(instance, "created_by") else None

    # ➤ Log de la suppression
    try:
        LogUtilisateur.log_action(
            instance=instance,
            action="Suppression",
            user=user,
            details=f"Suppression du document : {instance.nom_fichier}"
        )
        logger.info(f"[Signal] Log utilisateur enregistré pour {instance}")
    except Exception as e:
        logger.warning(f"⚠️ Impossible de journaliser la suppression du document #{instance.pk} : {e}")

    # ➤ Suppression du fichier physique
    file_path = getattr(instance.fichier, 'path', None)
    if file_path and os.path.isfile(file_path):
        try:
            os.remove(file_path)
            logger.info(f"[Signal] Fichier supprimé physiquement : {file_path}")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la suppression du fichier {file_path} : {e}")
