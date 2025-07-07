from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.urls import reverse
from usuarios.models import Usuario
from .models import Cuenta, SubCuenta, TransferenciaSubCuenta, TransferenciaCuentaPrincipal
from .forms import SubCuentaForm, TransferenciaSubCuentaForm, DepositoSubCuentaForm, RetiroSubCuentaForm, TransferenciaCuentaPrincipalForm
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
                        
                        return redirect(reverse("cuentas:profile") + "?tab=security")
                    else:
                        messages.error(request, "La nueva contraseña debe tener al menos 8 caracteres.")
                        return redirect(reverse("cuentas:profile") + "?tab=security")
                else:
                    messages.error(request, "Las nuevas contraseñas no coinciden.")
                    return redirect(reverse("cuentas:profile") + "?tab=security")
            else:
                messages.error(request, "La contraseña actual es incorrecta.")
                return redirect(reverse("cuentas:profile") + "?tab=security")
        
        # Si se está cambiando el PIN
        if action == "change_pin":
            # Construir el PIN actual desde los inputs individuales
            current_pin = ""
            for i in range(6):
                digit = request.POST.get(f"current_pin_{i}", "")
                current_pin += digit
            
            # Construir el nuevo PIN desde los inputs individuales
            new_pin = ""
            for i in range(6):
                digit = request.POST.get(f"new_pin_{i}", "")
                new_pin += digit
            
            # Construir el PIN de confirmación desde los inputs individuales
            confirm_pin = ""
            for i in range(6):
                digit = request.POST.get(f"confirm_pin_{i}", "")
                confirm_pin += digit
            
            print(f"🔍 DEBUG PIN CHANGE: Current: '{current_pin}', New: '{new_pin}', Confirm: '{confirm_pin}'")
            print(f"🔍 DEBUG PIN CHANGE: Usuario PIN actual: '{usuario.pin_acceso_rapido}'")
            
            # Validaciones
            if len(current_pin) != 6 or len(new_pin) != 6 or len(confirm_pin) != 6:
                messages.error(request, "Todos los PINs deben tener exactamente 6 dígitos.")
                return redirect(reverse("cuentas:profile") + "?tab=security")
            
            if not current_pin.isdigit() or not new_pin.isdigit() or not confirm_pin.isdigit():
                messages.error(request, "Los PINs solo pueden contener números.")
                return redirect(reverse("cuentas:profile") + "?tab=security")
            
            # Verificar que el PIN actual sea correcto
            if str(usuario.pin_acceso_rapido) != current_pin:
                messages.error(request, "El PIN actual es incorrecto.")
                return redirect(reverse("cuentas:profile") + "?tab=security")
            
            # Verificar que el nuevo PIN y la confirmación coincidan
            if new_pin != confirm_pin:
                messages.error(request, "El nuevo PIN y la confirmación no coinciden.")
                return redirect(reverse("cuentas:profile") + "?tab=security")
            
            # Verificar que el nuevo PIN sea diferente al actual
            if current_pin == new_pin:
                messages.warning(request, "El nuevo PIN debe ser diferente al actual.")
                return redirect(reverse("cuentas:profile") + "?tab=security")
            
            # Verificar que el nuevo PIN no esté siendo usado por otro usuario
            if Usuario.objects.filter(pin_acceso_rapido=new_pin).exclude(id=usuario.id).exists():
                messages.error(request, "Este PIN ya está siendo usado por otro usuario. Por favor, elige uno diferente.")
                return redirect(reverse("cuentas:profile") + "?tab=security")
            
            # Actualizar el PIN
            usuario.pin_acceso_rapido = new_pin
            usuario.save()
            
            print(f"✅ DEBUG PIN CHANGE: PIN actualizado exitosamente de '{current_pin}' a '{new_pin}'")
            messages.success(request, "PIN de acceso rápido actualizado correctamente.")
            return redirect(reverse("cuentas:profile") + "?tab=security")
        
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
    
    # Obtener estadísticas generales (incluir subcuentas independientes)
    total_subcuentas_vinculadas = SubCuenta.objects.filter(id_cuenta__id_usuario=request.user, activa=True).count()
    total_subcuentas_independientes = SubCuenta.objects.filter(propietario=request.user, id_cuenta__isnull=True, activa=True).count()
    total_subcuentas = total_subcuentas_vinculadas + total_subcuentas_independientes
    
    total_subcuentas_inactivas_vinculadas = SubCuenta.objects.filter(id_cuenta__id_usuario=request.user, activa=False).count()
    total_subcuentas_inactivas_independientes = SubCuenta.objects.filter(propietario=request.user, id_cuenta__isnull=True, activa=False).count()
    total_subcuentas_inactivas = total_subcuentas_inactivas_vinculadas + total_subcuentas_inactivas_independientes
    
    # Saldo total en subcuentas vinculadas
    total_saldo_subcuentas_vinculadas = sum([cuenta.saldo_total_subcuentas() for cuenta in cuentas])
    
    # Saldo total en subcuentas independientes
    subcuentas_independientes = SubCuenta.objects.filter(propietario=request.user, id_cuenta__isnull=True)
    total_saldo_subcuentas_independientes = sum([subcuenta.saldo for subcuenta in subcuentas_independientes])
    
    total_saldo_subcuentas = total_saldo_subcuentas_vinculadas + total_saldo_subcuentas_independientes
    
    # Obtener subcuentas por cuenta (vinculadas)
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
    
    # Obtener subcuentas independientes
    subcuentas_independientes_activas = SubCuenta.objects.filter(
        propietario=request.user, 
        id_cuenta__isnull=True, 
        activa=True
    )
    subcuentas_independientes_inactivas = SubCuenta.objects.filter(
        propietario=request.user, 
        id_cuenta__isnull=True, 
        activa=False
    )
    
    # Obtener transferencias recientes (incluir todos los tipos)
    transferencias_recientes = TransferenciaSubCuenta.objects.filter(
        id_usuario=request.user
    )[:10]
    
    return render(request, 'cuentas/subcuentas_dashboard_new.html', {
        'cuentas_con_subcuentas': cuentas_con_subcuentas,
        'subcuentas_independientes_activas': subcuentas_independientes_activas,
        'subcuentas_independientes_inactivas': subcuentas_independientes_inactivas,
        'total_subcuentas': total_subcuentas,
        'total_subcuentas_vinculadas': total_subcuentas_vinculadas,
        'total_subcuentas_independientes': total_subcuentas_independientes,
        'total_subcuentas_inactivas': total_subcuentas_inactivas,
        'total_saldo_subcuentas': total_saldo_subcuentas,
        'total_saldo_subcuentas_vinculadas': total_saldo_subcuentas_vinculadas,
        'total_saldo_subcuentas_independientes': total_saldo_subcuentas_independientes,
        'transferencias_recientes': transferencias_recientes,
    })


