from django.urls import path
from . import views

""" Urls App CUENTAS """
app_name = 'cuentas'

urlpatterns = [
    path("profile/", views.profile, name="profile"),
    path("settings/", views.settings, name="settings"),
    
    # URLs para subcuentas
    path("subcuentas/", views.subcuentas_dashboard, name="subcuentas_dashboard"),
    path("subcuentas/crear/", views.crear_subcuenta, name="crear_subcuenta_nueva"), # Para subcuentas independientes
    path("subcuentas/crear/<int:cuenta_id>/", views.crear_subcuenta, name="crear_subcuenta"),
    path("subcuentas/editar/<int:subcuenta_id>/", views.editar_subcuenta, name="editar_subcuenta"),
    path("subcuentas/eliminar/<int:subcuenta_id>/", views.eliminar_subcuenta, name="eliminar_subcuenta"),
    path("subcuentas/activar/<int:subcuenta_id>/", views.activar_subcuenta, name="activar_subcuenta"),
    path("subcuentas/transferir/", views.transferir_subcuentas, name="transferir_subcuentas"),
    path("subcuentas/depositar/<int:subcuenta_id>/", views.depositar_subcuenta, name="depositar_subcuenta"),
    path("subcuentas/retirar/<int:subcuenta_id>/", views.retirar_subcuenta, name="retirar_subcuenta"),
    path("subcuentas/historial/", views.historial_transferencias, name="historial_transferencias"),
    
    # URLs para transferencias con cuenta principal
    path("subcuentas/transferir-principal/<int:subcuenta_id>/", views.transferir_a_cuenta_principal, name="transferir_a_cuenta_principal"),
    path("subcuentas/transferir-principal-ajax/", views.transferir_a_cuenta_principal_ajax, name="transferir_a_cuenta_principal_ajax"),
    path("subcuentas/depositar-ajax/", views.depositar_subcuenta_ajax, name="depositar_subcuenta_ajax"),
    path("subcuentas/transferir-ajax/", views.transferir_subcuentas_ajax, name="transferir_subcuentas_ajax"),
    path("subcuentas/historial-principal/", views.historial_transferencias_cuenta_principal, name="historial_transferencias_cuenta_principal"),
]