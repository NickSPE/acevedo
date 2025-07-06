from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from .models import Notificacion, TipoNotificacion, ConfiguracionNotificacion
from usuarios.models import Usuario

@staff_member_required
def admin_notificaciones(request):
    """Vista administrativa para revisar el estado de las notificaciones"""
    
    # Estadísticas generales
    total_notificaciones = Notificacion.objects.count()
    notificaciones_hoy = Notificacion.objects.filter(
        fecha_creacion__date=timezone.now().date()
    ).count()
    
    notificaciones_pendientes = Notificacion.objects.filter(
        estado='pendiente'
    ).count()
    
    notificaciones_enviadas = Notificacion.objects.filter(
        estado='enviada'
    ).count()
    
    notificaciones_error = Notificacion.objects.filter(
        estado='error'
    ).count()
    
    # Notificaciones recientes (últimas 24 horas)
    hace_24h = timezone.now() - timedelta(hours=24)
    notificaciones_recientes = Notificacion.objects.filter(
        fecha_creacion__gte=hace_24h
    ).select_related('usuario', 'tipo_notificacion').order_by('-fecha_creacion')[:50]
    
    # Buscar posibles duplicados (mismo usuario, tipo y tiempo similar)
    duplicados_potenciales = []
    hace_1h = timezone.now() - timedelta(hours=1)
    
    # Agrupar por usuario y tipo de notificación
    grupos = Notificacion.objects.filter(
        fecha_creacion__gte=hace_1h
    ).values('usuario', 'tipo_notificacion__nombre').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    for grupo in grupos:
        notifs_grupo = Notificacion.objects.filter(
            usuario_id=grupo['usuario'],
            tipo_notificacion__nombre=grupo['tipo_notificacion__nombre'],
            fecha_creacion__gte=hace_1h
        ).order_by('-fecha_creacion')
        
        if notifs_grupo.count() > 1:
            duplicados_potenciales.append({
                'usuario': notifs_grupo.first().usuario,
                'tipo': grupo['tipo_notificacion__nombre'],
                'count': grupo['count'],
                'notificaciones': list(notifs_grupo)
            })
    
    # Estadísticas por tipo
    stats_por_tipo = Notificacion.objects.filter(
        fecha_creacion__gte=hace_24h
    ).values('tipo_notificacion__nombre').annotate(
        total=Count('id'),
        enviadas=Count('id', filter=Q(estado='enviada')),
        pendientes=Count('id', filter=Q(estado='pendiente')),
        errores=Count('id', filter=Q(estado='error'))
    ).order_by('-total')
    
    context = {
        'total_notificaciones': total_notificaciones,
        'notificaciones_hoy': notificaciones_hoy,
        'notificaciones_pendientes': notificaciones_pendientes,
        'notificaciones_enviadas': notificaciones_enviadas,
        'notificaciones_error': notificaciones_error,
        'notificaciones_recientes': notificaciones_recientes,
        'duplicados_potenciales': duplicados_potenciales,
        'stats_por_tipo': stats_por_tipo,
    }
    
    return render(request, 'alertas_notificaciones/admin_notificaciones.html', context)


@staff_member_required
def debug_duplicados(request):
    """Vista para debuggear notificaciones duplicadas"""
    
    # Buscar duplicados exactos en las últimas 2 horas
    hace_2h = timezone.now() - timedelta(hours=2)
    
    # Encontrar grupos de notificaciones que podrían ser duplicados
    potential_duplicates = {}
    
    notificaciones = Notificacion.objects.filter(
        fecha_creacion__gte=hace_2h
    ).select_related('usuario', 'tipo_notificacion').order_by('-fecha_creacion')
    
    for notif in notificaciones:
        # Crear una clave única basada en contenido principal
        key = f"{notif.usuario.id}_{notif.tipo_notificacion.nombre}_{notif.titulo}"
        
        # Si hay datos adicionales, incluir algunos campos relevantes
        if notif.datos_adicionales:
            if 'movimiento_id' in notif.datos_adicionales:
                key += f"_{notif.datos_adicionales.get('movimiento_id')}"
            elif 'meta_id' in notif.datos_adicionales:
                key += f"_meta_{notif.datos_adicionales.get('meta_id')}"
            elif 'monto' in notif.datos_adicionales:
                key += f"_monto_{notif.datos_adicionales.get('monto')}"
        
        if key not in potential_duplicates:
            potential_duplicates[key] = []
        potential_duplicates[key].append(notif)
    
    # Filtrar solo los que tienen duplicados
    duplicados_reales = {k: v for k, v in potential_duplicates.items() if len(v) > 1}
    
    context = {
        'duplicados_reales': duplicados_reales,
        'total_grupos_duplicados': len(duplicados_reales),
        'tiempo_busqueda': '2 horas'
    }
    
    return render(request, 'alertas_notificaciones/debug_duplicados.html', context)
