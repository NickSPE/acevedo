from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.db import models
from decimal import Decimal
import logging

from .models import MetaAhorro, AporteMetaAhorro, Movimiento
from cuentas.models import Cuenta, SubCuenta
from alertas_notificaciones.services import NotificationService
from alertas_notificaciones.signal_decorators import prevent_duplicate_signals

logger = logging.getLogger(__name__)


@receiver(post_save, sender=AporteMetaAhorro)
@prevent_duplicate_signals('aporte_meta_ahorro', timeout=60)
def notificar_nuevo_aporte(sender, instance, created, **kwargs):
    """Notifica cuando se realiza un nuevo aporte a una meta de ahorro"""
    if not created:
        return
        
    # Verificar duplicados
    from alertas_notificaciones.models import Notificacion
    from django.utils import timezone
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
        print(f"⚠️ Ya existe notificación para este aporte, saltando...")
        return
        
    meta = instance.id_meta_ahorro
    usuario = instance.id_usuario
    
    # Calcular progreso actual
    progreso_anterior = meta.porcentaje_progreso()
    
    # Determinar tipo de notificación basado en el progreso
    titulo = f"💰 Nuevo aporte registrado"
    mensaje = f"Has registrado un aporte de ${instance.monto:,.2f} a tu meta '{meta.nombre}'. "
    
    if meta.meta_alcanzada():
        # Meta alcanzada - notificación de felicitación
        titulo = f"🎉 ¡Meta alcanzada!"
        mensaje += f"¡Felicidades! Has alcanzado tu meta de ${meta.monto_objetivo:,.2f}. ¡Excelente trabajo!"
        categoria = "Logros"
        tipo_notificacion = "meta_alcanzada"
    elif progreso_anterior >= 90:
        # Cerca de la meta
        titulo = f"🎯 ¡Casi lo logras!"
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


