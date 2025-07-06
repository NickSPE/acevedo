from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import base64

from core.decorators import fast_access_pin_verified
from .models import Reporte, ConfiguracionReporte
from cuentas.models import Cuenta, SubCuenta, TransferenciaSubCuenta
from gestion_financiera_basica.models import Movimiento, MetaAhorro

@login_required
@fast_access_pin_verified
def reports(request):
    """Vista principal de reportes con dashboard interactivo"""
    # Configuración del usuario
    config, created = ConfiguracionReporte.objects.get_or_create(
        id_usuario=request.user,
        defaults={'periodo_default': 'mes_actual'}
    )
    
    # Obtener parámetros de filtro
    periodo = request.GET.get('periodo', config.periodo_default)
    fecha_inicio, fecha_fin = get_periodo_fechas(periodo)
    
    # Obtener cuentas del usuario
    cuentas = Cuenta.objects.filter(id_usuario=request.user)
    
    # Calcular estadísticas generales
    stats = calcular_estadisticas_generales(request.user, fecha_inicio, fecha_fin)
    
    # Datos para gráficos
    gastos_categoria = get_gastos_por_categoria(request.user, fecha_inicio, fecha_fin)
    ingresos_egresos = get_ingresos_vs_egresos(request.user, fecha_inicio, fecha_fin)
    subcuentas_data = get_estadisticas_subcuentas(request.user)
    flujo_mensual = get_flujo_mensual(request.user, fecha_inicio, fecha_fin)
    
    # Reportes recientes
    reportes_recientes = Reporte.objects.filter(id_usuario=request.user)[:5]
    
    context = {
        'stats': stats,
        'gastos_categoria': json.dumps(gastos_categoria),
        'ingresos_egresos': json.dumps(ingresos_egresos),
        'subcuentas_data': json.dumps(subcuentas_data),
        'flujo_mensual': json.dumps(flujo_mensual),
        'reportes_recientes': reportes_recientes,
        'periodo_actual': periodo,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'config': config,
        'cuentas': cuentas,
    }
    
    return render(request, 'analisis_reportes/reports.html', context)

@login_required
@fast_access_pin_verified
def generar_reporte(request):
    """Vista para generar un reporte específico"""
    if request.method == 'POST':
        tipo_reporte = request.POST.get('tipo_reporte')
        titulo = request.POST.get('titulo', f'Reporte {tipo_reporte}')
        fecha_inicio = datetime.strptime(request.POST.get('fecha_inicio'), '%Y-%m-%d')
        fecha_fin = datetime.strptime(request.POST.get('fecha_fin'), '%Y-%m-%d')
        
        # Generar datos según el tipo de reporte
        datos_reporte = {}
        
        if tipo_reporte == 'gastos_categoria':
            datos_reporte = get_gastos_por_categoria(request.user, fecha_inicio, fecha_fin)
        elif tipo_reporte == 'ingresos_egresos':
            datos_reporte = get_ingresos_vs_egresos(request.user, fecha_inicio, fecha_fin)
        elif tipo_reporte == 'subcuentas_analisis':
            datos_reporte = get_estadisticas_subcuentas(request.user)
        elif tipo_reporte == 'balance_general':
            datos_reporte = get_balance_general(request.user, fecha_inicio, fecha_fin)
        elif tipo_reporte == 'flujo_efectivo':
            datos_reporte = get_flujo_mensual(request.user, fecha_inicio, fecha_fin)
        
        # Crear el reporte
        reporte = Reporte.objects.create(
            tipo_reporte=tipo_reporte,
            titulo=titulo,
            descripcion=request.POST.get('descripcion', ''),
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            id_usuario=request.user,
            datos_json=json.dumps(datos_reporte, default=str)
        )
        
        messages.success(request, f'Reporte "{titulo}" generado exitosamente.')
        
        # Si se solicita exportación inmediata
        formato_export = request.POST.get('formato_export')
        if formato_export:
            return exportar_reporte(request, reporte.id, formato_export)
        
        return redirect('analisis_reportes:ver_reporte', reporte_id=reporte.id)
    
    return redirect('analisis_reportes:reports')

