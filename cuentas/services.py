"""Servicios para la app cuentas (lógica de negocio)"""

from django.db import transaction
from django.contrib.auth import update_session_auth_hash
from .models import TransferenciaSubCuenta, TransferenciaCuentaPrincipal
from .utils import es_subcuenta_negocio


def actualizar_perfil_usuario(usuario, nombres, apellido_paterno, apellido_materno, pais):
    """Actualiza la información personal del usuario"""
    usuario.nombres = nombres
    usuario.apellido_paterno = apellido_paterno
    usuario.apellido_materno = apellido_materno
    usuario.pais = pais
    usuario.save()


def actualizar_contacto_usuario(usuario, email, telefono=None):
    """Actualiza email y teléfono del usuario"""
    usuario.correo = email
    if telefono:
        usuario.telefono = telefono
    usuario.save()


def cambiar_password_usuario(usuario, actual_password, new_password, request=None):
    """
    Cambia la contraseña del usuario.
    Si se proporciona request, mantiene la sesión activa.
    """
    if not usuario.check_password(actual_password):
        return False, "La contraseña actual es incorrecta"
    
    usuario.set_password(new_password)
    usuario.save()
    
    # Mantener sesión activa si se proporciona request
    if request:
        update_session_auth_hash(request, usuario)
    
    return True, "Contraseña actualizada exitosamente"


def cambiar_pin_usuario(usuario, current_pin, new_pin):
    """Cambia el PIN de acceso rápido del usuario"""
    if not usuario.check_pin(current_pin):
        return False, "El PIN actual es incorrecto"

    usuario.set_pin(new_pin)
    usuario.save()

    return True, "PIN actualizado exitosamente"


def procesar_transferencia_entre_subcuentas(subcuenta_origen, subcuenta_destino, monto, usuario, descripcion=""):
    """Realiza transferencia entre dos subcuentas"""
    if subcuenta_origen.saldo < monto:
        return False, "Saldo insuficiente en la subcuenta origen"
    
    with transaction.atomic():
        subcuenta_origen.saldo -= monto
        subcuenta_destino.saldo += monto
        
        TransferenciaSubCuenta.objects.create(
            subcuenta_origen=subcuenta_origen,
            subcuenta_destino=subcuenta_destino,
            id_usuario=usuario,
            monto=monto,
            descripcion=descripcion or f'Transferencia de {subcuenta_origen.nombre} a {subcuenta_destino.nombre}'
        )
        
        subcuenta_origen.save()
        subcuenta_destino.save()
    
    return True, f"Transferencia de ${monto:.2f} realizada exitosamente"


def procesar_deposito_subcuenta(subcuenta, monto, usuario, descripcion=""):
    """Realiza depósito en una subcuenta (desde cuenta principal si es personal)"""
    es_negocio = es_subcuenta_negocio(subcuenta)
    
    with transaction.atomic():
        if es_negocio:
            # Para subcuentas de negocio, agregar dinero directamente
            subcuenta.saldo += monto
            subcuenta.save()
        else:
            # Para subcuentas personales, transferir desde cuenta principal
            if not subcuenta.id_cuenta:
                return False, "Error en la configuración de la subcuenta"
            
            cuenta_principal = subcuenta.id_cuenta
            saldo_disponible = cuenta_principal.saldo_disponible()
            
            if saldo_disponible < monto:
                return False, f"Saldo insuficiente. Disponible: ${saldo_disponible:.2f}"
            
            cuenta_principal.saldo_cuenta -= monto
            subcuenta.saldo += monto
            cuenta_principal.save()
            subcuenta.save()
    
    return True, f"Depósito de ${monto:.2f} realizado exitosamente"


def procesar_retiro_subcuenta(subcuenta, monto, usuario, descripcion=""):
    """Realiza retiro de una subcuenta"""
    if subcuenta.saldo < monto:
        return False, "Saldo insuficiente en la subcuenta"
    
    es_negocio = es_subcuenta_negocio(subcuenta)
    
    with transaction.atomic():
        if es_negocio:
            # Para subcuentas de negocio, restar dinero directamente
            subcuenta.saldo -= monto
            subcuenta.save()
        else:
            # Para subcuentas personales, transferir a cuenta principal
            if not subcuenta.id_cuenta:
                return False, "Error en la configuración de la subcuenta"
            
            cuenta_principal = subcuenta.id_cuenta
            subcuenta.saldo -= monto
            cuenta_principal.saldo_cuenta += monto
            
            TransferenciaCuentaPrincipal.objects.create(
                subcuenta=subcuenta,
                cuenta_destino=cuenta_principal,
                monto=monto,
                tipo='deposito',
                descripcion=descripcion or f'Retiro de {subcuenta.nombre}',
                id_usuario=usuario
            )
            
            subcuenta.save()
            cuenta_principal.save()
    
    return True, f"Retiro de ${monto:.2f} realizado exitosamente"


def procesar_transferencia_a_principal(subcuenta, cuenta_principal, monto, usuario, tipo='deposito', descripcion=""):
    """Realiza transferencia entre subcuenta y cuenta principal"""
    if tipo not in ['deposito', 'retiro']:
        return False, "Tipo de transferencia inválido"
    
    if tipo == 'deposito' and subcuenta.saldo < monto:
        return False, "Saldo insuficiente en la subcuenta"
    
    if tipo == 'retiro' and cuenta_principal.saldo_disponible() < monto:
        return False, "Saldo insuficiente en la cuenta principal"
    
    with transaction.atomic():
        if tipo == 'deposito':
            # Transferir de subcuenta a principal
            subcuenta.saldo -= monto
            cuenta_principal.saldo_cuenta += monto
            mensaje = f'Transferencia de ${monto:.2f} desde "{subcuenta.nombre}" a tu cuenta principal'
        else:
            # Transferir de principal a subcuenta
            cuenta_principal.saldo_cuenta -= monto
            subcuenta.saldo += monto
            mensaje = f'Transferencia de ${monto:.2f} desde tu cuenta principal a "{subcuenta.nombre}"'
        
        TransferenciaCuentaPrincipal.objects.create(
            subcuenta=subcuenta,
            cuenta_destino=cuenta_principal,
            monto=monto,
            tipo=tipo,
            descripcion=descripcion,
            id_usuario=usuario
        )
        
        subcuenta.save()
        cuenta_principal.save()
    
    return True, mensaje
