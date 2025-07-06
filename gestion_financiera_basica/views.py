from django.shortcuts import render, redirect, get_object_or_404
from .forms import MovimientoForm, MetaAhorroForm, AporteMetaAhorroForm
from cuentas.models import Cuenta
from django.shortcuts import render
from django.db.models import Sum, Q
from cuentas.models import Cuenta
from .models import Movimiento, MetaAhorro, AporteMetaAhorro
from django.contrib.auth.decorators import login_required
from core.decorators import fast_access_pin_verified
from alertas_notificaciones.services import NotificationService
import random
from datetime import datetime, timedelta

def generar_consejos_dinamicos(goals, promedio_progreso, metas_completadas):
    """Genera consejos dinámicos basados en el progreso del usuario"""
    consejos = []
    
    # Consejos basados en el progreso general
    if promedio_progreso >= 80:
        consejos.append({
            "tipo": "felicitacion",
            "emoji": "🎉",
            "titulo": "¡Excelente Progreso!",
            "mensaje": f"Tienes un promedio de {promedio_progreso:.1f}% de progreso. ¡Estás muy cerca de alcanzar tus metas!",
            "accion": "Mantén el ritmo y considera crear una nueva meta desafiante.",
            "color": "from-green-400 to-emerald-500"
        })
    elif promedio_progreso >= 50:
        consejos.append({
            "tipo": "motivacion",
            "emoji": "💪",
            "titulo": "¡Vas por Buen Camino!",
            "mensaje": f"Con {promedio_progreso:.1f}% de progreso promedio, estás en el camino correcto.",
            "accion": "Considera aumentar tus aportes mensuales para acelerar el progreso.",
            "color": "from-blue-400 to-blue-500"
        })
    elif promedio_progreso > 0:
        consejos.append({
            "tipo": "aliento",
            "emoji": "🚀",
            "titulo": "¡Cada Peso Cuenta!",
            "mensaje": f"Has avanzado {promedio_progreso:.1f}%. Recuerda que los grandes logros empiezan con pasos pequeños.",
            "accion": "Establece aportes automáticos semanales o quincenales.",
            "color": "from-yellow-400 to-orange-500"
        })
    else:
        consejos.append({
            "tipo": "inicio",
            "emoji": "🌟",
            "titulo": "¡Comienza Hoy!",
            "mensaje": "El mejor momento para empezar a ahorrar fue ayer. El segundo mejor momento es ahora.",
            "accion": "Realiza tu primer aporte, aunque sea pequeño.",
            "color": "from-purple-400 to-pink-500"
        })
    
    # Consejos específicos basados en metas individuales
    if goals:
        # Meta más próxima a completarse
        meta_mas_cerca = max(goals, key=lambda x: x['porcentaje_num'])
        if meta_mas_cerca['porcentaje_num'] >= 90:
            consejos.append({
                "tipo": "casi_completa",
                "emoji": "🏁",
                "titulo": "¡Final de Meta a la Vista!",
                "mensaje": f"Tu meta '{meta_mas_cerca['nombre']}' está al {meta_mas_cerca['porcentaje_num']:.1f}%.",
                "accion": f"Solo faltan ${meta_mas_cerca['falta_por_ahorrar']:.2f} para completarla.",
                "color": "from-emerald-400 to-teal-500"
            })
        
        # Meta con menos progreso
        meta_menos_progreso = min(goals, key=lambda x: x['porcentaje_num'])
        if meta_menos_progreso['porcentaje_num'] < 25:
            consejos.append({
                "tipo": "atencion",
                "emoji": "⚡",
                "titulo": "Meta Necesita Atención",
                "mensaje": f"'{meta_menos_progreso['nombre']}' tiene solo {meta_menos_progreso['porcentaje_num']:.1f}% de progreso.",
                "accion": "Considera hacer un aporte especial o revisar si la meta es realista.",
                "color": "from-red-400 to-pink-500"
            })
    
    # Consejos de celebración por metas completadas
    if metas_completadas > 0:
        consejos.append({
            "tipo": "celebracion",
            "emoji": "🎊",
            "titulo": "¡Metas Completadas!",
            "mensaje": f"Has completado {metas_completadas} meta{'s' if metas_completadas > 1 else ''}. ¡Increíble!",
            "accion": "Celebra tu éxito y considera crear nuevas metas más ambiciosas.",
            "color": "from-violet-400 to-purple-500"
        })
    
    # Consejos motivacionales aleatorios
    consejos_motivacionales = [
        {
            "tipo": "motivacion",
            "emoji": "💎",
            "titulo": "Invierte en tu Futuro",
            "mensaje": "Cada peso ahorrado hoy es una inversión en la persona que serás mañana.",
            "accion": "Visualiza cómo te sentirás cuando alcances tus metas.",
            "color": "from-indigo-400 to-purple-500"
        },
        {
            "tipo": "habito",
            "emoji": "🔄",
            "titulo": "Crea el Hábito",
            "mensaje": "Ahorrar es como hacer ejercicio: la consistencia es más importante que la intensidad.",
            "accion": "Establece recordatorios semanales para revisar y aportar a tus metas.",
            "color": "from-cyan-400 to-blue-500"
        },
        {
            "tipo": "progreso",
            "emoji": "📈",
            "titulo": "Progreso vs Perfección",
            "mensaje": "No necesitas aportes perfectos, solo aportes consistentes.",
            "accion": "Incluso $10 semanales pueden hacer una gran diferencia.",
            "color": "from-green-400 to-cyan-500"
        }
    ]
    
    # Agregar un consejo motivacional aleatorio
    consejos.append(random.choice(consejos_motivacionales))
    
    return consejos

