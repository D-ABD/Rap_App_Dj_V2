from django.urls import path

from .views.vae_jury_views import (HistoriqueStatutCreateView, ObjectifCentreUpdateView, SuiviJuryCreateView, SuiviJuryDeleteView, SuiviJuryDetailView, 
                                   SuiviJuryListView, SuiviJuryUpdateView, VAECreateView, VAEDeleteView, 
                                   VAEDetailView, VAEListView, VAEUpdateView, api_jurys_data, api_vae_data, modifier_objectifs_tous_centres, vae_jury_dashboard, vae_jury_home)

from .views.prepa_views import (PrepaGlobalCreateView, PrepaGlobalDetailView, PrepaGlobalListView, 
                                PrepaHomeView, PrepaObjectifsView,  
                                PrepaSemaineCreateView, PrepaSemaineDeleteView, PrepaSemaineDetailView, 
                                PrepaSemaineListView, PrepaSemaineUpdateView )


from . import views

from .views.historique_formation_views import HistoriqueFormationDeleteView, HistoriqueFormationDetailView, HistoriqueFormationListView

from .views.prospection_views import HistoriqueProspectionDetailView, HistoriqueProspectionListView, ProspectionCreateView, ProspectionDeleteView, ProspectionDetailView, ProspectionHomeView, ProspectionListView, ProspectionUpdateView, export_prospections_csv

from .views.company_views import CompanyCreateView, CompanyDeleteView, CompanyDetailView, CompanyListView, CompanyUpdateView, export_companies_csv

from .views.rapport_views import RapportCreationView, RapportDeleteView, RapportDetailView, RapportExportView, RapportListView


from .views.parametres_views import parametres
from .views.formations_views import UpdateFormationFieldView

from .views.users_views import (UserDeleteView, UserDetailView, UserListView, UserUpdateView, 
user_login, register, user_logout, user_profile, change_password,reset_password, 
)

from .views import (
    home_views, DashboardView, centres_views, statuts_views, types_offre_views,
    commentaires_views, documents_views, partenaires_views, evenements_views, formations_views
)  # Import des vues

