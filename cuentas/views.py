from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import json
import base64
from PIL import Image
import io
from decimal import Decimal
from usuarios.models import Usuario
from .models import Cuenta, SubCuenta, TransferenciaSubCuenta, TransferenciaCuentaPrincipal
from gestion_financiera_basica.models import Movimiento
from .forms import SubCuentaForm, TransferenciaSubCuentaForm, DepositoSubCuentaForm, RetiroSubCuentaForm, TransferenciaCuentaPrincipalForm
from core.decorators import fast_access_pin_verified
from alertas_notificaciones.models import Notificacion, TipoNotificacion
from django.db.models import Q, Sum
from django.urls import reverse
from usuarios.models import Usuario
from .models import Cuenta, SubCuenta, TransferenciaSubCuenta, TransferenciaCuentaPrincipal
from .forms import SubCuentaForm, TransferenciaSubCuentaForm, DepositoSubCuentaForm, RetiroSubCuentaForm, TransferenciaCuentaPrincipalForm
from core.decorators import fast_access_pin_verified

import base64
from PIL import Image
import io
import json

""" Views App CUENTAS """

# Función de detección automática eliminada - ahora el usuario selecciona manualmente

@login_required
@fast_access_pin_verified
def profile(request):
    user_id = request.user.id

    if request.method == "POST":
        action = request.POST.get("action")
        usuario = Usuario.objects.get(id=user_id)
        
        # Cambio de foto de perfil
        if action == "change_photo":
            imagen_perfil = request.FILES.get("imagen_perfil")
            if imagen_perfil:
                try:
                    # Validar que sea una imagen
                    imagen_bytes = imagen_perfil.read()
                    Image.open(io.BytesIO(imagen_bytes))  # Validar formato
                    
                    usuario.imagen_perfil = imagen_bytes
                    usuario.save()
                    messages.success(request, "✅ Foto de perfil actualizada correctamente.")
                except Exception as e:
                    messages.error(request, "❌ Error al procesar la imagen. Asegúrate de subir un archivo de imagen válido.")
            else:
                messages.error(request, "❌ No se seleccionó ninguna imagen.")
            return redirect("cuentas:profile")
        
        # Actualización de perfil general
        elif action == "update_profile":
            nombres = request.POST.get("nombres", "").strip()
            apellido_paterno = request.POST.get("apellido_paterno", "").strip()
            apellido_materno = request.POST.get("apellido_materno", "").strip()
            pais = request.POST.get("pais", "").strip()
            
            if nombres and apellido_paterno and pais:
                usuario.nombres = nombres
                usuario.apellido_paterno = apellido_paterno
                usuario.apellido_materno = apellido_materno
                usuario.pais = pais
                usuario.save()
                messages.success(request, "✅ Información personal actualizada correctamente.")
            else:
                messages.error(request, "❌ Los campos Nombres, Apellido Paterno y País son obligatorios.")
            return redirect("cuentas:profile")
        
        # Actualización de información de contacto
        elif action == "update_contact":
            email = request.POST.get("email", "").strip()
            telefono = request.POST.get("telefono", "").strip()
            
            if email:
                # Verificar que el email no esté siendo usado por otro usuario
                if Usuario.objects.filter(correo=email).exclude(id=usuario.id).exists():
                    messages.error(request, "❌ Este correo electrónico ya está siendo usado por otro usuario.")
                else:
                    usuario.correo = email
                    if telefono:
                        usuario.telefono = telefono
                    usuario.save()
                    messages.success(request, "✅ Información de contacto actualizada correctamente.")
            else:
                messages.error(request, "❌ El correo electrónico es obligatorio.")
            return redirect("cuentas:profile")
        
        # Cambio de contraseña
        elif action == "change_password":
            actual_password = request.POST.get("actual_password", "").strip()
            new_password = request.POST.get("new_password", "").strip()
            confirm_password = request.POST.get("confirm_password", "").strip()
            
            if not all([actual_password, new_password, confirm_password]):
                messages.error(request, "❌ Todos los campos de contraseña son obligatorios.")
                return redirect(reverse("cuentas:profile") + "?tab=security")
            
            # Verificar contraseña actual
            if not usuario.check_password(actual_password):
                messages.error(request, "❌ La contraseña actual es incorrecta.")
                return redirect(reverse("cuentas:profile") + "?tab=security")
            
            # Verificar que las nuevas contraseñas coincidan
            if new_password != confirm_password:
                messages.error(request, "❌ Las nuevas contraseñas no coinciden.")
                return redirect(reverse("cuentas:profile") + "?tab=security")
            
            # Verificar longitud mínima
            if len(new_password) < 8:
                messages.error(request, "❌ La nueva contraseña debe tener al menos 8 caracteres.")
                return redirect(reverse("cuentas:profile") + "?tab=security")
            
            # Verificar que la nueva contraseña sea diferente
            if actual_password == new_password:
                messages.warning(request, "⚠️ La nueva contraseña debe ser diferente a la actual.")
                return redirect(reverse("cuentas:profile") + "?tab=security")
            
            # Actualizar contraseña
            usuario.set_password(new_password)
            usuario.save()
            
            # Mantener la sesión del usuario después del cambio de contraseña
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, usuario)
            
            messages.success(request, "✅ Contraseña actualizada correctamente.")
            return redirect(reverse("cuentas:profile") + "?tab=security")
        
        # Cambio de PIN
        elif action == "change_pin":
            current_pin = request.POST.get("actual_pin", "").strip()
            new_pin = request.POST.get("new_pin", "").strip()
            confirm_pin = request.POST.get("confirm_pin", "").strip()
            
            if not all([current_pin, new_pin, confirm_pin]):
                messages.error(request, "❌ Todos los campos de PIN son obligatorios.")
                return redirect(reverse("cuentas:profile") + "?tab=security")
            
            # Verificar que todos sean números
            if not all(pin.isdigit() for pin in [current_pin, new_pin, confirm_pin]):
                messages.error(request, "❌ Los PINs solo pueden contener números.")
                return redirect(reverse("cuentas:profile") + "?tab=security")
            
            # Verificar PIN actual
            if str(usuario.pin_acceso_rapido) != current_pin:
                messages.error(request, "❌ El PIN actual es incorrecto.")
                return redirect(reverse("cuentas:profile") + "?tab=security")
            
            # Verificar que los nuevos PINs coincidan
            if new_pin != confirm_pin:
                messages.error(request, "❌ Los nuevos PINs no coinciden.")
                return redirect(reverse("cuentas:profile") + "?tab=security")
            
            # Verificar que el nuevo PIN sea diferente
            if current_pin == new_pin:
                messages.warning(request, "⚠️ El nuevo PIN debe ser diferente al actual.")
                return redirect(reverse("cuentas:profile") + "?tab=security")
            
            # Verificar que el PIN no esté siendo usado por otro usuario
            if Usuario.objects.filter(pin_acceso_rapido=new_pin).exclude(id=usuario.id).exists():
                messages.error(request, "❌ Este PIN ya está siendo usado. Por favor, elige uno diferente.")
                return redirect(reverse("cuentas:profile") + "?tab=security")
            
            # Actualizar PIN
            usuario.pin_acceso_rapido = new_pin
            usuario.save()
            messages.success(request, "✅ PIN de seguridad actualizado correctamente.")
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
    return render(request, "cuentas/profile_modern.html", {
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
    
    # Obtener cuenta principal para el modal
    cuenta_principal = cuentas.first() if cuentas.exists() else None
    
    # Calcular el balance total real (igual al dashboard principal)
    user_id = request.user.id
    total_ingresos = Movimiento.objects.filter(id_cuenta__id_usuario=user_id, tipo="ingreso").aggregate(total=Sum('monto'))['total'] or 0
    total_egresos = Movimiento.objects.filter(id_cuenta__id_usuario=user_id, tipo="egreso").aggregate(total=Sum('monto'))['total'] or 0
    saldo_inicial_cuentas = Cuenta.objects.filter(id_usuario=user_id).aggregate(total=Sum('saldo_cuenta'))['total'] or 0
    total_balance = float(saldo_inicial_cuentas) + float(total_ingresos) - float(total_egresos)
    
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
        'cuenta_principal': cuenta_principal,
        'total_balance': total_balance,
    })