@login_required
@fast_access_pin_verified
def crear_subcuenta(request, cuenta_id=None):
    """Vista para crear una nueva subcuenta"""
    cuenta = None
    if cuenta_id:
        cuenta = get_object_or_404(Cuenta, id=cuenta_id, id_usuario=request.user)
    
    if request.method == 'POST':
        form = SubCuentaForm(request.POST, user=request.user)
        if form.is_valid():
            subcuenta = form.save(commit=False)
            
            tipo_subcuenta_base = form.cleaned_data['tipo_subcuenta_base']
            
            if tipo_subcuenta_base == 'negocio':
                # Subcuenta de negocio independiente
                subcuenta.propietario = request.user
                subcuenta.id_cuenta = None
                subcuenta.es_negocio = True
                tipo_msg = "de negocio independiente"
            else:
                # Subcuenta personal vinculada a cuenta principal
                if not cuenta:
                    # Si no hay cuenta especificada, usar la primera cuenta del usuario
                    cuenta = request.user.cuenta_set.first()
                    if not cuenta:
                        messages.error(request, 'Necesitas tener una cuenta principal para crear subcuentas personales.')
                        return redirect('cuentas:subcuentas_dashboard')
                
                subcuenta.id_cuenta = cuenta
                subcuenta.propietario = None
                subcuenta.es_negocio = False
                tipo_msg = "personal vinculada a cuenta principal"
            
            # Asegurar que la subcuenta se cree como activa por defecto
            subcuenta.activa = True
            subcuenta.save()
            
            messages.success(request, f'SubCuenta "{subcuenta.nombre}" creada exitosamente como {tipo_msg}.')
            return redirect('cuentas:subcuentas_dashboard')
    else:
        form = SubCuentaForm(user=request.user)
    
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


