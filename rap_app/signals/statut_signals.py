import logging
import sys
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.apps import apps
from django.utils import timezone

from ..models.jury import SuiviJury
from ..models.vae import VAE, HistoriqueStatutVAE

from ..models.logs import LogUtilisateur

logger = logging.getLogger("rap_app.vae")


def skip_during_migrations() -> bool:
    """
    Ignore les signaux pendant les migrations.
    """
    return not apps.ready or 'migrate' in sys.argv or 'makemigrations' in sys.argv


# ---------------------------
# 🔁 Suivi des changements VAE
# ---------------------------

@receiver(pre_save, sender=VAE)
def track_vae_status_change(sender, instance, **kwargs):
    if skip_during_migrations() or not instance.pk:
        return

    try:
        old = VAE.objects.get(pk=instance.pk)
        instance._status_changed = old.statut != instance.statut
        instance._old_status = old.statut if instance._status_changed else None
    except VAE.DoesNotExist:
        instance._status_changed = False


@receiver(post_save, sender=VAE)
def create_vae_status_history(sender, instance, created, **kwargs):
    if skip_during_migrations():
        return

    try:
        if created:
            HistoriqueStatutVAE.objects.create(
                vae=instance,
                statut=instance.statut,
                date_changement_effectif=instance.created_at.date(),
                commentaire=f"Création de la VAE avec statut initial : {instance.get_statut_display()}"
            )
            LogUtilisateur.log_action(
                instance=instance,
                action="Création VAE",
                user=instance.created_by,
                details=f"Statut initial : {instance.get_statut_display()}"
            )
        elif getattr(instance, '_status_changed', False):
            HistoriqueStatutVAE.objects.create(
                vae=instance,
                statut=instance.statut,
                date_changement_effectif=timezone.now().date(),
                commentaire=f"Changement de statut : {dict(VAE.STATUT_CHOICES).get(instance._old_status)} → {instance.get_statut_display()}"
            )
            LogUtilisateur.log_action(
                instance=instance,
                action="Changement de statut VAE",
                user=instance.updated_by or instance.created_by,
                details=f"{dict(VAE.STATUT_CHOICES).get(instance._old_status)} → {instance.get_statut_display()}"
            )
            instance.invalidate_caches()
    except Exception as e:
        logger.error(f"❌ Erreur dans le signal VAE {getattr(instance, 'reference', instance.pk)} : {e}", exc_info=True)


# ---------------------------
# 📊 Log des suivis jury
# ---------------------------

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
            )
        )
        if hasattr(instance, 'invalidate_caches'):
            instance.invalidate_caches()
    except Exception as e:
        logger.warning(f"⚠️ [SuiviJury] Erreur de log : {e}", exc_info=True)
