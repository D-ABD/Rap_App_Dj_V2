from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

from ..models.rapports import Rapport
from ..models.logs import LogUtilisateur  # ✅ méthode de classe

logger = logging.getLogger("application.rapports")


@receiver(post_save, sender=Rapport)
def log_rapport_creation(sender, instance: Rapport, created: bool, **kwargs):
    """
    📄 Signal déclenché à chaque création ou mise à jour de rapport.
    Enregistre l’action dans les logs utilisateur + fichier serveur.
    """
    try:
        action = "Création" if created else "Mise à jour"
        user = getattr(instance, "utilisateur", None)

        LogUtilisateur.log_action(
            instance=instance,
            action=action,
            user=user,
            details=f"{action} du rapport : {instance.nom} ({instance.get_type_rapport_display()})"
        )

        logger.info(f"[Signal] {action} du rapport #{instance.pk} : {instance.nom}")
    except Exception as e:
        logger.warning(f"⚠️ Erreur lors du signal post_save Rapport : {e}")
