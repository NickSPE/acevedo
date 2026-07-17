from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.urls import reverse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime
from decimal import Decimal

# Modelos
from usuarios.models import Usuario
from .models import Cuenta, SubCuenta, TransferenciaSubCuenta, TransferenciaCuentaPrincipal

# Forms
from .forms import SubCuentaForm, TransferenciaSubCuentaForm, DepositoSubCuentaForm, RetiroSubCuentaForm, TransferenciaCuentaPrincipalForm

# Decoradores
from core.decorators import fast_access_pin_verified

# Servicios y utilidades
from .services import (
    actualizar_perfil_usuario,
    actualizar_contacto_usuario,
    cambiar_password_usuario,
    cambiar_pin_usuario,
    procesar_transferencia_entre_subcuentas,
    procesar_deposito_subcuenta,
    procesar_transferencia_a_principal
)
from .utils import (
    obtener_estadisticas_subcuentas,
    obtener_cuentas_con_subcuentas,
    obtener_subcuentas_independientes,
    obtener_transferencias_recientes,
    obtener_balance_total,
    obtener_cuentas_usuario,
)
from .helpers import procesar_imagen_perfil

# Views App CUENTAS

# Función de detección automática eliminada - ahora el usuario selecciona manualmente

@login_required
@fast_access_pin_verified
def profile(request):
    usuario = Usuario.objects.get(id=request.user.id)
    if request.method == "POST":
        return _handle_profile_action(request, usuario)

    imagen_base64, formato_imagen = None, None
    try:
        from .helpers import procesar_imagen_perfil
        imagen_base64, formato_imagen = procesar_imagen_perfil(usuario, solo_leer=True)
    except ImportError:
        pass
    tab = request.GET.get("tab", "general")
    return render(request, "cuentas/profile_modern.html", {
        "tab": tab,
        "usuario": usuario,
        "imagen_base64": imagen_base64,
        "formato_imagen": formato_imagen,
    })


def _handle_profile_action(request, usuario):
    action = request.POST.get("action")
    handlers = {
        "change_photo": _handle_change_photo,
        "update_profile": _handle_update_profile,
    }
    handler = handlers.get(action)
    if handler:
        return handler(request, usuario)
    messages.error(request, "❌ Acción no válida.")
    return redirect("cuentas:profile")

def _handle_change_photo(request, usuario):
    imagen_perfil = request.FILES.get("imagen_perfil")
    success, msg = procesar_imagen_perfil(usuario, imagen_perfil)
    if success:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect("cuentas:profile")

def _handle_update_profile(request, usuario):
    nombres = request.POST.get("nombres", "").strip()
    apellido_paterno = request.POST.get("apellido_paterno", "").strip()
    apellido_materno = request.POST.get("apellido_materno", "").strip()
    pais = request.POST.get("pais", "").strip()

    if nombres and apellido_paterno and pais:
        actualizar_perfil_usuario(usuario, nombres, apellido_paterno, apellido_materno, pais)
        messages.success(request, "✅ Información personal actualizada correctamente.")
    else:
        messages.error(request, "❌ Los campos Nombres, Apellido Paterno y País son obligatorios.")
    return redirect("cuentas:profile")

@login_required
@fast_access_pin_verified
def settings(request):
    return render(request, "cuentas/settings.html")


# === VISTAS PARA SUBCUENTAS ===