@login_required
@fast_access_pin_verified
def ver_reporte(request, reporte_id):
    """Vista para ver un reporte específico"""
    reporte = get_object_or_404(Reporte, id=reporte_id, id_usuario=request.user)
    datos = reporte.get_datos()
    
    # Procesar datos para el template
    datos_procesados = procesar_datos_para_template(reporte.tipo_reporte, datos)
    
    context = {
        'reporte': reporte,
        'datos': datos,
        'datos_procesados': datos_procesados,
        'datos_json': json.dumps(datos),
    }
    
    return render(request, 'analisis_reportes/ver_reporte.html', context)

@login_required
@fast_access_pin_verified  
def exportar_reporte(request, reporte_id, formato):
    """Vista para exportar reportes en diferentes formatos"""
    reporte = get_object_or_404(Reporte, id=reporte_id, id_usuario=request.user)
    datos = reporte.get_datos()
    
    if formato == 'pdf':
        return exportar_pdf(reporte, datos)
    elif formato == 'excel':
        return exportar_excel(reporte, datos)
    elif formato == 'csv':
        return exportar_csv(reporte, datos)
    else:
        messages.error(request, 'Formato de exportación no válido.')
        return redirect('analisis_reportes:ver_reporte', reporte_id=reporte_id)

@login_required
@fast_access_pin_verified
def api_datos_grafico(request):
    """API para obtener datos de gráficos via AJAX"""
    tipo = request.GET.get('tipo')
    periodo = request.GET.get('periodo', 'mes_actual')
    fecha_inicio, fecha_fin = get_periodo_fechas(periodo)
    
    if tipo == 'gastos_categoria':
        datos = get_gastos_por_categoria(request.user, fecha_inicio, fecha_fin)
    elif tipo == 'ingresos_egresos':
        datos = get_ingresos_vs_egresos(request.user, fecha_inicio, fecha_fin)
    elif tipo == 'subcuentas':
        datos = get_estadisticas_subcuentas(request.user)
    elif tipo == 'flujo_mensual':
        datos = get_flujo_mensual(request.user, fecha_inicio, fecha_fin)
    else:
        datos = {}
    
    return JsonResponse(datos)

# Funciones auxiliares para cálculos

