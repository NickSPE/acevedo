from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
import json

from .models import MetaAhorro, AporteMetaAhorro, Movimiento
from cuentas.models import Cuenta
from alertas_notificaciones.services import NotificationService


@login_required
def test_notifications(request):
    """Vista para probar el sistema de notificaciones"""
    if request.method == 'POST':
        test_type = request.POST.get('test_type')
        
        if test_type == 'aporte_meta':
            return _test_aporte_meta(request)
        elif test_type == 'movimiento_ingreso':
            return _test_movimiento_ingreso(request)
        elif test_type == 'movimiento_egreso':
            return _test_movimiento_egreso(request)
        elif test_type == 'saldo_bajo':
            return _test_saldo_bajo(request)
        elif test_type == 'nueva_meta':
            return _test_nueva_meta(request)
    
    # Obtener datos del usuario para mostrar en la vista
    context = {
        'metas': MetaAhorro.objects.filter(id_usuario=request.user),
        'cuentas': Cuenta.objects.filter(id_usuario=request.user),
    }
    
    return render(request, 'gestion_financiera_basica/test_notifications.html', context)


def _test_aporte_meta(request):
    """Simula un aporte a una meta de ahorro"""
    try:
        meta_id = request.POST.get('meta_id')
        monto = Decimal(request.POST.get('monto', '100'))
        
        if not meta_id:
            messages.error(request, 'Debes seleccionar una meta de ahorro')
            return redirect('gestion_financiera_basica:test_notifications')
        
        meta = MetaAhorro.objects.get(id=meta_id, id_usuario=request.user)
        
        # Crear el aporte (esto disparará la señal automáticamente)
        aporte = AporteMetaAhorro.objects.create(
            id_meta_ahorro=meta,
            monto=monto,
            descripcion="Aporte de prueba del sistema de notificaciones",
            id_usuario=request.user
        )
        
        messages.success(
            request, 
            f'✅ Aporte de ${monto} creado. Se ha enviado una notificación por email si tienes habilitadas las notificaciones.'
        )
        
    except Exception as e:
        messages.error(request, f'Error al crear aporte: {str(e)}')
    
    return redirect('gestion_financiera_basica:test_notifications')


def _test_movimiento_ingreso(request):
    """Simula un ingreso financiero"""
    try:
        cuenta_id = request.POST.get('cuenta_id')
        monto = Decimal(request.POST.get('monto', '500'))
        
        if not cuenta_id:
            messages.error(request, 'Debes seleccionar una cuenta')
            return redirect('gestion_financiera_basica:test_notifications')
        
        cuenta = Cuenta.objects.get(id=cuenta_id, id_usuario=request.user)
        
        # Crear el movimiento (esto disparará la señal automáticamente)
        movimiento = Movimiento.objects.create(
            nombre="Ingreso de prueba",
            tipo='ingreso',
            monto=monto,
            fecha_movimiento=timezone.now(),
            descripcion="Ingreso de prueba del sistema de notificaciones",
            id_cuenta=cuenta,
            id_usuario=request.user
        )
        
        # Actualizar saldo de cuenta
        cuenta.saldo_cuenta += monto
        cuenta.save()
        
        messages.success(
            request, 
            f'✅ Ingreso de ${monto} registrado. Se ha enviado una notificación por email.'
        )
        
    except Exception as e:
        messages.error(request, f'Error al crear ingreso: {str(e)}')
    
    return redirect('gestion_financiera_basica:test_notifications')


def _test_movimiento_egreso(request):
    """Simula un gasto financiero"""
    try:
        cuenta_id = request.POST.get('cuenta_id')
        monto = Decimal(request.POST.get('monto', '200'))
        
        if not cuenta_id:
            messages.error(request, 'Debes seleccionar una cuenta')
            return redirect('gestion_financiera_basica:test_notifications')
        
        cuenta = Cuenta.objects.get(id=cuenta_id, id_usuario=request.user)
        
        # Crear el movimiento (esto disparará la señal automáticamente)
        movimiento = Movimiento.objects.create(
            nombre="Gasto de prueba",
            tipo='egreso',
            monto=monto,
            fecha_movimiento=timezone.now(),
            descripcion="Gasto de prueba del sistema de notificaciones",
            id_cuenta=cuenta,
            id_usuario=request.user
        )
        
        # Actualizar saldo de cuenta
        cuenta.saldo_cuenta -= monto
        cuenta.save()
        
        messages.success(
            request, 
            f'✅ Gasto de ${monto} registrado. Se ha enviado una notificación por email.'
        )
        
    except Exception as e:
        messages.error(request, f'Error al crear gasto: {str(e)}')
    
    return redirect('gestion_financiera_basica:test_notifications')


def _test_saldo_bajo(request):
    """Simula un saldo bajo en cuenta"""
    try:
        cuenta_id = request.POST.get('cuenta_id')
        
        if not cuenta_id:
            messages.error(request, 'Debes seleccionar una cuenta')
            return redirect('gestion_financiera_basica:test_notifications')
        
        cuenta = Cuenta.objects.get(id=cuenta_id, id_usuario=request.user)
        saldo_anterior = cuenta.saldo_cuenta
        
        # Establecer un saldo bajo (esto disparará la señal automáticamente)
        cuenta.saldo_cuenta = Decimal('25.00')
        cuenta.save()
        
        messages.success(
            request, 
            f'✅ Saldo de cuenta cambiado de ${saldo_anterior} a ${cuenta.saldo_cuenta}. Se ha enviado una alerta de saldo bajo.'
        )
        
    except Exception as e:
        messages.error(request, f'Error al cambiar saldo: {str(e)}')
    
    return redirect('gestion_financiera_basica:test_notifications')


def _test_nueva_meta(request):
    """Simula la creación de una nueva meta"""
    try:
        cuenta_id = request.POST.get('cuenta_id')
        
        if not cuenta_id:
            messages.error(request, 'Debes seleccionar una cuenta')
            return redirect('gestion_financiera_basica:test_notifications')
        
        cuenta = Cuenta.objects.get(id=cuenta_id, id_usuario=request.user)
        
        # Crear nueva meta (esto disparará la señal automáticamente)
        from datetime import date, timedelta
        
        meta = MetaAhorro.objects.create(
            nombre=f"Meta de Prueba {timezone.now().strftime('%H:%M')}",
            descripcion="Meta creada para probar el sistema de notificaciones",
            monto_objetivo=Decimal('2000.00'),
            fecha_inicio=date.today(),
            fecha_limite=date.today() + timedelta(days=90),
            frecuencia_aporte='mensual',
            id_usuario=request.user,
            id_cuenta=cuenta
        )
        
        messages.success(
            request, 
            f'✅ Nueva meta "{meta.nombre}" creada. Se ha enviado una notificación de confirmación.'
        )
        
    except Exception as e:
        messages.error(request, f'Error al crear meta: {str(e)}')
    
    return redirect('gestion_financiera_basica:test_notifications')