@login_required
@fast_access_pin_verified
def subcuentas_dashboard(request):
    """Vista principal del dashboard de subcuentas"""
    # Obtener estadísticas
    stats = obtener_estadisticas_subcuentas(request.user)
    cuentas_con_subcuentas = obtener_cuentas_con_subcuentas(request.user)
    subcuentas_independientes = obtener_subcuentas_independientes(request.user)
    transferencias_recientes = obtener_transferencias_recientes(request.user)
    balance_total = obtener_balance_total(request.user)
    
    # Obtener cuenta principal
    cuenta_principal = obtener_cuentas_usuario(request.user).first()
    
    return render(request, 'cuentas/subcuentas_dashboard.html', {
        'cuentas_con_subcuentas': cuentas_con_subcuentas,
        'subcuentas_independientes_activas': subcuentas_independientes['activas'],
        'subcuentas_independientes_inactivas': subcuentas_independientes['inactivas'],
        'total_subcuentas': stats['total'],
        'total_subcuentas_vinculadas': stats['total_vinculadas'],
        'total_subcuentas_independientes': stats['total_independientes'],
        'total_subcuentas_inactivas': stats['total_inactivas'],
        'total_saldo_subcuentas': stats['saldo_total'],
        'total_saldo_subcuentas_vinculadas': stats['saldo_vinculadas'],
        'total_saldo_subcuentas_independientes': stats['saldo_independientes'],
        'transferencias_recientes': transferencias_recientes,
        'cuenta_principal': cuenta_principal,
        'total_balance': balance_total,
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
                
                # Obtener el tipo de subcuenta del cleaned_data seguro
                tipo_subcuenta = form.cleaned_data.get('tipo_subcuenta') or 'personal'
                
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
            
            # Si es una petición AJAX, devolver JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'SubCuenta "{subcuenta.nombre}" actualizada exitosamente.'
                })
            
            return redirect('cuentas:subcuentas_dashboard')
        else:
            # Si es AJAX y hay errores
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
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
    
    # Obtener subcuentas activas para el template (personales y de negocio)
    subcuentas_activas = SubCuenta.objects.filter(
        Q(id_cuenta__id_usuario=request.user) | Q(propietario=request.user),
        activa=True
    )
    
    return render(request, 'cuentas/transferir_subcuentas.html', {
        'form': form,
        'subcuentas': subcuentas_activas
    })


@login_required
@fast_access_pin_verified
def depositar_subcuenta(request, subcuenta_id):
    """Vista para depositar dinero a una subcuenta (personal o negocio)"""
    # Buscar subcuenta que pertenezca al usuario
    subcuenta = get_object_or_404(
        SubCuenta,
        Q(id=subcuenta_id) & (Q(id_cuenta__id_usuario=request.user) | Q(propietario=request.user))
    )
    
    # Obtener cuenta principal si es subcuenta personal
    cuenta = subcuenta.id_cuenta if subcuenta.id_cuenta else None
    es_negocio = not subcuenta.id_cuenta
    
    if request.method == 'POST':
        form = DepositoSubCuentaForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                monto = form.cleaned_data['monto']
                descripcion = form.cleaned_data['descripcion']
                
                if es_negocio:
                    # Para subcuentas de negocio, solo agregar el monto
                    subcuenta.saldo += monto
                    subcuenta.save()
                    messages.success(request, f'Depósito de ${monto:.2f} realizado exitosamente a "{subcuenta.nombre}".')
                    return redirect('cuentas:subcuentas_dashboard')
                else:
                    # Para subcuentas personales, transferir desde cuenta principal
                    if cuenta.saldo_disponible() >= monto:
                        # Restar de cuenta principal y agregar a subcuenta
                        cuenta.saldo_cuenta -= monto
                        subcuenta.saldo += monto
                        cuenta.save()
                        subcuenta.save()
                        
                        # Registrar la transferencia
                        TransferenciaCuentaPrincipal.objects.create(
                            subcuenta=subcuenta,
                            cuenta_destino=cuenta,
                            monto=monto,
                            tipo='retiro',  # Retiro de cuenta principal hacia subcuenta
                            descripcion=descripcion or f'Depósito a {subcuenta.nombre}',
                            id_usuario=request.user
                        )
                        
                        messages.success(request, f'Depósito de ${monto:.2f} realizado exitosamente a "{subcuenta.nombre}".')
                        return redirect('cuentas:subcuentas_dashboard')
                    else:
                        messages.error(request, 'No hay saldo suficiente en la cuenta principal.')
    else:
        form = DepositoSubCuentaForm()
    
    return render(request, 'cuentas/depositar_subcuenta.html', {
        'form': form,
        'subcuenta': subcuenta,
        'cuenta_principal': cuenta,
        'es_negocio': es_negocio
    })


