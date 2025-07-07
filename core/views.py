from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from gestion_financiera_basica.models import Movimiento
from usuarios.models import Usuario
from cuentas.models import Cuenta
from core.decorators import fast_access_pin_verified

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

    # Calcular saldo inicial de todas las cuentas del usuario
    saldo_inicial_cuentas = Cuenta.objects.filter(id_usuario=user_id).aggregate(total=Sum('saldo_cuenta'))['total']
    
    if(not saldo_inicial_cuentas):
        saldo_inicial_cuentas = 0

    if(total_ingresos == 0):
        porcentaje_de_ingresos_para_egresos = 0
    else:
        porcentaje_de_ingresos_para_egresos = (float(total_egresos) / float(total_ingresos)) * 100

    # Balance total = saldo inicial + ingresos - egresos
    total_balance = float(saldo_inicial_cuentas) + float(total_ingresos) - float(total_egresos)

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
        "saldo_inicial_cuentas": saldo_inicial_cuentas,
        "total_ingresos": total_ingresos,
        "cantidad_ingresos": cantidad_registros_ingresos,

        "total_egresos": total_egresos,
        "porcentaje_de_ingresos_para_egresos": porcentaje_de_ingresos_para_egresos,
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