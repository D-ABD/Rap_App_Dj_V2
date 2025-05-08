import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from ..models.prospection import Prospection, HistoriqueProspection
from ..models.logs import LogUtilisateur

logger = logging.getLogger("application.prospection")


@receiver(post_save, sender=Prospection)
def log_prospection_save(sender, instance, created, **kwargs):
    """
    Log utilisateur pour la création ou mise à jour d'une prospection.
    """
    try:
        action = "Création" if created else "Mise à jour"
        LogUtilisateur.log_action(
            instance=instance,
            user=instance.updated_by or instance.created_by,
            action=action,
            details=f"{action} prospection pour {instance.partenaire.nom}"
        )
    except Exception as e:
        logger.warning(f"⚠️ Impossible de journaliser la prospection : {e}")


@receiver(post_save, sender=HistoriqueProspection)
def log_historique_prospection_save(sender, instance, created, **kwargs):
    """
    Log utilisateur lors d'un changement de statut de prospection.
    """
    if created:
        message = (
            f"Changement de statut : {instance.get_ancien_statut_display()} "
            f"→ {instance.get_nouveau_statut_display()}"
        )
        logger.info(f"[Signal] Historique ajouté pour prospection #{instance.prospection.pk} – {message}")

        try:
            LogUtilisateur.log_action(
                instance=instance.prospection,
                action="Changement de statut",
                user=instance.utilisateur,
                details=message
            )
        except Exception as e:
            logger.warning(f"⚠️ Impossible de journaliser le changement de statut : {e}")
