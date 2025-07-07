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
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF
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
    
    # Manejar fechas personalizadas
    if periodo == 'personalizado':
        fecha_inicio_str = request.GET.get('fecha_inicio')
        fecha_fin_str = request.GET.get('fecha_fin')
        
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
    
    # Si es una request AJAX para actualizar filtros
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            stats = calcular_estadisticas_generales(request.user, fecha_inicio, fecha_fin)
            gastos_categoria = get_gastos_por_categoria(request.user, fecha_inicio, fecha_fin)
            ingresos_egresos = get_ingresos_vs_egresos(request.user, fecha_inicio, fecha_fin)
            subcuentas_data = get_estadisticas_subcuentas(request.user)
            flujo_mensual = get_flujo_mensual(request.user, fecha_inicio, fecha_fin)
            
            return JsonResponse({
                'success': True,
                'stats': stats,
                'gastos_categoria': gastos_categoria,
                'ingresos_egresos': ingresos_egresos,
                'subcuentas_data': subcuentas_data,
                'flujo_mensual': flujo_mensual,
                'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
                'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
                'periodo': periodo,
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
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
    reportes_recientes = Reporte.objects.filter(id_usuario=request.user).order_by('-fecha_creacion')[:5]
    
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
    
    # Total en subcuentas (incluir independientes)
    total_subcuentas = SubCuenta.objects.filter(
        Q(id_cuenta__id_usuario=usuario) | Q(propietario=usuario), 
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
    
    # Número de cuentas y subcuentas (incluir independientes)
    num_cuentas = cuentas.count()
    num_subcuentas = SubCuenta.objects.filter(
        Q(id_cuenta__id_usuario=usuario) | Q(propietario=usuario), 
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
    """Obtiene gastos agrupados por categoría de movimientos"""
    # Obtener gastos agrupados por categoría
    gastos_por_categoria = Movimiento.objects.filter(
        id_cuenta__id_usuario=usuario,
        tipo='egreso',
        fecha_movimiento__range=[fecha_inicio, fecha_fin]
    ).values('categoria').annotate(
        total=Sum('monto'),
        count=Count('id')
    ).order_by('-total')
    
    labels = []
    data = []
    counts = []
    
    if gastos_por_categoria.exists():
        for gasto in gastos_por_categoria:
            categoria_key = gasto['categoria'] or 'otros'
            
            # Buscar el nombre con emoji para la categoría
            nombre_categoria = 'Otros'
            for cat_key, cat_display in Movimiento.CATEGORIAS_GASTOS:
                if cat_key == categoria_key:
                    nombre_categoria = cat_display
                    break
            
            labels.append(nombre_categoria)
            data.append(float(gasto['total']))
            counts.append(gasto['count'])
    else:
        # Datos por defecto si no hay gastos
        labels = ['Sin gastos registrados']
        data = [0]
        counts = [0]
    
    return {
        'labels': labels,
        'data': data,
        'counts': counts,
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
        'total_transacciones': transacciones.count(),
    }

def get_estadisticas_subcuentas(usuario):
    """Obtiene estadísticas de subcuentas"""
    # Incluir tanto subcuentas vinculadas como independientes
    subcuentas = SubCuenta.objects.filter(
        Q(id_cuenta__id_usuario=usuario) | Q(propietario=usuario),
        activa=True
    ).select_related('id_cuenta')
    
    if not subcuentas.exists():
        return {
            'labels': ['Sin subcuentas'],
            'saldos': [0],
            'cantidades': [0],
            'tipos_detalle': [],
        }
    
    # Agrupar por tipo de subcuenta
    tipos_subcuentas = {}
    tipos_detalle = []
    
    for subcuenta in subcuentas:
        tipo = subcuenta.tipo or 'otros'
        tipo_display = subcuenta.get_tipo_display() or tipo.title()
        
        # Para la visualización, usar el display name
        if tipo_display not in tipos_subcuentas:
            tipos_subcuentas[tipo_display] = {
                'saldo_total': 0,
                'cantidad': 0,
                'es_negocio': subcuenta.es_negocio,
                'subcuentas': []
            }
        
        tipos_subcuentas[tipo_display]['saldo_total'] += float(subcuenta.saldo)
        tipos_subcuentas[tipo_display]['cantidad'] += 1
        tipos_subcuentas[tipo_display]['subcuentas'].append({
            'nombre': subcuenta.nombre,
            'saldo': float(subcuenta.saldo),
            'es_independiente': subcuenta.es_independiente(),
            'color': subcuenta.color
        })
        
        # Agregar detalles para el template
        tipos_detalle.append({
            'nombre': subcuenta.nombre,
            'tipo': tipo_display,
            'saldo': float(subcuenta.saldo),
            'es_negocio': subcuenta.es_negocio,
            'es_independiente': subcuenta.es_independiente(),
            'color': subcuenta.color
        })
    
    labels = list(tipos_subcuentas.keys())
    saldos = [data['saldo_total'] for data in tipos_subcuentas.values()]
    cantidades = [data['cantidad'] for data in tipos_subcuentas.values()]
    
    return {
        'labels': labels,
        'saldos': saldos,
        'cantidades': cantidades,
        'tipos_detalle': tipos_detalle,
        'total_subcuentas': len(subcuentas),
        'total_saldo': sum(saldos),
        'tipos_subcuentas': tipos_subcuentas,
    }

def get_flujo_mensual(usuario, fecha_inicio, fecha_fin):
    """Obtiene flujo de efectivo mensual"""
    meses = []
    ingresos_mes = []
    egresos_mes = []
    
    fecha_actual = fecha_inicio
    
    # Si el período es muy corto, mostrar por días
    diferencia_dias = (fecha_fin - fecha_inicio).days
    if diferencia_dias <= 7:
        # Mostrar por días
        while fecha_actual <= fecha_fin:
            transacciones_dia = Movimiento.objects.filter(
                id_cuenta__id_usuario=usuario,
                fecha_movimiento=fecha_actual
            )
            
            ingresos = transacciones_dia.filter(
                tipo='ingreso'
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            egresos = transacciones_dia.filter(
                tipo='egreso'
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            meses.append(fecha_actual.strftime('%d/%m'))
            ingresos_mes.append(float(ingresos))
            egresos_mes.append(float(egresos))
            
            fecha_actual += timedelta(days=1)
    else:
        # Mostrar por meses
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
            
            meses.append(fecha_actual.strftime('%b %Y'))
            ingresos_mes.append(float(ingresos))
            egresos_mes.append(float(egresos))
            
            # Avanzar al siguiente mes
            fecha_actual = (fecha_actual + timedelta(days=32)).replace(day=1)
    
    # Si no hay datos, mostrar valores por defecto
    if not meses:
        meses = [fecha_inicio.strftime('%b %Y')]
        ingresos_mes = [0]
        egresos_mes = [0]
    
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
    """Exporta reporte a PDF con formato ultra profesional y visualmente atractivo"""
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.graphics.shapes import Drawing, Rect, String
    from reportlab.graphics import renderPDF
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=50, leftMargin=50,
        topMargin=80, bottomMargin=80
    )
    styles = getSampleStyleSheet()
    story = []
    
    # Estilos personalizados ultra profesionales
    title_style = ParagraphStyle(
        'UltraTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#2C3E50'),
        alignment=TA_CENTER,
        spaceAfter=35,
        fontName='Helvetica-Bold',
        leading=32
    )
    
    brand_style = ParagraphStyle(
        'BrandStyle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#6C5CE7'),
        alignment=TA_CENTER,
        spaceBefore=5,
        spaceAfter=25,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'ProfessionalHeader',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#34495E'),
        spaceBefore=25,
        spaceAfter=15,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderPadding=0
    )
    
    subheader_style = ParagraphStyle(
        'SubHeader',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#5D6D7E'),
        spaceBefore=15,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )
    
    summary_style = ParagraphStyle(
        'SummaryStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2C3E50'),
        spaceBefore=5,
        spaceAfter=5,
        fontName='Helvetica',
        leading=14
    )
    
    # ENCABEZADO ULTRA PROFESIONAL
    # Crear un rectángulo de fondo para el header
    header_bg = Drawing(500, 60)
    header_bg.add(Rect(0, 0, 500, 60, fillColor=colors.HexColor('#F8F9FA'), strokeColor=None))
    story.append(header_bg)
    story.append(Spacer(1, -50))
    
    # Logo y brand (simulado con texto estilizado)
    story.append(Paragraph("FINGEST", brand_style))
    story.append(Paragraph("REPORTE FINANCIERO PROFESIONAL", title_style))
    
    # Línea decorativa
    line_drawing = Drawing(500, 5)
    line_drawing.add(Rect(0, 2, 500, 1, fillColor=colors.HexColor('#6C5CE7'), strokeColor=None))
    story.append(line_drawing)
    story.append(Spacer(1, 20))
    
    # INFORMACIÓN DEL REPORTE CON DISEÑO PREMIUM
    story.append(Paragraph("INFORMACIÓN DEL REPORTE", header_style))
    
    # Crear tabla de información más elegante
    info_data = [
        ['Tipo de Reporte:', reporte.get_tipo_reporte_display()],
        ['Fecha de Generación:', reporte.fecha_creacion.strftime('%d de %B de %Y a las %H:%M hrs')],
        ['Período Analizado:', f"Del {reporte.fecha_inicio.strftime('%d de %B de %Y')} al {reporte.fecha_fin.strftime('%d de %B de %Y')}"],
        ['Usuario:', str(reporte.id_usuario) if reporte.id_usuario else 'No especificado'],
    ]
    
    if reporte.descripcion:
        info_data.append(['Descripción:', reporte.descripcion])
    
    info_table = Table(info_data, colWidths=[2.8*inch, 4.2*inch])
    info_table.setStyle(TableStyle([
        # Estilo del encabezado
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F4FD')),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#FFFFFF')),
        
        # Bordes y líneas
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
        ('LINEBEFORE', (1, 0), (1, -1), 0.5, colors.HexColor('#BDC3C7')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#34495E')),
        
        # Fuentes y colores
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2C3E50')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#34495E')),
        
        # Alineación y espaciado
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 35))
    
    # Contenido específico según tipo de reporte con diseño ultra premium
    if reporte.tipo_reporte == 'gastos_categoria' and 'labels' in datos:
        story.append(Paragraph("ANÁLISIS DETALLADO DE GASTOS POR CATEGORÍA", header_style))
        
        # Resumen ejecutivo
        total = sum(datos['data'])
        total_transacciones = sum(datos.get('counts', []))
        promedio_por_categoria = total / len(datos['labels']) if datos['labels'] else 0
        
        summary_data = [
            ['RESUMEN EJECUTIVO'],
            [f'Gasto Total: ${total:,.2f} MXN'],
            [f'Total de Transacciones: {total_transacciones:,}'],
            [f'Promedio por Categoría: ${promedio_por_categoria:,.2f} MXN'],
            [f'Categorías Analizadas: {len(datos["labels"])}']
        ]
        
        summary_table = Table(summary_data, colWidths=[7*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#EBF5FF')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2C3E50')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#3498DB')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 25))
        
        # Tabla principal de gastos con diseño premium
        story.append(Paragraph("DESGLOSE DETALLADO POR CATEGORÍA", subheader_style))
        
        gastos_data = [['CATEGORÍA', 'MONTO (MXN)', 'CANTIDAD', 'PORCENTAJE', 'PROMEDIO']]
        
        for i, (label, monto, count) in enumerate(zip(datos['labels'], datos['data'], datos.get('counts', [0]*len(datos['labels'])))):
            porcentaje = (monto / total * 100) if total > 0 else 0
            promedio_item = monto / count if count > 0 else 0
            
            gastos_data.append([
                label,
                f"${monto:,.2f}",
                f"{count:,}",
                f"{porcentaje:.1f}%",
                f"${promedio_item:,.2f}"
            ])
        
        # Fila de total con estilo especial
        gastos_data.append([
            'TOTAL GENERAL', 
            f"${total:,.2f}", 
            f"{sum(datos.get('counts', [])):,}", 
            '100.0%',
            f"${total/len(datos['labels']) if datos['labels'] else 0:,.2f}"
        ])
        
        gastos_table = Table(gastos_data, colWidths=[2.2*inch, 1.3*inch, 1*inch, 1*inch, 1.2*inch])
        gastos_table.setStyle(TableStyle([
            # Encabezado principal
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Filas de datos
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 10),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            
            # Fila de total
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8F8F5')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#27AE60')),
            
            # Alternancia de colores en filas
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F8F9FA')]),
            
            # Bordes y líneas
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2C3E50')),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#27AE60')),
            
            # Espaciado
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(gastos_table)
        
        # Insights automáticos
        story.append(Spacer(1, 25))
        story.append(Paragraph("INSIGHTS AUTOMÁTICOS", subheader_style))
        
        # Encontrar la categoría con mayor gasto
        max_index = datos['data'].index(max(datos['data'])) if datos['data'] else 0
        categoria_mayor = datos['labels'][max_index] if max_index < len(datos['labels']) else 'N/A'
        porcentaje_mayor = (max(datos['data']) / total * 100) if total > 0 else 0
        
        insights = [
            f"• La categoría '{categoria_mayor}' representa el mayor gasto con {porcentaje_mayor:.1f}% del total",
            f"• Promedio de gasto por transacción: ${total/total_transacciones if total_transacciones > 0 else 0:,.2f} MXN",
            f"• Distribución: {len([x for x in datos['data'] if x > promedio_por_categoria])} categorías están por encima del promedio"
        ]
        
        for insight in insights:
            story.append(Paragraph(insight, summary_style))
            story.append(Spacer(1, 5))
        
    elif reporte.tipo_reporte == 'ingresos_egresos':
        story.append(Paragraph("ANÁLISIS FINANCIERO: INGRESOS VS EGRESOS", header_style))
        
        ingresos = datos['data'][0] if len(datos['data']) > 0 else 0
        egresos = datos['data'][1] if len(datos['data']) > 1 else 0
        balance = ingresos - egresos
        tasa_ahorro = (balance / ingresos * 100) if ingresos > 0 else 0
        
        # Dashboard financiero visual
        dashboard_data = [
            ['DASHBOARD FINANCIERO EJECUTIVO'],
            [f'Total de Ingresos: ${ingresos:,.2f} MXN'],
            [f'Total de Egresos: ${egresos:,.2f} MXN'],
            [f'Balance Neto: ${balance:,.2f} MXN'],
            [f'Tasa de Ahorro: {tasa_ahorro:.1f}%'],
            [f'Ratio de Gastos: {(egresos/ingresos*100) if ingresos > 0 else 0:.1f}%']
        ]
        
        # Color del balance
        balance_color = colors.HexColor('#27AE60') if balance >= 0 else colors.HexColor('#E74C3C')
        
        dashboard_table = Table(dashboard_data, colWidths=[7*inch])
        dashboard_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 1), (0, 2), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 3), (0, 3), balance_color),  # Color del balance
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#34495E')),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(dashboard_table)
        story.append(Spacer(1, 25))
        
        # Tabla comparativa detallada
        story.append(Paragraph("ANÁLISIS COMPARATIVO DETALLADO", subheader_style))
        
        ie_data = [
            ['CONCEPTO', 'MONTO (MXN)', 'PORCENTAJE', 'EVALUACIÓN'],
            ['Ingresos Totales', f"${ingresos:,.2f}", '100.0%', 'Base de cálculo'],
            ['Egresos Totales', f"${egresos:,.2f}", f"{(egresos/ingresos*100):.1f}%" if ingresos > 0 else '0.0%', 
             'Alto' if egresos/ingresos > 0.8 else 'Controlado' if egresos/ingresos <= 0.6 else 'Moderado'],
            ['Balance Final', f"${balance:,.2f}", f"{(balance/ingresos*100):.1f}%" if ingresos > 0 else '0.0%',
             'Excelente' if balance > 0 else 'Déficit'],
        ]
        
        ie_table = Table(ie_data, colWidths=[2*inch, 1.8*inch, 1.5*inch, 1.7*inch])
        ie_table.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Filas de datos
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ALIGN', (1, 1), (2, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            
            # Colores especiales para balance
            ('TEXTCOLOR', (0, -1), (-1, -1), balance_color),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            
            # Alternancia de colores
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2C3E50')),
            
            # Espaciado
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(ie_table)
        
        # Recomendaciones automáticas
        story.append(Spacer(1, 25))
        story.append(Paragraph("RECOMENDACIONES FINANCIERAS", subheader_style))
        
        recomendaciones = []
        if balance < 0:
            recomendaciones.append("URGENTE: Tienes un déficit financiero. Revisa tus gastos y busca reducir egresos.")
            recomendaciones.append("Elabora un presupuesto detallado para identificar gastos innecesarios.")
        elif tasa_ahorro < 10:
            recomendaciones.append("Tu tasa de ahorro es baja. Considera incrementar tus ingresos o reducir gastos.")
            recomendaciones.append("Meta recomendada: Ahorra al menos el 15-20% de tus ingresos.")
        else:
            recomendaciones.append("¡Excelente! Mantienes un balance positivo.")
            recomendaciones.append("Considera invertir tu excedente para hacer crecer tu patrimonio.")
        
        for rec in recomendaciones:
            story.append(Paragraph(f"• {rec}", summary_style))
            story.append(Spacer(1, 5))
        
    elif reporte.tipo_reporte == 'subcuentas_analisis' and 'labels' in datos:
        story.append(Paragraph("ANÁLISIS INTEGRAL DE SUBCUENTAS", header_style))
        
        # Resumen ejecutivo de subcuentas
        total_saldo = sum(datos['saldos'])
        total_cantidad = sum(datos['cantidades'])
        promedio_general = total_saldo / total_cantidad if total_cantidad > 0 else 0
        
        resumen_data = [
            ['RESUMEN EJECUTIVO DE SUBCUENTAS'],
            [f'Patrimonio Total: ${total_saldo:,.2f} MXN'],
            [f'Subcuentas Activas: {total_cantidad}'],
            [f'Saldo Promedio: ${promedio_general:,.2f} MXN'],
            [f'Tipos de Cuenta: {len(datos["labels"])}'],
            [f'Diversificación: {"Alta" if len(datos["labels"]) >= 3 else "Media" if len(datos["labels"]) == 2 else "Baja"}']
        ]
        
        resumen_table = Table(resumen_data, colWidths=[7*inch])
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8E44AD')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F4F2FF')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2C3E50')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#8E44AD')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(resumen_table)
        story.append(Spacer(1, 25))
        
        # Tabla detallada de subcuentas
        story.append(Paragraph("DESGLOSE DETALLADO POR TIPO DE SUBCUENTA", subheader_style))
        
        sc_data = [['TIPO DE SUBCUENTA', 'SALDO TOTAL', 'CANTIDAD', '% DEL TOTAL', 'PROMEDIO']]
        
        for i, label in enumerate(datos['labels']):
            saldo = datos['saldos'][i] if i < len(datos['saldos']) else 0
            cantidad = datos['cantidades'][i] if i < len(datos['cantidades']) else 0
            promedio = saldo / cantidad if cantidad > 0 else 0
            porcentaje = (saldo / total_saldo * 100) if total_saldo > 0 else 0
            
            sc_data.append([
                label,
                f"${saldo:,.2f}",
                str(cantidad),
                f"{porcentaje:.1f}%",
                f"${promedio:,.2f}"
            ])
        
        # Fila de totales
        sc_data.append([
            'TOTAL PATRIMONIAL', 
            f"${total_saldo:,.2f}", 
            str(total_cantidad), 
            '100.0%',
            f"${promedio_general:,.2f}"
        ])
        
        sc_table = Table(sc_data, colWidths=[2.2*inch, 1.4*inch, 1*inch, 1*inch, 1.2*inch])
        sc_table.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8E44AD')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Filas de datos
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 10),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            
            # Fila de total
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8F5E8')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#27AE60')),
            
            # Alternancia de colores
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F8F9FA')]),
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#8E44AD')),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#27AE60')),
            
            # Espaciado
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(sc_table)
        
        # Análisis y recomendaciones
        story.append(Spacer(1, 25))
        story.append(Paragraph("ANÁLISIS Y RECOMENDACIONES ESTRATÉGICAS", subheader_style))
        
        # Encontrar la subcuenta principal
        if datos['saldos']:
            max_saldo_idx = datos['saldos'].index(max(datos['saldos']))
            subcuenta_principal = datos['labels'][max_saldo_idx]
            porcentaje_principal = (max(datos['saldos']) / total_saldo * 100) if total_saldo > 0 else 0
            
            analisis = [
                f"• Subcuenta Principal: '{subcuenta_principal}' concentra {porcentaje_principal:.1f}% del patrimonio",
                f"• Distribución: {'Balanceada' if porcentaje_principal < 60 else 'Concentrada en una subcuenta'}",
                f"• Diversificación: {'Excelente' if len(datos['labels']) >= 4 else 'Buena' if len(datos['labels']) >= 2 else 'Limitada'}",
                f"• Saldo promedio por subcuenta: ${promedio_general:,.2f} MXN"
            ]
            
            if porcentaje_principal > 70:
                analisis.append("• Recomendación: Considera diversificar más tu patrimonio en diferentes subcuentas")
            elif total_cantidad < 3:
                analisis.append("• Sugerencia: Podrías beneficiarte de crear subcuentas adicionales para mejor organización")
            else:
                analisis.append("• Excelente organización financiera con buena distribución de subcuentas")
            
            for insight in analisis:
                story.append(Paragraph(insight, summary_style))
                story.append(Spacer(1, 5))
    
    # PIE DE PÁGINA PROFESIONAL Y BRAND
    story.append(Spacer(1, 40))
    
    # Línea separadora elegante
    separator = Drawing(500, 3)
    separator.add(Rect(0, 1, 500, 1, fillColor=colors.HexColor('#6C5CE7'), strokeColor=None))
    story.append(separator)
    story.append(Spacer(1, 20))
    
    # Información de contacto y legal
    footer_content = [
        ['FinGest - Gestión Financiera Inteligente'],
        ['Soporte: soporte@fingest.com | Tel: +52 (55) 1234-5678'],
        ['www.fingest.com | Descarga nuestra app móvil'],
        ['Este reporte es confidencial y de uso exclusivo del titular'],
        [f'Generado el {datetime.now().strftime("%d de %B de %Y a las %H:%M hrs")}']
    ]
    
    footer_table = Table(footer_content, colWidths=[7*inch])
    footer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#7F8C8D')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(footer_table)
    
    # Marca de agua de seguridad
    story.append(Spacer(1, 10))
    security_style = ParagraphStyle(
        'SecurityStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#95A5A6'),
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    story.append(Paragraph("Documento generado con tecnología segura FinGest | ID: " + 
                          f"FG-{reporte.id}-{reporte.fecha_creacion.strftime('%Y%m%d%H%M')}", security_style))
    
    doc.build(story)
    buffer.seek(0)
    
    # Nombre de archivo súper descriptivo
    tipo_clean = reporte.get_tipo_reporte_display().replace(' ', '_').replace('/', '-')
    fecha_str = reporte.fecha_creacion.strftime('%Y%m%d_%H%M')
    filename = f"FinGest_Reporte_{tipo_clean}_{fecha_str}.pdf"
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def exportar_excel(reporte, datos):
    """Exporta reporte a Excel con formato ultra profesional y limpio"""
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.chart import PieChart, BarChart, Reference, LineChart
    from openpyxl.utils import get_column_letter
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    # Nombre de archivo descriptivo y profesional
    tipo_clean = reporte.get_tipo_reporte_display().replace(' ', '_').replace('/', '-')
    fecha_str = reporte.fecha_creacion.strftime('%Y%m%d_%H%M')
    filename = f"FinGest_Reporte_{tipo_clean}_{fecha_str}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        # === HOJA 1: PORTADA EJECUTIVA ===
        portada_data = {
            'FINGEST - REPORTE FINANCIERO EJECUTIVO': [''],
            '': [''],
            'INFORMACIÓN DEL REPORTE': [''],
            'Título': [reporte.titulo],
            'Tipo': [reporte.get_tipo_reporte_display()],
            'Fecha de Generación': [reporte.fecha_creacion.strftime('%d de %B de %Y a las %H:%M hrs')],
            'Período de Análisis': [f"Del {reporte.fecha_inicio.strftime('%d/%m/%Y')} al {reporte.fecha_fin.strftime('%d/%m/%Y')}"],
            'Usuario': [str(reporte.id_usuario) if reporte.id_usuario else 'No especificado'],
            'Estado': ['COMPLETADO'],
            'Confidencialidad': ['CONFIDENCIAL - Uso exclusivo del titular'],
            '': [''],
            'Descripción': [reporte.descripcion or 'Análisis financiero integral generado automáticamente'],
        }
        
        portada_df = pd.DataFrame(portada_data)
        portada_df.to_excel(writer, sheet_name='PORTADA EJECUTIVA', index=False, header=False)
        
        # Formatear portada
        ws_portada = writer.sheets['PORTADA EJECUTIVA']
        
        # Título principal
        ws_portada['A1'].font = Font(name='Arial', bold=True, size=18, color='FFFFFF')
        ws_portada['A1'].fill = PatternFill(start_color='2C3E50', end_color='2C3E50', fill_type='solid')
        ws_portada['A1'].alignment = Alignment(horizontal='center', vertical='center')
        ws_portada.merge_cells('A1:B1')
        
        # Sección de información
        ws_portada['A3'].font = Font(name='Arial', bold=True, size=14, color='FFFFFF')
        ws_portada['A3'].fill = PatternFill(start_color='6C5CE7', end_color='6C5CE7', fill_type='solid')
        ws_portada['A3'].alignment = Alignment(horizontal='center')
        ws_portada.merge_cells('A3:B3')
        
        # Formatear filas de datos
        for row in range(4, 13):
            # Columna A (etiquetas)
            ws_portada.cell(row=row, column=1).font = Font(name='Arial', bold=True, size=11, color='2C3E50')
            ws_portada.cell(row=row, column=1).fill = PatternFill(start_color='ECF0F1', end_color='ECF0F1', fill_type='solid')
            ws_portada.cell(row=row, column=1).alignment = Alignment(horizontal='left', vertical='center')
            
            # Columna B (valores)
            ws_portada.cell(row=row, column=2).font = Font(name='Arial', size=11, color='34495E')
            ws_portada.cell(row=row, column=2).alignment = Alignment(horizontal='left', vertical='center')
        
        # Ajustar dimensiones
        ws_portada.column_dimensions['A'].width = 25
        ws_portada.column_dimensions['B'].width = 50
        ws_portada.row_dimensions[1].height = 30
        ws_portada.row_dimensions[3].height = 25
        
        # === HOJA 2: DATOS ESPECÍFICOS SEGÚN TIPO DE REPORTE ===
        if reporte.tipo_reporte == 'gastos_categoria' and 'labels' in datos:
            # Análisis de Gastos por Categoría
            total = sum(datos['data'])
            total_transacciones = sum(datos.get('counts', []))
            
            # Crear hoja de datos principales
            gastos_data = {
                'Categoría': datos['labels'],
                'Monto (MXN)': datos['data'],
                'Cantidad de Transacciones': datos.get('counts', [0] * len(datos['labels'])),
                'Porcentaje del Total': [(monto / total * 100) if total > 0 else 0 for monto in datos['data']],
                'Promedio por Transacción': [monto / count if count > 0 else 0 for monto, count in zip(datos['data'], datos.get('counts', [1] * len(datos['data'])))]
            }
            
            gastos_df = pd.DataFrame(gastos_data)
            gastos_df.to_excel(writer, sheet_name='GASTOS POR CATEGORIA', index=False)
            
            # Formatear hoja de gastos
            ws_gastos = writer.sheets['GASTOS POR CATEGORIA']
            
            # Encabezados profesionales
            header_font = Font(name='Arial', bold=True, size=12, color='FFFFFF')
            header_fill = PatternFill(start_color='E74C3C', end_color='E74C3C', fill_type='solid')
            header_alignment = Alignment(horizontal='center', vertical='center')
            
            for col in range(1, 6):
                cell = ws_gastos.cell(row=1, column=col)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
                ws_gastos.row_dimensions[1].height = 25
            
            # Formatear datos con alternancia de colores
            for row in range(2, len(gastos_df) + 2):
                # Alternar colores de fondo
                bg_color = 'F8F9FA' if row % 2 == 0 else 'FFFFFF'
                
                for col in range(1, 6):
                    cell = ws_gastos.cell(row=row, column=col)
                    cell.fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type='solid')
                    cell.font = Font(name='Arial', size=10, color='2C3E50')
                    cell.alignment = Alignment(horizontal='center' if col > 1 else 'left', vertical='center')
                
                # Formatear números específicamente
                ws_gastos.cell(row=row, column=2).number_format = '"$"#,##0.00'  # Monto
                ws_gastos.cell(row=row, column=3).number_format = '#,##0'        # Cantidad
                ws_gastos.cell(row=row, column=4).number_format = '0.0"%"'       # Porcentaje
                ws_gastos.cell(row=row, column=5).number_format = '"$"#,##0.00'  # Promedio
            
            # Fila de totales
            total_row = len(gastos_df) + 2
            ws_gastos.cell(row=total_row, column=1, value='TOTAL GENERAL')
            ws_gastos.cell(row=total_row, column=2, value=total)
            ws_gastos.cell(row=total_row, column=3, value=total_transacciones)
            ws_gastos.cell(row=total_row, column=4, value=100.0)
            ws_gastos.cell(row=total_row, column=5, value=total/total_transacciones if total_transacciones > 0 else 0)
            
            # Formatear fila de totales
            for col in range(1, 6):
                cell = ws_gastos.cell(row=total_row, column=col)
                cell.font = Font(name='Arial', bold=True, size=11, color='FFFFFF')
                cell.fill = PatternFill(start_color='27AE60', end_color='27AE60', fill_type='solid')
                cell.alignment = Alignment(horizontal='center' if col > 1 else 'left', vertical='center')
            
            # Formatear números en totales
            ws_gastos.cell(row=total_row, column=2).number_format = '"$"#,##0.00'
            ws_gastos.cell(row=total_row, column=3).number_format = '#,##0'
            ws_gastos.cell(row=total_row, column=4).number_format = '0.0"%"'
            ws_gastos.cell(row=total_row, column=5).number_format = '"$"#,##0.00'
            
            # Ajustar anchos de columna
            ws_gastos.column_dimensions['A'].width = 25
            ws_gastos.column_dimensions['B'].width = 18
            ws_gastos.column_dimensions['C'].width = 20
            ws_gastos.column_dimensions['D'].width = 18
            ws_gastos.column_dimensions['E'].width = 22
            
            # Crear gráfico de pie
            if len(datos['labels']) > 0:
                pie = PieChart()
                labels = Reference(ws_gastos, min_col=1, min_row=2, max_row=len(gastos_df)+1)
                data = Reference(ws_gastos, min_col=2, min_row=1, max_row=len(gastos_df)+1)
                pie.add_data(data, titles_from_data=True)
                pie.set_categories(labels)
                pie.title = "Distribución de Gastos por Categoría"
                pie.height = 12
                pie.width = 20
                ws_gastos.add_chart(pie, "H2")
            
            # === HOJA DE ANÁLISIS Y INSIGHTS ===
            insights_data = {
                'Tipo de Análisis': [
                    'RESUMEN EJECUTIVO',
                    'GASTO TOTAL',
                    'TRANSACCIONES',
                    'PROMEDIO GENERAL',
                    'CATEGORÍA PRINCIPAL',
                    'RECOMENDACIÓN'
                ],
                'Valor/Descripción': [
                    f'Análisis de {len(datos["labels"])} categorías de gasto',
                    f'${total:,.2f} MXN',
                    f'{total_transacciones:,} transacciones registradas',
                    f'${total/total_transacciones if total_transacciones > 0 else 0:,.2f} MXN por transacción',
                    f'{datos["labels"][datos["data"].index(max(datos["data"]))] if datos["data"] else "N/A"} ({max(datos["data"])/total*100 if total > 0 else 0:.1f}%)',
                    f'{"Revisar gastos en la categoría principal" if max(datos["data"])/total > 0.4 else "Distribución balanceada de gastos"}'
                ]
            }
            
            insights_df = pd.DataFrame(insights_data)
            insights_df.to_excel(writer, sheet_name='ANALISIS E INSIGHTS', index=False)
            
            ws_insights = writer.sheets['ANALISIS E INSIGHTS']
            
            # Formatear insights
            for row in range(1, len(insights_df) + 2):
                ws_insights.cell(row=row, column=1).font = Font(name='Arial', bold=True, size=11, color='FFFFFF')
                ws_insights.cell(row=row, column=1).fill = PatternFill(start_color='3498DB', end_color='3498DB', fill_type='solid')
                ws_insights.cell(row=row, column=2).font = Font(name='Arial', size=11, color='2C3E50')
                ws_insights.cell(row=row, column=2).fill = PatternFill(start_color='EBF5FF', end_color='EBF5FF', fill_type='solid')
            
            ws_insights.column_dimensions['A'].width = 25
            ws_insights.column_dimensions['B'].width = 50
            
        elif reporte.tipo_reporte == 'ingresos_egresos':
            # Análisis de Ingresos vs Egresos
            ingresos = datos['data'][0] if len(datos['data']) > 0 else 0
            egresos = datos['data'][1] if len(datos['data']) > 1 else 0
            balance = ingresos - egresos
            tasa_ahorro = (balance / ingresos * 100) if ingresos > 0 else 0
            
            ie_data = {
                'Concepto Financiero': ['INGRESOS TOTALES', 'EGRESOS TOTALES', 'BALANCE NETO', 'TASA DE AHORRO'],
                'Monto (MXN)': [ingresos, egresos, balance, f'{tasa_ahorro:.1f}%'],
                'Porcentaje del Ingreso': ['100.0%', f'{(egresos/ingresos*100):.1f}%' if ingresos > 0 else '0.0%', 
                                         f'{(balance/ingresos*100):.1f}%' if ingresos > 0 else '0.0%', '-'],
                'Evaluación': ['Base de ingresos', 
                             'Alto' if egresos/ingresos > 0.8 else 'Controlado' if egresos/ingresos <= 0.6 else 'Moderado',
                             'Positivo' if balance > 0 else 'Déficit',
                             'Excelente' if tasa_ahorro >= 20 else 'Bueno' if tasa_ahorro >= 10 else 'Bajo']
            }
            
            ie_df = pd.DataFrame(ie_data)
            ie_df.to_excel(writer, sheet_name='INGRESOS VS EGRESOS', index=False)
            
            # Formatear hoja
            ws_ie = writer.sheets['INGRESOS VS EGRESOS']
            
            # Encabezados
            for col in range(1, 5):
                cell = ws_ie.cell(row=1, column=col)
                cell.font = Font(name='Arial', bold=True, size=12, color='FFFFFF')
                cell.fill = PatternFill(start_color='2C3E50', end_color='2C3E50', fill_type='solid')
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # Formatear filas de datos
            for row in range(2, 6):
                # Alternar colores
                bg_color = 'F1C40F' if row == 2 else 'E74C3C' if row == 3 else '27AE60' if row == 4 else '3498DB'
                text_color = 'FFFFFF'
                
                for col in range(1, 5):
                    cell = ws_ie.cell(row=row, column=col)
                    cell.font = Font(name='Arial', bold=True, size=11, color=text_color)
                    cell.fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type='solid')
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                
                # Formatear números (solo las primeras 3 filas)
                if row <= 4:
                    if isinstance(ws_ie.cell(row=row, column=2).value, (int, float)):
                        ws_ie.cell(row=row, column=2).number_format = '"$"#,##0.00'
            
            # Ajustar anchos
            ws_ie.column_dimensions['A'].width = 25
            ws_ie.column_dimensions['B'].width = 20
            ws_ie.column_dimensions['C'].width = 20
            ws_ie.column_dimensions['D'].width = 20
            
            # Crear gráfico de barras
            bar_chart = BarChart()
            bar_chart.type = "col"
            bar_chart.style = 10
            bar_chart.title = "Comparativo Ingresos vs Egresos"
            bar_chart.y_axis.title = 'Monto (MXN)'
            bar_chart.x_axis.title = 'Conceptos'
            
            data = Reference(ws_ie, min_col=2, min_row=2, max_row=4)
            cats = Reference(ws_ie, min_col=1, min_row=2, max_row=4)
            bar_chart.add_data(data)
            bar_chart.set_categories(cats)
            bar_chart.height = 10
            bar_chart.width = 15
            ws_ie.add_chart(bar_chart, "F2")
            
        elif reporte.tipo_reporte == 'subcuentas_analisis' and 'labels' in datos:
            # Análisis de Subcuentas
            total_saldo = sum(datos['saldos'])
            total_cantidad = sum(datos['cantidades'])
            
            sc_data = {
                'Tipo de Subcuenta': [f"{label}" for label in datos['labels']],
                'Saldo Total (MXN)': datos['saldos'],
                'Cantidad': datos['cantidades'],
                'Porcentaje del Total': [(saldo / total_saldo * 100) if total_saldo > 0 else 0 for saldo in datos['saldos']],
                'Promedio por Subcuenta': [saldo / cantidad if cantidad > 0 else 0 for saldo, cantidad in zip(datos['saldos'], datos['cantidades'])],
                'Clasificación': []
            }
            
            # Agregar clasificación
            for i, saldo in enumerate(datos['saldos']):
                porcentaje = (saldo / total_saldo * 100) if total_saldo > 0 else 0
                if porcentaje >= 40:
                    sc_data['Clasificación'].append('Principal')
                elif porcentaje >= 20:
                    sc_data['Clasificación'].append('Importante')
                elif porcentaje >= 10:
                    sc_data['Clasificación'].append('Activa')
                else:
                    sc_data['Clasificación'].append('Menor')
            
            sc_df = pd.DataFrame(sc_data)
            sc_df.to_excel(writer, sheet_name='ANALISIS SUBCUENTAS', index=False)
            
            # Formatear hoja
            ws_sc = writer.sheets['ANALISIS SUBCUENTAS']
            
            # Encabezados
            for col in range(1, 7):
                cell = ws_sc.cell(row=1, column=col)
                cell.font = Font(name='Arial', bold=True, size=11, color='FFFFFF')
                cell.fill = PatternFill(start_color='8E44AD', end_color='8E44AD', fill_type='solid')
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # Formatear filas de datos
            for row in range(2, len(sc_df) + 2):
                bg_color = 'F8F9FA' if row % 2 == 0 else 'FFFFFF'
                
                for col in range(1, 7):
                    cell = ws_sc.cell(row=row, column=col)
                    cell.fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type='solid')
                    cell.font = Font(name='Arial', size=10, color='2C3E50')
                    cell.alignment = Alignment(horizontal='center' if col > 1 else 'left', vertical='center')
                
                # Formatear números
                ws_sc.cell(row=row, column=2).number_format = '"$"#,##0.00'  # Saldo
                ws_sc.cell(row=row, column=3).number_format = '#,##0'        # Cantidad
                ws_sc.cell(row=row, column=4).number_format = '0.0"%"'       # Porcentaje
                ws_sc.cell(row=row, column=5).number_format = '"$"#,##0.00'  # Promedio
            
            # Fila de totales
            total_row = len(sc_df) + 2
            ws_sc.cell(row=total_row, column=1, value='TOTAL PATRIMONIAL')
            ws_sc.cell(row=total_row, column=2, value=total_saldo)
            ws_sc.cell(row=total_row, column=3, value=total_cantidad)
            ws_sc.cell(row=total_row, column=4, value=100.0)
            ws_sc.cell(row=total_row, column=5, value=total_saldo/total_cantidad if total_cantidad > 0 else 0)
            ws_sc.cell(row=total_row, column=6, value='Resumen')
            
            # Formatear totales
            for col in range(1, 7):
                cell = ws_sc.cell(row=total_row, column=col)
                cell.font = Font(name='Arial', bold=True, size=11, color='FFFFFF')
                cell.fill = PatternFill(start_color='27AE60', end_color='27AE60', fill_type='solid')
                cell.alignment = Alignment(horizontal='center' if col > 1 else 'left', vertical='center')
            
            ws_sc.cell(row=total_row, column=2).number_format = '"$"#,##0.00'
            ws_sc.cell(row=total_row, column=3).number_format = '#,##0'
            ws_sc.cell(row=total_row, column=4).number_format = '0.0"%"'
            ws_sc.cell(row=total_row, column=5).number_format = '"$"#,##0.00'
            
            # Ajustar anchos
            ws_sc.column_dimensions['A'].width = 25
            ws_sc.column_dimensions['B'].width = 18
            ws_sc.column_dimensions['C'].width = 12
            ws_sc.column_dimensions['D'].width = 15
            ws_sc.column_dimensions['E'].width = 20
            ws_sc.column_dimensions['F'].width = 15
        
        # === HOJA FINAL: RESUMEN EJECUTIVO ===
        resumen_data = {
            'FINGEST - RESUMEN EJECUTIVO': [''],
            '': [''],
            'MÉTRICAS CLAVE DEL PERÍODO': [''],
            'Tipo de Análisis': [reporte.get_tipo_reporte_display()],
            'Período Analizado': [f"{reporte.fecha_inicio.strftime('%d/%m/%Y')} - {reporte.fecha_fin.strftime('%d/%m/%Y')}"],
            'Fecha de Generación': [datetime.now().strftime('%d de %B de %Y')],
            '': [''],
            'Estado del Reporte': ['COMPLETADO'],
            'Nivel de Confianza': ['ALTO - Datos verificados'],
            'Recomendación': ['Revisar periódicamente para seguimiento'],
            '': [''],
            'PRÓXIMOS PASOS': [''],
            '1. Monitoreo continuo': ['Establecer alertas para cambios significativos'],
            '2. Análisis comparativo': ['Comparar con períodos anteriores'],
            '3. Planificación estratégica': ['Usar insights para toma de decisiones'],
        }
        
        resumen_df = pd.DataFrame(resumen_data)
        resumen_df.to_excel(writer, sheet_name='RESUMEN EJECUTIVO', index=False, header=False)
        
        # Formatear resumen
        ws_resumen = writer.sheets['RESUMEN EJECUTIVO']
        
        # Título
        ws_resumen['A1'].font = Font(name='Arial', bold=True, size=16, color='FFFFFF')
        ws_resumen['A1'].fill = PatternFill(start_color='2C3E50', end_color='2C3E50', fill_type='solid')
        ws_resumen['A1'].alignment = Alignment(horizontal='center', vertical='center')
        ws_resumen.merge_cells('A1:B1')
        
        # Secciones
        section_rows = [3, 8, 12]
        for row_num in section_rows:
            ws_resumen.cell(row=row_num, column=1).font = Font(name='Arial', bold=True, size=12, color='FFFFFF')
            ws_resumen.cell(row=row_num, column=1).fill = PatternFill(start_color='3498DB', end_color='3498DB', fill_type='solid')
            ws_resumen.merge_cells(f'A{row_num}:B{row_num}')
        
        # Formatear datos
        for row in range(4, 16):
            if row not in [7, 11]:  # Skip empty rows
                ws_resumen.cell(row=row, column=1).font = Font(name='Arial', bold=True, size=10, color='2C3E50')
                ws_resumen.cell(row=row, column=1).fill = PatternFill(start_color='ECF0F1', end_color='ECF0F1', fill_type='solid')
                ws_resumen.cell(row=row, column=2).font = Font(name='Arial', size=10, color='34495E')
        
        ws_resumen.column_dimensions['A'].width = 30
        ws_resumen.column_dimensions['B'].width = 50
    
    return response

