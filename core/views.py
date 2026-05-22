from django.db.models import Sum, Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from gestion_financiera_basica.models import Movimiento
from usuarios.models import Usuario
from cuentas.models import Cuenta
from core.decorators import fast_access_pin_verified
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings

""" Views App CORE """
def Inicio(request):
    if(not request.user.is_authenticated):
        return render(request , 'core/index.html')
    else:
        # Solo verificar PIN si llegó por acceso rápido
        if(request.session.get('login_method') == 'pin' and not request.session.get('pin_acceso_rapido_validado')):
            return redirect('usuarios:acceso_rapido')
        return redirect('core:dashboard')

@login_required
@fast_access_pin_verified
def dashboard(request):
    # Verificar si el usuario necesita completar onboarding
    if not request.user.onboarding_completed:
        return redirect('usuarios:onboarding')
        
    user_id = request.user.id

    simbolo_moneda = Usuario.objects.filter(id=user_id).values('id_moneda__simbolo').all()
    simbolo_moneda = simbolo_moneda.first()
    simbolo_moneda = simbolo_moneda["id_moneda__simbolo"]
    movimientos = Movimiento.objects.filter(id_usuario_id=user_id)

    # Calcular ingresos de movimientos
    total_ingresos = Movimiento.objects.filter(id_cuenta__id_usuario=user_id , tipo="ingreso").aggregate(total=Sum('monto'))['total']
    cantidad_registros_ingresos = Movimiento.objects.filter(id_usuario__id=user_id , tipo="ingreso").count()

    if(not total_ingresos):
        total_ingresos = 0

    # Calcular egresos de movimientos
    total_egresos = Movimiento.objects.filter(id_cuenta__id_usuario=user_id , tipo="egreso").aggregate(total=Sum('monto'))['total']

    if(not total_egresos):
        total_egresos = 0

    # Calcular saldo actual de todas las cuentas del usuario
    # NOTA: saldo_cuenta ahora se actualiza automáticamente con cada ingreso/egreso
    # Por lo tanto, ya incluye el saldo inicial + todos los ingresos - todos los egresos
    saldo_inicial_cuentas = Cuenta.objects.filter(id_usuario=user_id).aggregate(total=Sum('saldo_cuenta'))['total']
    
    if(not saldo_inicial_cuentas):
        saldo_inicial_cuentas = 0

    if(total_ingresos == 0):
        porcentaje_de_ingresos_para_egresos = 0
    else:
        porcentaje_de_ingresos_para_egresos = (float(total_egresos) / float(total_ingresos)) * 100

    # Ahora saldo_cuenta ya incluye ingresos y egresos aplicados
    # El total_balance incluye el dinero en cuentas principales + dinero en subcuentas
    from cuentas.models import SubCuenta, TransferenciaCuentaPrincipal
    
    # Saldo en subcuentas del usuario
    saldo_subcuentas = SubCuenta.objects.filter(
        Q(id_cuenta__id_usuario=user_id) | Q(propietario_id=user_id),
        activa=True
    ).aggregate(total=Sum('saldo'))['total'] or 0
    
    # Calcular total transferido a subcuentas (dinero movido, no gastado)
    total_transferencias_subcuentas = TransferenciaCuentaPrincipal.objects.filter(
        cuenta_destino__id_usuario=user_id,
        tipo='retiro'  # Retiros de cuenta principal hacia subcuentas
    ).aggregate(total=Sum('monto'))['total'] or 0
    
    # Balance total = SOLO dinero disponible en cuentas principales
    # Este valor ya representa ingresos - egresos porque saldo_cuenta se actualiza con cada transacción
    total_balance = float(saldo_inicial_cuentas)
    
    # Patrimonio total = Balance disponible (ingresos - egresos)
    # El saldo_cuenta ya incluye todos los ingresos menos todos los egresos
    total_patrimonio = float(saldo_inicial_cuentas)
    
    # Para calcular el porcentaje de gastos sobre ingresos
    # Usar ingresos totales como base, no recursos históricos
    if(total_ingresos == 0):
        porcentaje_de_recursos_para_egresos = 0
        salud_financiera_score = 100  # Puntuación perfecta si no hay gastos
    else:
        porcentaje_de_recursos_para_egresos = (float(total_egresos) / float(total_ingresos)) * 100
        salud_financiera_score = max(0, 100 - int(porcentaje_de_recursos_para_egresos))  # Score dinámico

    # Datos para gráfico de gastos por categoría
    gastos_por_categoria = []
    if total_egresos > 0:
        # Obtener gastos agrupados por categoría
        gastos_por_cat = Movimiento.objects.filter(
            id_cuenta__id_usuario=user_id, 
            tipo="egreso"
        ).values('categoria').annotate(total=Sum('monto')).order_by('-total')
        
        # Convertir a lista para el gráfico con nombres y emojis
        for gasto in gastos_por_cat:
            categoria_key = gasto['categoria'] or 'otros'
            monto = float(gasto['total'])
            porcentaje = (monto / float(total_egresos)) * 100
            
            # Buscar el nombre con emoji para la categoría
            nombre_categoria = 'Otros'
            for cat_key, cat_display in Movimiento.CATEGORIAS_GASTOS:
                if cat_key == categoria_key:
                    nombre_categoria = cat_display
                    break
            
            gastos_por_categoria.append({
                'categoria': nombre_categoria,
                'monto': monto,
                'porcentaje': round(porcentaje, 1)
            })
    
    tab = request.GET.get("tab", "overview")

    return render(request , 'core/dashboard.html' , {
        "tab": tab,
        "total_balance": total_balance,
        "total_patrimonio": total_patrimonio,
        "saldo_inicial_cuentas": saldo_inicial_cuentas,
        "saldo_subcuentas": saldo_subcuentas,
        "total_transferencias_subcuentas": total_transferencias_subcuentas,
        "total_ingresos": total_ingresos,
        "cantidad_ingresos": cantidad_registros_ingresos,

        "total_egresos": total_egresos,
        "porcentaje_de_ingresos_para_egresos": porcentaje_de_ingresos_para_egresos,
        "porcentaje_de_recursos_para_egresos": porcentaje_de_recursos_para_egresos,
        "salud_financiera_score": salud_financiera_score,
        "gastos_por_categoria": gastos_por_categoria,

        "movimientos": movimientos,
        "simbolo_moneda": simbolo_moneda,
    })

