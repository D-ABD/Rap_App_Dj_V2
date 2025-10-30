from .views import home_views

from django.urls import path, include







urlpatterns = [
    # Page d'accueil
    path('', home_views.home, name='home'),
    # === API principale ===
    path('api/', include('rap_app.api.api_urls')),

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