@login_required
@fast_access_pin_verified
def retirar_subcuenta(request, subcuenta_id):
    """Vista para retirar dinero de una subcuenta (personal o negocio)"""
    # Buscar subcuenta que pertenezca al usuario
    subcuenta = get_object_or_404(
        SubCuenta,
        Q(id=subcuenta_id) & (Q(id_cuenta__id_usuario=request.user) | Q(propietario=request.user))
    )
    
    # Obtener cuenta principal si es subcuenta personal
    cuenta = subcuenta.id_cuenta if subcuenta.id_cuenta else None
    es_negocio = not subcuenta.id_cuenta
    
    if request.method == 'POST':
        form = RetiroSubCuentaForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                monto = form.cleaned_data['monto']
                descripcion = form.cleaned_data['descripcion']
                
                if es_negocio:
                    # Para subcuentas de negocio, solo restar el monto
                    subcuenta.saldo -= monto
                    subcuenta.save()
                    messages.success(request, f'Retiro de ${monto:.2f} realizado exitosamente desde "{subcuenta.nombre}".')
                    return redirect('cuentas:subcuentas_dashboard')
                else:
                    # Para subcuentas personales, transferir a cuenta principal
                    subcuenta.saldo -= monto
                    cuenta.saldo_cuenta += monto
                    subcuenta.save()
                    cuenta.save()
                    
                    # Registrar la transferencia
                    TransferenciaCuentaPrincipal.objects.create(
                        subcuenta=subcuenta,
                        cuenta_destino=cuenta,
                        monto=monto,
                        tipo='deposito',  # Depósito de subcuenta hacia cuenta principal
                        descripcion=descripcion or f'Retiro de {subcuenta.nombre}',
                        id_usuario=request.user
                    )
                    
                    messages.success(request, f'Retiro de ${monto:.2f} realizado exitosamente desde "{subcuenta.nombre}".')
                    return redirect('cuentas:subcuentas_dashboard')
    else:
        form = RetiroSubCuentaForm()
    
    return render(request, 'cuentas/retirar_subcuenta.html', {
        'form': form,
        'subcuenta': subcuenta,
        'cuenta_principal': cuenta,
        'es_negocio': es_negocio
    })


@login_required
@fast_access_pin_verified
def historial_transferencias(request):
    """Vista para ver el historial de transferencias"""
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
    
    # Contar depósitos y retiros (solo movimientos con cuenta principal)
    total_depositos = sum(1 for trans in todas_transferencias if trans.get('tipo_transferencia') == 'deposito')
    total_retiros = sum(1 for trans in todas_transferencias if trans.get('tipo_transferencia') == 'retiro')
    total_movimientos = total_transferencias  # Todos los movimientos incluyendo entre subcuentas
    
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
        'total_depositos': total_depositos,
        'total_retiros': total_retiros,
        'total_movimientos': total_movimientos,
        'todas_subcuentas': todas_subcuentas,
        'is_paginated': transferencias_paginadas.has_other_pages(),
        'page_obj': transferencias_paginadas,
    })


