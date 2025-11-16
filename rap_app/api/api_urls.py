# rap_app/api/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter

from .viewsets.stats_viewsets.prepa_stats_viewsets import PrepaStatsViewSet

from .viewsets.prepa_objectifs_viewsets import ObjectifPrepaViewSet

from .viewsets.declic_objectifs_viewsets import ObjectifDeclicViewSet


from .viewsets.stats_viewsets.declic_stats_viewsets import DeclicStatsViewSet

# 🔢 Imports des ViewSets existants
from .viewsets.stats_viewsets.prospection_comment_stats_viewset import ProspectionCommentStatsViewSet
from .viewsets.stats_viewsets.commentaires_stats_viewsets import CommentaireStatsViewSet
from .viewsets.stats_viewsets.atelier_tre_stats_viewset import AtelierTREStatsViewSet
from .viewsets.stats_viewsets.appairages_stats_viewsets import AppairageStatsViewSet
from .viewsets.stats_viewsets.partenaires_stats_viewsets import PartenaireStatsViewSet
from .viewsets.stats_viewsets.candidats_stats_viewsets import CandidatStatsViewSet
from .viewsets.stats_viewsets.prospection_stats_viewsets import ProspectionStatsViewSet
from .viewsets.stats_viewsets.formation_stats_viewsets import FormationStatsViewSet
from .viewsets.stats_viewsets.appairage_comment_stats_viewset import AppairageCommentaireStatsViewSet

# 📦 ViewSets métiers
from .viewsets.appairage_viewsets import AppairageViewSet
from .viewsets.appairage_commentaires_viewset import CommentaireAppairageViewSet
from .viewsets.atelier_tre_viewsets import AtelierTREViewSet
from .viewsets.auth_viewset import EmailTokenObtainPairView
from .viewsets.candidat_viewsets import CandidatViewSet
from .viewsets.centres_viewsets import CentreViewSet
from .viewsets.commentaires_viewsets import CommentaireViewSet
from .viewsets.documents_viewsets import DocumentViewSet
from .viewsets.evenements_viewsets import EvenementViewSet
from .viewsets.formations_viewsets import FormationViewSet
from .viewsets.login_logout_viewset import LoginAPIView, LogoutAPIView
from .viewsets.logs_viewsets import LogUtilisateurViewSet
from .viewsets.partenaires_viewsets import PartenaireViewSet
from .viewsets.prospection_viewsets import ProspectionViewSet
from .viewsets.prospection_comment_viewsets import ProspectionCommentViewSet
from .viewsets.rapports_viewsets import RapportViewSet
from .viewsets.search_viewset import SearchView
from .viewsets.statut_viewsets import StatutViewSet
from .viewsets.temporaire_viewset import test_token_view
from .viewsets.types_offre_viewsets import TypeOffreViewSet
from .viewsets.user_viewsets import CustomUserViewSet, RegisterView
from .viewsets.jury_viewsets import SuiviJuryViewSet
from .viewsets.vae_viewsets import VAEViewSet

# 👤 API "Me" et rôles
from .viewsets.me_viewsets import MeAPIView, RoleChoicesView

# 🧮 PrépaComp et Déclic
from .viewsets.prepa_viewset import PrepaViewSet
from .viewsets.declic_viewset import DeclicViewSet


# ───────────────────────────────────────────────
# Router principal
# ───────────────────────────────────────────────
router = DefaultRouter()

# 🔐 Auth & Users
urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("token/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("test-token/", test_token_view, name="test_token"),

    # Profil & rôles
    path("me/", MeAPIView.as_view(), name="me"),
    path("roles/", RoleChoicesView.as_view(), name="roles"),
]

# 👤 Utilisateurs
router.register(r'users', CustomUserViewSet, basename='user')

# 📌 Structures & Référentiels
router.register(r'centres', CentreViewSet, basename='centre')
router.register(r'statuts', StatutViewSet, basename='statut')
router.register(r'typeoffres', TypeOffreViewSet, basename='typeoffre')

# 📚 Formations & contenus associés
router.register(r'formations', FormationViewSet, basename='formation')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'evenements', EvenementViewSet, basename='evenement')
router.register(r'commentaires', CommentaireViewSet, basename='commentaire')

# 👥 Candidats & accompagnement
router.register(r'candidats', CandidatViewSet, basename='candidat')

# 🤝 Appairages
router.register(r'appairages', AppairageViewSet, basename='appairage')
router.register(r"appairage-commentaires", CommentaireAppairageViewSet, basename="appairage-commentaire")

# 🧑‍🏫 Ateliers TRE
router.register(r'ateliers-tre', AtelierTREViewSet, basename='ateliers-tre')

# 🧭 Prospection & partenaires
router.register(r'partenaires', PartenaireViewSet, basename='partenaire')
router.register(r'prospections', ProspectionViewSet, basename='prospection')
router.register(r"prospection-comments", ProspectionCommentViewSet, basename="prospection-comment")

# 🧾 Suivi jury & VAE
router.register(r'suivis-jury', SuiviJuryViewSet, basename='suivijury')
router.register(r'vaes', VAEViewSet, basename='vae')

# 📊 Prépa compétences
router.register(r'prepa', PrepaViewSet, basename='prepa')
router.register(r'prepa-objectifs', ObjectifPrepaViewSet, basename='objectif-prepa')
router.register(r"prepa-stats", PrepaStatsViewSet, basename="prepa-stats")

# 📊 Déclic
router.register(r'declic', DeclicViewSet, basename='declic')
# 🎯 Objectifs Déclic
router.register(r"objectifs-declic", ObjectifDeclicViewSet, basename="objectifs-declic")

# 🪵 Logs & rapports
router.register(r'logs', LogUtilisateurViewSet, basename='logutilisateur')
router.register(r'rapports', RapportViewSet, basename='rapport')

# 🔎 Recherche
urlpatterns += [
    path("search/", SearchView.as_view(), name="search"), 
]

# 📈 Statistiques / KPIs
router.register(r'formation-stats', FormationStatsViewSet, basename='formation-stats')
router.register(r'prospection-stats', ProspectionStatsViewSet, basename='prospection-stats')
router.register(r'candidat-stats', CandidatStatsViewSet, basename='candidat-stats')
router.register(r'partenaire-stats', PartenaireStatsViewSet, basename='partenaire-stats')
router.register(r"ateliertre-stats", AtelierTREStatsViewSet, basename="ateliertre-stats")
router.register(r'appairage-stats', AppairageStatsViewSet, basename='appairage-stats')
router.register(r"commentaire-stats", CommentaireStatsViewSet, basename="commentaire-stats")
router.register(r"prospection-comment-stats", ProspectionCommentStatsViewSet, basename="prospection-comment-stats")
router.register(r"appairage-commentaire-stats", AppairageCommentaireStatsViewSet, basename="appairage-commentaire-stats")
router.register(r"appairage-comment-stats", AppairageCommentaireStatsViewSet, basename="appairage-comment-stats")
router.register(r"declic-stats", DeclicStatsViewSet, basename="declic-stats") 


# 🔗 Ajout des routes REST
urlpatterns += router.urls
