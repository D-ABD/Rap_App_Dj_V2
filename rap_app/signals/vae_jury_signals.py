from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
import logging

from ..models.vae_jury import VAE, HistoriqueStatutVAE
from ..models.logs import LogUtilisateur

logger = logging.getLogger("application.vae")


@receiver(pre_save, sender=VAE)
def track_vae_status_change(sender, instance, **kwargs):
    """
    Détecte un changement de statut avant la sauvegarde de la VAE.
    """
    if instance.pk is None:
        return
    
    try:
        old_instance = VAE.objects.get(pk=instance.pk)
        instance._status_changed = old_instance.statut != instance.statut
        instance._old_status = old_instance.statut if instance._status_changed else None
    except VAE.DoesNotExist:
        instance._status_changed = False


@receiver(post_save, sender=VAE)
def create_vae_status_history(sender, instance, created, **kwargs):
    """
    Crée un HistoriqueStatutVAE et logue l'action utilisateur.
    """
    if created:
        historique = HistoriqueStatutVAE.objects.create(
            vae=instance,
            statut=instance.statut,
            date_changement_effectif=instance.created_at,
            commentaire=f"Création de la VAE avec statut initial : {instance.get_statut_display()}"
        )
        logger.info(f"Historique initial créé pour VAE {instance.reference}: {historique}")

        LogUtilisateur.log_action(
            instance=instance,
            action="Création VAE",
            user=instance.created_by,
            details=f"Statut initial : {instance.get_statut_display()}"
        )

    elif getattr(instance, '_status_changed', False):
        historique = HistoriqueStatutVAE.objects.create(
            vae=instance,
            statut=instance.statut,
            date_changement_effectif=timezone.now().date(),
            commentaire=f"Changement de statut : {dict(VAE.STATUT_CHOICES).get(instance._old_status)} → {instance.get_statut_display()}"
        )
        logger.info(f"Changement de statut enregistré pour VAE {instance.reference}: {historique}")

        LogUtilisateur.log_action(
            instance=instance,
            action="Changement de statut VAE",
            user=instance.updated_by or instance.created_by,
            details=f"{dict(VAE.STATUT_CHOICES).get(instance._old_status)} → {instance.get_statut_display()}"
        )
from ..models.prepacomp import Semaine
from ..models.vae_jury import SuiviJury  # ou à adapter selon ton arborescence


@receiver(post_save, sender=Semaine)
def log_semaine_save(sender, instance, created, **kwargs):
    """
    Log l'enregistrement ou la mise à jour d'une Semaine via LogUtilisateur.
    """
    try:
        LogUtilisateur.log_action(
            instance=instance,
            action="Création" if created else "Mise à jour",
            user=instance.updated_by or instance.created_by,
            details=f"Semaine enregistrée pour {instance.centre} – {instance.get_periode_display()}"
        )
    except Exception as e:
        logger.warning(f"[Semaine] Échec journalisation : {e}")


@receiver(post_save, sender=SuiviJury)
def log_suivijury_save(sender, instance, created, **kwargs):
    """
    Log l'enregistrement ou la mise à jour d'un SuiviJury via LogUtilisateur.
    """
    try:
        LogUtilisateur.log_action(
            instance=instance,
            action="Création" if created else "Mise à jour",
            user=instance.updated_by or instance.created_by,
            details=f"Suivi jury pour {instance.centre} – {instance.get_periode_display()} ({instance.jurys_realises}/{instance.get_objectif_auto()} jurys)"
        )
    except Exception as e:
        logger.warning(f"[SuiviJury] Échec journalisation : {e}")
