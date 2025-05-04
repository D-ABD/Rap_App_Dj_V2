from rap_app.models.logs import LogUtilisateur

def log_action(utilisateur, instance, action, details=None):
    LogUtilisateur.objects.create(
        utilisateur=utilisateur,
        modele=instance.__class__.__name__,
        object_id=instance.id,
        action=action,
        details=details
    )
