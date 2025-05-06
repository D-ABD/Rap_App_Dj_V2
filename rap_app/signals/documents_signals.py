from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from ..models.documents import Document, log_action

@receiver(post_save, sender=Document)
def log_document_save(sender, instance, created, **kwargs):
    """
    Enregistre une action de création ou de mise à jour d’un document dans les logs utilisateurs.
    """
    action = "Création" if created else "Mise à jour"
    log_action(
        instance=instance,
        action=action,
        user=instance.utilisateur,
        details=f"{action} du document : {instance.nom_fichier}"
    )

@receiver(post_delete, sender=Document)
def log_document_delete(sender, instance, **kwargs):
    """
    Enregistre une action de suppression d’un document dans les logs utilisateurs.
    """
    log_action(
        instance=instance,
        action="Suppression",
        user=instance.utilisateur,
        details=f"Suppression du document : {instance.nom_fichier}"
    )
