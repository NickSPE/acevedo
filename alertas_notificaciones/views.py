from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from .models import TipoNotificacion, ConfiguracionNotificacion, Notificacion
from .services import NotificationService, ConfigurationNotificationService

from .utils import get_relative_time

URL_CONFIGURACIONES = 'alertas_notificaciones:configuraciones'

@login_required
def configuraciones(request):
    """Vista para la configuración de notificaciones"""
    if request.method == 'POST':
        return _manejar_actualizacion_configuracion(request)
    
    # Obtener tipos de notificaciones activos
    tipos_notificaciones = TipoNotificacion.objects.filter(activo=True)
    
    # Obtener configuraciones actuales del usuario
    configuraciones_usuario = {}
    for tipo in tipos_notificaciones:
        config = ConfiguracionNotificacion.objects.filter(
            usuario=request.user,
            tipo_notificacion=tipo
        ).first()
        
        if config:
            configuraciones_usuario[tipo.nombre] = {
                'email_habilitado': config.email_habilitado,
                'push_habilitado': config.push_habilitado,
                'sms_habilitado': config.sms_habilitado,
                'activo': config.activo,
                'umbral_monto': config.umbral_monto,
                'frecuencia_resumen': config.frecuencia_resumen,
            }
        else:
            # Valores por defecto
            configuraciones_usuario[tipo.nombre] = {
                'email_habilitado': True,
                'push_habilitado': True,
                'sms_habilitado': False,
                'activo': True,
                'umbral_monto': None,
                'frecuencia_resumen': 'weekly',
            }
    
    context = {
        'tipos_notificaciones': tipos_notificaciones,
        'configuraciones': configuraciones_usuario,
    }
    
    return render(request, 'alertas_notificaciones/configuraciones.html', context)

def _manejar_actualizacion_configuracion(request):
    """Maneja la actualización de configuraciones de notificación"""
    try:
        cambios_realizados = []
        
        # Obtener todos los tipos de notificaciones
        tipos_notificaciones = TipoNotificacion.objects.filter(activo=True)
        
        for tipo in tipos_notificaciones:
            # Obtener configuración actual o crear una nueva
            config, _ = ConfiguracionNotificacion.objects.get_or_create(
                usuario=request.user,
                tipo_notificacion=tipo,
                defaults={
                    'email_habilitado': True,
                    'push_habilitado': True,
                    'sms_habilitado': False,
                    'activo': True
                }
            )
            
            # Valores anteriores para comparar cambios
            email_anterior = config.email_habilitado
            push_anterior = config.push_habilitado
            
            # Actualizar configuraciones desde POST
            email_key = f'email_{tipo.nombre}'
            push_key = f'push_{tipo.nombre}'
            activo_key = f'activo_{tipo.nombre}'
            
            config.email_habilitado = email_key in request.POST
            config.push_habilitado = push_key in request.POST
            config.activo = activo_key in request.POST
            
            # Configuraciones específicas
            umbral_key = f'umbral_{tipo.nombre}'
            if umbral_key in request.POST and request.POST[umbral_key]:
                try:
                    config.umbral_monto = float(request.POST[umbral_key])
                except ValueError:
                    pass
            
            config.save()
            
            # Registrar cambios para notificación
            if email_anterior != config.email_habilitado:
                cambios_realizados.append({
                    'tipo': 'email_habilitado',
                    'tipo_notificacion': tipo.nombre,
                    'valor_anterior': email_anterior,
                    'nuevo_valor': config.email_habilitado
                })
            
            if push_anterior != config.push_habilitado:
                cambios_realizados.append({
                    'tipo': 'push_habilitado',
                    'tipo_notificacion': tipo.nombre,
                    'valor_anterior': push_anterior,
                    'nuevo_valor': config.push_habilitado
                })
        
        # Enviar notificación de confirmación si hubo cambios
        if cambios_realizados:
            ConfigurationNotificationService.notificar_cambio_configuracion(
                request.user,
                cambios_realizados
            )
            
            messages.success(
                request, 
                '✅ Configuración actualizada correctamente. Hemos enviado una confirmación a tu email.'
            )
        else:
            messages.info(request, 'No se detectaron cambios en la configuración.')
        
        return redirect(URL_CONFIGURACIONES)
        
    except Exception as e:
        messages.error(request, f'Error al actualizar configuración: {str(e)}')
        return redirect(URL_CONFIGURACIONES)

