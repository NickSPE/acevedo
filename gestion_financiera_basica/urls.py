from django.urls import path
from . import views
from . import test_views

""" Urls App GESTION_FINANCIERA_BASICA """
app_name = 'gestion_financiera_basica'

urlpatterns = [
    path("transactions/", views.transactions, name="transactions"),
    path("savings-goals/", views.savings_goals, name="savings_goals"),
    path('movimientos/agregar/', views.agregar_movimiento, name='agregar_movimiento'),
    path('metas/agregar/', views.agregar_meta_ahorro, name='agregar_meta_ahorro'),
    path('metas/<int:meta_id>/aportar/', views.aportar_meta_ahorro, name='aportar_meta_ahorro'),
    path('metas/<int:meta_id>/editar/', views.editar_meta_ahorro, name='editar_meta_ahorro'),
    path('metas/<int:meta_id>/detalle/', views.detalle_meta_ahorro, name='detalle_meta_ahorro'),
    # Pruebas de notificaciones
    path('test-notifications/', test_views.test_notifications, name='test_notifications'),
]