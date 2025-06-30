from django.urls import path
from . import views

urlpatterns = [
    path('notificaciones/', views.notification_history, name='notifications'),
    path('alertas-automaticas/', views.alertas_automaticas, name='alertas_automaticas'),
    path('historial/', views.historial, name='historial'),
    path('configuraciones/', views.configuraciones, name='configuraciones'),
]