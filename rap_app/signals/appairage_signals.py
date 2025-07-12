from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils.timezone import now
from ..models.appairage import Appairage, AppairageStatut, Candidat
from ..models.candidat import Candidat, HistoriquePlacement

@receiver(post_save, sender=Appairage)
def sync_appairage_to_candidat(sender, instance: Appairage, created: bool, **kwargs):
    candidat = instance.candidat

    if instance.statut == AppairageStatut.ACCEPTE:
        # Si appairage accepté → on remplit les champs placement du candidat
        if not candidat.entreprise_placement:
            candidat.entreprise_placement = instance.partenaire
            candidat.date_placement = instance.date_appairage.date()
            resultat=instance.statut if instance.statut in [
                AppairageStatut.ACCEPTE,
                AppairageStatut.REFUSE,
                AppairageStatut.ANNULE,
                AppairageStatut.EN_ATTENTE,
                AppairageStatut.TRANSMIS
            ] else "autre",
            if hasattr(instance, "_user"):
                candidat.responsable_placement = instance._user
            candidat.save()

            # Ajout à l'historique
            HistoriquePlacement.objects.get_or_create(
                candidat=candidat,
                date=instance.date_appairage.date(),
                entreprise=instance.partenaire,
                resultat="admis",
                defaults={"responsable": getattr(instance, "_user", None)},
            )

    elif not created and instance.statut != AppairageStatut.ACCEPTE:
        # Si l'appairage était lié au placement en cours, on le retire
        if candidat.entreprise_placement == instance.partenaire:
            candidat.entreprise_placement = None
            candidat.resultat_placement = None
            candidat.date_placement = None
            candidat.save()


@receiver(post_delete, sender=Appairage)
def unsync_appairage_from_candidat(sender, instance: Appairage, **kwargs):
    candidat = instance.candidat
    if candidat.entreprise_placement == instance.partenaire:
        candidat.entreprise_placement = None
        candidat.resultat_placement = None
        candidat.date_placement = None
        candidat.save()


@receiver(pre_save, sender=Candidat)
def sync_candidat_to_appairage(sender, instance: Candidat, **kwargs):
    if not instance.pk:
        return  # Nouveau candidat, pas de sync à faire

    original = Candidat.objects.filter(pk=instance.pk).first()
    if not original:
        return

    # Si changement de partenaire de placement, on met à jour l’appairage associé s’il existe
    if instance.entreprise_placement and instance.entreprise_placement != original.entreprise_placement:
        appairage = Appairage.objects.filter(
            candidat=instance,
            partenaire=instance.entreprise_placement,
            statut__in=[AppairageStatut.TRANSMIS, AppairageStatut.EN_ATTENTE],
        ).first()
        if appairage:
            appairage.statut = AppairageStatut.ACCEPTE
            appairage.save()
