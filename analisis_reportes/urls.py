from django.urls import path
from . import views

app_name = 'analisis_reportes'

urlpatterns = [
    path('', views.reports, name='reports'),
    path('reports/', views.reports, name='reports'),
    path('generar/', views.generar_reporte, name='generar_reporte'),
    path('ver/<int:reporte_id>/', views.ver_reporte, name='ver_reporte'),
    path('exportar/<int:reporte_id>/<str:formato>/', views.exportar_reporte, name='exportar_reporte'),
    path('exportar-excel/', views.exportar_excel, name='exportar_excel'),
    path('exportar-pdf/', views.exportar_pdf_simple, name='exportar_pdf'),
    path('api/datos/<str:tipo>/', views.api_datos_grafico, name='api_datos_grafico'),
]