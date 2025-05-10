import logging
import sys
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.apps import apps

from ..models.vae_jury import VAE, HistoriqueStatutVAE, SuiviJury
from ..models.prepacomp import Semaine
from ..models.logs import LogUtilisateur

logger = logging.getLogger("rap_app.vae")


def skip_during_migrations():
    return not apps.ready or 'migrate' in sys.argv or 'makemigrations' in sys.argv


# ==============================
# 🔄 Suivi des changements de statut VAE
# ==============================

@receiver(pre_save, sender=VAE)
def track_vae_status_change(sender, instance, **kwargs):
    if skip_during_migrations():
        return

    if not instance.pk:
        return

    try:
        old_instance = VAE.objects.get(pk=instance.pk)
        instance._status_changed = old_instance.statut != instance.statut
        instance._old_status = old_instance.statut if instance._status_changed else None
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
                date_changement_effectif=instance.created_at,
                commentaire=f"Création de la VAE avec statut initial : {instance.get_statut_display()}"
            )
            logger.info(f"[Signal] Historique initial créé pour VAE {instance.reference}")

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
            logger.info(f"[Signal] Changement de statut enregistré pour VAE {instance.reference}")

            LogUtilisateur.log_action(
                instance=instance,
                action="Changement de statut VAE",
                user=instance.updated_by or instance.created_by,
                details=f"{dict(VAE.STATUT_CHOICES).get(instance._old_status)} → {instance.get_statut_display()}"
            )

            if hasattr(instance, "invalidate_caches"):
                instance.invalidate_caches()

    except Exception as e:
        logger.error(f"[Signal] Erreur VAE {getattr(instance, 'reference', instance.pk)} : {e}", exc_info=True)


# ==============================
# 📅 Semaine : log d'activité
# ==============================

@receiver(post_save, sender=Semaine)
def log_semaine_save(sender, instance, created, **kwargs):
    if skip_during_migrations():
        return

    try:
        LogUtilisateur.log_action(
            instance=instance,
            action="Création" if created else "Mise à jour",
            user=instance.updated_by or instance.created_by,
            details=f"Semaine enregistrée pour {instance.centre} – {instance.get_periode_display()}"
        )
        if hasattr(instance, "invalidate_caches"):
            instance.invalidate_caches()
    except Exception as e:
        logger.warning(f"[Signal] Échec journalisation Semaine #{instance.pk} : {e}", exc_info=True)


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
            )
        )
        if hasattr(instance, "invalidate_caches"):
            instance.invalidate_caches()
    except Exception as e:
        logger.warning(f"[Signal] Échec journalisation SuiviJury #{instance.pk} : {e}", exc_info=True)
