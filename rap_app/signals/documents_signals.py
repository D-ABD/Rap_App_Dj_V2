import os
import sys
import logging
from django.apps import apps
from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage

from ..models.documents import Document
from ..models.logs import LogUtilisateur

logger = logging.getLogger("rap_app.documents")


@receiver(post_delete, sender=Document)
def log_and_cleanup_document(sender, instance, **kwargs):
    """
    🔁 Signal exécuté après la suppression d'un document :
    - Enregistre un log utilisateur
    - Supprime physiquement le fichier associé
    """
    # ⛔ Ne rien faire durant les migrations
    if not apps.ready or 'migrate' in sys.argv or 'makemigrations' in sys.argv:
        return

    user = kwargs.get('user') or getattr(instance, 'modified_by', None) or getattr(instance, 'created_by', None)

    nom_fichier = getattr(instance, 'nom_fichier', 'Document inconnu')
    document_id = getattr(instance, 'pk', '?')
    formation_id = getattr(instance, 'formation_id', None)

    # ➤ Log de la suppression
    try:
        LogUtilisateur.log_action(
            instance=instance,
            action="suppression",
            user=user,
            details=f"Suppression du document : {nom_fichier} (formation #{formation_id})"
        )
        logger.info(f"[Signal] Log utilisateur enregistré pour la suppression du document #{document_id}")
    except Exception as e:
        logger.warning(f"⚠️ Erreur lors du log de suppression du document #{document_id} : {e}")

    # ➤ Suppression du fichier physique
    if instance.fichier and instance.fichier.name:
        try:
            if default_storage.exists(instance.fichier.name):
                default_storage.delete(instance.fichier.name)
                logger.info(f"[Signal] Fichier supprimé physiquement : {instance.fichier.name}")
            else:
                logger.warning(f"[Signal] Fichier introuvable, pas de suppression : {instance.fichier.name}")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la suppression physique du fichier {instance.fichier.name} : {e}", exc_info=True)
    else:
        logger.warning(f"[Signal] Aucun fichier à supprimer pour document #{document_id}")