@login_required
@fast_access_pin_verified
def crear_subcuenta(request, cuenta_id=None):
    """Vista para crear una nueva subcuenta"""
    cuenta_principal = None
    
    # Obtener la cuenta principal del usuario
    try:
        cuenta_principal = Cuenta.objects.get(id_usuario=request.user)
    except Cuenta.DoesNotExist:
        messages.error(request, 'Necesitas tener una cuenta principal para crear subcuentas.')
        return redirect('core:dashboard')
    
    # Contar subcuentas existentes
    subcuentas_count = SubCuenta.objects.filter(
        Q(id_cuenta=cuenta_principal) | Q(propietario=request.user)
    ).count()
    
    if request.method == 'POST':
        form = SubCuentaForm(request.POST, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                subcuenta = form.save(commit=False)
                
                # Obtener el tipo de subcuenta del POST
                tipo_subcuenta = request.POST.get('tipo_subcuenta', 'personal')
                
                if tipo_subcuenta == 'business':
                    # Subcuenta de negocio - COMPLETAMENTE INDEPENDIENTE
                    subcuenta.propietario = request.user
                    subcuenta.id_cuenta = None  # No vinculada a cuenta principal
                    subcuenta.es_negocio = True
                    subcuenta.saldo = 0  # Empieza con $0 - es independiente
                    
                    tipo_msg = "de negocio independiente (empieza con $0)"
                else:
                    # Subcuenta personal - VINCULADA A CUENTA PRINCIPAL
                    subcuenta.id_cuenta = cuenta_principal  # Vinculada a cuenta principal
                    subcuenta.propietario = None
                    subcuenta.es_negocio = False
                    subcuenta.saldo = 0  # Las subcuentas personales NO tienen saldo propio
                    tipo_msg = "personal (vinculada a cuenta principal)"
                
                # Asegurar que la subcuenta se cree como activa por defecto
                subcuenta.activa = True
                subcuenta.save()
                
                messages.success(request, f'Subcuenta "{subcuenta.nombre}" creada exitosamente como {tipo_msg}.')
                return redirect('cuentas:subcuentas_dashboard')
    else:
        form = SubCuentaForm(user=request.user)
    
    return render(request, 'cuentas/crear_subcuenta.html', {
        'form': form,
        'cuenta_principal': cuenta_principal,
        'subcuentas_count': subcuentas_count
    })


@login_required
@fast_access_pin_verified
def editar_subcuenta(request, subcuenta_id):
    """Vista para editar una subcuenta existente"""
    # Buscar subcuenta que pertenezca al usuario (ya sea por cuenta principal o propietario directo)
    subcuenta = get_object_or_404(
        SubCuenta, 
        Q(id=subcuenta_id) & (Q(id_cuenta__id_usuario=request.user) | Q(propietario=request.user))
    )
    
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
    subcuenta = get_object_or_404(
        SubCuenta, 
        Q(id=subcuenta_id) & (Q(id_cuenta__id_usuario=request.user) | Q(propietario=request.user))
    )
    
    if request.method == 'POST':
        # Si la subcuenta tiene saldo, transferirlo de vuelta a la cuenta principal
        if subcuenta.saldo > 0:
            # Solo transferir si es una subcuenta vinculada (personal)
            if subcuenta.id_cuenta:
                with transaction.atomic():
                    subcuenta.id_cuenta.saldo_cuenta += subcuenta.saldo
                    subcuenta.id_cuenta.save()
                    subcuenta.saldo = 0
                    subcuenta.activa = False
                    subcuenta.save()
                    
                messages.success(request, f'SubCuenta "{subcuenta.nombre}" eliminada y su saldo (${subcuenta.saldo:.2f}) transferido a la cuenta principal.')
            else:
                # Para subcuentas independientes, solo desactivar (no transferir)
                subcuenta.activa = False
                subcuenta.save()
                messages.warning(request, f'SubCuenta de negocio "{subcuenta.nombre}" eliminada. El saldo (${subcuenta.saldo:.2f}) se mantiene registrado.')
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


@login_required
@fast_access_pin_verified
def transferir_a_cuenta_principal_ajax(request):
    """Vista AJAX para transferir dinero desde una subcuenta independiente a la cuenta principal"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        subcuenta_id = request.POST.get('subcuenta_id')
        monto = Decimal(str(request.POST.get('monto', '0')))
        descripcion = request.POST.get('descripcion', '')
        
        if monto <= Decimal('0'):
            return JsonResponse({'success': False, 'error': 'El monto debe ser mayor a 0'})
        
        # Obtener la subcuenta
        subcuenta = get_object_or_404(SubCuenta, id=subcuenta_id)
        
        # Verificar permisos
        if not (subcuenta.propietario == request.user or 
                (subcuenta.id_cuenta and subcuenta.id_cuenta.id_usuario == request.user)):
            return JsonResponse({'success': False, 'error': 'No tienes permisos sobre esta subcuenta'})
        
        # Verificar saldo suficiente
        if subcuenta.saldo < monto:
            return JsonResponse({'success': False, 'error': 'Saldo insuficiente en la subcuenta'})
        
        # Obtener cuenta principal
        cuenta_principal = request.user.cuenta_set.first()
        if not cuenta_principal:
            return JsonResponse({'success': False, 'error': 'No tienes una cuenta principal'})
        
        # Realizar la transferencia
        with transaction.atomic():
            subcuenta.saldo -= monto
            cuenta_principal.saldo_cuenta += monto
            
            # Crear registro de transferencia
            transferencia = TransferenciaCuentaPrincipal.objects.create(
                subcuenta=subcuenta,
                cuenta_destino=cuenta_principal,
                id_usuario=request.user,
                monto=monto,
                tipo='deposito',
                descripcion=descripcion or f'Transferencia desde {subcuenta.nombre}'
            )
            
            subcuenta.save()
            cuenta_principal.save()
            
            # Crear notificación persistente
            crear_notificacion_movimiento(
                usuario=request.user,
                titulo=f"🏦 Transferencia a cuenta principal",
                mensaje=f"Se transfirió ${monto:.2f} desde '{subcuenta.nombre}' a tu cuenta principal. {descripcion}".strip(),
                categoria='Transferencias',
                datos_adicionales={
                    'tipo_movimiento': 'transferencia_a_principal',
                    'subcuenta_id': subcuenta.id,
                    'subcuenta_nombre': subcuenta.nombre,
                    'monto': float(monto),
                    'saldo_subcuenta_restante': float(subcuenta.saldo),
                    'saldo_principal_resultante': float(cuenta_principal.saldo_cuenta)
                }
            )
        
        return JsonResponse({
            'success': True, 
            'message': f'Transferencia de ${monto:.2f} realizada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@fast_access_pin_verified
def depositar_subcuenta_ajax(request):
    """Vista AJAX para depositar dinero en una subcuenta"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        subcuenta_id = request.POST.get('subcuenta_id')
        monto = Decimal(str(request.POST.get('monto', '0')))
        descripcion = request.POST.get('descripcion', '')
        tipo_deposito = request.POST.get('tipo_deposito', 'personal')
        
        print(f"DEBUG: subcuenta_id={subcuenta_id}, monto={monto}, tipo_deposito={tipo_deposito}")
        
        if monto <= Decimal('0'):
            return JsonResponse({'success': False, 'error': 'El monto debe ser mayor a 0'})
        
        # Obtener la subcuenta
        subcuenta = get_object_or_404(SubCuenta, id=subcuenta_id)
        print(f"DEBUG: Subcuenta encontrada: {subcuenta.nombre}, es_negocio={subcuenta.es_negocio}, id_cuenta={subcuenta.id_cuenta}")
        
        # Verificar permisos
        if not (subcuenta.propietario == request.user or 
                (subcuenta.id_cuenta and subcuenta.id_cuenta.id_usuario == request.user)):
            return JsonResponse({'success': False, 'error': 'No tienes permisos sobre esta subcuenta'})
        
        # Determinar si es subcuenta de negocio o personal basado en la estructura
        es_subcuenta_negocio = subcuenta.es_negocio or (subcuenta.propietario and not subcuenta.id_cuenta)
        
        with transaction.atomic():
            if es_subcuenta_negocio:
                # Para subcuentas de negocio (independientes), simplemente agregar el dinero
                print(f"DEBUG: Agregando dinero a subcuenta de negocio independiente")
                subcuenta.saldo += monto
                subcuenta.save()
                print(f"DEBUG: Nuevo saldo subcuenta de negocio: {subcuenta.saldo}")
                
                # Crear notificación persistente
                crear_notificacion_movimiento(
                    usuario=request.user,
                    titulo=f"💼 Ingreso registrado en {subcuenta.nombre}",
                    mensaje=f"Se registró un ingreso de ${monto:.2f} en tu subcuenta de negocio '{subcuenta.nombre}'. {descripcion}".strip(),
                    categoria='Ingresos',
                    datos_adicionales={
                        'tipo_movimiento': 'deposito_negocio',
                        'subcuenta_id': subcuenta.id,
                        'subcuenta_nombre': subcuenta.nombre,
                        'monto': float(monto),
                        'saldo_resultante': float(subcuenta.saldo)
                    }
                )
                
            else:
                # Para subcuentas personales (vinculadas), transferir desde cuenta principal
                if not subcuenta.id_cuenta:
                    return JsonResponse({'success': False, 'error': 'Error en la configuración de la subcuenta'})
                
                cuenta_principal = subcuenta.id_cuenta
                saldo_disponible = cuenta_principal.saldo_disponible()
                print(f"DEBUG: Cuenta principal saldo_cuenta={cuenta_principal.saldo_cuenta}, saldo_disponible={saldo_disponible}")
                
                if saldo_disponible < monto:
                    return JsonResponse({'success': False, 'error': f'Saldo insuficiente en la cuenta principal. Disponible: ${saldo_disponible:.2f}'})
                
                # Realizar la transferencia interna
                cuenta_principal.saldo_cuenta -= monto
                subcuenta.saldo += monto
                cuenta_principal.save()
                subcuenta.save()
                print(f"DEBUG: Transferencia completada. Nuevo saldo subcuenta: {subcuenta.saldo}")
                
                # Crear notificación persistente
                crear_notificacion_movimiento(
                    usuario=request.user,
                    titulo=f"💰 Depósito en {subcuenta.nombre}",
                    mensaje=f"Se transfirió ${monto:.2f} desde tu cuenta principal a '{subcuenta.nombre}'. {descripcion}".strip(),
                    categoria='Transferencias',
                    datos_adicionales={
                        'tipo_movimiento': 'deposito_personal',
                        'subcuenta_id': subcuenta.id,
                        'subcuenta_nombre': subcuenta.nombre,
                        'monto': float(monto),
                        'saldo_subcuenta': float(subcuenta.saldo),
                        'saldo_principal_restante': float(cuenta_principal.saldo_cuenta)
                    }
                )
        
        tipo_operacion = "Ingreso registrado" if es_subcuenta_negocio else "Depósito realizado"
        return JsonResponse({
            'success': True, 
            'message': f'{tipo_operacion}: ${monto:.2f} en {subcuenta.nombre}'
        })
        
    except Exception as e:
        print(f"ERROR en depositar_subcuenta_ajax: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@fast_access_pin_verified
def transferir_subcuentas_ajax(request):
    """Vista AJAX para transferir dinero entre subcuentas"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        subcuenta_origen_id = request.POST.get('subcuenta_origen')
        subcuenta_destino_id = request.POST.get('subcuenta_destino')
        monto = Decimal(str(request.POST.get('monto', '0')))
        descripcion = request.POST.get('descripcion', '')
        
        if monto <= Decimal('0'):
            return JsonResponse({'success': False, 'error': 'El monto debe ser mayor a 0'})
        
        if subcuenta_origen_id == subcuenta_destino_id:
            return JsonResponse({'success': False, 'error': 'No puedes transferir a la misma subcuenta'})
        
        # Obtener subcuentas
        subcuenta_origen = get_object_or_404(SubCuenta, id=subcuenta_origen_id)
        subcuenta_destino = get_object_or_404(SubCuenta, id=subcuenta_destino_id)
        
        # Verificar permisos
        usuario = request.user
        if not ((subcuenta_origen.propietario == usuario or 
                (subcuenta_origen.id_cuenta and subcuenta_origen.id_cuenta.id_usuario == usuario)) and
               (subcuenta_destino.propietario == usuario or 
                (subcuenta_destino.id_cuenta and subcuenta_destino.id_cuenta.id_usuario == usuario))):
            return JsonResponse({'success': False, 'error': 'No tienes permisos sobre estas subcuentas'})
        
        # Verificar saldo suficiente
        if subcuenta_origen.saldo < monto:
            return JsonResponse({'success': False, 'error': 'Saldo insuficiente en la subcuenta origen'})
        
        # Realizar la transferencia
        with transaction.atomic():
            subcuenta_origen.saldo -= monto
            subcuenta_destino.saldo += monto
            
            # Crear registro de transferencia
            transferencia = TransferenciaSubCuenta.objects.create(
                subcuenta_origen=subcuenta_origen,
                subcuenta_destino=subcuenta_destino,
                id_usuario=usuario,
                monto=monto,
                descripcion=descripcion or f'Transferencia de {subcuenta_origen.nombre} a {subcuenta_destino.nombre}'
            )
            
            subcuenta_origen.save()
            subcuenta_destino.save()
            
            # Crear notificación persistente
            crear_notificacion_movimiento(
                usuario=request.user,
                titulo=f"🔄 Transferencia entre subcuentas",
                mensaje=f"Se transfirió ${monto:.2f} desde '{subcuenta_origen.nombre}' a '{subcuenta_destino.nombre}'. {descripcion}".strip(),
                categoria='Transferencias',
                datos_adicionales={
                    'tipo_movimiento': 'transferencia_entre_subcuentas',
                    'subcuenta_origen_id': subcuenta_origen.id,
                    'subcuenta_origen_nombre': subcuenta_origen.nombre,
                    'subcuenta_destino_id': subcuenta_destino.id,
                    'subcuenta_destino_nombre': subcuenta_destino.nombre,
                    'monto': float(monto),
                    'saldo_origen_restante': float(subcuenta_origen.saldo),
                    'saldo_destino_resultante': float(subcuenta_destino.saldo)
                }
            )
        
        return JsonResponse({
            'success': True, 
            'message': f'Transferencia de ${monto:.2f} realizada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def crear_notificacion_movimiento(usuario, titulo, mensaje, categoria='Transacciones', datos_adicionales=None):
    """Función auxiliar para crear notificaciones persistentes de movimientos financieros"""
    try:
        # Buscar o crear el tipo de notificación para transacciones
        tipo_notificacion, created = TipoNotificacion.objects.get_or_create(
            nombre='Movimiento Financiero',
            defaults={
                'categoria': 'info',
                'descripcion': 'Notificaciones sobre movimientos en cuentas y subcuentas',
                'icono': '💰',
                'color': '#10b981'
            }
        )
        
        # Crear la notificación
        notificacion = Notificacion.objects.create(
            usuario=usuario,
            tipo_notificacion=tipo_notificacion,
            titulo=titulo,
            mensaje=mensaje,
            categoria=categoria,
            modulo_origen='cuentas',
            datos_adicionales=datos_adicionales or {},
            estado='enviada',
            prioridad='media'
        )
        
        return notificacion
    except Exception as e:
        print(f"Error creando notificación: {e}")
        return None