@login_required
@fast_access_pin_verified
def savings_goals(request):
    # Obtener metas de ahorro reales del usuario
    user_goals = MetaAhorro.objects.filter(id_usuario=request.user).order_by('-fecha_inicio')
    
    goals = []
    total_objetivo = 0
    total_ahorrado = 0
    metas_completadas = 0
    
    for meta in user_goals:
        # Usar los métodos del modelo para calcular el progreso
        monto_ahorrado = float(meta.monto_ahorrado())
        objetivo = float(meta.monto_objetivo)
        porcentaje = meta.porcentaje_progreso()
        
        total_objetivo += objetivo
        total_ahorrado += monto_ahorrado
        if meta.meta_alcanzada():
            metas_completadas += 1
        
        goals.append({
            'id': meta.id,
            'nombre': meta.nombre,
            'progreso': f"${monto_ahorrado:.2f} / ${objetivo:.2f}",
            'porcentaje': f"{porcentaje:.1f}%",
            'porcentaje_num': porcentaje,
            'fecha_limite': meta.fecha_limite.strftime("%B %d, %Y"),
            'descripcion': meta.descripcion,
            'meta_alcanzada': meta.meta_alcanzada(),
            'falta_por_ahorrar': float(meta.falta_por_ahorrar()),
            'objetivo': objetivo,
            'monto_ahorrado': monto_ahorrado
        })

    # Calcular estadísticas para consejos personalizados
    porcentaje_total = (float(total_ahorrado) / float(total_objetivo) * 100) if total_objetivo > 0 else 0
    promedio_progreso = sum([goal['porcentaje_num'] for goal in goals]) / len(goals) if goals else 0
    
    # Generar consejos dinámicos basados en el progreso
    tips_dinamicos = generar_consejos_dinamicos(goals, promedio_progreso, metas_completadas)
    
    # Consejos estáticos base
    tips_base = [
        ("📂", "Regla 50/30/20", "Destina 50% de ingresos a necesidades, 30% a gustos, y 20% a ahorros."),
        ("🌱", "Págrate Primero", "Transfiere dinero a ahorros tan pronto como recibas ingresos."),
        ("🎯", "Metas Específicas", "Define objetivos claros y fechas límite para tus ahorros."),
        ("📊", "Revisa Regularmente", "Monitorea tu progreso y ajusta tus estrategias si es necesario."),
    ]

    return render(request, "gestion_financiera_basica/savings_goals.html", {
        "goals": goals,
        "tips": tips_base,
        "tips_dinamicos": tips_dinamicos,
        "estadisticas": {
            "total_objetivo": float(total_objetivo),
            "total_ahorrado": float(total_ahorrado),
            "falta_ahorrar": float(total_objetivo - total_ahorrado),
            "porcentaje_total": porcentaje_total,
            "metas_completadas": metas_completadas,
            "total_metas": len(goals),
            "promedio_progreso": promedio_progreso
        }
    })

