from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.timezone import now
import logging

from ..models.evenements import Evenement
from ..models.formations import Formation, HistoriqueFormation

logger = logging.getLogger("application.evenements")


@receiver(post_save, sender=Evenement)
@receiver(post_delete, sender=Evenement)
def update_nombre_evenements(sender, instance, **kwargs):
    """
    🔁 Met à jour automatiquement le champ `nombre_evenements` de la formation liée.
    Crée également une entrée d'historique si le compteur est modifié.
    """
    formation = instance.formation
    if not formation:
        return

    try:
        nouveau_total = Evenement.objects.filter(formation=formation).count()
        formation_ref = Formation.objects.only("nombre_evenements").get(pk=formation.pk)

        if formation_ref.nombre_evenements != nouveau_total:
            Formation.objects.filter(pk=formation.pk).update(nombre_evenements=nouveau_total)
            logger.info(f"🟢 MAJ nombre_evenements pour Formation #{formation.pk} : {nouveau_total}")

            # Journalisation dans l'historique
            HistoriqueFormation.objects.create(
                formation=formation,
                champ_modifie="nombre_evenements",
                ancienne_valeur=str(formation_ref.nombre_evenements),
                nouvelle_valeur=str(nouveau_total),
                commentaire="Mise à jour automatique du compteur d'événements via signal",
                created_by=getattr(instance, "created_by", None)
            )
    except Exception as e:
        logger.error(f"❌ Erreur lors de la mise à jour du compteur d'événements pour Formation #{formation.pk}", exc_info=True)
