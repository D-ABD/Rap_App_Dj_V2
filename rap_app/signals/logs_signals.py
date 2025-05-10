
# signals/logs.py - Version améliorée
import logging
import sys
from django.conf import settings
from django.db.models.signals import post_save, post_delete  # Un seul import
from django.dispatch import receiver
from django.apps import apps

from ..models.logs import LogUtilisateur

logger = logging.getLogger(__name__)

# Modèles et applications à exclure par défaut
EXCLUDED_MODELS = [
    'LogUtilisateur', 'LogEntry', 'Permission', 'Group', 
    'ContentType', 'Session'
]
EXCLUDED_APPS = ['admin', 'contenttypes', 'sessions', 'auth']


def skip_logging() -> bool:
    """Détermine si la journalisation doit être ignorée (migrations, tests, etc.)"""
    if not apps.ready or 'migrate' in sys.argv or 'test' in sys.argv:
        return True
        
    return getattr(settings, 'DISABLE_MODEL_LOGS', False)


def should_log_model(instance) -> bool:
    """Vérifie si le modèle doit être loggué selon la configuration."""
    # Ignorer certains modèles de base
    model_name = instance.__class__.__name__
    app_label = instance._meta.app_label
    model_path = f"{app_label}.{model_name}"
    
    if model_name in EXCLUDED_MODELS or app_label in EXCLUDED_APPS:
        return False
        
    # Vérifier les exclusions dans les paramètres
    excluded = getattr(settings, 'LOG_EXCLUDED_MODELS', [])
    if model_path in excluded:
        return False
        
    # Si une whitelist est définie, n'autoriser que ces modèles
    whitelist = getattr(settings, 'LOG_MODELS', None)
    if whitelist and model_path not in whitelist:
        return False
        
    return True


def get_user(instance, kwargs):
    """Récupère l'utilisateur associé à l'action."""
    return (
        kwargs.get('user') or 
        getattr(instance, '_user', None) or
        getattr(instance, 'updated_by', None) or
        getattr(instance, 'created_by', None)
    )


@receiver(post_save)
def log_save(sender, instance, created, **kwargs):
    """Log automatique des créations et modifications."""
    if skip_logging() or not should_log_model(instance):
        return

    try:
        # Définir l'action avant d'entrer dans le bloc qui pourrait échouer
        action = LogUtilisateur.ACTION_CREATE if created else LogUtilisateur.ACTION_UPDATE
        user = get_user(instance, kwargs)

        # Message détaillé pour l'audit
        if created:
            details = f"Création de {instance.__class__.__name__} #{instance.pk}"
        elif hasattr(instance, 'get_changed_fields') and callable(instance.get_changed_fields):
            # Support pour les modèles avec tracking de changements
            changes = instance.get_changed_fields()
            if changes:
                changed_fields = ', '.join(changes.keys())
                details = f"Champs modifiés: {changed_fields}"
            else:
                details = f"Modification de {instance.__class__.__name__} #{instance.pk} (aucun changement détecté)"
        else:
            details = f"Modification de {instance.__class__.__name__} #{instance.pk}"

        # Utilisation correcte du manager (objects)
        LogUtilisateur.objects.log_action(
            instance=instance,
            action=action,
            user=user,
            details=details
        )
    except Exception as e:
        # Référence sécurisée à action
        current_action = action if 'action' in locals() else 'inconnue'
        logger.error(f"Erreur de log ({current_action}): {e}", exc_info=True)


@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    """Log automatique des suppressions."""
    if skip_logging() or not should_log_model(instance):
        return

    try:
        user = get_user(instance, kwargs)
        details = f"Suppression de {instance.__class__.__name__} #{instance.pk}: {str(instance)}"

        # Utilisation correcte du manager (objects)
        LogUtilisateur.objects.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_DELETE,
            user=user,
            details=details
        )
    except Exception as e:
        logger.error(f"Erreur de log (suppression): {e}", exc_info=True)


def setup_log_signals():
    """Configure les signaux selon les paramètres.
    À appeler dans AppConfig.ready()"""
    
    # Désactivation explicite des signaux existants pour éviter les doublons
    try:
        post_save.disconnect(log_save)
        post_delete.disconnect(log_delete)
    except Exception:
        # Les signaux n'étaient peut-être pas encore connectés, ignorer l'erreur
        pass
    
    # Si la journalisation est désactivée, on s'arrête là
    if getattr(settings, 'DISABLE_MODEL_LOGS', False):
        logger.info("Système de logs utilisateur désactivé")
        return
        
    # Mode sélectif basé sur LOG_MODELS
    log_models = getattr(settings, 'LOG_MODELS', [])
    
    if not log_models:
        # Mode global: connexion pour tous les modèles (filtrés par should_log_model)
        logger.info("Système de logs utilisateur activé (mode global)")
        post_save.connect(log_save)
        post_delete.connect(log_delete)
        return
        
    # Mode sélectif: uniquement les modèles listés dans LOG_MODELS
    for model_path in log_models:
        try:
            app_label, model_name = model_path.split('.')
            model = apps.get_model(app_label, model_name)
            
            post_save.connect(log_save, sender=model)
            post_delete.connect(log_delete, sender=model)
            
            logger.info(f"Logs activés pour {model_path}")
        except Exception as e:
            logger.error(f"Erreur config logs pour {model_path}: {e}")