@login_required
@fast_access_pin_verified
def transactions(request):
    user_id = request.user.id
    filter_type = request.GET.get("filter", "all")
    search_query = request.GET.get("search", "").strip()
    sort_by = request.GET.get("sort", "newest")

    # Obtener transacciones reales de la base de datos
    transacciones = Movimiento.objects.filter(id_cuenta__id_usuario=user_id)

    # Aplicar filtros
    if filter_type == "income":
        transacciones = transacciones.filter(tipo="ingreso")
    elif filter_type == "expenses":
        transacciones = transacciones.filter(tipo="egreso")

    # Aplicar búsqueda
    if search_query:
        transacciones = transacciones.filter(
            Q(nombre__icontains=search_query) |
            Q(descripcion__icontains=search_query) |
            Q(id_cuenta__nombre__icontains=search_query)
        )

    # Aplicar ordenación
    if sort_by == "newest":
        transacciones = transacciones.order_by('-fecha_movimiento')
    elif sort_by == "oldest":
        transacciones = transacciones.order_by('fecha_movimiento')
    elif sort_by == "highest":
        transacciones = transacciones.order_by('-monto')
    elif sort_by == "lowest":
        transacciones = transacciones.order_by('monto')
    else:
        transacciones = transacciones.order_by('-fecha_movimiento')

    return render(request, "gestion_financiera_basica/transactions.html", {
        "transactions": transacciones,
        "filter_type": filter_type,
        "search_query": search_query,
        "sort_by": sort_by,
    })
    
@login_required
@fast_access_pin_verified
def agregar_movimiento(request):
    if request.method == 'POST':
        form = MovimientoForm(request.POST, user=request.user)
        
        if form.is_valid():
            # Guardar el movimiento en la base de datos sin commit
            movimiento = form.save(commit=False)
            
            # Asegurarse de que el usuario esté establecido
            movimiento.id_usuario = request.user
            
            tipo = movimiento.tipo  # 'ingreso' o 'egreso'
            monto = movimiento.monto
            id_cuenta = movimiento.id_cuenta  # Obtener la cuenta relacionada

            # Verificar si la cuenta existe
            try:
                cuenta = Cuenta.objects.get(id=id_cuenta.id)
            except Cuenta.DoesNotExist:
                form.add_error('id_cuenta', 'La cuenta seleccionada no existe.')
                return render(request, 'gestion_financiera_basica/add_transaction.html', {'form': form})

            # Si el tipo es "ingreso", aumentar el saldo
            if tipo == 'ingreso':
                cuenta.saldo_cuenta += monto  # Aumentar el saldo
            elif tipo == 'egreso':
                cuenta.saldo_cuenta -= monto  # Reducir el saldo
            
            # Verificar que el saldo no sea negativo (si es necesario)
            if cuenta.saldo_cuenta < 0 and tipo == 'egreso':
                form.add_error('monto', 'El saldo no puede ser negativo. Saldo actual: ${}'.format(cuenta.saldo_cuenta + monto))
                return render(request, 'gestion_financiera_basica/add_transaction.html', {'form': form})

            # Guardar la cuenta actualizada
            cuenta.save()

            # Ahora guardar el movimiento
            movimiento.save()
            
            # 🔔 NOTA: Las notificaciones se envían automáticamente vía señales en signals.py
            print(f"✅ Movimiento guardado: {movimiento.tipo} - ${movimiento.monto} - {movimiento.nombre}")

            # Redirigir a la vista de transacciones para ver el resultado
            return redirect('gestion_financiera_basica:transactions')
        else:
            # Si el formulario no es válido, renderizar con errores
            # El template mostrará los errores específicos de cada campo
            return render(request, 'gestion_financiera_basica/add_transaction.html', {'form': form})

    else:
        form = MovimientoForm(user=request.user)

    return render(request, 'gestion_financiera_basica/add_transaction.html', {'form': form})


