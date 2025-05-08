# ------------------
# SIGNAUX FORMATIONS
# ------------------

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from ..models.formations import Formation
from ..models.formations import HistoriqueFormation  # même fichier, chargement groupé

logger_formation = logging.getLogger("application.formation")
logger_historique = logging.getLogger("application.historiqueformation")


@receiver(post_save, sender=Formation)
def log_formation_saved(sender, instance, created, **kwargs):
    """
    Log technique lors de la sauvegarde d'une formation (création ou mise à jour).

    Args:
        sender: Classe du modèle (Formation)
        instance: Instance de Formation sauvegardée
        created (bool): True si nouvel objet créé, False sinon
        **kwargs: Paramètres supplémentaires du signal
    """
    action = "créée" if created else "modifiée"
    logger_formation.info(f"[Signal] Formation {action} : {instance.nom} (ID={instance.pk})")


# -----------------------------
# SIGNAUX HISTORIQUE_FORMATIONS
# -----------------------------

@receiver(post_save, sender=HistoriqueFormation)
def log_historique_ajout(sender, instance, created, **kwargs):
    """
    Log technique lors de la création d’un historique de modification.

    Args:
        sender: Classe du modèle (HistoriqueFormation)
        instance: Instance créée
        created (bool): True si nouvel historique
        **kwargs: Paramètres supplémentaires
    """
    if created:
        logger_historique.info(
            f"[Signal] Historique créé pour formation #{instance.formation_id} "
            f"– champ : {instance.champ_modifie} | "
            f"{instance.ancienne_valeur} → {instance.nouvelle_valeur}"
        )