urlpatterns = [
    # Page d'accueil
    path('', home_views.home, name='home'),

    # Rapports
    # Liste des rapports
    path('rapports/', RapportListView.as_view(), name='rapport-list'),
    path('rapports/creer/', RapportCreationView.as_view(), name='rapport-create'),
    path('rapports/<int:pk>/', RapportDetailView.as_view(), name='rapport-detail'),
    path('rapports/<int:pk>/supprimer/', RapportDeleteView.as_view(), name='rapport-delete'),
    path('rapports/<int:pk>/export/', RapportExportView.as_view(), name='rapport-export'),

    # USERS
    path("register/", register, name="register"),
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),
    path("profile/", user_profile, name="user-profile"),
    path("password_change/", change_password, name="password_change"),
    path("password_reset/", reset_password, name="password_reset"),
    
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path("users/<int:pk>/update/", UserUpdateView.as_view(), name="user-update"),
    path("users/<int:pk>/delete/", UserDeleteView.as_view(), name="user-delete"),


    # Dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),


    # Centres de formation
    path('centres/', centres_views.CentreListView.as_view(), name='centre-list'),
    path('centres/<int:pk>/', centres_views.CentreDetailView.as_view(), name='centre-detail'),
    path('centres/ajouter/', centres_views.CentreCreateView.as_view(), name='centre-create'),
    path('centres/<int:pk>/modifier/', centres_views.CentreUpdateView.as_view(), name='centre-update'),
    path('centres/<int:pk>/supprimer/', centres_views.CentreDeleteView.as_view(), name='centre-delete'),

    # Statuts des formations
    path('statuts/', statuts_views.StatutListView.as_view(), name='statut-list'),
    path('statuts/<int:pk>/', statuts_views.StatutDetailView.as_view(), name='statut-detail'),
    path('statuts/ajouter/', statuts_views.StatutCreateView.as_view(), name='statut-create'),
    path('statuts/<int:pk>/modifier/', statuts_views.StatutUpdateView.as_view(), name='statut-update'),
    path('statuts/<int:pk>/supprimer/', statuts_views.StatutDeleteView.as_view(), name='statut-delete'),

    # Types d'offres
    path('types-offres/', types_offre_views.TypeOffreListView.as_view(), name='type-offre-list'),
    path('types-offres/<int:pk>/', types_offre_views.TypeOffreDetailView.as_view(), name='type-offre-detail'),
    path('types-offres/ajouter/', types_offre_views.TypeOffreCreateView.as_view(), name='type-offre-create'),
    path('types-offres/<int:pk>/modifier/', types_offre_views.TypeOffreUpdateView.as_view(), name='type-offre-update'),
    path('types-offres/<int:pk>/supprimer/', types_offre_views.TypeOffreDeleteView.as_view(), name='type-offre-delete'),

    # Commentaires
    path('commentaires/', commentaires_views.CommentaireListView.as_view(), name='commentaire-list'),
    path('commentaires/<int:pk>/', commentaires_views.CommentaireDetailView.as_view(), name='commentaire-detail'),
    path('commentaires/ajouter/', commentaires_views.CommentaireCreateView.as_view(), name='commentaire-create'),
    path('commentaires/<int:pk>/modifier/', commentaires_views.CommentaireUpdateView.as_view(), name='commentaire-update'),
    path('commentaires/<int:pk>/supprimer/', commentaires_views.CommentaireDeleteView.as_view(), name='commentaire-delete'),
    path('commentaires_all/', commentaires_views.AllCommentairesView.as_view(), name='all-commentaires'),
    path('export-commentaires/', commentaires_views.ExportCommentairesView.as_view(), name='export-commentaires'),

    # Documents
    path('documents/', documents_views.DocumentListView.as_view(), name='document-list'),
    path('documents/<int:pk>/', documents_views.DocumentDetailView.as_view(), name='document-detail'),
    path('documents/ajouter/', documents_views.DocumentCreateView.as_view(), name='document-create'),
    path('documents/ajouter/<int:formation_id>/', documents_views.DocumentCreateView.as_view(), name='document-create-formation'),
    path('documents/<int:pk>/modifier/', documents_views.DocumentUpdateView.as_view(), name='document-update'),
    path('documents/<int:pk>/supprimer/', documents_views.DocumentDeleteView.as_view(), name='document-delete'),
    
    # Partenaires
    path('partenaires/', partenaires_views.PartenaireListView.as_view(), name='partenaire-list'),
    path('partenaires/<int:pk>/', partenaires_views.PartenaireDetailView.as_view(), name='partenaire-detail'),
    path('partenaires/ajouter/', partenaires_views.PartenaireCreateView.as_view(), name='partenaire-create'),
    path('partenaires/<int:pk>/modifier/', partenaires_views.PartenaireUpdateView.as_view(), name='partenaire-update'),
    path('partenaires/<int:pk>/supprimer/', partenaires_views.PartenaireDeleteView.as_view(), name='partenaire-delete'),
    path('partenaires/ajouter/formation/<int:formation_id>/', partenaires_views.PartenaireCreateViewFormation.as_view(), name='partenaire-add-formation'),
    path('partenaires/export-csv/', partenaires_views.ExportPartenairesCSVView.as_view(), name='export-partenaires-csv'),

    # Événements
    path('evenements/', evenements_views.EvenementListView.as_view(), name='evenement-list'),
    path('evenements/<int:pk>/', evenements_views.EvenementDetailView.as_view(), name='evenement-detail'),
    path('evenements/ajouter/', evenements_views.EvenementCreateView.as_view(), name='evenement-create'),
    path('evenements/<int:pk>/modifier/', evenements_views.EvenementUpdateView.as_view(), name='evenement-update'),
    path('evenements/<int:pk>/supprimer/', evenements_views.EvenementDeleteView.as_view(), name='evenement-delete'),
    
    # Formations
    path('formations/', formations_views.FormationListView.as_view(), name='formation-list'),
    path('formations/<int:pk>/', formations_views.FormationDetailView.as_view(), name='formation-detail'),
    path('formations/ajouter/', formations_views.FormationCreateView.as_view(), name='formation-create'),
    path('formations/<int:pk>/modifier/', formations_views.FormationUpdateView.as_view(), name='formation-update'),
    path('formations/<int:pk>/supprimer/', formations_views.FormationDeleteView.as_view(), name='formation-delete'),
    path('formations/<int:pk>/commentaire/', formations_views.FormationAddCommentView.as_view(), name='formation-add-comment'),
    path("formations/export-excel/", formations_views.ExportFormationsExcelView.as_view(), name="export-formations-excel"),
    path("formations/update-champ/<int:id>/", UpdateFormationFieldView.as_view(), name="update_formation_field"),

        # Historique des Formations
    path('historique-formations/', HistoriqueFormationListView.as_view(), name='historique-formation-list'),
    path('historique-formations/<int:pk>/', HistoriqueFormationDetailView.as_view(), name='historique-formation-detail'),
    path("historique-formations/<int:pk>/delete/", HistoriqueFormationDeleteView.as_view(), name="historique-formation-delete"),

    # Company
    path('companies/', CompanyListView.as_view(), name='company-list'),
    path('companies/<int:pk>/', CompanyDetailView.as_view(), name='company-detail'),
    path('companies/add/', CompanyCreateView.as_view(), name='company-create'),
    path('companies/<int:pk>/edit/', CompanyUpdateView.as_view(), name='company-update'),
    path('companies/<int:pk>/delete/', CompanyDeleteView.as_view(), name='company-delete'),
    path('companies/export/', export_companies_csv, name='company-export'),

    # Paramètres
    path('parametres/', parametres, name='parametres'),

    # Prospections
    path('prospection_home', ProspectionHomeView, name='prospection-home'),
    path('prospections/', ProspectionListView.as_view(), name='prospection-list'),
    path('prospections/<int:pk>/', ProspectionDetailView.as_view(), name='prospection-detail'),
    path('prospections/add/', ProspectionCreateView.as_view(), name='prospection-add'),
    path('prospections/<int:pk>/edit/', ProspectionUpdateView.as_view(), name='prospection-update'),
    path('prospections/<int:pk>/delete/', ProspectionDeleteView.as_view(), name='prospection-delete'),
    path('historique-prospections/', HistoriqueProspectionListView.as_view(), name='historique-prospection-list'),
    path('historique-prospections/<int:pk>/', HistoriqueProspectionDetailView.as_view(), name='historique-prospection-detail'),
    path("prospections/export/", export_prospections_csv, name="prospection-export"),

 # Prepa_Comp
    path('prepa/', PrepaHomeView.as_view(), name='prepa_home'),
    path('prepa/objectifs/', PrepaObjectifsView.as_view(), name='prepa_objectifs'),
    path('prepa/objectifs/<int:annee>/', PrepaObjectifsView.as_view(), name='prepa_objectifs_annee'),


    # ---- Semaines ----
    path('prepa/semaines/', PrepaSemaineListView.as_view(), name='prepa_semaine_list'),
    path('prepa/semaines/ajouter/', PrepaSemaineCreateView.as_view(), name='prepa_semaine_create'),
    path('prepa/semaines/<int:pk>/', PrepaSemaineDetailView.as_view(), name='prepa_semaine_detail'),
    path('prepa/semaines/<int:pk>/modifier/', PrepaSemaineUpdateView.as_view(), name='prepa_semaine_update'),
    path('prepa/semaines/<int:pk>/supprimer/', PrepaSemaineDeleteView.as_view(), name='prepa_semaine_delete'),


    # ---- Global annuel ----
    path('prepa/global/', PrepaGlobalListView.as_view(), name='prepa_global_list'),
    path('prepa/global/<int:pk>/', PrepaGlobalDetailView.as_view(), name='prepa_global_detail'),
    path('prepa/global/ajouter/', PrepaGlobalCreateView.as_view(), name='prepa_global_create'),

    path('vae-jury/', vae_jury_home, name='vae-jury-home'),
    path('vae-jury/dashboard/', vae_jury_dashboard, name='vae-jury-dashboard'),
    path('vae-jury/<int:pk>/objectifs/', ObjectifCentreUpdateView.as_view(), name='centre-objectifs'),

    path('vae-jury/objectifs-centres/', modifier_objectifs_tous_centres, name='objectifs-centres'),
    path('vae/<int:vae_id>/historique/ajouter/', HistoriqueStatutCreateView.as_view(), name='vae-historique-create'),
    
    # Suivis des jurys
    path('jurys/', SuiviJuryListView.as_view(), name='jury-list'),
    path('jurys/<int:pk>/', SuiviJuryDetailView.as_view(), name='jury-detail'),
    path('jurys/nouveau/', SuiviJuryCreateView.as_view(), name='jury-create'),
    path('jurys/<int:pk>/modifier/', SuiviJuryUpdateView.as_view(), name='jury-update'),
    path('jurys/<int:pk>/supprimer/', SuiviJuryDeleteView.as_view(), name='jury-delete'),
    
    # VAE
    path('vae/', VAEListView.as_view(), name='vae-list'),
    path('vae/<int:pk>/', VAEDetailView.as_view(), name='vae-detail'),
    path('vae/nouvelle/', VAECreateView.as_view(), name='vae-create'),
    path('vae/<int:pk>/modifier/', VAEUpdateView.as_view(), name='vae-update'),
    path('vae/<int:pk>/supprimer/', VAEDeleteView.as_view(), name='vae-delete'),
    

    path('api/jurys-data/', api_jurys_data, name='api-jurys-data'),
    path('api/vae-data/', api_vae_data, name='api-vae-data'),
        
    # Historique des statuts VAE
    path('vae/<int:vae_id>/statut/', HistoriqueStatutCreateView.as_view(), name='historique-create'),   
    
    
    ]