def _map_notification_to_dict(notif):
    """Mapea una notificación a un diccionario con tipos visuales y timestamps formateados"""
    if notif.prioridad == 'urgente':
        visual_type = 'critical'
    elif notif.prioridad == 'alta':
        visual_type = 'warning'
    else:
        visual_type = 'info'
        
    timestamp = notif.fecha_creacion
    timestamp_str = timestamp.isoformat() if hasattr(timestamp, 'isoformat') else timestamp
    relative_time = get_relative_time(timestamp)
    
    return {
        "id": notif.id,
        "type": visual_type,
        "title": notif.titulo,
        "message": notif.mensaje,
        "timestamp": timestamp,
        "timestamp_str": timestamp_str,
        "relative_time": relative_time,
        "read": notif.estado == 'leida',
        "category": notif.categoria,
        "action": notif.url_accion,
        "priority": notif.prioridad,
        "tipo_notificacion": notif.tipo_notificacion.nombre,
        "estado": notif.estado,
        "email_enviado": notif.email_enviado,
        "push_enviado": notif.push_enviado,
    }

@login_required
@require_GET
def historial(request):
    """Vista para el historial de notificaciones - 3 más recientes con opción de ver todas"""
    show_all = request.GET.get('show_all', 'false') == 'true'
    
    # Query base de notificaciones del usuario
    query = Notificacion.objects.filter(usuario=request.user)
    query_ordered = query.select_related('tipo_notificacion').order_by('-fecha_creacion')
    total_notifications = query.count()
    
    # Limitar según la opción seleccionada
    if show_all:
        from django.core.paginator import Paginator
        paginator = Paginator(query_ordered, 20)  # 20 por página
        page = request.GET.get('page', 1)
        try:
            notificaciones_db = paginator.page(page)
        except Exception:
            notificaciones_db = paginator.page(1)
    else:
        notificaciones_db = list(query_ordered[:3])
        paginator = None
    
    # Convertir a formato esperado por el template
    notifications = [_map_notification_to_dict(notif) for notif in notificaciones_db]
    unread_in_page = sum(1 for notif in notifications if not notif['read'])
    
    context = {
        'notifications': notifications,
        'total_notificaciones': total_notifications,
        'showing_total': len(notifications),
        'unread_in_page': unread_in_page,
        'show_all': show_all,
        'is_limited': not show_all,
        'has_more': total_notifications > 3,
    }
    
    # Agregar paginación solo si se muestran todas
    if show_all and paginator:
        context.update({
            'page_obj': notificaciones_db,
            'paginator': paginator,
            'is_paginated': paginator.num_pages > 1,
        })
        
    return render(request, 'alertas_notificaciones/historial.html', context)

@login_required
@require_GET
def alertas_automaticas(request):
    """Vista para alertas automáticas"""
    return render(request, 'alertas_notificaciones/alertas_automaticas.html')

@login_required
@require_GET
def index(request):
    """Vista principal del módulo de alertas"""
    return render(request, 'alertas_notificaciones/index.html')

