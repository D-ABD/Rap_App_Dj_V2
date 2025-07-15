from django.urls import path
from rest_framework.routers import DefaultRouter

# ViewSets
from .viewsets.appairage_viewsets import AppairageViewSet, HistoriqueAppairageViewSet
from .viewsets.atelier_tre_viewsets import AtelierTREViewSet, ParticipationAtelierTREViewSet
from .viewsets.auth_viewset import EmailTokenObtainPairView
from .viewsets.candidat_viewsets import CandidatViewSet, HistoriquePlacementViewSet
from .viewsets.centres_viewsets import CentreViewSet
from .viewsets.commentaires_viewsets import CommentaireViewSet
from .viewsets.documents_viewsets import DocumentViewSet
from .viewsets.evenements_viewsets import EvenementViewSet
from .viewsets.formations_viewsets import FormationViewSet, HistoriqueFormationGroupedView, HistoriqueFormationViewSet
from .viewsets.login_logout_viewset import LoginAPIView, LogoutAPIView
from .viewsets.logs_viewsets import LogUtilisateurViewSet
from .viewsets.partenaires_viewsets import PartenaireViewSet
from .viewsets.prepacomp_viewsets import PrepaCompGlobalViewSet, SemaineViewSet
from .viewsets.prospection_viewsets import HistoriqueProspectionViewSet, ProspectionViewSet
from .viewsets.rapports_viewsets import RapportViewSet
from .viewsets.search_viewset import SearchView
from .viewsets.statut_viewsets import StatutViewSet
from .viewsets.temporaire_viewset import test_token_view
from .viewsets.types_offre_viewsets import TypeOffreViewSet
from .viewsets.user_viewsets import CustomUserViewSet, RegisterView
from .viewsets.vae_jury_viewsets import HistoriqueStatutVAEViewSet, SuiviJuryViewSet, VAEViewSet

# Router
router = DefaultRouter()

# 🔐 Auth & Users
urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("token/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("test-token/", test_token_view, name="test_token"),
    path('formations/historique/grouped/', HistoriqueFormationGroupedView.as_view(), name='historique-grouped'),

]
router.register(r'users', CustomUserViewSet, basename='user')

# 📌 Structures & Référentiels
router.register(r'centres', CentreViewSet, basename='centre')
router.register(r'statuts', StatutViewSet, basename='statut')
router.register(r'typeoffres', TypeOffreViewSet, basename='typeoffre')

# 📚 Formations & contenus associés
router.register(r'formations', FormationViewSet, basename='formation')
router.register(r'historiques', HistoriqueFormationViewSet, basename='historiques')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'evenements', EvenementViewSet, basename='evenement')
router.register(r'commentaires', CommentaireViewSet, basename='commentaire')

# 👥 Candidats & accompagnement
router.register(r'candidats', CandidatViewSet, basename='candidat')
router.register(r'historiques-placements', HistoriquePlacementViewSet, basename='historiqueplacement')

# 🤝 Appairages
router.register(r'appairages', AppairageViewSet, basename='appairage')
router.register(r'historiques-appairages', HistoriqueAppairageViewSet, basename='historique-appairage')

# 🧑‍🏫 Ateliers TRE
router.register(r'atelierstre', AtelierTREViewSet, basename='atelierstre')
router.register(r'participations-atelierstre', ParticipationAtelierTREViewSet, basename='participations-atelierstre')

# 🧭 Prospection & partenaires
router.register(r'partenaires', PartenaireViewSet, basename='partenaire')
router.register(r'prospections', ProspectionViewSet, basename='prospection')
router.register(r'historiques-prospection', HistoriqueProspectionViewSet, basename='historiqueprospection')

# 🧾 Suivi jury & VAE
router.register(r'suivis-jury', SuiviJuryViewSet, basename='suivijury')
router.register(r'vaes', VAEViewSet, basename='vae')
router.register(r'historiques-vae', HistoriqueStatutVAEViewSet, basename='historiquestatutvae')

# 📊 Prépa compétences
router.register(r'semaines', SemaineViewSet, basename='semaine')
router.register(r'prepa-globaux', PrepaCompGlobalViewSet, basename='prepa-global')

# 🪵 Logs & rapports
router.register(r'logs', LogUtilisateurViewSet, basename='logutilisateur')
router.register(r'rapports', RapportViewSet, basename='rapport')

# 🔎 Recherche
urlpatterns += [
    path("search/", SearchView.as_view(), name="search"),
]

# 🔗 Ajout des routes REST
urlpatterns += router.urls
