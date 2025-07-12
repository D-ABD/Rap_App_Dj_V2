import sys
import logging
from django.db import transaction
from django.utils.timezone import now
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.apps import apps

from ..models.formations import Formation, HistoriqueFormation
from ..middleware import get_current_user

# Loggers
logger_formation = logging.getLogger("rap_app.formation")
logger_historique = logging.getLogger("rap_app.historiqueformation")


def skip_during_migrations() -> bool:
    """
    ⛔ Empêche l'exécution des signaux pendant les migrations.

    Returns:
        bool: True si les migrations sont en cours, sinon False.
    """
    return not apps.ready or 'migrate' in sys.argv or 'makemigrations' in sys.argv


def get_user(instance):
    """
    🔍 Récupère l'utilisateur lié à l'action depuis l'instance, ou via le middleware.

    Args:
        instance (Model): Instance Django à inspecter.

    Returns:
        User | None: Utilisateur courant si trouvé, sinon None.
    """
    return (
        getattr(instance, '_user', None)
        or getattr(instance, 'updated_by', None)
        or getattr(instance, 'created_by', None)
        or get_current_user()
    )


@receiver(post_save, sender=Formation)
def log_formation_saved(sender, instance, created, **kwargs):
    """
    📝 Enregistre un message dans le log lorsqu'une formation est créée ou modifiée.
    Crée aussi une ligne dans HistoriqueFormation si création.

    Args:
        sender (Model): Le modèle ayant émis le signal.
        instance (Formation): L’instance concernée.
        created (bool): True si nouvel objet, False si mise à jour.
    """
    if skip_during_migrations():
        return

    action = "créée" if created else "modifiée"
    user = get_user(instance)
    user_info = f"par {user.get_full_name() or user.username}" if user else "par Système"

    logger_formation.info(
        f"[Signal] Formation {action} : {instance.nom} (ID={instance.pk}) {user_info}"
    )

    if created:
        try:
            HistoriqueFormation.objects.create(
                formation=instance,
                action='création',
                champ_modifie='formation',
                nouvelle_valeur=str(instance.nom),
                commentaire="Création de la formation (via signal)",
                created_by=user
            )
        except Exception as e:
            logger_historique.error(f"[Signal] Erreur lors de l’historique de création : {e}", exc_info=True)


@receiver(pre_delete, sender=Formation)
def log_formation_deleted(sender, instance, **kwargs):
    if skip_during_migrations():
        return

    user = get_user(instance)
    user_info = f"par {user.get_full_name() or user.username}" if user else "par Système"

    logger_formation.warning(
        f"[Signal] Formation supprimée : {instance.nom} (ID={instance.pk}) {user_info}"
    )

    try:
        with transaction.atomic():
            HistoriqueFormation.objects.create(
                formation=None,  # ⛔ surtout pas `formation=instance`
                action=HistoriqueFormation.ActionType.SUPPRESSION,
                champ_modifie='formation',
                ancienne_valeur=instance.nom,
                nouvelle_valeur=None,
                commentaire=f"Formation supprimée le {now().strftime('%d/%m/%Y à %H:%M')}",
                created_by=user,
                details={
                    "id": instance.pk,
                    "nom": instance.nom,
                    "centre": str(instance.centre) if instance.centre_id else None,
                    "type_offre": str(instance.type_offre) if instance.type_offre_id else None,
                    "date_suppression": now().isoformat()
                }
            )
    except Exception as e:
        logger_historique.error(f"[Signal] Erreur lors de l’historique de suppression : {e}", exc_info=True)


@receiver(post_save, sender=HistoriqueFormation)
def log_historique_ajout(sender, instance, created, **kwargs):
    """
    📘 Enregistre un log quand une entrée HistoriqueFormation est créée.

    Args:
        sender (Model): Le modèle ayant émis le signal.
        instance (HistoriqueFormation): L’instance créée.
        created (bool): True si nouvel objet.
    """
    if skip_during_migrations() or not created:
        return

    ancienne = instance.ancienne_valeur or "—"
    nouvelle = instance.nouvelle_valeur or "—"
    user = instance.created_by
    user_info = f"par {user.get_full_name() or user.username}" if user else "par Système"

    logger_historique.info(
        f"[Signal] Historique enregistré pour formation #{instance.formation_id} "
        f"{user_info} – {instance.get_action_display()} du champ '{instance.champ_modifie}' : "
        f"{ancienne} → {nouvelle}"
    )

    if instance.action == 'suppression':
        logger_historique.warning(
            f"[Signal] Suppression enregistrée pour formation #{instance.formation_id}"
        )


@receiver(pre_delete, sender=HistoriqueFormation)
def log_historique_suppression(sender, instance, **kwargs):
    """
    🗑️ Enregistre un log lorsqu’une ligne HistoriqueFormation est supprimée.

    Args:
        sender (Model): Le modèle ayant émis le signal.
        instance (HistoriqueFormation): L’instance supprimée.
    """
    if skip_during_migrations():
        return

    logger_historique.warning(
        f"[Signal] Suppression d’un historique (ID={instance.pk}) lié à la formation #{instance.formation_id}"
    )
