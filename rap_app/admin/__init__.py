"""
Importe les classes admin pour l'interface d'administration Django.
L'importation des classes admin enregistre automatiquement les modèles avec admin.site.
"""

from .centres_admin import CentreAdmin
from .statuts_admin import StatutAdmin
from .types_offre_admin import TypeOffreAdmin
from .formations_admin import FormationAdmin
from .commentaires_admin import CommentaireAdmin
from .partenaires_admin import PartenaireAdmin
from .evenements_admin import EvenementAdmin
from .documents_admin import DocumentAdmin
from .prospection_admin import ProspectionAdmin, HistoriqueProspection
from .prepa_admin import SemaineAdmin, PrepaCompGlobalAdmin  