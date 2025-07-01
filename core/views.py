from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from gestion_financiera_basica.models import Movimiento
from usuarios.models import Usuario
from cuentas.models import Cuenta

""" Views App CORE """
def Inicio(request):
    if(not request.session.get('pin_validado')):
        return render(request , 'core/index.html')
    if(not request.user.is_authenticated):
        return render(request , 'core/index.html')
    else:
        return redirect('core:dashboard')

@login_required
def dashboard(request):
    user_id = request.user.id

    simbolo_moneda = Usuario.objects.filter(id=user_id).values('id_moneda__simbolo').all()
    simbolo_moneda = simbolo_moneda.first()
    simbolo_moneda = simbolo_moneda["id_moneda__simbolo"]
    movimientos = Movimiento.objects.filter(id_usuario_id=user_id)

    total_ingresos = Movimiento.objects.filter(id_cuenta__id_usuario=user_id , tipo="ingreso").aggregate(total=Sum('monto'))['total']
    cantidad_registros_ingresos = Movimiento.objects.filter(id_usuario__id=user_id , tipo="ingreso").count()

    if(not total_ingresos):
        total_ingresos = 0

    total_egresos = Movimiento.objects.filter(id_cuenta__id_usuario=user_id , tipo="egreso").aggregate(total=Sum('monto'))['total']

    if(not total_egresos):
        total_egresos = 0

    if(total_ingresos == 0):
        porcentaje_de_ingresos_para_egresos = 0
    else:
        porcentaje_de_ingresos_para_egresos = (float(total_egresos) / float(total_ingresos)) * 100

    total_balance = float(total_ingresos) - float(total_egresos)

    tab = request.GET.get("tab", "overview")

    return render(request , 'core/dashboard.html' , {
        "tab": tab,
        "total_balance": total_balance,
        "total_ingresos": total_ingresos,
        "cantidad_ingresos": cantidad_registros_ingresos,

        "total_egresos": total_egresos,
        "porcentaje_de_ingresos_para_egresos": porcentaje_de_ingresos_para_egresos,

        "movimientos": movimientos,
        "simbolo_moneda": simbolo_moneda,
    })

@login_required
def logout_view(request):
    request.session.flush()
    return redirect('core:index')

