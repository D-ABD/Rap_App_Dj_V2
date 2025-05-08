from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
import logging

from ..models.prepacomp import PrepaCompGlobal, Semaine
# from ..models.logs import LogUtilisateur  # Décommente si tu veux activer le log manuel

logger = logging.getLogger("application.prepacomp")


def recalculer_totaux(prepa: PrepaCompGlobal):
    """
    Recalcule tous les totaux de PrepaCompGlobal à partir des semaines associées.
    """
    qs = Semaine.objects.filter(centre=prepa.centre, annee=prepa.annee)
    agrégats = qs.aggregate(
        total_adh=Sum('nombre_adhesions'),
        total_pres=Sum('nombre_presents_ic'),
        total_presc=Sum('nombre_prescriptions'),
        total_places=Sum('nombre_places_ouvertes')
    )

    prepa.adhesions = agrégats['total_adh'] or 0
    prepa.total_presents = agrégats['total_pres'] or 0
    prepa.total_prescriptions = agrégats['total_presc'] or 0
    prepa.total_places_ouvertes = agrégats['total_places'] or 0
    prepa.save()

    logger.debug(f"✅ Totaux recalculés pour PrepaCompGlobal #{prepa.pk} ({prepa.annee})")

    # Facultatif : log utilisateur (activer si nécessaire)
    # LogUtilisateur.log_action(
    #     instance=prepa,
    #     action="Recalcul automatique",
    #     user=None,  # ou instance.updated_by si tu le veux
    #     details="Mise à jour des totaux suite à modification d’une semaine"
    # )


@receiver(post_save, sender=Semaine)
@receiver(post_delete, sender=Semaine)
def update_prepa_global(sender, instance, **kwargs):
    """
    Met à jour PrepaCompGlobal associé à chaque modification ou suppression de Semaine.
    """
    if not instance.centre or not instance.annee:
        return

    prepa, _ = PrepaCompGlobal.objects.get_or_create(
        centre=instance.centre,
        annee=instance.annee
    )
    recalculer_totaux(prepa)
