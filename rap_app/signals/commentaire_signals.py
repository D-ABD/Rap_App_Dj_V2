import logging
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from ..models.commentaires import Commentaire
from ..models.formations import Formation

logger = logging.getLogger(__name__)

# ========================
# 📦 Fonctions métier
# ========================

def update_formation_stats_on_save(commentaire: Commentaire):
    """
    Met à jour la formation associée après la sauvegarde d'un commentaire :
    - Dernier commentaire
    - Saturation si fournie
    """
    try:
        with transaction.atomic():
            formation = commentaire.formation
            if not formation:
                return

            updates = {}
            if commentaire.saturation is not None:
                updates['saturation'] = commentaire.saturation
                logger.info(
                    f"⚙️ Saturation mise à jour sur formation #{formation.id} → {commentaire.saturation}%"
                )

            dernier = Commentaire.objects.filter(formation=formation).order_by('-created_at').first()
            if dernier:
                updates['dernier_commentaire'] = dernier.contenu

            if updates:
                Formation.objects.filter(id=formation.id).update(**updates)
                logger.debug(f"✅ Formation #{formation.id} mise à jour suite à post_save")
    except Exception as e:
        logger.error(f"❌ Erreur post_save Commentaire : {e}")


def update_formation_stats_on_delete(commentaire: Commentaire):
    """
    Met à jour la formation après suppression d’un commentaire :
    - Réinitialise le champ `dernier_commentaire`
    """
    try:
        with transaction.atomic():
            formation = commentaire.formation
            if not formation:
                return

            logger.info(f"🗑️ Commentaire supprimé, mise à jour formation #{formation.id}")

            dernier = Commentaire.objects.filter(formation=formation).order_by('-created_at').first()
            contenu = dernier.contenu if dernier else ""
            Formation.objects.filter(id=formation.id).update(dernier_commentaire=contenu)

            logger.debug(f"🔁 Dernier commentaire recalculé sur formation #{formation.id}")
    except Exception as e:
        logger.error(f"❌ Erreur post_delete Commentaire : {e}")

# ========================
# 🧩 Signaux
# ========================

@receiver(post_save, sender=Commentaire)
def commentaire_post_save(sender, instance, **kwargs):
    """
    Signal post_save pour les commentaires.
    """
    update_formation_stats_on_save(instance)


@receiver(post_delete, sender=Commentaire)
def commentaire_post_delete(sender, instance, **kwargs):
    """
    Signal post_delete pour les commentaires.
    """
    update_formation_stats_on_delete(instance)