# API Views para JavaScript
@login_required
@require_http_methods(["POST"])
def marcar_notificacion_leida(request, notificacion_id):
    """API para marcar notificación como leída"""
    try:
        success = NotificationService.marcar_como_leida(notificacion_id, request.user)
        if success:
            return JsonResponse({'status': 'success', 'message': 'Notificación marcada como leída'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Notificación no encontrada'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
@require_http_methods(["POST"])
def marcar_todas_leidas(request):
    """API para marcar todas las notificaciones como leídas"""
    try:
        count = Notificacion.objects.filter(
            usuario=request.user,
@login_required
@require_POST
def marcar_notificaciones_leidas(request):
    try:
        count = Notificacion.objects.filter(
            usuario=request.user,
            estado__in=['enviada', 'pendiente']
        ).update(
            estado='leida',
            fecha_lectura=timezone.now()
        )
        
        return JsonResponse({
            'status': 'success', 
            'message': f'{count} notificaciones marcadas como leídas'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
@require_GET
def obtener_contador_notificaciones(request):
    """API para obtener contador de notificaciones no leídas"""
    try:
        count = NotificationService.obtener_contador_no_leidas(request.user)
        return JsonResponse({'count': count})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

# Función de prueba para enviar notificación
@login_required
@require_POST
def test_notification(request):
    """Vista de prueba para enviar notificación (solo para desarrollo)"""
    if request.method == 'POST':
        try:
            # Crear notificación de prueba
            notificacion = NotificationService.crear_notificacion(
                usuario=request.user,
                tipo_notificacion='configuracion_actualizada',
                titulo='Prueba de Notificación',
                mensaje='Esta es una notificación de prueba para verificar que el sistema funciona correctamente.',
                categoria='Pruebas',
                prioridad='media'
            )
            
            if notificacion:
                messages.success(request, '✅ Notificación de prueba enviada correctamente!')
            else:
                messages.warning(request, '⚠️ No se pudo enviar la notificación (posiblemente deshabilitada)')
                
        except Exception as e:
            messages.error(request, f'❌ Error enviando notificación de prueba: {str(e)}')
    
    return redirect(URL_CONFIGURACIONES)
@require_GET
def marcar_leida_simple(request, notificacion_id):
    """Vista simple para marcar notificación como leída (GET request)"""
    try:
        notificacion = Notificacion.objects.get(
            id=notificacion_id,
            usuario=request.user
        )
        
        if notificacion.estado != 'leida':
            notificacion.estado = 'leida'
            notificacion.fecha_lectura = timezone.now()
            notificacion.save()
            messages.success(request, 'Notificación marcada como leída')
        else:
            # Si ya está leída, marcar como no leída
            notificacion.estado = 'enviada'
            notificacion.fecha_lectura = None
            notificacion.save()
            messages.success(request, 'Notificación marcada como no leída')
            
    except Notificacion.DoesNotExist:
        messages.error(request, 'Notificación no encontrada')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('alertas_notificaciones:historial')

@login_required
@require_GET
def marcar_todas_leidas_simple(request):
    """Vista simple para marcar todas las notificaciones como leídas (GET request)"""
    try:
        count = Notificacion.objects.filter(
            usuario=request.user,
            estado__in=['enviada', 'pendiente']
        ).update(
            estado='leida',
            fecha_lectura=timezone.now()
        )
        
        if count > 0:
            messages.success(request, f'{count} notificaciones marcadas como leídas')
        else:
            messages.info(request, 'No hay notificaciones pendientes por marcar')
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('alertas_notificaciones:historial')

@login_required
@require_GET
def test_currency(request):
    """Vista de prueba para mostrar el formateo de moneda"""
    return render(request, 'alertas_notificaciones/test_currency.html')

@login_required
@require_GET
def debug_currency(request):
    """Vista de debug para verificar la moneda del usuario"""
    debug_info = {
        'user_authenticated': request.user.is_authenticated,
        'user_id': request.user.id if request.user.is_authenticated else None,
        'user_email': request.user.correo if request.user.is_authenticated else None,
        'has_id_moneda': hasattr(request.user, 'id_moneda') if request.user.is_authenticated else False,
        'id_moneda_value': None,
        'moneda_simbolo': None,
        'moneda_codigo': None,
        'moneda_nombre': None,
        'error': None
    }
    
    if request.user.is_authenticated:
        try:
            if hasattr(request.user, 'id_moneda') and request.user.id_moneda:
                moneda = request.user.id_moneda
                debug_info.update({
                    'id_moneda_value': moneda.id,
                    'moneda_simbolo': moneda.simbolo,
                    'moneda_codigo': moneda.codigo,
                    'moneda_nombre': moneda.nombre,
                })
            else:
                debug_info['error'] = 'Usuario no tiene moneda asignada o es None'
        except Exception as e:
            debug_info['error'] = str(e)
    
    # Probar el context processor manualmente
    from core.context_processors import currency_context
    context_result = currency_context(request)
    
    return JsonResponse({
        'debug_info': debug_info,
        'context_processor_result': context_result
    })

@login_required
@require_GET
def debug_simple(request):
    """Vista de debug simple para verificar moneda"""
    context = {
        'user_currency': getattr(request.user.id_moneda, 'simbolo', 'No encontrado') if hasattr(request.user, 'id_moneda') and request.user.id_moneda else 'Sin moneda',
        'user_name': f"{request.user.nombres} {request.user.apellido_paterno}",
        'user_email': request.user.correo,
    }
    return render(request, 'alertas_notificaciones/debug_simple.html', context)