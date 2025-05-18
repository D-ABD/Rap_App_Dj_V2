from rest_framework.routers import DefaultRouter
from django.urls import path

from .viewsets.auth_viewset import EmailTokenObtainPairView
from .viewsets.temporaire_viewset import test_token_view
from .viewsets.rapports_viewsets import RapportViewSet  
from .viewsets.logs_viewsets import LogUtilisateurViewSet 
from .viewsets.prepacomp_viewsets import PrepaCompGlobalViewSet, SemaineViewSet
from .viewsets.vae_jury_viewsets import HistoriqueStatutVAEViewSet, SuiviJuryViewSet, VAEViewSet
from .viewsets.prospection_viewsets import HistoriqueProspectionViewSet, ProspectionViewSet
from .viewsets.partenaires_viewsets import PartenaireViewSet 
from .viewsets.commentaires_viewsets import CommentaireViewSet
from .viewsets.evenements_viewsets import EvenementViewSet 
from .viewsets.documents_viewsets import DocumentViewSet
from .viewsets.formations_viewsets import FormationViewSet
from .viewsets.types_offre_viewsets import TypeOffreViewSet
from .viewsets.statut_viewsets import StatutViewSet
from .viewsets.centres_viewsets import CentreViewSet
from .viewsets.user_viewsets import CustomUserViewSet 
from .viewsets.login_logout_viewset import LoginAPIView, LogoutAPIView

router = DefaultRouter()

# ViewSets
router.register(r'users', CustomUserViewSet, basename='user')

router.register(r"centres", CentreViewSet, basename="centre")

router.register(r'statuts', StatutViewSet, basename='statut')

router.register(r"typeoffres", TypeOffreViewSet, basename="typeoffre")

router.register(r'formations', FormationViewSet, basename='formation')

router.register(r"documents", DocumentViewSet, basename="document")

router.register(r"evenements", EvenementViewSet, basename="evenement")

router.register(r"commentaires", CommentaireViewSet, basename="commentaire")

router.register(r'partenaires', PartenaireViewSet, basename='partenaire')

router.register(r'prospections', ProspectionViewSet, basename='prospection')

router.register(r'historiques-prospection', HistoriqueProspectionViewSet, basename='historiqueprospection')

router.register(r'suivis-jury', SuiviJuryViewSet, basename='suivijury')

router.register(r'vaes', VAEViewSet, basename='vae')

router.register(r'historiques-vae', HistoriqueStatutVAEViewSet, basename='historiquestatutvae')

router.register("semaines", SemaineViewSet, basename="semaine")

router.register("prepa-globaux", PrepaCompGlobalViewSet, basename="prepa-global")

router.register("logs", LogUtilisateurViewSet, basename="logutilisateur")

router.register("rapports", RapportViewSet, basename="rapport")

# Autres endpoints manuels
urlpatterns = router.urls + [
    path('login/', LoginAPIView.as_view(), name='login'),

    path('token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('test-token/', test_token_view, name='test_token'),
    
    # path("users/me/profile/", MeAPIView.as_view(), name="me-profile"),  # ❌ on le retire si on garde l’action `me` dans ViewSet
]