@login_required
@fast_access_pin_verified
def transferir_a_cuenta_principal_ajax(request):
    """Vista AJAX para transferir dinero desde una subcuenta a la cuenta principal"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    subcuenta_id = request.POST.get('subcuenta_id')
    monto = Decimal(str(request.POST.get('monto', '0')))
    
    # Validaciones
    if monto <= Decimal('0'):
        return JsonResponse({'success': False, 'error': 'El monto debe ser mayor a 0'})
    
    subcuenta = get_object_or_404(SubCuenta, id=subcuenta_id)
    
    if not validar_permisos_subcuenta(request.user, subcuenta):
        return JsonResponse({'success': False, 'error': 'No tienes permisos sobre esta subcuenta'})
    
    cuenta_principal = request.user.cuenta_set.first()
    if not cuenta_principal:
        return JsonResponse({'success': False, 'error': 'No tienes una cuenta principal'})
    
    # Procesar
    success, message = procesar_transferencia_a_principal(
        subcuenta,
        cuenta_principal,
        monto,
        request.user,
        tipo='deposito',
        descripcion=request.POST.get('descripcion', '')
    )
    
    if success:
        crear_notificacion_movimiento(
            usuario=request.user,
            titulo="🏦 Transferencia a cuenta principal",
            mensaje=message,
            datos_adicionales={
                'tipo_movimiento': 'transferencia_a_principal',
                'subcuenta_id': subcuenta.id,
                'monto': float(monto)
            }
        )
        return JsonResponse({'success': True, 'message': message})
    
    return JsonResponse({'success': False, 'error': message})


@login_required
@fast_access_pin_verified
def depositar_subcuenta_ajax(request):
    """Vista AJAX para depositar dinero en una subcuenta"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    subcuenta_id = request.POST.get('subcuenta_id')
    monto = Decimal(str(request.POST.get('monto', '0')))
    
    # Validaciones previas
    if monto <= Decimal('0'):
        return JsonResponse({'success': False, 'error': 'El monto debe ser mayor a 0'})
    
    subcuenta = get_object_or_404(SubCuenta, id=subcuenta_id)
    
    if not validar_permisos_subcuenta(request.user, subcuenta):
        return JsonResponse({'success': False, 'error': 'No tienes permisos sobre esta subcuenta'})
    
    # Procesar
    success, message = procesar_deposito_subcuenta(
        subcuenta,
        monto,
        request.user,
        request.POST.get('descripcion', '')
    )
    
    if success:
        es_negocio = es_subcuenta_negocio(subcuenta)
        titulo = f"💼 Ingreso registrado en {subcuenta.nombre}" if es_negocio else f"💰 Depósito en {subcuenta.nombre}"
        
        crear_notificacion_movimiento(
            usuario=request.user,
            titulo=titulo,
            mensaje=message,
            datos_adicionales={
                'tipo_movimiento': 'deposito_negocio' if es_negocio else 'deposito_personal',
                'subcuenta_id': subcuenta.id,
                'monto': float(monto),
                'saldo_resultante': float(subcuenta.saldo)
            }
        )
        return JsonResponse({'success': True, 'message': message})
    
    return JsonResponse({'success': False, 'error': message})



@login_required
@fast_access_pin_verified
def transferir_subcuentas_ajax(request):
    """Vista AJAX para transferir dinero entre subcuentas"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    subcuenta_origen_id = request.POST.get('subcuenta_origen')
    subcuenta_destino_id = request.POST.get('subcuenta_destino')
    monto = Decimal(str(request.POST.get('monto', '0')))
    
    # Validaciones
    if monto <= Decimal('0'):
        return JsonResponse({'success': False, 'error': 'El monto debe ser mayor a 0'})
    
    if subcuenta_origen_id == subcuenta_destino_id:
        return JsonResponse({'success': False, 'error': 'No puedes transferir a la misma subcuenta'})
    
    subcuenta_origen = get_object_or_404(SubCuenta, id=subcuenta_origen_id)
    subcuenta_destino = get_object_or_404(SubCuenta, id=subcuenta_destino_id)
    
    if not validar_permisos_ambas_subcuentas(request.user, subcuenta_origen, subcuenta_destino):
        return JsonResponse({'success': False, 'error': 'No tienes permisos sobre estas subcuentas'})
    
    # Procesar
    success, message = procesar_transferencia_entre_subcuentas(
        subcuenta_origen,
        subcuenta_destino,
        monto,
        request.user,
        request.POST.get('descripcion', '')
    )
    
    if success:
        crear_notificacion_movimiento(
            usuario=request.user,
            titulo="🔄 Transferencia entre subcuentas",
            mensaje=message,
            datos_adicionales={
                'tipo_movimiento': 'transferencia_entre_subcuentas',
                'subcuenta_origen_id': subcuenta_origen.id,
                'subcuenta_destino_id': subcuenta_destino.id,
                'monto': float(monto)
            }
        )
        return JsonResponse({'success': True, 'message': message})
    
    return JsonResponse({'success': False, 'error': message})