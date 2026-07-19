from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import models
import logging

from .models import MetaAhorro, AporteMetaAhorro, Movimiento
from cuentas.models import Cuenta
from alertas_notificaciones.services import NotificationService
from alertas_notificaciones.signal_decorators import prevent_duplicate_signals

logger = logging.getLogger(__name__)


@receiver(post_save, sender=AporteMetaAhorro)
@prevent_duplicate_signals('aporte_meta_ahorro', timeout=60)
def notificar_nuevo_aporte(_sender, instance, created, **kwargs):
    """Notifica cuando se realiza un nuevo aporte a una meta de ahorro"""
    if not created:
        return
        
    # Verificar duplicados
    from alertas_notificaciones.models import Notificacion
    from datetime import timedelta
    
    hace_5_min = timezone.now() - timedelta(minutes=5)
    existe_notificacion = Notificacion.objects.filter(
        usuario=instance.id_usuario,
        tipo_notificacion__nombre__in=["aporte_realizado", "progreso_meta", "meta_alcanzada"],
        datos_adicionales__meta_id=instance.id_meta_ahorro.id,
        datos_adicionales__aporte_monto=float(instance.monto),
        fecha_creacion__gte=hace_5_min
    ).exists()
    
    if existe_notificacion:
        print("WARNING: Ya existe notificacion para este aporte, saltando...")
        return
        
    meta = instance.id_meta_ahorro
    usuario = instance.id_usuario
    
    # Calcular progreso actual
    progreso_anterior = meta.porcentaje_progreso()
    
    # Determinar tipo de notificación basado en el progreso
    titulo = "💰 Nuevo aporte registrado"
    mensaje = f"Has registrado un aporte de ${instance.monto:,.2f} a tu meta '{meta.nombre}'. "
    
    if meta.meta_alcanzada():
        # Meta alcanzada - notificación de felicitación
        titulo = "🎉 ¡Meta alcanzada!"
        mensaje += f"¡Felicidades! Has alcanzado tu meta de ${meta.monto_objetivo:,.2f}. ¡Excelente trabajo!"
        categoria = "Logros"
        tipo_notificacion = "meta_alcanzada"
    elif progreso_anterior >= 90:
        # Cerca de la meta
        titulo = "🎯 ¡Casi lo logras!"
        mensaje += f"Ya tienes {progreso_anterior:.1f}% de tu meta. Solo te faltan ${meta.falta_por_ahorrar():,.2f}."
        categoria = "Metas"
        tipo_notificacion = "progreso_meta"
    elif progreso_anterior >= 75:
        # Buen progreso
        mensaje += f"Vas muy bien, ya tienes {progreso_anterior:.1f}% de tu meta."
        categoria = "Metas"
        tipo_notificacion = "progreso_meta"
    else:
        # Progreso normal
        mensaje += f"Progreso actual: {progreso_anterior:.1f}% de tu meta."
        categoria = "Metas"
        tipo_notificacion = "aporte_realizado"
    
    # Crear la notificación
    NotificationService.crear_notificacion(
        usuario=usuario,
        tipo_notificacion=tipo_notificacion,
        titulo=titulo,
        mensaje=mensaje,
        categoria=categoria,
        prioridad='media' if not meta.meta_alcanzada() else 'alta',
        datos_adicionales={
            'meta_id': meta.id,
            'meta_nombre': meta.nombre,
            'aporte_monto': float(instance.monto),
            'progreso_porcentaje': progreso_anterior,
            'monto_objetivo': float(meta.monto_objetivo),
            'monto_ahorrado': meta.monto_ahorrado()
        }
    )


def _es_notificacion_movimiento_duplicada(usuario, cuenta, instance, hace_5_min):
    from alertas_notificaciones.models import Notificacion
    existe_notificacion = Notificacion.objects.filter(
        usuario=usuario,
        tipo_notificacion__nombre="movimiento_financiero",
        datos_adicionales__movimiento_id=instance.id,
        fecha_creacion__gte=hace_5_min
    ).exists()
    
    if existe_notificacion:
        return True
    
    duplicado_por_contenido = Notificacion.objects.filter(
        usuario=usuario,
        tipo_notificacion__nombre="movimiento_financiero",
        datos_adicionales__monto=float(instance.monto),
        datos_adicionales__movimiento_tipo=instance.tipo,
        datos_adicionales__cuenta_id=cuenta.id,
        fecha_creacion__gte=hace_5_min
    ).exists()
    return duplicado_por_contenido


