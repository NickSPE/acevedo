from django.urls import path
from .api_views import (
    ReportsDashboardStatsAPIView,
    ReporteListCreateAPIView,
    ReporteDetailAPIView,
    ExportarReporteAPIView,
    ConfiguracionReporteAPIView,
)

urlpatterns = [
    # Dashboard estadístico
    path('dashboard/', ReportsDashboardStatsAPIView.as_view(), name='api_reports_dashboard'),
    
    # Reportes CRUD
    path('reportes/', ReporteListCreateAPIView.as_view(), name='api_reportes_list_create'),
    path('reportes/<int:pk>/', ReporteDetailAPIView.as_view(), name='api_reporte_detail'),
    path('reportes/<int:pk>/exportar/<str:formato>/', ExportarReporteAPIView.as_view(), name='api_reporte_exportar'),
    
    # Configuración
    path('configuracion/', ConfiguracionReporteAPIView.as_view(), name='api_reportes_configuracion'),
]
