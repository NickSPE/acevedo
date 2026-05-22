from django.urls import path
from . import views
from . import email_views
from . import admin_views

app_name = 'alertas_notificaciones'

urlpatterns = [
    path('', views.index, name='index'),
    path('alertas-automaticas/', views.alertas_automaticas, name='alertas_automaticas'),
    path('historial/', views.historial, name='historial'),
    path('configuraciones/', views.configuraciones, name='configuraciones'),
    path('marcar-leida/<int:notificacion_id>/', views.marcar_notificacion_leida, name='marcar_leida'),
    path('marcar-todas-leidas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
    path('marcar-todas-leidas-simple/', views.marcar_todas_leidas_simple, name='marcar_todas_leidas_simple'),
    path('contador/', views.obtener_contador_notificaciones, name='contador'),
    path('test/', views.test_notification, name='test'),
    path('test-currency/', views.test_currency, name='test_currency'),
    path('debug-currency/', views.debug_currency, name='debug_currency'),
    path('debug-simple/', views.debug_simple, name='debug_simple'),
    # Nuevas vistas para emails
    path('emails/', email_views.ver_emails_enviados, name='ver_emails'),
    path('email/<str:filename>/', email_views.ver_email_completo, name='ver_email_completo'),
    
    # URLs administrativas
    path('admin/', admin_views.admin_notificaciones, name='admin_notificaciones'),
    path('admin/debug-duplicados/', admin_views.debug_duplicados, name='debug_duplicados'),
]