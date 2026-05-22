from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    # Autenticación JWT estándar
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Enrutamiento de cada app
    path('usuarios/', include('usuarios.api_urls')),
    path('cuentas/', include('cuentas.api_urls')),
    path('gestion-financiera/', include('gestion_financiera_basica.api_urls')),
    path('educacion-financiera/', include('educacion_financiera.api_urls')),
    path('analisis-reportes/', include('analisis_reportes.api_urls')),
    path('alertas-notificaciones/', include('alertas_notificaciones.api_urls')),
]
