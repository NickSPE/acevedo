from django.urls import path
from .api_views import (
    MovimientoListCreateAPIView,
    MovimientoRetrieveUpdateDestroyAPIView,
    MetaAhorroListCreateAPIView,
    MetaAhorroRetrieveUpdateDestroyAPIView,
    AporteMetaAhorroCreateAPIView,
)

urlpatterns = [
    # Transacciones (Movimientos)
    path('movimientos/', MovimientoListCreateAPIView.as_view(), name='api_movimientos_list_create'),
    path('movimientos/<int:pk>/', MovimientoRetrieveUpdateDestroyAPIView.as_view(), name='api_movimiento_detail'),
    
    # Metas de ahorro
    path('metas/', MetaAhorroListCreateAPIView.as_view(), name='api_metas_list_create'),
    path('metas/<int:pk>/', MetaAhorroRetrieveUpdateDestroyAPIView.as_view(), name='api_meta_detail'),
    path('metas/aporte/', AporteMetaAhorroCreateAPIView.as_view(), name='api_aporte_create'),
]