def exportar_csv(reporte, datos):
    """Exporta reporte a CSV con formato ultra estructurado y profesional"""
    import csv
    from io import StringIO
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    
    # Nombre de archivo súper descriptivo
    tipo_clean = reporte.get_tipo_reporte_display().replace(' ', '_').replace('/', '-')
    fecha_str = reporte.fecha_creacion.strftime('%Y%m%d_%H%M')
    filename = f"FinGest_Reporte_{tipo_clean}_{fecha_str}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Agregar BOM para Excel (soporte UTF-8)
    response.write('\ufeff')
    
    writer = csv.writer(response)
    
    # === ENCABEZADO PROFESIONAL ===
    writer.writerow(['=' * 80])
    writer.writerow(['FINGEST - SISTEMA DE GESTIÓN FINANCIERA INTELIGENTE'])
    writer.writerow(['REPORTE FINANCIERO EJECUTIVO'])
    writer.writerow(['=' * 80])
    writer.writerow([])
    
    # === INFORMACIÓN EJECUTIVA DEL REPORTE ===
    writer.writerow(['INFORMACIÓN EJECUTIVA DEL REPORTE'])
    writer.writerow(['-' * 50])
    writer.writerow(['Título del Reporte', reporte.titulo])
    writer.writerow(['Tipo de Análisis', reporte.get_tipo_reporte_display()])
    writer.writerow(['Fecha de Generación', reporte.fecha_creacion.strftime('%d de %B de %Y a las %H:%M hrs')])
    writer.writerow(['Período de Análisis', f"Del {reporte.fecha_inicio.strftime('%d de %B de %Y')} al {reporte.fecha_fin.strftime('%d de %B de %Y')}"])
    writer.writerow(['Usuario Responsable', str(reporte.id_usuario) if reporte.id_usuario else 'No especificado'])
    writer.writerow(['Estado del Reporte', 'COMPLETADO Y VERIFICADO'])
    writer.writerow(['Nivel de Confidencialidad', 'CONFIDENCIAL - Uso exclusivo del titular'])
    
    if reporte.descripcion:
        writer.writerow(['Descripción', reporte.descripcion])
    
    writer.writerow([])
    writer.writerow([])
    
    # === DATOS ESPECÍFICOS SEGÚN TIPO DE REPORTE ===
    if reporte.tipo_reporte == 'gastos_categoria' and 'labels' in datos:
        total = sum(datos['data'])
        total_transacciones = sum(datos.get('counts', []))
        
        # Resumen ejecutivo
        writer.writerow(['RESUMEN EJECUTIVO - ANÁLISIS DE GASTOS POR CATEGORÍA'])
        writer.writerow(['=' * 60])
        writer.writerow(['MÉTRICAS PRINCIPALES'])
        writer.writerow(['Gasto Total del Período (MXN)', f'{total:,.2f}'])
        writer.writerow(['Total de Transacciones', f'{total_transacciones:,}'])
        writer.writerow(['Promedio por Transacción (MXN)', f'{total/total_transacciones if total_transacciones > 0 else 0:,.2f}'])
        writer.writerow(['Número de Categorías Analizadas', len(datos['labels'])])
        writer.writerow(['Promedio por Categoría (MXN)', f'{total/len(datos["labels"]) if datos["labels"] else 0:,.2f}'])
        writer.writerow([])
        
        # Tabla principal detallada
        writer.writerow(['DESGLOSE DETALLADO POR CATEGORÍA'])
        writer.writerow(['-' * 60])
        writer.writerow(['Categoría', 'Monto (MXN)', 'Cantidad de Transacciones', 'Porcentaje del Total (%)', 'Promedio por Transacción (MXN)', 'Clasificación'])
        
        for i, label in enumerate(datos['labels']):
            monto = datos['data'][i]
            cantidad = datos.get('counts', [0] * len(datos['labels']))[i]
            porcentaje = (monto / total * 100) if total > 0 else 0
            promedio_transaccion = monto / cantidad if cantidad > 0 else 0
            
            # Clasificación automática
            if porcentaje >= 30:
                clasificacion = "GASTO ALTO - Requiere atención"
            elif porcentaje >= 15:
                clasificacion = "GASTO MEDIO - Monitorear"
            elif porcentaje >= 5:
                clasificacion = "GASTO NORMAL - Controlado"
            else:
                clasificacion = "GASTO BAJO - Excelente"
            
            writer.writerow([
                f'{label}',
                f'{monto:,.2f}',
                f'{cantidad:,}',
                f'{porcentaje:.2f}',
                f'{promedio_transaccion:,.2f}',
                clasificacion
            ])
        
        # Fila de totales
        writer.writerow(['-' * 60])
        writer.writerow([
            'TOTAL GENERAL',
            f'{total:,.2f}',
            f'{total_transacciones:,}',
            '100.00',
            f'{total/total_transacciones if total_transacciones > 0 else 0:,.2f}',
            'RESUMEN COMPLETO'
        ])
        
        writer.writerow([])
        
        # Insights automáticos
        writer.writerow(['INSIGHTS Y ANÁLISIS AUTOMÁTICO'])
        writer.writerow(['-' * 60])
        
        if datos['data']:
            max_gasto_idx = datos['data'].index(max(datos['data']))
            categoria_principal = datos['labels'][max_gasto_idx]
            porcentaje_principal = (max(datos['data']) / total * 100) if total > 0 else 0
            
            writer.writerow(['Categoría con Mayor Gasto', categoria_principal])
            writer.writerow(['Monto de Categoría Principal (MXN)', f'{max(datos["data"]):,.2f}'])
            writer.writerow(['Participación de Categoría Principal (%)', f'{porcentaje_principal:.2f}'])
            writer.writerow(['Distribución de Gastos', 'Concentrada' if porcentaje_principal > 40 else 'Balanceada' if porcentaje_principal < 25 else 'Moderada'])
            
            # Recomendaciones automáticas
            writer.writerow([])
            writer.writerow(['RECOMENDACIONES ESTRATÉGICAS'])
            writer.writerow(['-' * 40])
            
            if porcentaje_principal > 50:
                writer.writerow(['Alerta', 'Una categoría concentra más del 50% del gasto total'])
                writer.writerow(['Recomendación 1', 'Revisar y optimizar los gastos en la categoría principal'])
                writer.writerow(['Recomendación 2', 'Considerar redistribuir gastos en otras categorías'])
            elif porcentaje_principal < 15:
                writer.writerow(['Excelente', 'Distribución muy balanceada de gastos'])
                writer.writerow(['Recomendación', 'Mantener la estrategia actual de distribución'])
            else:
                writer.writerow(['Bueno', 'Distribución razonable de gastos'])
                writer.writerow(['Recomendación', 'Monitorear tendencias y ajustar según objetivos'])
        
    elif reporte.tipo_reporte == 'ingresos_egresos':
        ingresos = datos['data'][0] if len(datos['data']) > 0 else 0
        egresos = datos['data'][1] if len(datos['data']) > 1 else 0
        balance = ingresos - egresos
        tasa_ahorro = (balance / ingresos * 100) if ingresos > 0 else 0
        ratio_gastos = (egresos / ingresos * 100) if ingresos > 0 else 0
        
        # Dashboard financiero
        writer.writerow(['DASHBOARD FINANCIERO EJECUTIVO'])
        writer.writerow(['=' * 60])
        writer.writerow(['INDICADORES CLAVE DE RENDIMIENTO (KPIs)'])
        writer.writerow(['Total de Ingresos (MXN)', f'{ingresos:,.2f}'])
        writer.writerow(['Total de Egresos (MXN)', f'{egresos:,.2f}'])
        writer.writerow(['Balance Neto (MXN)', f'{balance:,.2f}'])
        writer.writerow(['Tasa de Ahorro (%)', f'{tasa_ahorro:.2f}'])
        writer.writerow(['Ratio de Gastos (%)', f'{ratio_gastos:.2f}'])
        writer.writerow([])
        
        # Análisis comparativo
        writer.writerow(['ANÁLISIS COMPARATIVO DETALLADO'])
        writer.writerow(['-' * 60])
        writer.writerow(['Concepto', 'Monto (MXN)', 'Porcentaje del Ingreso (%)', 'Evaluación Financiera', 'Meta Recomendada'])
        
        writer.writerow([
            'Ingresos Totales',
            f'{ingresos:,.2f}',
            '100.00',
            'Base de cálculo financiero',
            'Incrementar anualmente'
        ])
        
        evaluacion_egresos = 'CRÍTICO' if ratio_gastos > 90 else 'ALTO' if ratio_gastos > 80 else 'MODERADO' if ratio_gastos > 70 else 'CONTROLADO'
        writer.writerow([
            'Egresos Totales',
            f'{egresos:,.2f}',
            f'{ratio_gastos:.2f}',
            evaluacion_egresos,
            'Máximo 70% de ingresos'
        ])
        
        evaluacion_balance = 'EXCELENTE' if tasa_ahorro >= 20 else 'BUENO' if tasa_ahorro >= 10 else 'BAJO' if balance > 0 else 'DÉFICIT'
        writer.writerow([
            'Balance Final',
            f'{balance:,.2f}',
            f'{tasa_ahorro:.2f}',
            evaluacion_balance,
            'Mínimo 15% de ahorro'
        ])
        
        writer.writerow([])
        
        # Diagnóstico financiero
        writer.writerow(['DIAGNÓSTICO FINANCIERO INTEGRAL'])
        writer.writerow(['-' * 60])
        
        # Salud financiera
        if balance < 0:
            salud = "CRÍTICA - Déficit financiero"
            color_semaforo = "ROJO"
        elif tasa_ahorro >= 20:
            salud = "EXCELENTE - Finanzas muy saludables"
            color_semaforo = "VERDE"
        elif tasa_ahorro >= 10:
            salud = "BUENA - Finanzas estables"
            color_semaforo = "AMARILLO"
        else:
            salud = "REGULAR - Necesita mejoras"
            color_semaforo = "NARANJA"
        
        writer.writerow(['Estado de Salud Financiera', salud])
        writer.writerow(['Semáforo Financiero', color_semaforo])
        writer.writerow(['Índice de Liquidez', f'{balance/egresos if egresos > 0 else 0:.2f}' + ' meses' if egresos > 0 else 'Infinito'])
        
        writer.writerow([])
        
        # Recomendaciones estratégicas
        writer.writerow(['PLAN DE ACCIÓN Y RECOMENDACIONES'])
        writer.writerow(['-' * 60])
        
        if balance < 0:
            writer.writerow(['ACCIÓN INMEDIATA 1', 'Reducir gastos no esenciales urgentemente'])
            writer.writerow(['ACCIÓN INMEDIATA 2', 'Buscar fuentes adicionales de ingresos'])
            writer.writerow(['PLAZO', 'Implementar en los próximos 30 días'])
        elif tasa_ahorro < 10:
            writer.writerow(['RECOMENDACIÓN 1', 'Incrementar tasa de ahorro al 15-20%'])
            writer.writerow(['RECOMENDACIÓN 2', 'Revisar gastos variables y optimizar'])
            writer.writerow(['META', 'Alcanzar en los próximos 3-6 meses'])
        else:
            writer.writerow(['FELICITACIONES', 'Excelente manejo financiero'])
            writer.writerow(['SIGUIENTE NIVEL', 'Considerar opciones de inversión'])
            writer.writerow(['OBJETIVO', 'Hacer crecer el patrimonio'])
        
    elif reporte.tipo_reporte == 'subcuentas_analisis' and 'labels' in datos:
        total_saldo = sum(datos['saldos'])
        total_cantidad = sum(datos['cantidades'])
        promedio_general = total_saldo / total_cantidad if total_cantidad > 0 else 0
        
        # Resumen patrimonial
        writer.writerow(['ANÁLISIS PATRIMONIAL INTEGRAL DE SUBCUENTAS'])
        writer.writerow(['=' * 70])
        writer.writerow(['RESUMEN PATRIMONIAL EJECUTIVO'])
        writer.writerow(['Patrimonio Total (MXN)', f'{total_saldo:,.2f}'])
        writer.writerow(['Subcuentas Activas', f'{total_cantidad:,}'])
        writer.writerow(['Saldo Promedio por Subcuenta (MXN)', f'{promedio_general:,.2f}'])
        writer.writerow(['Tipos de Subcuenta', len(datos['labels'])])
        
        # Evaluación de diversificación
        diversificacion = "ALTA" if len(datos['labels']) >= 4 else "MEDIA" if len(datos['labels']) >= 3 else "BAJA"
        writer.writerow(['Nivel de Diversificación', diversificacion])
        writer.writerow([])
        
        # Desglose detallado
        writer.writerow(['DESGLOSE DETALLADO POR TIPO DE SUBCUENTA'])
        writer.writerow(['-' * 70])
        writer.writerow(['Tipo de Subcuenta', 'Saldo Total (MXN)', 'Cantidad', '% del Total', 'Promedio (MXN)', 'Clasificación', 'Evaluación'])
        
        for i, label in enumerate(datos['labels']):
            saldo = datos['saldos'][i] if i < len(datos['saldos']) else 0
            cantidad = datos['cantidades'][i] if i < len(datos['cantidades']) else 0
            promedio = saldo / cantidad if cantidad > 0 else 0
            porcentaje = (saldo / total_saldo * 100) if total_saldo > 0 else 0
            
            # Clasificación por participación
            if porcentaje >= 40:
                clasificacion = "PRINCIPAL"
                evaluacion = "Concentra la mayor parte del patrimonio"
            elif porcentaje >= 20:
                clasificacion = "IMPORTANTE"
                evaluacion = "Contribución significativa al patrimonio"
            elif porcentaje >= 10:
                clasificacion = "ACTIVA"
                evaluacion = "Participación relevante y saludable"
            else:
                clasificacion = "MENOR"
                evaluacion = "Participación limitada, considerar optimizar"
            
            writer.writerow([
                f'{label}',
                f'{saldo:,.2f}',
                f'{cantidad:,}',
                f'{porcentaje:.2f}',
                f'{promedio:,.2f}',
                clasificacion,
                evaluacion
            ])
        
        # Totales
        writer.writerow(['-' * 70])
        writer.writerow([
            'TOTAL PATRIMONIAL',
            f'{total_saldo:,.2f}',
            f'{total_cantidad:,}',
            '100.00',
            f'{promedio_general:,.2f}',
            'CONSOLIDADO',
            'Patrimonio total consolidado'
        ])
        
        writer.writerow([])
        
        # Análisis estratégico
        writer.writerow(['ANÁLISIS ESTRATÉGICO PATRIMONIAL'])
        writer.writerow(['-' * 70])
        
        if datos['saldos']:
            subcuenta_principal_idx = datos['saldos'].index(max(datos['saldos']))
            subcuenta_principal = datos['labels'][subcuenta_principal_idx]
            concentracion = (max(datos['saldos']) / total_saldo * 100) if total_saldo > 0 else 0
            
            writer.writerow(['Subcuenta Principal', subcuenta_principal])
            writer.writerow(['Saldo Principal (MXN)', f'{max(datos["saldos"]):,.2f}'])
            writer.writerow(['Concentración (%)', f'{concentracion:.2f}'])
            
            # Evaluación de concentración
            if concentracion > 70:
                evaluacion_concentracion = "ALTA - Riesgo de concentración"
                recomendacion = "Diversificar en múltiples subcuentas"
            elif concentracion > 50:
                evaluacion_concentracion = "MODERADA - Monitorear distribución"
                recomendacion = "Considerar rebalanceo patrimonial"
            else:
                evaluacion_concentracion = "BALANCEADA - Distribución saludable"
                recomendacion = "Mantener estrategia actual"
            
            writer.writerow(['Evaluación de Concentración', evaluacion_concentracion])
            writer.writerow(['Recomendación Principal', recomendacion])
        
        writer.writerow([])
        
        # Recomendaciones estratégicas
        writer.writerow(['RECOMENDACIONES ESTRATÉGICAS PARA OPTIMIZACIÓN'])
        writer.writerow(['-' * 70])
        
        if len(datos['labels']) < 3:
            writer.writerow(['Diversificación', 'Crear subcuentas adicionales para mejor organización'])
            writer.writerow(['Sugerencia', 'Separar fondos por propósito (ahorro, gastos, inversión)'])
        elif concentracion > 60:
            writer.writerow(['Rebalanceo', 'Redistribuir patrimonio para menor concentración'])
            writer.writerow(['Acción', 'Transferir fondos a subcuentas menos concentradas'])
        else:
            writer.writerow(['Excelente Gestión', 'Organización patrimonial muy efectiva'])
            writer.writerow(['Siguiente Nivel', 'Considerar estrategias de crecimiento patrimonial'])
    
    # === PIE DE PÁGINA PROFESIONAL ===
    writer.writerow([])
    writer.writerow([])
    writer.writerow(['=' * 80])
    writer.writerow(['FINGEST - GESTIÓN FINANCIERA INTELIGENTE'])
    writer.writerow(['Soporte Técnico: soporte@fingest.com'])
    writer.writerow(['Atención al Cliente: +52 (55) 1234-5678'])
    writer.writerow(['Portal Web: www.fingest.com'])
    writer.writerow(['Descarga nuestra aplicación móvil'])
    writer.writerow([])
    writer.writerow(['AVISO LEGAL'])
    writer.writerow(['Este reporte es CONFIDENCIAL y de uso exclusivo del titular de la cuenta.'])
    writer.writerow(['Los datos presentados han sido verificados y procesados con tecnología segura.'])
    writer.writerow(['Para consultas sobre este reporte, contacte a nuestro equipo de soporte.'])
    writer.writerow([])
    writer.writerow([f'Documento generado el {datetime.now().strftime("%d de %B de %Y a las %H:%M hrs")}'])
    writer.writerow([f'ID de Seguridad: FG-{reporte.id}-{reporte.fecha_creacion.strftime("%Y%m%d%H%M")}'])
    writer.writerow(['Tecnología FinGest - Todos los derechos reservados'])
    writer.writerow(['=' * 80])
    
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