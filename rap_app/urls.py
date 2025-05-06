from django.urls import path

from .views import home_views






urlpatterns = [
    # Page d'accueil
    path('', home_views.home, name='home'),

    # Rapports
    # Liste des rapports

    # USERS


    # Dashboard


    # Centres de formation
    # Statuts des formations
    # Types d'offres

    # Commentaires

    # Documents
    
    # Partenaires
    # Événements
    
    # Formations
        # Historique des Formations

    # Paramètres

    # Prospections

 # Prepa_Comp


    # ---- Semaines ----


    # ---- Global annuel ----
    
    # Suivis des jurys    
    # VAE
        
    # Historique des statuts VAE
    
    
    ]

