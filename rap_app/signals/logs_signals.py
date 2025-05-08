from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings

from ..models.logs import LogUtilisateur


def is_loggable(instance):
    """
    Détermine si l'instance doit être loguée.
    Exclut certains modèles internes ou techniques.
    """
    if isinstance(instance, LogUtilisateur):
        return False
    if instance._meta.app_label in ['admin', 'contenttypes', 'sessions']:
        return False
    return True


@receiver(post_save)
def log_post_save(sender, instance, created, **kwargs):
    """
    Log les créations ou modifications.
    """
    if not is_loggable(instance):
        return

    action = "Création" if created else "Mise à jour"
    try:
        LogUtilisateur.log_action(instance, action)  # ✅ méthode de classe
    except Exception as e:
        if getattr(settings, "DEBUG", False):
            print(f"[log_post_save] Erreur : {e}")


@receiver(post_delete)
def log_post_delete(sender, instance, **kwargs):
    """
    Log les suppressions.
    """
    if not is_loggable(instance):
        return

    try:
        LogUtilisateur.log_action(instance, "Suppression")  # ✅ méthode de classe
    except Exception as e:
        if getattr(settings, "DEBUG", False):
            print(f"[log_post_delete] Erreur : {e}")
