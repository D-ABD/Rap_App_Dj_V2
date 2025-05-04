# urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter

from .viewsets.auth_viewset import EmailTokenObtainPairView
from .viewsets.login_logout_viewset import LoginAPIView, LogoutAPIView
from .viewsets.me_viewset import me_view
from .viewsets.temporaire_viewset import test_token_view
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .viewsets.user_profile_viewsets import UserViewSet

from ..api.viewsets.centres_viewsets import CentreViewSet
from ..api.viewsets.commentaires_viewsets import CommentaireViewSet
from ..api.viewsets.company_viewsets import CompanyViewSet
from ..api.viewsets.documents_viewsets import DocumentViewSet
from ..api.viewsets.evenements_viewsets import EvenementViewSet
from ..api.viewsets.formations_viewsets import FormationViewSet
from ..api.viewsets.logs_viewsets import LogUtilisateurViewSet
from ..api.viewsets.partenaires_viewsets import PartenaireViewSet
from ..api.viewsets.prepacomp_viewsets import PrepaCompGlobalViewSet, SemaineViewSet
from ..api.viewsets.prospection_viewsets import HistoriqueProspectionViewSet, ProspectionViewSet
from ..api.viewsets.rapports_viewsets import RapportViewSet
from ..api.viewsets.statut_viewsets import StatutViewSet
from ..api.viewsets.types_offre_viewsets import TypeOffreViewSet
from ..api.viewsets.vae_jury_viewsets import HistoriqueStatutVAEViewSet, SuiviJuryViewSet, VAEViewSet


router = DefaultRouter()
 
router.register(r'centres', CentreViewSet, basename='centre')

router.register(r'commentaires', CommentaireViewSet, basename='commentaire')

router.register(r'companies', CompanyViewSet, basename='company')

router.register(r'documents', DocumentViewSet, basename='document')

router.register(r'evenements', EvenementViewSet, basename='evenement')

router.register(r'formations', FormationViewSet, basename='formation')

router.register(r'logs-utilisateurs', LogUtilisateurViewSet, basename='log-utilisateur')

router.register(r'partenaires', PartenaireViewSet, basename='partenaire')

router.register(r'semaine', SemaineViewSet, basename="semaine")

router.register(r'prepacompglobal', PrepaCompGlobalViewSet, basename="prepacompglobal")

router.register(r'prospections', ProspectionViewSet, basename='prospection')

router.register(r'historique-prospections', HistoriqueProspectionViewSet, basename='historique-prospection')

router.register(r'rapports', RapportViewSet, basename='rapport')

router.register(r'statuts', StatutViewSet, basename='statut')

router.register(r"type-offres", TypeOffreViewSet, basename="type-offre")

router.register(r'suivis-jury', SuiviJuryViewSet, basename='suivijury')

router.register(r'vae', VAEViewSet, basename='vae')

router.register(r'historiques-vae', HistoriqueStatutVAEViewSet, basename='historiquevae') 

router.register(r'users', UserViewSet, basename='user')

urlpatterns = router.urls + [
    path('token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('login/', LoginAPIView.as_view(), name='api_login'),
    path('logout/', LogoutAPIView.as_view(), name='api_logout'),

    path('api/me/', me_view, name='me'),
    path('test-token/', test_token_view),


]