import sys
import logging
from django.db import transaction
from django.utils.timezone import now
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps

from ..models.evenements import Evenement
from ..models.formations import Formation, HistoriqueFormation
from ..middleware import get_current_user  # ThreadLocalMiddleware pour récupérer l'utilisateur

logger = logging.getLogger("rap_app.evenements")


def skip_during_migrations() -> bool:
    """
    ⛔ Utilitaire pour éviter l'exécution des signaux pendant les migrations.
    """
    return not apps.ready or 'migrate' in sys.argv or 'makemigrations' in sys.argv


def get_user_from_instance(instance):
    """
    🔍 Récupère l'utilisateur à l'origine de la modification.
    """
    return getattr(instance, "updated_by", None) or getattr(instance, "created_by", None) or get_current_user()


def maj_nombre_evenements(formation: Formation, operation: str, user=None):
    """
    ⚙️ Met à jour `nombre_evenements` sur la formation et enregistre un historique.

    Args:
        formation (Formation): La formation concernée
        operation (str): Action effectuée ("créé", "modifié", "supprimé")
        user (User, optional): Utilisateur déclencheur
    """
    try:
        with transaction.atomic():
            nouveau_total = Evenement.objects.filter(formation=formation).count()
            ancien_total = Formation.objects.only("nombre_evenements").get(pk=formation.pk).nombre_evenements or 0

            if ancien_total != nouveau_total:
                Formation.objects.filter(pk=formation.pk).update(
                    nombre_evenements=nouveau_total,
                    updated_at=now()
                )

                logger.info(
                    f"🟢 MAJ nombre_evenements pour Formation #{formation.pk} : {ancien_total} → {nouveau_total} ({operation})"
                )

                HistoriqueFormation.objects.create(
                    formation=formation,
                    champ_modifie="nombre_evenements",
                    ancienne_valeur=str(ancien_total),
                    nouvelle_valeur=str(nouveau_total),
                    commentaire=f"Mise à jour auto via signal (événement {operation})",
                    created_by=user,
                )
            else:
                logger.debug(f"🔵 Aucun changement de nombre_evenements sur Formation #{formation.pk} ({nouveau_total})")

    except Exception as e:
        logger.error(
            f"❌ Erreur lors de la MAJ du nombre_evenements pour Formation #{formation.pk} : {str(e)}",
            exc_info=True
        )


@receiver(post_save, sender=Evenement)
def evenement_post_save(sender, instance, created, **kwargs):
    """
    📌 Signal `post_save` déclenché après la création/modification d'un événement.
    """
    if skip_during_migrations():
        return

    if not instance.formation_id:
        logger.debug("🔵 Événement sans formation associée (post_save)")
        return

    operation = "créé" if created else "modifié"
    user = get_user_from_instance(instance)
    maj_nombre_evenements(instance.formation, operation, user=user)


@receiver(post_delete, sender=Evenement)
def evenement_post_delete(sender, instance, **kwargs):
    """
    🗑️ Signal `post_delete` déclenché après la suppression d'un événement.
    """
    if skip_during_migrations():
        return

    if not instance.formation_id:
        logger.debug("🔵 Événement sans formation associée (post_delete)")
        return

    user = get_user_from_instance(instance)
    maj_nombre_evenements(instance.formation, "supprimé", user=user)
