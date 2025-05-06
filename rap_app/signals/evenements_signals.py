from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now
from ..models.logs import LogUtilisateur
import logging
from ..models.evenements import Evenement
from ..models.formations import Formation
from ..models.logs import LogUtilisateur
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Evenement)
@receiver(post_delete, sender=Evenement)
def update_nombre_evenements(sender, instance, **kwargs):
    """Met à jour automatiquement le compteur d'événements dans la formation associée."""
    if instance.formation:
        try:
            count = Evenement.objects.filter(formation=instance.formation).count()
            Formation.objects.filter(pk=instance.formation.pk).update(nombre_evenements=count)
            logger.debug(f"Compteur MAJ pour Formation #{instance.formation.pk} : {count}")
        except Exception as e:
            logger.error(f"Erreur MAJ compteur événements : {e}", exc_info=True)