def get_periodo_fechas(periodo):
    """Convierte un período en fechas de inicio y fin"""
    hoy = timezone.now().date()
    
    if periodo == 'semana_actual':
        inicio = hoy - timedelta(days=hoy.weekday())
        fin = inicio + timedelta(days=6)
    elif periodo == 'mes_actual':
        inicio = hoy.replace(day=1)
        fin = (inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    elif periodo == 'trimestre_actual':
        mes_inicio = ((hoy.month - 1) // 3) * 3 + 1
        inicio = hoy.replace(month=mes_inicio, day=1)
        fin = (inicio + timedelta(days=92)).replace(day=1) - timedelta(days=1)
    elif periodo == 'año_actual':
        inicio = hoy.replace(month=1, day=1)
        fin = hoy.replace(month=12, day=31)
    elif periodo == 'ultimos_30_dias':
        fin = hoy
        inicio = hoy - timedelta(days=30)
    elif periodo == 'ultimos_90_dias':
        fin = hoy
        inicio = hoy - timedelta(days=90)
    else:
        # Por defecto, mes actual
        inicio = hoy.replace(day=1)
        fin = (inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    return inicio, fin

def calcular_estadisticas_generales(usuario, fecha_inicio, fecha_fin):
    """Calcula estadísticas generales del usuario"""
    cuentas = Cuenta.objects.filter(id_usuario=usuario)
    
    # Balance total
    balance_total = sum([cuenta.saldo_cuenta for cuenta in cuentas])
    
    # Total en subcuentas
    total_subcuentas = SubCuenta.objects.filter(
        id_cuenta__id_usuario=usuario, 
        activa=True
    ).aggregate(total=Sum('saldo'))['total'] or 0
    
    # Transacciones del período
    transacciones_periodo = Movimiento.objects.filter(
        id_cuenta__id_usuario=usuario,
        fecha_movimiento__range=[fecha_inicio, fecha_fin]
    )
    
    ingresos_periodo = transacciones_periodo.filter(
        tipo='ingreso'
    ).aggregate(total=Sum('monto'))['total'] or 0
    
    gastos_periodo = transacciones_periodo.filter(
        tipo='egreso'
    ).aggregate(total=Sum('monto'))['total'] or 0
    
    # Número de cuentas y subcuentas
    num_cuentas = cuentas.count()
    num_subcuentas = SubCuenta.objects.filter(
        id_cuenta__id_usuario=usuario, 
        activa=True
    ).count()
    
    # Promedio de transacciones
    promedio_transaccion = transacciones_periodo.aggregate(
        promedio=Avg('monto')
    )['promedio'] or 0
    
    return {
        'balance_total': float(balance_total),
        'total_subcuentas': float(total_subcuentas),
        'ingresos_periodo': float(ingresos_periodo),
        'gastos_periodo': float(gastos_periodo),
        'balance_periodo': float(ingresos_periodo - gastos_periodo),
        'num_cuentas': num_cuentas,
        'num_subcuentas': num_subcuentas,
        'promedio_transaccion': float(promedio_transaccion),
        'total_transacciones': transacciones_periodo.count(),
    }

def get_gastos_por_categoria(usuario, fecha_inicio, fecha_fin):
    """Obtiene gastos agrupados por categoría de subcuenta"""
    gastos = SubCuenta.objects.filter(
        id_cuenta__id_usuario=usuario,
        activa=True
    ).values('tipo').annotate(
        total=Sum('saldo'),
        count=Count('id')
    ).order_by('-total')
    
    return {
        'labels': [gasto['tipo'].title() for gasto in gastos],
        'data': [float(gasto['total']) for gasto in gastos],
        'counts': [gasto['count'] for gasto in gastos],
    }

def get_ingresos_vs_egresos(usuario, fecha_inicio, fecha_fin):
    """Obtiene comparación de ingresos vs egresos"""
    transacciones = Movimiento.objects.filter(
        id_cuenta__id_usuario=usuario,
        fecha_movimiento__range=[fecha_inicio, fecha_fin]
    )
    
    ingresos = transacciones.filter(
        tipo='ingreso'
    ).aggregate(total=Sum('monto'))['total'] or 0
    
    egresos = transacciones.filter(
        tipo='egreso'
    ).aggregate(total=Sum('monto'))['total'] or 0
    
    return {
        'labels': ['Ingresos', 'Egresos'],
        'data': [float(ingresos), float(egresos)],
        'balance': float(ingresos - egresos),
    }

def get_estadisticas_subcuentas(usuario):
    """Obtiene estadísticas de subcuentas"""
    subcuentas = SubCuenta.objects.filter(
        id_cuenta__id_usuario=usuario,
        activa=True
    ).values('tipo').annotate(
        total_saldo=Sum('saldo'),
        cantidad=Count('id')
    )
    
    return {
        'labels': [sc['tipo'].title() for sc in subcuentas],
        'saldos': [float(sc['total_saldo']) for sc in subcuentas],
        'cantidades': [sc['cantidad'] for sc in subcuentas],
    }

def get_flujo_mensual(usuario, fecha_inicio, fecha_fin):
    """Obtiene flujo de efectivo mensual"""
    # Simplificado - se puede hacer más complejo con datos reales mensuales
    meses = []
    ingresos_mes = []
    egresos_mes = []
    
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        mes_inicio = fecha_actual.replace(day=1)
        mes_fin = (mes_inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        transacciones_mes = Movimiento.objects.filter(
            id_cuenta__id_usuario=usuario,
            fecha_movimiento__range=[mes_inicio, min(mes_fin, fecha_fin)]
        )
        
        ingresos = transacciones_mes.filter(
            tipo='ingreso'
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        egresos = transacciones_mes.filter(
            tipo='egreso'
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        meses.append(fecha_actual.strftime('%B %Y'))
        ingresos_mes.append(float(ingresos))
        egresos_mes.append(float(egresos))
        
        # Avanzar al siguiente mes
        fecha_actual = (fecha_actual + timedelta(days=32)).replace(day=1)
    
    return {
        'labels': meses,
        'ingresos': ingresos_mes,
        'egresos': egresos_mes,
    }

def get_balance_general(usuario, fecha_inicio, fecha_fin):
    """Obtiene balance general del período"""
    cuentas = Cuenta.objects.filter(id_usuario=usuario)
    
    balance_data = []
    for cuenta in cuentas:
        subcuentas = SubCuenta.objects.filter(id_cuenta=cuenta, activa=True)
        total_subcuentas = sum([sc.saldo for sc in subcuentas])
        
        balance_data.append({
            'cuenta': cuenta.nombre,
            'saldo_principal': float(cuenta.saldo_cuenta),
            'saldo_subcuentas': float(total_subcuentas),
            'saldo_total': float(cuenta.saldo_cuenta + total_subcuentas),
            'subcuentas': [{
                'nombre': sc.nombre,
                'tipo': sc.tipo,
                'saldo': float(sc.saldo)
            } for sc in subcuentas]
        })
    
    return balance_data

def exportar_pdf(reporte, datos):
    """Exporta reporte a PDF con formato profesional"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=72, leftMargin=72,
        topMargin=72, bottomMargin=18
    )
    styles = getSampleStyleSheet()
    story = []
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#6C5CE7'),
        alignment=1,  # Center
        spaceAfter=30
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2d3436'),
        spaceBefore=20,
        spaceAfter=12
    )
    
    # Encabezado con logo (simulado)
    story.append(Paragraph("FinGest - Gestión Financiera", title_style))
    story.append(Paragraph(reporte.titulo, header_style))
    story.append(Spacer(1, 20))
    
    # Información del reporte mejorada
    info_data = [
        ['Tipo de Reporte:', reporte.get_tipo_reporte_display()],
        ['Fecha de Generación:', reporte.fecha_creacion.strftime('%d/%m/%Y %H:%M')],
        ['Período Analizado:', f"{reporte.fecha_inicio.strftime('%d/%m/%Y')} - {reporte.fecha_fin.strftime('%d/%m/%Y')}"],
        ['Usuario:', str(reporte.id_usuario) if reporte.id_usuario else 'No especificado'],
    ]
    
    if reporte.descripcion:
        info_data.append(['Descripción:', reporte.descripcion])
    
    info_table = Table(info_data, colWidths=[2.5*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ddd')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 30))
    
    # Contenido específico según tipo de reporte
    if reporte.tipo_reporte == 'gastos_categoria' and 'labels' in datos:
        story.append(Paragraph("Análisis de Gastos por Categoría", header_style))
        
        # Tabla de gastos
        gastos_data = [['Categoría', 'Monto (MXN)', 'Cantidad', 'Porcentaje']]
        total = sum(datos['data'])
        
        for i, (label, monto, count) in enumerate(zip(datos['labels'], datos['data'], datos.get('counts', [0]*len(datos['labels'])))):
            porcentaje = (monto / total * 100) if total > 0 else 0
            gastos_data.append([
                label,
                f"${monto:,.2f}",
                str(count),
                f"{porcentaje:.1f}%"
            ])
        
        # Fila de total
        gastos_data.append(['TOTAL', f"${total:,.2f}", str(sum(datos.get('counts', []))), '100.0%'])
        
        gastos_table = Table(gastos_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1*inch])
        gastos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6C5CE7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f1f3f4')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(gastos_table)
        
    elif reporte.tipo_reporte == 'ingresos_egresos':
        story.append(Paragraph("Análisis de Ingresos vs Egresos", header_style))
        
        ingresos = datos['data'][0] if len(datos['data']) > 0 else 0
        egresos = datos['data'][1] if len(datos['data']) > 1 else 0
        balance = ingresos - egresos
        
        ie_data = [
            ['Concepto', 'Monto (MXN)', 'Porcentaje'],
            ['Ingresos', f"${ingresos:,.2f}", '100.0%' if ingresos > 0 else '0.0%'],
            ['Egresos', f"${egresos:,.2f}", f"{(egresos/ingresos*100):.1f}%" if ingresos > 0 else '0.0%'],
            ['Balance', f"${balance:,.2f}", f"{(balance/ingresos*100):.1f}%" if ingresos > 0 else '0.0%'],
        ]
        
        ie_table = Table(ie_data, colWidths=[2*inch, 2*inch, 1.5*inch])
        ie_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6C5CE7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.green if balance >= 0 else colors.red),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(ie_table)
        
    elif reporte.tipo_reporte == 'subcuentas_analisis' and 'labels' in datos:
        story.append(Paragraph("Análisis de Subcuentas", header_style))
        
        sc_data = [['Tipo de Subcuenta', 'Saldo Total (MXN)', 'Cantidad', 'Promedio (MXN)']]
        
        for i, label in enumerate(datos['labels']):
            saldo = datos['saldos'][i] if i < len(datos['saldos']) else 0
            cantidad = datos['cantidades'][i] if i < len(datos['cantidades']) else 0
            promedio = saldo / cantidad if cantidad > 0 else 0
            
            sc_data.append([
                label,
                f"${saldo:,.2f}",
                str(cantidad),
                f"${promedio:,.2f}"
            ])
        
        # Total
        total_saldo = sum(datos['saldos'])
        total_cantidad = sum(datos['cantidades'])
        sc_data.append(['TOTAL', f"${total_saldo:,.2f}", str(total_cantidad), f"${total_saldo/total_cantidad if total_cantidad > 0 else 0:,.2f}"])
        
        sc_table = Table(sc_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1.5*inch])
        sc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6C5CE7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f1f3f4')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(sc_table)
    
    # Pie de página con fecha
    story.append(Spacer(1, 50))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=1
    )
    story.append(Paragraph(f"Generado por FinGest el {datetime.now().strftime('%d/%m/%Y %H:%M')}", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    
    # Nombre de archivo más descriptivo
    filename = f"FinGest_{reporte.get_tipo_reporte_display().replace(' ', '_')}_{reporte.fecha_creacion.strftime('%Y%m%d_%H%M')}.pdf"
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def exportar_excel(reporte, datos):
    """Exporta reporte a Excel con formato profesional"""
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils.dataframe import dataframe_to_rows
    from openpyxl.chart import PieChart, BarChart, Reference
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    # Nombre de archivo más descriptivo
    filename = f"FinGest_{reporte.get_tipo_reporte_display().replace(' ', '_')}_{reporte.fecha_creacion.strftime('%Y%m%d_%H%M')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        # Hoja de información general
        info_data = {
            'Campo': ['Título', 'Tipo de Reporte', 'Fecha de Generación', 'Período Inicio', 'Período Fin', 'Usuario', 'Descripción'],
            'Valor': [
                reporte.titulo,
                reporte.get_tipo_reporte_display(),
                reporte.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
                reporte.fecha_inicio.strftime('%d/%m/%Y'),
                reporte.fecha_fin.strftime('%d/%m/%Y'),
                str(reporte.id_usuario) if reporte.id_usuario else 'No especificado',
                reporte.descripcion or 'Sin descripción'
            ]
        }
        
        info_df = pd.DataFrame(info_data)
        info_df.to_excel(writer, sheet_name='Información', index=False)
        
        # Formatear hoja de información
        ws_info = writer.sheets['Información']
        ws_info['A1'].font = Font(bold=True, color='FFFFFF')
        ws_info['B1'].font = Font(bold=True, color='FFFFFF')
        ws_info['A1'].fill = PatternFill(start_color='6C5CE7', end_color='6C5CE7', fill_type='solid')
        ws_info['B1'].fill = PatternFill(start_color='6C5CE7', end_color='6C5CE7', fill_type='solid')
        
        # Ajustar ancho de columnas
        ws_info.column_dimensions['A'].width = 20
        ws_info.column_dimensions['B'].width = 40
        
        # Hoja de datos específicos según tipo de reporte
        if reporte.tipo_reporte == 'gastos_categoria' and 'labels' in datos:
            # Datos de gastos por categoría
            total = sum(datos['data'])
            gastos_data = {
                'Categoría': datos['labels'],
                'Monto': datos['data'],
                'Cantidad': datos.get('counts', [0] * len(datos['labels'])),
                'Porcentaje': [(monto / total * 100) if total > 0 else 0 for monto in datos['data']]
            }
            
            gastos_df = pd.DataFrame(gastos_data)
            gastos_df.to_excel(writer, sheet_name='Gastos por Categoría', index=False)
            
            # Formatear hoja de gastos
            ws_gastos = writer.sheets['Gastos por Categoría']
            
            # Encabezados
            for col in range(1, 5):
                cell = ws_gastos.cell(row=1, column=col)
                cell.font = Font(bold=True, color='FFFFFF')
                cell.fill = PatternFill(start_color='6C5CE7', end_color='6C5CE7', fill_type='solid')
                cell.alignment = Alignment(horizontal='center')
            
            # Formatear montos
            for row in range(2, len(gastos_df) + 2):
                ws_gastos.cell(row=row, column=2).number_format = '"$"#,##0.00'
                ws_gastos.cell(row=row, column=4).number_format = '0.0"%"'
            
            # Ajustar anchos
            ws_gastos.column_dimensions['A'].width = 20
            ws_gastos.column_dimensions['B'].width = 15
            ws_gastos.column_dimensions['C'].width = 12
            ws_gastos.column_dimensions['D'].width = 12
            
        elif reporte.tipo_reporte == 'ingresos_egresos':
            ingresos = datos['data'][0] if len(datos['data']) > 0 else 0
            egresos = datos['data'][1] if len(datos['data']) > 1 else 0
            balance = ingresos - egresos
            
            ie_data = {
                'Concepto': ['Ingresos', 'Egresos', 'Balance'],
                'Monto': [ingresos, egresos, balance],
                'Porcentaje': [100.0 if ingresos > 0 else 0, (egresos/ingresos*100) if ingresos > 0 else 0, (balance/ingresos*100) if ingresos > 0 else 0]
            }
            
            ie_df = pd.DataFrame(ie_data)
            ie_df.to_excel(writer, sheet_name='Ingresos vs Egresos', index=False)
            
            # Formatear hoja
            ws_ie = writer.sheets['Ingresos vs Egresos']
            
            # Encabezados
            for col in range(1, 4):
                cell = ws_ie.cell(row=1, column=col)
                cell.font = Font(bold=True, color='FFFFFF')
                cell.fill = PatternFill(start_color='6C5CE7', end_color='6C5CE7', fill_type='solid')
                cell.alignment = Alignment(horizontal='center')
            
            # Formatear datos
            for row in range(2, 5):
                ws_ie.cell(row=row, column=2).number_format = '"$"#,##0.00'
                ws_ie.cell(row=row, column=3).number_format = '0.0"%"'
                
                # Color para balance
                if row == 4:  # Fila del balance
                    color = '00B894' if balance >= 0 else 'E17055'
                    ws_ie.cell(row=row, column=2).font = Font(bold=True, color=color)
            
            # Ajustar anchos
            ws_ie.column_dimensions['A'].width = 15
            ws_ie.column_dimensions['B'].width = 15
            ws_ie.column_dimensions['C'].width = 12
            
        elif reporte.tipo_reporte == 'subcuentas_analisis' and 'labels' in datos:
            sc_data = {
                'Tipo de Subcuenta': datos['labels'],
                'Saldo Total': datos['saldos'],
                'Cantidad': datos['cantidades'],
                'Promedio': [saldo / cantidad if cantidad > 0 else 0 for saldo, cantidad in zip(datos['saldos'], datos['cantidades'])]
            }
            
            sc_df = pd.DataFrame(sc_data)
            sc_df.to_excel(writer, sheet_name='Análisis Subcuentas', index=False)
            
            # Formatear hoja
            ws_sc = writer.sheets['Análisis Subcuentas']
            
            # Encabezados
            for col in range(1, 5):
                cell = ws_sc.cell(row=1, column=col)
                cell.font = Font(bold=True, color='FFFFFF')
                cell.fill = PatternFill(start_color='6C5CE7', end_color='6C5CE7', fill_type='solid')
                cell.alignment = Alignment(horizontal='center')
            
            # Formatear montos
            for row in range(2, len(sc_df) + 2):
                ws_sc.cell(row=row, column=2).number_format = '"$"#,##0.00'
                ws_sc.cell(row=row, column=4).number_format = '"$"#,##0.00'
            
            # Ajustar anchos
            ws_sc.column_dimensions['A'].width = 20
            ws_sc.column_dimensions['B'].width = 15
            ws_sc.column_dimensions['C'].width = 12
            ws_sc.column_dimensions['D'].width = 15
        
        elif reporte.tipo_reporte == 'flujo_efectivo' and 'labels' in datos:
            flujo_data = {
                'Período': datos['labels'],
                'Ingresos': datos['ingresos'],
                'Egresos': datos['egresos'],
                'Balance': [ingresos - egresos for ingresos, egresos in zip(datos['ingresos'], datos['egresos'])]
            }
            
            flujo_df = pd.DataFrame(flujo_data)
            flujo_df.to_excel(writer, sheet_name='Flujo de Efectivo', index=False)
            
            # Formatear hoja
            ws_flujo = writer.sheets['Flujo de Efectivo']
            
            # Encabezados
            for col in range(1, 5):
                cell = ws_flujo.cell(row=1, column=col)
                cell.font = Font(bold=True, color='FFFFFF')
                cell.fill = PatternFill(start_color='6C5CE7', end_color='6C5CE7', fill_type='solid')
                cell.alignment = Alignment(horizontal='center')
            
            # Formatear montos
            for row in range(2, len(flujo_df) + 2):
                for col in range(2, 5):
                    ws_flujo.cell(row=row, column=col).number_format = '"$"#,##0.00'
                    
                    # Color para balance
                    if col == 4:  # Columna de balance
                        balance_val = flujo_df.iloc[row-2]['Balance']
                        color = '00B894' if balance_val >= 0 else 'E17055'
                        ws_flujo.cell(row=row, column=col).font = Font(color=color)
            
            # Ajustar anchos
            ws_flujo.column_dimensions['A'].width = 15
            ws_flujo.column_dimensions['B'].width = 15
            ws_flujo.column_dimensions['C'].width = 15
            ws_flujo.column_dimensions['D'].width = 15
    
    return response

def exportar_csv(reporte, datos):
    """Exporta reporte a CSV con formato estructurado"""
    import csv
    from io import StringIO
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    
    # Nombre de archivo más descriptivo
    filename = f"FinGest_{reporte.get_tipo_reporte_display().replace(' ', '_')}_{reporte.fecha_creacion.strftime('%Y%m%d_%H%M')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Agregar BOM para Excel
    response.write('\ufeff')
    
    writer = csv.writer(response)
    
    # Encabezado del reporte
    writer.writerow(['FinGest - Reporte Financiero'])
    writer.writerow([])
    writer.writerow(['Información del Reporte'])
    writer.writerow(['Título', reporte.titulo])
    writer.writerow(['Tipo', reporte.get_tipo_reporte_display()])
    writer.writerow(['Fecha de Generación', reporte.fecha_creacion.strftime('%d/%m/%Y %H:%M')])
    writer.writerow(['Período Inicio', reporte.fecha_inicio.strftime('%d/%m/%Y')])
    writer.writerow(['Período Fin', reporte.fecha_fin.strftime('%d/%m/%Y')])
    writer.writerow(['Usuario', str(reporte.id_usuario) if reporte.id_usuario else 'No especificado'])
    if reporte.descripcion:
        writer.writerow(['Descripción', reporte.descripcion])
    writer.writerow([])
    writer.writerow([])
    
    # Datos específicos según tipo de reporte
    if reporte.tipo_reporte == 'gastos_categoria' and 'labels' in datos:
        writer.writerow(['Análisis de Gastos por Categoría'])
        writer.writerow([])
        writer.writerow(['Categoría', 'Monto (MXN)', 'Cantidad', 'Porcentaje (%)'])
        
        total = sum(datos['data'])
        for i, label in enumerate(datos['labels']):
            monto = datos['data'][i]
            cantidad = datos.get('counts', [0] * len(datos['labels']))[i]
            porcentaje = (monto / total * 100) if total > 0 else 0
            writer.writerow([label, f"{monto:.2f}", cantidad, f"{porcentaje:.1f}"])
        
        writer.writerow([])
        writer.writerow(['TOTAL', f"{total:.2f}", sum(datos.get('counts', [])), '100.0'])
        
    elif reporte.tipo_reporte == 'ingresos_egresos':
        writer.writerow(['Análisis de Ingresos vs Egresos'])
        writer.writerow([])
        writer.writerow(['Concepto', 'Monto (MXN)', 'Porcentaje (%)'])
        
        ingresos = datos['data'][0] if len(datos['data']) > 0 else 0
        egresos = datos['data'][1] if len(datos['data']) > 1 else 0
        balance = ingresos - egresos
        
        writer.writerow(['Ingresos', f"{ingresos:.2f}", '100.0' if ingresos > 0 else '0.0'])
        writer.writerow(['Egresos', f"{egresos:.2f}", f"{(egresos/ingresos*100):.1f}" if ingresos > 0 else '0.0'])
        writer.writerow(['Balance', f"{balance:.2f}", f"{(balance/ingresos*100):.1f}" if ingresos > 0 else '0.0'])
        
    elif reporte.tipo_reporte == 'subcuentas_analisis' and 'labels' in datos:
        writer.writerow(['Análisis de Subcuentas'])
        writer.writerow([])
        writer.writerow(['Tipo de Subcuenta', 'Saldo Total (MXN)', 'Cantidad', 'Promedio (MXN)'])
        
        for i, label in enumerate(datos['labels']):
            saldo = datos['saldos'][i] if i < len(datos['saldos']) else 0
            cantidad = datos['cantidades'][i] if i < len(datos['cantidades']) else 0
            promedio = saldo / cantidad if cantidad > 0 else 0
            
            writer.writerow([label, f"{saldo:.2f}", cantidad, f"{promedio:.2f}"])
        
        writer.writerow([])
        total_saldo = sum(datos['saldos'])
        total_cantidad = sum(datos['cantidades'])
        writer.writerow(['TOTAL', f"{total_saldo:.2f}", total_cantidad, f"{total_saldo/total_cantidad if total_cantidad > 0 else 0:.2f}"])
        
    elif reporte.tipo_reporte == 'flujo_efectivo' and 'labels' in datos:
        writer.writerow(['Flujo de Efectivo'])
        writer.writerow([])
        writer.writerow(['Período', 'Ingresos (MXN)', 'Egresos (MXN)', 'Balance (MXN)'])
        
        for i, periodo in enumerate(datos['labels']):
            ingresos = datos['ingresos'][i] if i < len(datos['ingresos']) else 0
            egresos = datos['egresos'][i] if i < len(datos['egresos']) else 0
            balance = ingresos - egresos
            
            writer.writerow([periodo, f"{ingresos:.2f}", f"{egresos:.2f}", f"{balance:.2f}"])
    
    # Pie de página
    writer.writerow([])
    writer.writerow([])
    writer.writerow(['Generado por FinGest'])
    writer.writerow([f'Fecha de generación: {datetime.now().strftime("%d/%m/%Y %H:%M")}'])
    
    return response

def procesar_datos_para_template(tipo_reporte, datos):
    """Procesa los datos del reporte para que sean más fáciles de usar en el template"""
    if not datos:
        return {}
    
    if tipo_reporte == 'gastos_categoria' and 'labels' in datos:
        # Crear lista de diccionarios para gastos por categoría
        total = sum(datos.get('data', []))
        resultado = []
        
        for i, label in enumerate(datos['labels']):
            monto = datos['data'][i] if i < len(datos['data']) else 0
            cantidad = datos.get('counts', [])[i] if i < len(datos.get('counts', [])) else 0
            porcentaje = (monto / total * 100) if total > 0 else 0
            
            resultado.append({
                'categoria': label,
                'monto': monto,
                'cantidad': cantidad,
                'porcentaje': porcentaje
            })
        
        return {
            'tipo': 'gastos_categoria',
            'items': resultado,
            'total': total,
            'total_cantidad': sum(datos.get('counts', []))
        }
    
    elif tipo_reporte == 'ingresos_egresos' and 'data' in datos:
        ingresos = datos['data'][0] if len(datos['data']) > 0 else 0
        egresos = datos['data'][1] if len(datos['data']) > 1 else 0
        balance = ingresos - egresos
        
        return {
            'tipo': 'ingresos_egresos',
            'ingresos': ingresos,
            'egresos': egresos,
            'balance': balance,
            'porcentaje_egresos': (egresos / ingresos * 100) if ingresos > 0 else 0,
            'porcentaje_balance': (balance / ingresos * 100) if ingresos > 0 else 0
        }
    
    elif tipo_reporte == 'subcuentas_analisis' and 'labels' in datos:
        resultado = []
        
        for i, label in enumerate(datos['labels']):
            saldo = datos['saldos'][i] if i < len(datos['saldos']) else 0
            cantidad = datos['cantidades'][i] if i < len(datos['cantidades']) else 0
            promedio = saldo / cantidad if cantidad > 0 else 0
            
            resultado.append({
                'tipo': label,
                'saldo': saldo,
                'cantidad': cantidad,
                'promedio': promedio
            })
        
        total_saldo = sum(datos['saldos'])
        total_cantidad = sum(datos['cantidades'])
        promedio_total = total_saldo / total_cantidad if total_cantidad > 0 else 0
        
        return {
            'tipo': 'subcuentas_analisis',
            'items': resultado,
            'total_saldo': total_saldo,
            'total_cantidad': total_cantidad,
            'promedio_total': promedio_total
        }
    
    elif tipo_reporte == 'flujo_efectivo' and 'labels' in datos:
        resultado = []
        
        for i, periodo in enumerate(datos['labels']):
            ingresos = datos['ingresos'][i] if i < len(datos['ingresos']) else 0
            egresos = datos['egresos'][i] if i < len(datos['egresos']) else 0
            balance = ingresos - egresos
            
            resultado.append({
                'periodo': periodo,
                'ingresos': ingresos,
                'egresos': egresos,
                'balance': balance
            })
        
        return {
            'tipo': 'flujo_efectivo',
            'items': resultado
        }
    
    return {'tipo': 'otros', 'datos_raw': datos}