@login_required
@fast_access_pin_verified
def agregar_meta_ahorro(request):
    if request.method == 'POST':
        form = MetaAhorroForm(request.POST, user=request.user)
        
        if form.is_valid():
            # Guardar la meta de ahorro en la base de datos sin commit
            meta_ahorro = form.save(commit=False)
            
            # Asegurarse de que el usuario esté establecido
            meta_ahorro.id_usuario = request.user
            
            # Verificar si la cuenta existe
            try:
                cuenta = Cuenta.objects.get(id=meta_ahorro.id_cuenta.id, id_usuario=request.user)
            except Cuenta.DoesNotExist:
                form.add_error('id_cuenta', 'La cuenta seleccionada no existe o no te pertenece.')
                return render(request, 'gestion_financiera_basica/add_savings_goal.html', {'form': form})

            # Guardar la meta de ahorro
            meta_ahorro.save()

            # Redirigir a la vista de metas de ahorro para ver el resultado
            return redirect('gestion_financiera_basica:savings_goals')
        else:
            # Si el formulario no es válido, renderizar con errores
            return render(request, 'gestion_financiera_basica/add_savings_goal.html', {'form': form})

    else:
        form = MetaAhorroForm(user=request.user)

    return render(request, 'gestion_financiera_basica/add_savings_goal.html', {'form': form})


@login_required
@fast_access_pin_verified
def aportar_meta_ahorro(request, meta_id):
    # Obtener la meta de ahorro
    meta = get_object_or_404(MetaAhorro, id=meta_id, id_usuario=request.user)
    
    if request.method == 'POST':
        form = AporteMetaAhorroForm(request.POST, meta_ahorro=meta)
        
        if form.is_valid():
            # Guardar el aporte sin commit
            aporte = form.save(commit=False)
            
            # Establecer la meta de ahorro y el usuario
            aporte.id_meta_ahorro = meta
            aporte.id_usuario = request.user
            
            # Guardar el aporte
            aporte.save()
            
            # Redirigir de vuelta a las metas de ahorro
            return redirect('gestion_financiera_basica:savings_goals')
        else:
            # Si el formulario no es válido, renderizar con errores
            return render(request, 'gestion_financiera_basica/add_fund_to_goal.html', {
                'form': form, 
                'meta': meta
            })
    else:
        form = AporteMetaAhorroForm(meta_ahorro=meta)
    
    return render(request, 'gestion_financiera_basica/add_fund_to_goal.html', {
        'form': form, 
        'meta': meta
    })


@login_required
@fast_access_pin_verified
def editar_meta_ahorro(request, meta_id):
    # Obtener la meta de ahorro
    meta = get_object_or_404(MetaAhorro, id=meta_id, id_usuario=request.user)
    
    if request.method == 'POST':
        form = MetaAhorroForm(request.POST, instance=meta, user=request.user)
        
        if form.is_valid():
            # Guardar la meta de ahorro editada
            meta_ahorro = form.save(commit=False)
            meta_ahorro.id_usuario = request.user
            meta_ahorro.save()
            
            # Redirigir de vuelta a las metas de ahorro
            return redirect('gestion_financiera_basica:savings_goals')
        else:
            # Si el formulario no es válido, renderizar con errores
            return render(request, 'gestion_financiera_basica/edit_savings_goal.html', {
                'form': form, 
                'meta': meta
            })
    else:
        form = MetaAhorroForm(instance=meta, user=request.user)
    
    return render(request, 'gestion_financiera_basica/edit_savings_goal.html', {
        'form': form, 
        'meta': meta
    })


@login_required
@fast_access_pin_verified
def detalle_meta_ahorro(request, meta_id):
    # Obtener la meta de ahorro
    meta = get_object_or_404(MetaAhorro, id=meta_id, id_usuario=request.user)
    
    # Obtener todos los aportes de esta meta
    aportes = AporteMetaAhorro.objects.filter(id_meta_ahorro=meta).order_by('-fecha_aporte')
    
    return render(request, 'gestion_financiera_basica/savings_goal_detail.html', {
        'meta': meta,
        'aportes': aportes
    })