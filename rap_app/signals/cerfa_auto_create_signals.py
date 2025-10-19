import os
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from rap_app.models import Candidat, CerfaContrat
from rap_app.utils.pdf_cerfa_utils import generer_pdf_cerfa

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Candidat)
def create_cerfa_simplifie_for_candidat(sender, instance, created, **kwargs):
    """
    🧩 Version simplifiée du signal CERFA :
    - Crée un CERFA basique à la création du candidat (sans clé étrangère).
    - Remplit quelques champs pour test PDF.
    - Génère un PDF si possible.
    """

    try:
        if not created:
            return  # on ne fait rien à la mise à jour

        # Vérifie s’il existe déjà un CERFA avec le même nom/prénom
        existing = CerfaContrat.objects.filter(
            apprenti_nom_naissance=instance.nom_naissance or instance.nom,
            apprenti_prenom=instance.prenom,
        ).first()
        if existing:
            logger.info(f"🟡 CERFA déjà existant pour {instance.nom} (ID {existing.id})")
            return

        # Crée un CERFA simplifié
        cerfa = CerfaContrat.objects.create(
            auto_generated=True,
            apprenti_nom_naissance=instance.nom_naissance or instance.nom,
            apprenti_prenom=instance.prenom,
            apprenti_email=instance.email,
            apprenti_code_postal=getattr(instance, "code_postal", None),
            apprenti_commune=getattr(instance, "ville", None),
            employeur_nom="Employeur de test",
            employeur_commune="Ville de test",
            type_contrat="Apprentissage",
        )

        logger.info(f"✅ CERFA simplifié créé pour {instance.nom} (ID {cerfa.id})")

        # Tente de générer le PDF (si ton utilitaire est fonctionnel)
        try:
            pdf_path = generer_pdf_cerfa(cerfa)
            rel_path = os.path.relpath(pdf_path, start=settings.MEDIA_ROOT)
            cerfa.pdf_fichier.name = rel_path
            cerfa.save(update_fields=["pdf_fichier"])
            logger.info(f"🧾 PDF généré automatiquement pour {instance.nom} (CERFA {cerfa.id})")
        except Exception as pdf_error:
            logger.warning(f"⚠️ CERFA créé mais PDF non généré : {pdf_error}")

    except Exception as e:
        logger.error(f"❌ Erreur signal CERFA simplifié pour {instance}: {e}", exc_info=True)
