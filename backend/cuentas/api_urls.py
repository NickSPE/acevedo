from django.urls import path
from .api_views import (
    DashboardStatsAPIView,
    SubCuentaListCreateAPIView,
    SubCuentaRetrieveUpdateDestroyAPIView,
    SubCuentaActivarAPIView,
    TransferenciaSubCuentaListCreateAPIView,
    TransferenciaCuentaPrincipalListCreateAPIView,
    UpdateProfileAPIView,
    UpdateContactAPIView,
    ChangePasswordAPIView,
    ChangePinAPIView,
)

urlpatterns = [
    path('dashboard/stats/', DashboardStatsAPIView.as_view(), name='api_dashboard_stats'),
    
    # SubCuentas CRUD
    path('subcuentas/', SubCuentaListCreateAPIView.as_view(), name='api_subcuentas_list_create'),
    path('subcuentas/<int:pk>/', SubCuentaRetrieveUpdateDestroyAPIView.as_view(), name='api_subcuenta_detail'),
    path('subcuentas/<int:pk>/activar/', SubCuentaActivarAPIView.as_view(), name='api_subcuenta_activar'),
    
    # Transferencias
    path('transferencias/entre-subcuentas/', TransferenciaSubCuentaListCreateAPIView.as_view(), name='api_transferir_subcuentas'),
    path('transferencias/cuenta-principal/', TransferenciaCuentaPrincipalListCreateAPIView.as_view(), name='api_transferir_cuenta_principal'),
    
    # Perfil / Ajustes
    path('profile/update/', UpdateProfileAPIView.as_view(), name='api_profile_update'),
    path('profile/contact/', UpdateContactAPIView.as_view(), name='api_profile_contact'),
    path('profile/password/', ChangePasswordAPIView.as_view(), name='api_profile_password'),
    path('profile/pin/', ChangePinAPIView.as_view(), name='api_profile_pin'),
]
