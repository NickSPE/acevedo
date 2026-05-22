import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from datetime import datetime

from .models import Reporte, ConfiguracionReporte
from .api_serializers import ReporteSerializer, ConfiguracionReporteSerializer
from .views import (
    get_periodo_fechas,
    calcular_estadisticas_generales,
    get_gastos_por_categoria,
    get_ingresos_vs_egresos,
    get_estadisticas_subcuentas,
    get_flujo_mensual,
    get_balance_general,
    exportar_pdf,
    exportar_reporte_excel,
    exportar_csv
)

class ReportsDashboardStatsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        config, _ = ConfiguracionReporte.objects.get_or_create(
            id_usuario=user,
            defaults={'periodo_default': 'mes_actual'}
        )
        
        periodo = request.query_params.get('periodo', config.periodo_default)
        
        if periodo == 'personalizado':
            fecha_inicio_str = request.query_params.get('fecha_inicio')
            fecha_fin_str = request.query_params.get('fecha_fin')
            if fecha_inicio_str and fecha_fin_str:
                try:
                    fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
                    fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
                except ValueError:
                    fecha_inicio, fecha_fin = get_periodo_fechas('mes_actual')
            else:
                fecha_inicio, fecha_fin = get_periodo_fechas('mes_actual')
        else:
            fecha_inicio, fecha_fin = get_periodo_fechas(periodo)

        stats = calcular_estadisticas_generales(user, fecha_inicio, fecha_fin)
        gastos_categoria = get_gastos_por_categoria(user, fecha_inicio, fecha_fin)
        ingresos_egresos = get_ingresos_vs_egresos(user, fecha_inicio, fecha_fin)
        subcuentas_data = get_estadisticas_subcuentas(user)
        flujo_mensual = get_flujo_mensual(user, fecha_inicio, fecha_fin)
        reportes_recientes = Reporte.objects.filter(id_usuario=user).order_by('-fecha_creacion')[:5]

        # Formatear top gastos de stats para JSON
        top_gastos = []
        if 'top_gastos' in stats:
            for g in stats['top_gastos']:
                top_gastos.append({
                    'nombre': g.nombre,
                    'monto': float(g.monto),
                    'fecha': g.fecha_movimiento.strftime('%Y-%m-%d'),
                    'tipo': g.tipo
                })
            stats['top_gastos'] = top_gastos

        return Response({
            'success': True,
            'stats': stats,
            'gastos_categoria': gastos_categoria,
            'ingresos_egresos': ingresos_egresos,
            'subcuentas_data': subcuentas_data,
            'flujo_mensual': flujo_mensual,
            'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
            'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
            'periodo': periodo,
            'reportes_recientes': ReporteSerializer(reportes_recientes, many=True).data
        })

class ReporteListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReporteSerializer

    def get_queryset(self):
        return Reporte.objects.filter(id_usuario=self.request.user).order_by('-fecha_creacion')

    def perform_create(self, serializer):
        user = self.request.user
        tipo_reporte = self.request.data.get('tipo_reporte')
        titulo = self.request.data.get('titulo', f'Reporte {tipo_reporte}')
        
        fecha_inicio = datetime.strptime(self.request.data.get('fecha_inicio'), '%Y-%m-%d')
        fecha_fin = datetime.strptime(self.request.data.get('fecha_fin'), '%Y-%m-%d')

        datos_reporte = {}
        if tipo_reporte == 'gastos_categoria':
            datos_reporte = get_gastos_por_categoria(user, fecha_inicio, fecha_fin)
        elif tipo_reporte == 'ingresos_egresos':
            datos_reporte = get_ingresos_vs_egresos(user, fecha_inicio, fecha_fin)
        elif tipo_reporte == 'subcuentas_analisis':
            datos_reporte = get_estadisticas_subcuentas(user)
        elif tipo_reporte == 'balance_general':
            datos_reporte = get_balance_general(user, fecha_inicio, fecha_fin)
        elif tipo_reporte == 'flujo_efectivo':
            datos_reporte = get_flujo_mensual(user, fecha_inicio, fecha_fin)

        serializer.save(
            id_usuario=user,
            titulo=titulo,
            tipo_reporte=tipo_reporte,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            datos_json=json.dumps(datos_reporte, default=str)
        )

class ReporteDetailAPIView(generics.RetrieveDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReporteSerializer

    def get_queryset(self):
        return Reporte.objects.filter(id_usuario=self.request.user)

class ExportarReporteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, formato):
        reporte = get_object_or_404(Reporte, id=pk, id_usuario=request.user)
        datos = reporte.get_datos()
        
        if formato == 'pdf':
            return exportar_pdf(reporte, datos)
        elif formato == 'excel':
            return exportar_reporte_excel(reporte, datos)
        elif formato == 'csv':
            return exportar_csv(reporte, datos)
        return Response({'error': 'Formato no soportado.'}, status=status.HTTP_400_BAD_REQUEST)

class ConfiguracionReporteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        config, _ = ConfiguracionReporte.objects.get_or_create(id_usuario=request.user)
        serializer = ConfiguracionReporteSerializer(config)
        return Response(serializer.data)

    def put(self, request):
        config, _ = ConfiguracionReporte.objects.get_or_create(id_usuario=request.user)
        serializer = ConfiguracionReporteSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
