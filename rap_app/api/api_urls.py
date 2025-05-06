from django.urls import path
from rest_framework.routers import DefaultRouter

from .viewsets.auth_viewset import EmailTokenObtainPairView
from .viewsets.login_logout_viewset import LoginAPIView, LogoutAPIView
from .viewsets.temporaire_viewset import test_token_view
from rest_framework_simplejwt.views import TokenRefreshView

# ViewSets
# ✅ Ajout pour permettre reverse('api:...') dans les tests
app_name = "api"

router = DefaultRouter()

urlpatterns = router.urls + [
    # Authentification
    path('token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', LoginAPIView.as_view(), name='api_login'),
    path('logout/', LogoutAPIView.as_view(), name='api_logout'),

    # Infos utilisateur et test
    path('test-token/', test_token_view),
]
