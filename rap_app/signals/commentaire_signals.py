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
    - Statistiques calculées (saturation moyenne, nombre de commentaires)
    
    Args:
        commentaire (Commentaire): L'instance de commentaire sauvegardée
    """
    try:
        with transaction.atomic():
            formation = commentaire.formation
            if not formation:
                return

            updates = {}
            
            # Mise à jour de la saturation si fournie
            if commentaire.saturation is not None:
                updates['saturation'] = commentaire.saturation
                logger.info(
                    f"⚙️ Saturation mise à jour sur formation #{formation.id} → {commentaire.saturation}%"
                )
            
            # Récupération du dernier commentaire
            dernier = Commentaire.objects.filter(formation=formation).order_by('-created_at').first()
            if dernier:
                updates['dernier_commentaire'] = dernier.contenu
            
            # Calcul de la saturation moyenne si le champ existe
            if hasattr(formation, 'saturation_moyenne'):
                from django.db.models import Avg
                saturation_avg = (
                    Commentaire.objects.filter(
                        formation=formation, 
                        saturation__isnull=False
                    ).aggregate(Avg('saturation')).get('saturation__avg')
                )
                updates['saturation_moyenne'] = saturation_avg
                logger.info(f"📊 Saturation moyenne calculée: {saturation_avg}%")
            
            # Mise à jour du nombre de commentaires si le champ existe
            if hasattr(formation, 'nb_commentaires'):
                nb_commentaires = Commentaire.objects.filter(formation=formation).count()
                updates['nb_commentaires'] = nb_commentaires
                logger.info(f"🔢 Nombre de commentaires mis à jour: {nb_commentaires}")

            # Application des mises à jour
            if updates:
                Formation.objects.filter(id=formation.id).update(**updates)
                logger.debug(f"✅ Formation #{formation.id} mise à jour suite à post_save")
    except Exception as e:
        logger.error(f"❌ Erreur post_save Commentaire : {e}", exc_info=True)


def update_formation_stats_on_delete(commentaire: Commentaire):
    """
    Met à jour la formation après suppression d'un commentaire :
    - Réinitialise le champ `dernier_commentaire`
    - Recalcule les statistiques (saturation moyenne, nombre de commentaires)
    
    Args:
        commentaire (Commentaire): L'instance de commentaire supprimée
    """
    try:
        with transaction.atomic():
            formation = commentaire.formation
            if not formation:
                return

            logger.info(f"🗑️ Commentaire supprimé, mise à jour formation #{formation.id}")

            updates = {}
            
            # Mise à jour du dernier commentaire
            dernier = Commentaire.objects.filter(formation=formation).order_by('-created_at').first()
            contenu = dernier.contenu if dernier else ""
            updates['dernier_commentaire'] = contenu

            # Recalcul de la saturation moyenne si le champ existe
            if hasattr(formation, 'saturation_moyenne'):
                from django.db.models import Avg
                saturation_avg = (
                    Commentaire.objects.filter(
                        formation=formation, 
                        saturation__isnull=False
                    ).aggregate(Avg('saturation')).get('saturation__avg')
                )
                updates['saturation_moyenne'] = saturation_avg
                logger.info(f"📊 Saturation moyenne recalculée: {saturation_avg}%")
            
            # Mise à jour du nombre de commentaires si le champ existe
            if hasattr(formation, 'nb_commentaires'):
                nb_commentaires = Commentaire.objects.filter(formation=formation).count()
                updates['nb_commentaires'] = nb_commentaires
                logger.info(f"🔢 Nombre de commentaires mis à jour: {nb_commentaires}")
            
            # Application des mises à jour
            Formation.objects.filter(id=formation.id).update(**updates)
            logger.debug(f"🔁 Statistiques recalculées sur formation #{formation.id}")
    except Exception as e:
        logger.error(f"❌ Erreur post_delete Commentaire : {e}", exc_info=True)

# ========================
# 🧩 Signaux
# ========================

@receiver(post_save, sender=Commentaire)
def commentaire_post_save(sender, instance, created, **kwargs):
    """
    Signal post_save pour les commentaires.
    Met à jour les statistiques de la formation associée.
    
    Args:
        sender: Classe du modèle envoyant le signal
        instance (Commentaire): Instance du commentaire sauvegardé
        created (bool): True si création, False si modification
    """
    action = "créé" if created else "modifié"
    logger.debug(f"[Signal] Commentaire #{instance.pk} {action} pour formation #{instance.formation_id}")
    update_formation_stats_on_save(instance)


@receiver(post_delete, sender=Commentaire)
def commentaire_post_delete(sender, instance, **kwargs):
    """
    Signal post_delete pour les commentaires.
    Met à jour les statistiques de la formation après suppression.
    
    Args:
        sender: Classe du modèle envoyant le signal
        instance (Commentaire): Instance du commentaire supprimé
    """
    logger.debug(f"[Signal] Commentaire #{instance.pk} supprimé de formation #{instance.formation_id}")
    update_formation_stats_on_delete(instance)