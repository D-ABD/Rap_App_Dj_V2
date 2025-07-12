from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),
    # API
    path('api/', include('rap_app.api.api_urls')),



    # Vues Web (HTML)
    path('', include('rap_app.urls')),

        # Documentation de l'API
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),  # <-- JSON brut
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),  # <-- UI Swagger
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),  # (facultatif)
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
