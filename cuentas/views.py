from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.urls import reverse
from usuarios.models import Usuario
from .models import Cuenta, SubCuenta, TransferenciaSubCuenta
from .forms import SubCuentaForm, TransferenciaSubCuentaForm, DepositoSubCuentaForm, RetiroSubCuentaForm
from core.decorators import fast_access_pin_verified

import base64
from PIL import Image
import io

""" Views App CUENTAS """

# Función de detección automática eliminada - ahora el usuario selecciona manualmente

@login_required
@fast_access_pin_verified
def profile(request):
    user_id = request.user.id

    if request.method == "POST":
        action = request.POST.get("action")
        
        # Si es solo un cambio de foto
        if action == "change_photo":
            imagen_perfil = request.FILES.get("imagen_perfil")
            if imagen_perfil:
                usuario = Usuario.objects.get(id=user_id)
                # Leer el archivo y convertirlo a bytes
                imagen_bytes = imagen_perfil.read()
                usuario.imagen_perfil = imagen_bytes
                usuario.save()
                messages.success(request, "Foto de perfil actualizada correctamente.")
            else:
                messages.error(request, "No se seleccionó ninguna imagen.")
            return redirect("cuentas:profile")
        
        # Si es actualización de datos generales
        nombres = request.POST.get("nombres")
        apellido_paterno = request.POST.get("apellido_paterno")
        apellido_materno = request.POST.get("apellido_materno")
        email = request.POST.get("email")
        telefono = request.POST.get("telefono")
        pais = request.POST.get("pais")
        
        # Campos de cambio de contraseña
        actual_password = request.POST.get("actual_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        # Obtener el usuario para actualizar
        usuario = Usuario.objects.get(id=user_id)
        
        # Si se están actualizando campos básicos
        if nombres or apellido_paterno or apellido_materno or email or telefono or pais:
            # Actualizar campos básicos
            if nombres:
                usuario.nombres = nombres
            if apellido_paterno:
                usuario.apellido_paterno = apellido_paterno
            if apellido_materno:
                usuario.apellido_materno = apellido_materno
            if email:
                usuario.correo = email
            if telefono:
                usuario.telefono = telefono
            if pais:
                usuario.pais = pais
            
            # Guardar los cambios
            usuario.save()
            messages.success(request, "Perfil actualizado correctamente.")
        
        # Si se está cambiando la contraseña
        if actual_password and new_password and confirm_password:
            # Verificar que la contraseña actual sea correcta
            if usuario.check_password(actual_password):
                # Verificar que las nuevas contraseñas coincidan
                if new_password == confirm_password:
                    # Verificar que la nueva contraseña tenga al menos 8 caracteres
                    if len(new_password) >= 8:
                        # Cambiar la contraseña
                        usuario.set_password(new_password)
                        usuario.save()
                        messages.success(request, "Contraseña actualizada correctamente.")
                        
                        # Mantener la sesión del usuario después del cambio de contraseña
                        from django.contrib.auth import update_session_auth_hash
                        update_session_auth_hash(request, usuario)
                        
                        return redirect("cuentas:profile" + "?tab=security")
                    else:
                        messages.error(request, "La nueva contraseña debe tener al menos 8 caracteres.")
                        return redirect("cuentas:profile" + "?tab=security")
                else:
                    messages.error(request, "Las nuevas contraseñas no coinciden.")
                    return redirect("cuentas:profile" + "?tab=security")
            else:
                messages.error(request, "La contraseña actual es incorrecta.")
                return redirect("cuentas:profile" + "?tab=security")
        
        return redirect("cuentas:profile")

    usuario = Usuario.objects.get(id=user_id)
    
    # Si el usuario no tiene país asignado, usar Perú como predeterminado
    if not usuario.pais or usuario.pais == "":
        usuario.pais = "Peru"
        usuario.save()
    
    formato_imagen = None
    imagen_base64 = None
    if(usuario.imagen_perfil):
        try:
            imagen_bytes = usuario.imagen_perfil
            imagen_base64 = base64.b64encode(imagen_bytes).decode('utf-8')
            formato_imagen = Image.open(io.BytesIO(imagen_bytes)).format
        except Exception as e:
            # Si hay error al procesar la imagen, limpiarla
            print(f"Error procesando imagen de perfil para usuario {usuario.id}: {e}")
            usuario.imagen_perfil = None
            usuario.save()
            imagen_base64 = None
            formato_imagen = None

    tab = request.GET.get("tab", "general")
    return render(request, "cuentas/profile.html", {
        "tab": tab , 
        "usuario": usuario,
        "imagen_base64": imagen_base64,
        "formato_imagen": formato_imagen,
    })

@login_required
@fast_access_pin_verified
def settings(request):
    return render(request, "cuentas/settings.html")


# === VISTAS PARA SUBCUENTAS ===

@login_required
@fast_access_pin_verified
def subcuentas_dashboard(request):
    """Vista principal del dashboard de subcuentas"""
    # Obtener todas las cuentas del usuario
    cuentas = Cuenta.objects.filter(id_usuario=request.user)
    
    # Obtener estadísticas generales
    total_subcuentas = SubCuenta.objects.filter(id_cuenta__id_usuario=request.user, activa=True).count()
    total_subcuentas_inactivas = SubCuenta.objects.filter(id_cuenta__id_usuario=request.user, activa=False).count()
    total_saldo_subcuentas = sum([cuenta.saldo_total_subcuentas() for cuenta in cuentas])
    
    # Obtener subcuentas por cuenta (TODAS, activas e inactivas)
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
    
    # Obtener transferencias recientes
    transferencias_recientes = TransferenciaSubCuenta.objects.filter(
        id_usuario=request.user
    )[:10]
    
    return render(request, 'cuentas/subcuentas_dashboard_new.html', {
        'cuentas_con_subcuentas': cuentas_con_subcuentas,
        'total_subcuentas': total_subcuentas,
        'total_subcuentas_inactivas': total_subcuentas_inactivas,
        'total_saldo_subcuentas': total_saldo_subcuentas,
        'transferencias_recientes': transferencias_recientes,
    })


@login_required
@fast_access_pin_verified
def crear_subcuenta(request, cuenta_id):
    """Vista para crear una nueva subcuenta"""
    cuenta = get_object_or_404(Cuenta, id=cuenta_id, id_usuario=request.user)
    
    if request.method == 'POST':
        form = SubCuentaForm(request.POST)
        if form.is_valid():
            subcuenta = form.save(commit=False)
            subcuenta.id_cuenta = cuenta
            subcuenta.save()
            
            messages.success(request, f'SubCuenta "{subcuenta.nombre}" creada exitosamente.')
            return redirect('cuentas:subcuentas_dashboard')
    else:
        form = SubCuentaForm()
    
    return render(request, 'cuentas/crear_subcuenta.html', {
        'form': form,
        'cuenta': cuenta
    })


@login_required
@fast_access_pin_verified
def editar_subcuenta(request, subcuenta_id):
    """Vista para editar una subcuenta existente"""
    subcuenta = get_object_or_404(SubCuenta, id=subcuenta_id, id_cuenta__id_usuario=request.user)
    
    if request.method == 'POST':
        form = SubCuentaForm(request.POST, instance=subcuenta)
        if form.is_valid():
            form.save()
            messages.success(request, f'SubCuenta "{subcuenta.nombre}" actualizada exitosamente.')
            return redirect('cuentas:subcuentas_dashboard')
    else:
        form = SubCuentaForm(instance=subcuenta)
    
    return render(request, 'cuentas/editar_subcuenta.html', {
        'form': form,
        'subcuenta': subcuenta
    })


@login_required
@fast_access_pin_verified
def eliminar_subcuenta(request, subcuenta_id):
    """Vista para eliminar (desactivar) una subcuenta"""
    subcuenta = get_object_or_404(SubCuenta, id=subcuenta_id, id_cuenta__id_usuario=request.user)
    
    if request.method == 'POST':
        # Si la subcuenta tiene saldo, transferirlo de vuelta a la cuenta principal
        if subcuenta.saldo > 0:
            with transaction.atomic():
                subcuenta.id_cuenta.saldo_cuenta += subcuenta.saldo
                subcuenta.id_cuenta.save()
                subcuenta.saldo = 0
                subcuenta.activa = False
                subcuenta.save()
                
            messages.success(request, f'SubCuenta "{subcuenta.nombre}" eliminada y su saldo (${subcuenta.saldo:.2f}) transferido a la cuenta principal.')
        else:
            subcuenta.activa = False
            subcuenta.save()
            messages.success(request, f'SubCuenta "{subcuenta.nombre}" eliminada exitosamente.')
        
        return redirect('cuentas:subcuentas_dashboard')
    
    # Verificar si tiene transferencias
    tiene_transferencias = TransferenciaSubCuenta.objects.filter(
        Q(subcuenta_origen=subcuenta) | Q(subcuenta_destino=subcuenta)
    ).exists()
    
    return render(request, 'cuentas/eliminar_subcuenta.html', {
        'subcuenta': subcuenta,
        'tiene_transferencias': tiene_transferencias
    })


@login_required
@fast_access_pin_verified
def transferir_subcuentas(request):
    """Vista para transferir dinero entre subcuentas"""
    if request.method == 'POST':
        form = TransferenciaSubCuentaForm(request.POST, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                transferencia = form.save(commit=False)
                transferencia.id_usuario = request.user
                
                # Realizar la transferencia
                origen = transferencia.subcuenta_origen
                destino = transferencia.subcuenta_destino
                monto = transferencia.monto
                
                origen.saldo -= monto
                destino.saldo += monto
                
                origen.save()
                destino.save()
                transferencia.save()
                
            messages.success(request, f'Transferencia de ${monto:.2f} realizada exitosamente de "{origen.nombre}" a "{destino.nombre}".')
            return redirect('cuentas:subcuentas_dashboard')
    else:
        form = TransferenciaSubCuentaForm(user=request.user)
    
    # Obtener subcuentas activas para el template
    subcuentas_activas = SubCuenta.objects.filter(
        id_cuenta__id_usuario=request.user, 
        activa=True
    )
    
    return render(request, 'cuentas/transferir_subcuentas.html', {
        'form': form,
        'subcuentas_activas': subcuentas_activas
    })


@login_required
@fast_access_pin_verified
def depositar_subcuenta(request, subcuenta_id):
    """Vista para depositar dinero de la cuenta principal a una subcuenta"""
    subcuenta = get_object_or_404(SubCuenta, id=subcuenta_id, id_cuenta__id_usuario=request.user)
    cuenta = subcuenta.id_cuenta
    
    if request.method == 'POST':
        form = DepositoSubCuentaForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                monto = form.cleaned_data['monto']
                descripcion = form.cleaned_data['descripcion']
                
                # Verificar que hay saldo suficiente
                if cuenta.saldo_disponible() >= monto:
                    # Realizar el depósito
                    subcuenta.saldo += monto
                    subcuenta.save()
                    
                    messages.success(request, f'Depósito de ${monto:.2f} realizado exitosamente a "{subcuenta.nombre}".')
                    return redirect('cuentas:subcuentas_dashboard')
                else:
                    messages.error(request, 'No hay saldo suficiente en la cuenta principal.')
    else:
        form = DepositoSubCuentaForm()
    
    return render(request, 'cuentas/depositar_subcuenta.html', {
        'form': form,
        'subcuenta': subcuenta,
        'cuenta': cuenta
    })


@login_required
@fast_access_pin_verified
def retirar_subcuenta(request, subcuenta_id):
    """Vista para retirar dinero de una subcuenta a la cuenta principal"""
    subcuenta = get_object_or_404(SubCuenta, id=subcuenta_id, id_cuenta__id_usuario=request.user)
    cuenta = subcuenta.id_cuenta
    
    if request.method == 'POST':
        form = RetiroSubCuentaForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                monto = form.cleaned_data['monto']
                descripcion = form.cleaned_data['descripcion']
                
                # Realizar el retiro
                subcuenta.saldo -= monto
                cuenta.saldo_cuenta += monto
                
                subcuenta.save()
                cuenta.save()
                
            messages.success(request, f'Retiro de ${monto:.2f} realizado exitosamente desde "{subcuenta.nombre}".')
            return redirect('cuentas:subcuentas_dashboard')
    else:
        form = RetiroSubCuentaForm()
    
    return render(request, 'cuentas/retirar_subcuenta.html', {
        'form': form,
        'subcuenta': subcuenta,
        'cuenta': cuenta
    })


@login_required
@fast_access_pin_verified
def historial_transferencias(request):
    """Vista para ver el historial de transferencias"""
    from datetime import datetime, timedelta
    from django.utils import timezone
    from django.core.paginator import Paginator
    
    # Obtener todas las transferencias del usuario
    transferencias_query = TransferenciaSubCuenta.objects.filter(
        id_usuario=request.user
    )
    
    # Filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    subcuenta_id = request.GET.get('subcuenta')
    monto_min = request.GET.get('monto_min')
    orden = request.GET.get('orden', '-fecha_transferencia')
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            transferencias_query = transferencias_query.filter(fecha_transferencia__date__gte=fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            transferencias_query = transferencias_query.filter(fecha_transferencia__date__lte=fecha_hasta_dt)
        except ValueError:
            pass
    
    if subcuenta_id:
        try:
            subcuenta_id = int(subcuenta_id)
            transferencias_query = transferencias_query.filter(
                Q(subcuenta_origen_id=subcuenta_id) | Q(subcuenta_destino_id=subcuenta_id)
            )
        except ValueError:
            pass
    
    if monto_min:
        try:
            monto_min = float(monto_min)
            transferencias_query = transferencias_query.filter(monto__gte=monto_min)
        except ValueError:
            pass
    
    # Ordenamiento
    if orden in ['fecha_transferencia', '-fecha_transferencia', 'monto', '-monto']:
        transferencias_query = transferencias_query.order_by(orden)
    else:
        transferencias_query = transferencias_query.order_by('-fecha_transferencia')
    
    # Estadísticas
    total_transferencias = transferencias_query.count()
    monto_total = transferencias_query.aggregate(Sum('monto'))['monto__sum'] or 0
    
    # Transferencias del mes actual
    fecha_inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    transferencias_mes = TransferenciaSubCuenta.objects.filter(
        id_usuario=request.user,
        fecha_transferencia__gte=fecha_inicio_mes
    ).count()
    
    promedio_monto = monto_total / total_transferencias if total_transferencias > 0 else 0
    
    # Paginación
    paginator = Paginator(transferencias_query, 20)
    page_number = request.GET.get('page')
    transferencias = paginator.get_page(page_number)
    
    # Obtener todas las subcuentas para el filtro
    todas_subcuentas = SubCuenta.objects.filter(id_cuenta__id_usuario=request.user)
    
    return render(request, 'cuentas/historial_transferencias.html', {
        'transferencias': transferencias,
        'total_transferencias': total_transferencias,
        'monto_total': monto_total,
        'transferencias_mes': transferencias_mes,
        'promedio_monto': promedio_monto,
        'todas_subcuentas': todas_subcuentas,
        'is_paginated': transferencias.has_other_pages(),
        'page_obj': transferencias,
    })


@login_required
@fast_access_pin_verified
def activar_subcuenta(request, subcuenta_id):
    """Vista para activar una subcuenta inactiva"""
    subcuenta = get_object_or_404(SubCuenta, id=subcuenta_id, id_cuenta__id_usuario=request.user)
    
    if request.method == 'POST':
        subcuenta.activa = True
        subcuenta.save()
        
        messages.success(request, f'SubCuenta "{subcuenta.nombre}" activada exitosamente.')
        return redirect('cuentas:subcuentas_dashboard')
    
    return render(request, 'cuentas/activar_subcuenta.html', {
        'subcuenta': subcuenta
    })