@login_required
@fast_access_pin_verified
def logout_view(request):
    request.session.flush()
    return redirect('core:index')

@login_required
def temporary_logout(request):
    request.session["pin_acceso_rapido_validado"] = False
    return redirect("usuarios:acceso_rapido")

def privacy_policy(request):
    """Vista para la política de privacidad"""
    return render(request, 'core/privacy.html')

def terms_of_service(request):
    """Vista para los términos y condiciones"""
    return render(request, 'core/terms.html')

def help_center(request):
    """Vista para el centro de ayuda"""
    return render(request, 'core/help.html')

def contact_view(request):
    """Vista para la página de contacto"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        if name and email and subject and message:
            try:
                # Enviar email al equipo de soporte
                full_message = f"""
Nuevo mensaje de contacto desde FinGest:

Nombre: {name}
Email: {email}
Asunto: {subject}

Mensaje:
{message}

---
Este mensaje fue enviado desde el formulario de contacto de FinGest.
Responder directamente a: {email}
                """
                
                send_mail(
                    f'[FinGest] Contacto: {subject}',
                    full_message,
                    settings.DEFAULT_FROM_EMAIL,
                    ['contacto@fingest.com'],  # Email de destino
                    fail_silently=False,
                )
                
                messages.success(request, '¡Mensaje enviado correctamente! Te responderemos pronto.')
                return redirect('core:contact')
            except Exception as e:
                # Log del error para desarrollo
                print(f"Error enviando email: {e}")
                messages.error(request, 'Hubo un error al enviar el mensaje. Inténtalo de nuevo más tarde.')
        else:
            messages.error(request, 'Por favor, completa todos los campos obligatorios.')
    
    return render(request, 'core/contact.html')