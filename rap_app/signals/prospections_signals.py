import logging
import sys
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps

from ..models.prospection import Prospection, HistoriqueProspection, ProspectionChoices
from ..models.logs import LogUtilisateur

logger = logging.getLogger("rap_app.prospection")

def skip_during_migrations():
    return not apps.ready or 'migrate' in sys.argv or 'makemigrations' in sys.argv


def get_user(instance, kwargs=None):
    """
    Tente de récupérer l'utilisateur associé à une instance ou au signal.
    """
    if kwargs:
        return (
            kwargs.get('user') or
            getattr(instance, '_user', None) or
            getattr(instance, 'updated_by', None) or
            getattr(instance, 'created_by', None)
        )
    return getattr(instance, '_user', None) or getattr(instance, 'updated_by', None) or getattr(instance, 'created_by', None)


@receiver(post_save, sender=Prospection)
def log_prospection_save(sender, instance, created, **kwargs):
    if skip_during_migrations():
        return

    try:
        user = get_user(instance, kwargs)
        action = LogUtilisateur.ACTION_CREATE if created else LogUtilisateur.ACTION_UPDATE
        partenaire = getattr(instance, 'partenaire', None)
        partenaire_nom = getattr(partenaire, 'nom', 'Partenaire inconnu')

        suffix = {
            ProspectionChoices.STATUT_ACCEPTEE: " (Acceptée)",
            ProspectionChoices.STATUT_REFUSEE: " (Refusée)"
        }.get(instance.statut, "")

        LogUtilisateur.log_action(
            instance=instance,
            user=user,
            action=action,
            details=f"{action.capitalize()} prospection pour {partenaire_nom}{suffix}"
        )

        logger.info(f"[Signal] {action.capitalize()} prospection #{instance.pk} pour partenaire {partenaire_nom}")
    except Exception as e:
        logger.warning(f"⚠️ Impossible de journaliser prospection #{getattr(instance, 'pk', 'Unknown')} : {e}", exc_info=True)


@receiver(post_save, sender=HistoriqueProspection)
def log_historique_prospection_save(sender, instance, created, **kwargs):
    if skip_during_migrations() or not created:
        return

    try:
        ancien = instance.get_ancien_statut_display()
        nouveau = instance.get_nouveau_statut_display()
        message = f"Changement de statut : {ancien} → {nouveau}"

        if instance.prochain_contact:
            message += f" (Prochain contact : {instance.prochain_contact.strftime('%d/%m/%Y')})"

        logger.info(f"[Signal] Historique ajouté pour prospection #{instance.prospection_id} – {message}")

        user = get_user(instance)

        LogUtilisateur.log_action(
            instance=instance.prospection,
            action="changement de statut",
            user=user,
            details=message
        )
    except Exception as e:
        logger.warning(f"⚠️ Impossible de journaliser historique #{getattr(instance, 'pk', 'Unknown')} : {e}", exc_info=True)


@receiver(post_delete, sender=Prospection)
def log_prospection_delete(sender, instance, **kwargs):
    if skip_during_migrations():
        return

    try:
        user = get_user(instance, kwargs)
        partenaire = getattr(instance, 'partenaire', None)
        partenaire_nom = getattr(partenaire, 'nom', 'Partenaire inconnu')
        partenaire_id = getattr(partenaire, 'pk', 'N/A')
        formation_nom = getattr(getattr(instance, 'formation', None), 'nom', None)

        details = f"Suppression d'une prospection pour {partenaire_nom} (#{partenaire_id})"
        if formation_nom:
            details += f", formation : {formation_nom}"

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_DELETE,
            user=user,
            details=details
        )

        logger.warning(f"[Signal] Suppression prospection #{instance.pk} pour {partenaire_nom}")
    except Exception as e:
        logger.error(f"⚠️ Erreur lors du log de suppression prospection #{getattr(instance, 'pk', 'Unknown')} : {e}", exc_info=True)
