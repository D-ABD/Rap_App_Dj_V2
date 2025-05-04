# rap_app/api/paginations.py

from rest_framework.pagination import PageNumberPagination

class RapAppPagination(PageNumberPagination):
    """
    Pagination personnalisée pour l'API Rap App.
    
    - page_size : nombre d'éléments par défaut par page (10)
    - page_size_query_param : permet au client de demander plus/moins d'éléments avec ?page_size=
    - max_page_size : limite maximale autorisée pour éviter les abus (100)
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