@login_required
@fast_access_pin_verified
def transferir_a_cuenta_principal(request, subcuenta_id):
    """Vista para transferir dinero desde una subcuenta independiente a la cuenta principal"""
    # Obtener la subcuenta (puede ser independiente o vinculada)
    subcuenta = get_object_or_404(
        SubCuenta, 
        id=subcuenta_id
    )
    
    # Verificar que el usuario tiene permisos sobre esta subcuenta
    if not (subcuenta.propietario == request.user or 
            (subcuenta.id_cuenta and subcuenta.id_cuenta.id_usuario == request.user)):
        messages.error(request, 'No tienes permisos para acceder a esta subcuenta.')
        return redirect('cuentas:subcuentas_dashboard')
    
    # Obtener la cuenta principal del usuario
    cuenta_principal = request.user.cuenta_set.first()
    if not cuenta_principal:
        messages.error(request, 'Necesitas tener una cuenta principal para recibir transferencias.')
        return redirect('cuentas:subcuentas_dashboard')
    
    if request.method == 'POST':
        form = TransferenciaCuentaPrincipalForm(request.POST, subcuenta=subcuenta)
        if form.is_valid():
            with transaction.atomic():
                transferencia = form.save(commit=False)
                transferencia.subcuenta = subcuenta
                transferencia.cuenta_destino = cuenta_principal
                transferencia.id_usuario = request.user
                
                monto = transferencia.monto
                
                # Realizar la transferencia
                if transferencia.tipo == 'deposito':
                    # Transferir de subcuenta a cuenta principal
                    subcuenta.saldo -= monto
                    cuenta_principal.saldo_cuenta += monto
                    mensaje = f'Transferencia de ${monto:.2f} realizada exitosamente desde "{subcuenta.nombre}" a tu cuenta principal.'
                else:
                    # Transferir de cuenta principal a subcuenta
                    if cuenta_principal.saldo_disponible() >= monto:
                        cuenta_principal.saldo_cuenta -= monto
                        subcuenta.saldo += monto
                        mensaje = f'Transferencia de ${monto:.2f} realizada exitosamente desde tu cuenta principal a "{subcuenta.nombre}".'
                    else:
                        messages.error(request, 'No hay saldo suficiente en la cuenta principal.')
                        return render(request, 'cuentas/transferir_cuenta_principal.html', {
                            'form': form,
                            'subcuenta': subcuenta,
                            'cuenta_principal': cuenta_principal
                        })
                
                subcuenta.save()
                cuenta_principal.save()
                transferencia.save()
                
                messages.success(request, mensaje)
                return redirect('cuentas:subcuentas_dashboard')
    else:
        form = TransferenciaCuentaPrincipalForm(subcuenta=subcuenta)
    
    return render(request, 'cuentas/transferir_cuenta_principal.html', {
        'form': form,
        'subcuenta': subcuenta,
        'cuenta_principal': cuenta_principal
    })


