# models/__init__.py

# Modèles principaux
from .base import BaseModel
from .centres import Centre
from .statut import Statut
from .types_offre import TypeOffre
from .formations import Formation, FormationManager, HistoriqueFormation
from .commentaires import Commentaire
from .evenements import Evenement
from .documents import Document
from .partenaires import Partenaire
from .rapports import Rapport
from .prospection import Prospection, HistoriqueProspection
from .prepacomp import Semaine, PrepaCompGlobal
from .vae_jury import VAE, SuiviJury, HistoriqueStatutVAE
from .logs import LogUtilisateur
from .custom_user import CustomUser
from .models_test import DummyModel
from .candidat import Candidat
from .appairage import Appairage, HistoriqueAppairage
from .atelier_tre import AtelierTRE

__all__ = ['CustomUser']  # Important pour l'importation

default_app_config = "rap_app.apps.RapAppConfig"


# ✅ Import des fichiers contenant des signaux (obligatoire pour qu'ils soient déclenchés)
from . import (
    centres,
    commentaires,
    documents,
    evenements,
    formations,
    logs,
    partenaires,
    prepacomp,
    prospection,
    rapports,
    statut,
    types_offre,
    custom_user,
    vae_jury,
    candidat,
    appairage,
    atelier_tre,
    
)