def _obtener_titulo_y_mensaje_movimiento(instance, cuenta, usuario):
    """Genera el título y mensaje detallado para la notificación de movimiento."""
    if instance.tipo == 'ingreso':
        titulo = "💵 Nuevo ingreso registrado"
        motivacional = f"\n\n¡Excelente! Tus ingresos suman ${instance.monto:,.2f} más a tu patrimonio. 🎉"
    else:  # egreso
        titulo = "💸 Nuevo gasto registrado"
        if instance.monto >= 1000:
            motivacional = "\n\n⚠️ Este es un gasto considerable. Recuerda revisar tu presupuesto mensual."
        elif instance.monto >= 500:
            motivacional = "\n\n💡 Gasto registrado. Mantén el control de tus finanzas."
        else:
            motivacional = "\n\n✅ Gasto registrado correctamente en tu historial financiero."

    mensaje = (
        f"Hola {usuario.nombres},\n\n"
        f"Se ha registrado un {instance.tipo} con los siguientes detalles:\n\n"
        f"🏷️ **{instance.nombre}**\n"
        f"💰 Monto: ${instance.monto:,.2f}\n"
        f"🏦 Cuenta: {cuenta.nombre}\n"
    )
    if instance.descripcion:
        mensaje += f"📝 Descripción: {instance.descripcion}\n"
    
    mensaje += f"\n💳 Saldo actual de la cuenta: ${cuenta.saldo_cuenta:,.2f}" + motivacional
    return titulo, mensaje


def _obtener_prioridad_movimiento(monto):
    """Determina la prioridad de la notificación basada en el monto."""
    if monto >= 1000:
        return 'alta'
    elif monto >= 500:
        return 'media'
    return 'baja'


@receiver(post_save, sender=Movimiento)
@prevent_duplicate_signals('movimiento_financiero', timeout=60)
def notificar_movimiento_financiero(sender, instance, created, **kwargs):
    """Notifica cuando se registra un nuevo movimiento financiero"""
    print(f"SIGNAL EXECUTED: Movimiento {instance.tipo} - ${instance.monto} para usuario {instance.id_usuario.nombres}")
    print(f"Created: {created}, Sender: {sender.__name__}, ID: {instance.id}")
    
    if not created:
        print("WARNING: Movimiento actualizado, no se creo notificacion")
        return
    
    usuario = instance.id_usuario
    cuenta = instance.id_cuenta
    
    from datetime import timedelta
    hace_5_min = timezone.now() - timedelta(minutes=5)
    
    if _es_notificacion_movimiento_duplicada(usuario, cuenta, instance, hace_5_min):
        print(f"WARNING: Ya existe notificacion duplicada para movimiento ID {instance.id}, saltando...")
        return
    
    try:
        titulo, mensaje = _obtener_titulo_y_mensaje_movimiento(instance, cuenta, usuario)
        prioridad = _obtener_prioridad_movimiento(instance.monto)
        
        print("Creando notificacion de movimiento")
        
        # Crear la notificación
        NotificationService.crear_notificacion(
            usuario=usuario,
            tipo_notificacion="movimiento_financiero",
            titulo=titulo,
            mensaje=mensaje,
            categoria="Transacciones",
            prioridad=prioridad,
            datos_adicionales={
                'movimiento_id': instance.id,
                'movimiento_tipo': instance.tipo,
                'movimiento_nombre': instance.nombre,
                'monto': float(instance.monto),
                'cuenta_id': cuenta.id,
                'cuenta_nombre': cuenta.nombre,
                'saldo_actual': float(cuenta.saldo_cuenta),
                'fecha_movimiento': instance.fecha_movimiento.isoformat(),
                'descripcion': instance.descripcion or ''
            }
        )
        
        print("OK: Notificacion creada exitosamente")
        
    except Exception:
        logger.exception("Error en notificación de movimiento")
    else:
        print("WARNING: Movimiento actualizado, no se creo notificacion")


@receiver(post_save, sender=Cuenta)
def notificar_cambio_saldo_cuenta(sender, instance, created, **kwargs):
    """Notifica sobre cambios importantes en el saldo de una cuenta"""
    if not created:  # Solo para actualizaciones, no creaciones
        usuario = instance.id_usuario
        
        # Verificar si el saldo está en números rojos
        if instance.saldo_cuenta < 0:
            titulo = "🚨 Saldo negativo"
            mensaje = f"¡Atención! Tu cuenta '{instance.nombre}' tiene saldo negativo: ${instance.saldo_cuenta:,.2f}. "
            mensaje += "Es recomendable hacer un depósito lo antes posible."
            
            NotificationService.crear_notificacion(
                usuario=usuario,
                tipo_notificacion="saldo_negativo",
                titulo=titulo,
                mensaje=mensaje,
                categoria="Saldo",
                prioridad='urgente',
                datos_adicionales={
                    'cuenta_id': instance.id,
                    'cuenta_nombre': instance.nombre,
                    'saldo_actual': float(instance.saldo_cuenta)
                }
            )
        
        # Verificar si el saldo está bajo (menos de $50)
        elif instance.saldo_cuenta < 50:
            titulo = "⚠️ Saldo bajo en cuenta"
            mensaje = f"Tu cuenta '{instance.nombre}' tiene un saldo bajo: ${instance.saldo_cuenta:,.2f}. "
            mensaje += "Considera revisar tus gastos o hacer un depósito."
            
            NotificationService.crear_notificacion(
                usuario=usuario,
                tipo_notificacion="saldo_bajo",
                titulo=titulo,
                mensaje=mensaje,
                categoria="Saldo",
                prioridad='alta',
                datos_adicionales={
                    'cuenta_id': instance.id,
                    'cuenta_nombre': instance.nombre,
                    'saldo_actual': float(instance.saldo_cuenta)
                }
            )


