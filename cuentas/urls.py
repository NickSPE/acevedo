from django.urls import path
from . import views

""" Urls App CUENTAS """
app_name = 'cuentas'

urlpatterns = [
    path("profile/", views.profile, name="profile"),
    path("settings/", views.settings, name="settings"),
    
    # URLs para subcuentas
    path("subcuentas/", views.subcuentas_dashboard, name="subcuentas_dashboard"),
    path("subcuentas/crear/<int:cuenta_id>/", views.crear_subcuenta, name="crear_subcuenta"),
    path("subcuentas/editar/<int:subcuenta_id>/", views.editar_subcuenta, name="editar_subcuenta"),
    path("subcuentas/eliminar/<int:subcuenta_id>/", views.eliminar_subcuenta, name="eliminar_subcuenta"),
    path("subcuentas/activar/<int:subcuenta_id>/", views.activar_subcuenta, name="activar_subcuenta"),
    path("subcuentas/transferir/", views.transferir_subcuentas, name="transferir_subcuentas"),
    path("subcuentas/depositar/<int:subcuenta_id>/", views.depositar_subcuenta, name="depositar_subcuenta"),
    path("subcuentas/retirar/<int:subcuenta_id>/", views.retirar_subcuenta, name="retirar_subcuenta"),
    path("subcuentas/historial/", views.historial_transferencias, name="historial_transferencias"),
]