@receiver(post_save, sender=Movimiento)
@prevent_duplicate_signals('movimiento_financiero', timeout=60)
def notificar_movimiento_financiero(sender, instance, created, **kwargs):
    """Notifica cuando se registra un nuevo movimiento financiero"""
    print(f"🔔 SEÑAL EJECUTADA: Movimiento {instance.tipo} - ${instance.monto} para usuario {instance.id_usuario.nombres}")
    print(f"🔍 Created: {created}, Sender: {sender.__name__}, ID: {instance.id}")
    
    if not created:
        print(f"⚠️ Movimiento actualizado, no se creó notificación")
        return
    
    usuario = instance.id_usuario
    cuenta = instance.id_cuenta
    
    # Verificar si ya existe una notificación para este movimiento (evitar duplicados)
    from alertas_notificaciones.models import Notificacion
    from django.utils import timezone
    from datetime import timedelta
    
    # Buscar notificaciones duplicadas en los últimos 5 minutos para el mismo movimiento
    hace_5_min = timezone.now() - timedelta(minutes=5)
    existe_notificacion = Notificacion.objects.filter(
        usuario=usuario,
        tipo_notificacion__nombre="movimiento_financiero",
        datos_adicionales__movimiento_id=instance.id,
        fecha_creacion__gte=hace_5_min
    ).exists()
    
    if existe_notificacion:
        print(f"⚠️ Ya existe notificación para movimiento ID {instance.id}, saltando...")
        return
    
    # Verificar también por monto, fecha y tipo para evitar duplicados por problemas de timing
    duplicado_por_contenido = Notificacion.objects.filter(
        usuario=usuario,
        tipo_notificacion__nombre="movimiento_financiero",
        datos_adicionales__monto=float(instance.monto),
        datos_adicionales__movimiento_tipo=instance.tipo,
        datos_adicionales__cuenta_id=cuenta.id,
        fecha_creacion__gte=hace_5_min
    ).exists()
    
    if duplicado_por_contenido:
        print(f"⚠️ Ya existe notificación similar para este tipo de movimiento, saltando...")
        return
    
    try:
        if instance.tipo == 'ingreso':
            titulo = f"💵 Nuevo ingreso registrado"
            emoji = "💵"
            color = "verde"
        else:  # egreso
            titulo = f"💸 Nuevo gasto registrado"
            emoji = "💸"
            color = "rojo"
        
        # Mensaje más detallado con el nombre de la transacción
        mensaje = f"Hola {usuario.nombres},\n\n"
        mensaje += f"Se ha registrado un {instance.tipo} con los siguientes detalles:\n\n"
        mensaje += f"🏷️ **{instance.nombre}**\n"
        mensaje += f"💰 Monto: ${instance.monto:,.2f}\n"
        mensaje += f"🏦 Cuenta: {cuenta.nombre}\n"
        
        if instance.descripcion:
            mensaje += f"📝 Descripción: {instance.descripcion}\n"
        
        mensaje += f"\n💳 Saldo actual de la cuenta: ${cuenta.saldo_cuenta:,.2f}"
        
        # Agregar mensaje motivacional o de alerta según el caso
        if instance.tipo == 'ingreso':
            mensaje += f"\n\n¡Excelente! Tus ingresos suman ${instance.monto:,.2f} más a tu patrimonio. 🎉"
        else:
            if instance.monto >= 1000:
                mensaje += f"\n\n⚠️ Este es un gasto considerable. Recuerda revisar tu presupuesto mensual."
            elif instance.monto >= 500:
                mensaje += f"\n\n💡 Gasto registrado. Mantén el control de tus finanzas."
            else:
                mensaje += f"\n\n✅ Gasto registrado correctamente en tu historial financiero."
        
        # Determinar prioridad basada en el monto
        if instance.monto >= 1000:
            prioridad = 'alta'
        elif instance.monto >= 500:
            prioridad = 'media'
        else:
            prioridad = 'baja'
        
        print(f"🔔 Creando notificación: {titulo}")
        
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
        
        print(f"✅ Notificación creada exitosamente")
        
    except Exception as e:
        print(f"❌ Error en notificación: {str(e)}")
        logger.error(f"Error en notificación de movimiento: {str(e)}")
    else:
        print(f"⚠️ Movimiento actualizado, no se creó notificación")


@receiver(post_save, sender=Cuenta)
def notificar_cambio_saldo_cuenta(sender, instance, created, **kwargs):
    """Notifica sobre cambios importantes en el saldo de una cuenta"""
    if not created:  # Solo para actualizaciones, no creaciones
        usuario = instance.id_usuario
        
        # Verificar si el saldo está bajo (menos de $50)
        if instance.saldo_cuenta < 50:
            titulo = f"⚠️ Saldo bajo en cuenta"
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
        
        # Verificar si el saldo está en números rojos
        elif instance.saldo_cuenta < 0:
            titulo = f"🚨 Saldo negativo"
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


@receiver(post_save, sender=MetaAhorro)
@prevent_duplicate_signals('nueva_meta_ahorro', timeout=60)
def notificar_nueva_meta_ahorro(sender, instance, created, **kwargs):
    """Notifica cuando se crea una nueva meta de ahorro"""
    if not created:
        return
        
    # Verificar duplicados
    from alertas_notificaciones.models import Notificacion
    from django.utils import timezone
    from datetime import timedelta
    
    hace_5_min = timezone.now() - timedelta(minutes=5)
    existe_notificacion = Notificacion.objects.filter(
        usuario=instance.id_usuario,
        tipo_notificacion__nombre="nueva_meta",
        datos_adicionales__meta_id=instance.id,
        fecha_creacion__gte=hace_5_min
    ).exists()
    
    if existe_notificacion:
        print(f"⚠️ Ya existe notificación para esta nueva meta, saltando...")
        return
        
    usuario = instance.id_usuario
    
    titulo = f"🎯 Nueva meta de ahorro creada"
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
    from datetime import datetime, timedelta
    
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
            titulo = f"⏰ Meta por vencer hoy"
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
