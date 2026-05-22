from django.urls import path
from .api_views import (
    ConfiguracionesNotificacionAPIView,
    HistorialNotificacionesAPIView,
    MarcarNotificacionLeidaAPIView,
    MarcarTodasLeidasAPIView,
    ObtenerContadorNotificacionesAPIView,
    TestNotificationAPIView,
)

urlpatterns = [
    # Configuración de notificaciones
    path('configuracion/', ConfiguracionesNotificacionAPIView.as_view(), name='api_notificaciones_configuracion'),
    
    # Historial y lectura
    path('historial/', HistorialNotificacionesAPIView.as_view(), name='api_notificaciones_historial'),
    path('notificaciones/<int:pk>/leer/', MarcarNotificacionLeidaAPIView.as_view(), name='api_notificacion_leer'),
    path('notificaciones/leer-todas/', MarcarTodasLeidasAPIView.as_view(), name='api_notificaciones_leer_todas'),
    
    # Contador de no leídas
    path('contador/', ObtenerContadorNotificacionesAPIView.as_view(), name='api_notificaciones_contador'),
    
    # Notificación de prueba
    path('test/', TestNotificationAPIView.as_view(), name='api_notificaciones_test'),
]