@receiver(post_save, sender=MetaAhorro)
@prevent_duplicate_signals('nueva_meta_ahorro', timeout=60)
def notificar_nueva_meta_ahorro(_sender, instance, created, **_kwargs):
    """Notifica cuando se crea una nueva meta de ahorro"""
    if not created:
        return
        
    # Verificar duplicados
    from alertas_notificaciones.models import Notificacion
    from datetime import timedelta
    
    hace_5_min = timezone.now() - timedelta(minutes=5)
    existe_notificacion = Notificacion.objects.filter(
        usuario=instance.id_usuario,
        tipo_notificacion__nombre="nueva_meta",
        datos_adicionales__meta_id=instance.id,
        fecha_creacion__gte=hace_5_min
    ).exists()
    
    if existe_notificacion:
        print("WARNING: Ya existe notificacion para esta nueva meta, saltando...")
        return
        
    usuario = instance.id_usuario
    
    titulo = "🎯 Nueva meta de ahorro creada"
    mensaje = f"Has creado la meta '{instance.nombre}' con un objetivo de ${instance.monto_objetivo:,.2f}. "
    mensaje += f"Fecha límite: {instance.fecha_limite.strftime('%d/%m/%Y')}. ¡Comienza a ahorrar!"
    
    NotificationService.crear_notificacion(
        usuario=usuario,
        tipo_notificacion="nueva_meta",
        titulo=titulo,
        mensaje=mensaje,
        categoria="Metas",
        prioridad='media',
        datos_adicionales={
            'meta_id': instance.id,
            'meta_nombre': instance.nombre,
            'monto_objetivo': float(instance.monto_objetivo),
            'fecha_limite': instance.fecha_limite.isoformat(),
            'frecuencia_aporte': instance.frecuencia_aporte
        }
    )


def verificar_metas_vencidas():
    """
    Función auxiliar para verificar metas que están próximas a vencer
    Esta función debería ser llamada por un cron job o tarea programada
    """
    from datetime import timedelta
    
    # Buscar metas que vencen en los próximos 7 días
    fecha_limite = timezone.now().date() + timedelta(days=7)
    metas_por_vencer = MetaAhorro.objects.filter(
        fecha_limite__lte=fecha_limite,
        fecha_limite__gte=timezone.now().date()
    ).exclude(
        # Excluir metas ya alcanzadas
        id__in=MetaAhorro.objects.filter(
            aportes__isnull=False
        ).annotate(
            total_ahorrado=models.Sum('aportes__monto')
        ).filter(
            total_ahorrado__gte=models.F('monto_objetivo')
        )
    )
    
    for meta in metas_por_vencer:
        dias_restantes = (meta.fecha_limite - timezone.now().date()).days
        progreso = meta.porcentaje_progreso()
        
        if dias_restantes <= 1:
            titulo = "⏰ Meta por vencer hoy"
            prioridad = 'urgente'
        elif dias_restantes <= 3:
            titulo = f"⏰ Meta por vencer en {dias_restantes} días"
            prioridad = 'alta'
        else:
            titulo = f"📅 Meta por vencer en {dias_restantes} días"
            prioridad = 'media'
        
        mensaje = f"Tu meta '{meta.nombre}' vence el {meta.fecha_limite.strftime('%d/%m/%Y')}. "
        mensaje += f"Progreso actual: {progreso:.1f}%. "
        
        if progreso < 90:
            falta = meta.falta_por_ahorrar()
            mensaje += f"Te faltan ${falta:,.2f} para alcanzarla."
        else:
            mensaje += "¡Estás muy cerca de lograrla!"
        
        NotificationService.crear_notificacion(
            usuario=meta.id_usuario,
            tipo_notificacion="meta_por_vencer",
            titulo=titulo,
            mensaje=mensaje,
            categoria="Metas",
            prioridad=prioridad,
            datos_adicionales={
                'meta_id': meta.id,
                'meta_nombre': meta.nombre,
                'dias_restantes': dias_restantes,
                'progreso_porcentaje': progreso,
                'monto_faltante': meta.falta_por_ahorrar()
            }
        )