@login_required
@fast_access_pin_verified
def historial_transferencias_cuenta_principal(request):
    """Vista para ver el historial completo de transferencias del usuario"""
    from datetime import datetime
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    # Obtener todas las transferencias del usuario (tanto entre subcuentas como con cuenta principal)
    transferencias_subcuentas = TransferenciaSubCuenta.objects.filter(
        id_usuario=request.user
    ).select_related('subcuenta_origen', 'subcuenta_destino')
    
    transferencias_principal = TransferenciaCuentaPrincipal.objects.filter(
        id_usuario=request.user
    ).select_related('subcuenta', 'cuenta_destino')
    
    # Filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    subcuenta_id = request.GET.get('subcuenta')
    tipo_transferencia = request.GET.get('tipo')
    orden = request.GET.get('orden', '-fecha_transferencia')
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            transferencias_subcuentas = transferencias_subcuentas.filter(fecha_transferencia__date__gte=fecha_desde_dt)
            transferencias_principal = transferencias_principal.filter(fecha_transferencia__date__gte=fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            transferencias_subcuentas = transferencias_subcuentas.filter(fecha_transferencia__date__lte=fecha_hasta_dt)
            transferencias_principal = transferencias_principal.filter(fecha_transferencia__date__lte=fecha_hasta_dt)
        except ValueError:
            pass
    
    if subcuenta_id:
        try:
            subcuenta_id = int(subcuenta_id)
            # Filtrar transferencias entre subcuentas que involucren la subcuenta específica
            transferencias_subcuentas = transferencias_subcuentas.filter(
                Q(subcuenta_origen_id=subcuenta_id) | Q(subcuenta_destino_id=subcuenta_id)
            )
            # Filtrar transferencias con cuenta principal de la subcuenta específica
            transferencias_principal = transferencias_principal.filter(subcuenta_id=subcuenta_id)
        except ValueError:
            pass
    
    if tipo_transferencia:
        if tipo_transferencia == 'entre_subcuentas':
            transferencias_principal = TransferenciaCuentaPrincipal.objects.none()
        elif tipo_transferencia == 'con_principal':
            transferencias_subcuentas = TransferenciaSubCuenta.objects.none()
        elif tipo_transferencia in ['deposito', 'retiro']:
            transferencias_principal = transferencias_principal.filter(tipo=tipo_transferencia)
            transferencias_subcuentas = TransferenciaSubCuenta.objects.none()
    
    # Combinar y ordenar todas las transferencias
    todas_transferencias = []
    
    # Añadir transferencias entre subcuentas
    for trans in transferencias_subcuentas:
        todas_transferencias.append({
            'tipo': 'entre_subcuentas',
            'fecha': trans.fecha_transferencia,
            'monto': trans.monto,
            'descripcion': trans.descripcion or 'Transferencia entre subcuentas',
            'origen': trans.subcuenta_origen.nombre,
            'destino': trans.subcuenta_destino.nombre,
            'subcuenta_origen': trans.subcuenta_origen,
            'subcuenta_destino': trans.subcuenta_destino,
            'objeto': trans
        })
    
    # Añadir transferencias con cuenta principal
    for trans in transferencias_principal:
        direccion = "hacia cuenta principal" if trans.tipo == 'deposito' else "desde cuenta principal"
        todas_transferencias.append({
            'tipo': 'con_principal',
            'fecha': trans.fecha_transferencia,
            'monto': trans.monto,
            'descripcion': trans.descripcion or f'Transferencia {direccion}',
            'origen': trans.subcuenta.nombre if trans.tipo == 'deposito' else trans.cuenta_destino.nombre,
            'destino': trans.cuenta_destino.nombre if trans.tipo == 'deposito' else trans.subcuenta.nombre,
            'subcuenta': trans.subcuenta,
            'cuenta': trans.cuenta_destino,
            'tipo_transferencia': trans.tipo,
            'objeto': trans
        })
    
    # Ordenamiento
    reverse_order = orden.startswith('-')
    orden_campo = orden.lstrip('-')
    
    if orden_campo == 'fecha_transferencia':
        todas_transferencias.sort(key=lambda x: x['fecha'], reverse=reverse_order)
    elif orden_campo == 'monto':
        todas_transferencias.sort(key=lambda x: x['monto'], reverse=reverse_order)
    else:
        todas_transferencias.sort(key=lambda x: x['fecha'], reverse=True)
    
    # Estadísticas
    total_transferencias = len(todas_transferencias)
    monto_total = sum(trans['monto'] for trans in todas_transferencias)
    
    # Paginación manual
    paginator = Paginator(todas_transferencias, 20)
    page_number = request.GET.get('page')
    transferencias_paginadas = paginator.get_page(page_number)
    
    # Obtener todas las subcuentas para el filtro
    todas_subcuentas = SubCuenta.objects.filter(
        Q(propietario=request.user) | Q(id_cuenta__id_usuario=request.user)
    )
    
    return render(request, 'cuentas/historial_transferencias_cuenta_principal.html', {
        'transferencias': transferencias_paginadas,
        'total_transferencias': total_transferencias,
        'monto_total': monto_total,
        'todas_subcuentas': todas_subcuentas,
        'is_paginated': transferencias_paginadas.has_other_pages(),
        'page_obj': transferencias_paginadas,
    })