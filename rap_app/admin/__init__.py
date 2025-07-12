"""
Initialisation du module d'administration Django.

Ce fichier importe tous les sous-modules de l'administration
afin d'enregistrer tous les ModelAdmin automatiquement.
"""
from .base_admin import *
from .centres_admin import *
from .commentaires_admin import *
from .documents_admin import *
from .evenements_admin import *
from .formations_admin import *
from .logs_admin import *
from .partenaires_admin import *
from .prepa_admin import *
from .prospection_admin import *
from .rapports_admin import *
from .statuts_admin import *
from .types_offre_admin import *
from .user_admin import *
from .vae_jury_admin import *
from .appairage_admin import *
from .atelier_tre_admin import *
from .atelier_tre_admin import ParticipationAtelierTREInline
from .candidat_admin import *
