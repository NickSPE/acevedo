"""Funciones utilitarias para la app cuentas"""

from django.db.models import Q, Sum
from .models import Cuenta, SubCuenta, TransferenciaSubCuenta, TransferenciaCuentaPrincipal
from gestion_financiera_basica.models import Movimiento


def obtener_cuentas_usuario(usuario):
    """Obtiene todas las cuentas del usuario"""
    return Cuenta.objects.filter(id_usuario=usuario)


def obtener_estadisticas_subcuentas(usuario):
    """Calcula estadísticas de subcuentas del usuario"""
    cuentas = obtener_cuentas_usuario(usuario)
    
    # Contar subcuentas
    total_vinculadas = SubCuenta.objects.filter(id_cuenta__id_usuario=usuario, activa=True).count()
    total_independientes = SubCuenta.objects.filter(propietario=usuario, id_cuenta__isnull=True, activa=True).count()
    total = total_vinculadas + total_independientes
    
    inactivas_vinculadas = SubCuenta.objects.filter(id_cuenta__id_usuario=usuario, activa=False).count()
    inactivas_independientes = SubCuenta.objects.filter(propietario=usuario, id_cuenta__isnull=True, activa=False).count()
    total_inactivas = inactivas_vinculadas + inactivas_independientes
    
    # Calcular saldos
    saldo_vinculadas = sum([cuenta.saldo_total_subcuentas() for cuenta in cuentas])
    
    subcuentas_independientes = SubCuenta.objects.filter(propietario=usuario, id_cuenta__isnull=True)
    saldo_independientes = sum([sc.saldo for sc in subcuentas_independientes])
    
    saldo_total = saldo_vinculadas + saldo_independientes
    
    return {
        'total_vinculadas': total_vinculadas,
        'total_independientes': total_independientes,
        'total': total,
        'total_inactivas': total_inactivas,
        'saldo_vinculadas': saldo_vinculadas,
        'saldo_independientes': saldo_independientes,
        'saldo_total': saldo_total,
    }


def obtener_balance_total(usuario):
    """Calcula el balance total del usuario (similar al dashboard principal)"""
    user_id = usuario.id
    
    total_ingresos = Movimiento.objects.filter(
        id_cuenta__id_usuario=user_id, tipo="ingreso"
    ).aggregate(total=Sum('monto'))['total'] or 0
    
    total_egresos = Movimiento.objects.filter(
        id_cuenta__id_usuario=user_id, tipo="egreso"
    ).aggregate(total=Sum('monto'))['total'] or 0
    
    saldo_inicial = Cuenta.objects.filter(
        id_usuario=user_id
    ).aggregate(total=Sum('saldo_cuenta'))['total'] or 0
    
    return float(saldo_inicial) + float(total_ingresos) - float(total_egresos)


def obtener_cuentas_con_subcuentas(usuario):
    """Obtiene cuentas con sus subcuentas"""
    cuentas = obtener_cuentas_usuario(usuario)
    cuentas_con_subcuentas = []
    
    for cuenta in cuentas:
        subcuentas_activas = SubCuenta.objects.filter(id_cuenta=cuenta, activa=True)
        subcuentas_inactivas = SubCuenta.objects.filter(id_cuenta=cuenta, activa=False)
        
        cuentas_con_subcuentas.append({
            'cuenta': cuenta,
            'subcuentas': subcuentas_activas,
            'subcuentas_inactivas': subcuentas_inactivas,
            'saldo_disponible': cuenta.saldo_disponible()
        })
    
    return cuentas_con_subcuentas


def obtener_subcuentas_independientes(usuario):
    """Obtiene subcuentas independientes del usuario"""
    activas = SubCuenta.objects.filter(propietario=usuario, id_cuenta__isnull=True, activa=True)
    inactivas = SubCuenta.objects.filter(propietario=usuario, id_cuenta__isnull=True, activa=False)
    
    return {
        'activas': activas,
        'inactivas': inactivas,
        'todas': list(activas) + list(inactivas)
    }


def obtener_transferencias_recientes(usuario, limite=10):
    """Obtiene transferencias recientes del usuario"""
    return TransferenciaSubCuenta.objects.filter(id_usuario=usuario)[:limite]


def es_subcuenta_negocio(subcuenta):
    """Determina si una subcuenta es de negocio (independiente)"""
    return subcuenta.es_negocio or (subcuenta.propietario and not subcuenta.id_cuenta)
