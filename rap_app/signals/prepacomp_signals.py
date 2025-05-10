import logging
import sys
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import Sum
from django.db import transaction
from django.utils import timezone
from django.apps import apps

from ..models.prepacomp import PrepaCompGlobal, Semaine
from ..models.logs import LogUtilisateur

logger = logging.getLogger("rap_app.prepacomp")

def skip_during_migrations():
    return not apps.ready or 'migrate' in sys.argv or 'makemigrations' in sys.argv


def recalculer_totaux(prepa: PrepaCompGlobal):
    """
    Recalcule tous les totaux de PrepaCompGlobal à partir des semaines associées.
    """
    if skip_during_migrations():
        return False

    if not prepa.centre:
        logger.warning(f"[Signal] PrepaCompGlobal #{prepa.pk} sans centre associé")
        return False

    try:
        with transaction.atomic():
            qs = Semaine.objects.filter(centre=prepa.centre, annee=prepa.annee)

            if not qs.exists():
                logger.info(f"[Signal] Aucune semaine pour {prepa.centre.nom} en {prepa.annee} → remise à zéro")
                prepa.adhesions = 0
                prepa.total_presents = 0
                prepa.total_prescriptions = 0
                prepa.total_places_ouvertes = 0
                prepa.save(update_fields=[
                    'adhesions', 'total_presents', 'total_prescriptions', 'total_places_ouvertes'
                ])
                return True

            aggr = qs.aggregate(
                total_adh=Sum('nombre_adhesions'),
                total_pres=Sum('nombre_presents_ic'),
                total_presc=Sum('nombre_prescriptions'),
                total_places=Sum('nombre_places_ouvertes')
            )

            prepa.adhesions = aggr.get('total_adh') or 0
            prepa.total_presents = aggr.get('total_pres') or 0
            prepa.total_prescriptions = aggr.get('total_presc') or 0
            prepa.total_places_ouvertes = aggr.get('total_places') or 0

            prepa.save(update_fields=[
                'adhesions', 'total_presents', 'total_prescriptions', 'total_places_ouvertes'
            ])

            logger.info(
                f"[Signal] ✅ Totaux recalculés pour PrepaCompGlobal #{prepa.pk} : "
                f"{prepa.adhesions} adhésions, {prepa.total_presents} présents"
            )

            LogUtilisateur.log_action(
                instance=prepa,
                action="recalcul automatique",
                user=getattr(prepa, 'updated_by', None),
                details="Totaux mis à jour suite à modification d'une semaine"
            )

            return True

    except Exception as e:
        logger.error(f"[Signal] ❌ Erreur recalcul PrepaCompGlobal #{prepa.pk} : {e}", exc_info=True)
        return False


@receiver(post_save, sender=Semaine)
def update_prepa_global_on_semaine_save(sender, instance, created, **kwargs):
    if skip_during_migrations():
        return

    if not instance.centre or not instance.annee:
        return

    action = "créée" if created else "modifiée"
    logger.info(f"[Signal] Semaine {action} : {instance} → recalcul PrepaCompGlobal")

    try:
        prepa, is_new = PrepaCompGlobal.objects.get_or_create(
            centre=instance.centre,
            annee=instance.annee,
            defaults={
                'objectif_annuel_prepa': instance.objectif_annuel_prepa,
                'objectif_hebdomadaire_prepa': instance.objectif_hebdo_prepa,
            }
        )

        if is_new:
            logger.info(f"[Signal] 🎯 Nouveau PrepaCompGlobal créé pour {instance.centre.nom} - {instance.annee}")

        recalculer_totaux(prepa)

    except Exception as e:
        logger.error(f"[Signal] ❌ Erreur post_save semaine #{instance.pk} : {e}", exc_info=True)


@receiver(post_delete, sender=Semaine)
def update_prepa_global_on_semaine_delete(sender, instance, **kwargs):
    if skip_during_migrations():
        return

    if not instance.centre or not instance.annee:
        return

    logger.info(f"[Signal] Semaine supprimée : {instance} → recalcul PrepaCompGlobal")

    try:
        prepa = PrepaCompGlobal.objects.filter(
            centre=instance.centre,
            annee=instance.annee
        ).first()

        if not prepa:
            logger.warning(f"[Signal] Aucun PrepaCompGlobal trouvé pour {instance.centre.nom} - {instance.annee}")
            return

        recalculer_totaux(prepa)

    except Exception as e:
        logger.error(f"[Signal] ❌ Erreur post_delete semaine #{instance.pk} : {e}", exc_info=True)


@receiver(pre_save, sender=PrepaCompGlobal)
def sync_objectifs_to_semaines(sender, instance, **kwargs):
    if skip_during_migrations():
        return

    if not instance.pk or not instance.centre:
        return

    try:
        old_instance = PrepaCompGlobal.objects.get(pk=instance.pk)
        objectifs_changed = (
            old_instance.objectif_annuel_prepa != instance.objectif_annuel_prepa or
            old_instance.objectif_hebdomadaire_prepa != instance.objectif_hebdomadaire_prepa
        )

        if not objectifs_changed:
            logger.debug(f"[Signal] Aucun changement d’objectifs pour PrepaCompGlobal #{instance.pk}")
            return

        today = timezone.now().date()
        future_semaines = Semaine.objects.filter(
            centre=instance.centre,
            annee=instance.annee,
            date_debut_semaine__gte=today
        )

        if not future_semaines.exists():
            logger.debug(f"[Signal] Aucune semaine future à synchroniser pour {instance.centre.nom} - {instance.annee}")
            return

        count = future_semaines.update(
            objectif_annuel_prepa=instance.objectif_annuel_prepa,
            objectif_hebdo_prepa=instance.objectif_hebdomadaire_prepa
        )

        logger.info(f"[Signal] 🔁 Objectifs synchronisés sur {count} semaines futures de {instance.centre.nom} - {instance.annee}")

    except PrepaCompGlobal.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"[Signal] ❌ Erreur synchronisation objectifs PrepaCompGlobal : {e}", exc_info=True)
