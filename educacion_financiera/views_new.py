from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from core.decorators import fast_access_pin_verified
from django.contrib.auth.decorators import login_required
from .models import CursoExterno, FavoritoCurso

""" Views App EDUCACION_FINANCIERA """
@login_required
@fast_access_pin_verified
def calculators(request):
    tab = request.GET.get("tab", "savings")  # default tab
    result = None

    if request.method == "POST":
        if tab == "savings":
            try:
                initial = float(request.POST.get("initial", 0))
                monthly = float(request.POST.get("monthly", 0))
                rate = float(request.POST.get("rate", 0)) / 100
                years = int(request.POST.get("years", 0))
                months = years * 12
                future_value = initial * (1 + rate/12) ** months + monthly * (((1 + rate/12) ** months - 1) / (rate/12))
                result = round(future_value, 2)
            except:
                result = "Error en los valores ingresados"
        
        elif tab == "loan":
            try:
                amount = float(request.POST.get("amount", 0))
                rate = float(request.POST.get("rate", 0)) / 100
                years = int(request.POST.get("years", 0))
                months = years * 12
                monthly_rate = rate / 12
                payment = amount * monthly_rate / (1 - (1 + monthly_rate) ** -months)
                result = round(payment, 2)
            except:
                result = "Error en los valores ingresados"

    return render(request, "educacion_financiera/calculators.html", {
        "tab": tab,
        "result": result
    })

@login_required
@fast_access_pin_verified
def courses(request):
    """Vista de lista de cursos externos"""
    cursos = CursoExterno.objects.filter(activo=True).order_by('orden', 'titulo')
    
    # Obtener favoritos del usuario
    favoritos_ids = FavoritoCurso.objects.filter(
        usuario=request.user
    ).values_list('curso_id', flat=True)
    
    # Preparar datos de cursos
    cursos_data = []
    for curso in cursos:
        cursos_data.append({
            'id': curso.id,
            'titulo': curso.titulo,
            'descripcion': curso.descripcion,
            'nivel': curso.get_nivel_display(),
            'plataforma': curso.get_plataforma_display(),
            'plataforma_icon': curso.plataforma_icon,
            'nivel_color': curso.nivel_color,
            'instructor': curso.instructor,
            'duracion': curso.duracion_estimada,
            'gratis': curso.gratis,
            'url_externa': curso.url_externa,
            'imagen_url': curso.imagen_url,
            'es_favorito': curso.id in favoritos_ids,
        })
    
    return render(request, "educacion_financiera/courses.html", {
        "courses": cursos_data
    })

@login_required
@fast_access_pin_verified
def toggle_favorito(request, curso_id):
    """Agregar/quitar curso de favoritos"""
    if request.method == 'POST':
        curso = get_object_or_404(CursoExterno, id=curso_id)
        favorito, created = FavoritoCurso.objects.get_or_create(
            usuario=request.user,
            curso=curso
        )
        
        if not created:
            favorito.delete()
            es_favorito = False
        else:
            es_favorito = True
            
        return JsonResponse({'es_favorito': es_favorito})
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
@fast_access_pin_verified
def tips(request):
    tab = request.GET.get("tab", "daily")

    tips_data = {
        "daily": [
            ("📘", "Regla 50/30/20", "Destina 50% de ingresos a necesidades, 30% a deseos y 20% a ahorros."),
            ("🌱", "Págate a ti primero", "Transfiere dinero a ahorros tan pronto como recibas ingresos."),
            ("📊", "Seguimiento de Gastos", "Rastrea todos tus gastos diarios para identificar patrones."),
            ("⏰", "Establecer Recordatorios", "Configura recordatorios para pagar facturas a tiempo."),
            ("🍽️", "Planificación de Menús", "Planifica tus comidas semanalmente para reducir desperdicio."),
            ("🛍️", "Compras Conscientes", "Espera 24h antes de compras no esenciales.")
        ],
        "savings": [
            ("💧", "Automatizar Ahorros", "Configura transferencias automáticas a tu cuenta de ahorros."),
            ("🛟", "Fondo de Emergencia", "Construye un fondo que cubra 3-6 meses de gastos básicos."),
            ("💪", "Desafío de No Gastar", "Realiza un día/fin de semana sin gastos mensuales.")
        ],
        "debt": [
            ("📉", "Método Avalancha", "Paga primero deudas con tasa de interés más alta."),
            ("💱", "Consolidación de Deudas", "Unifica deudas con intereses altos en una sola con menor tasa."),
            ("📝", "Negociación de Deudas", "Contacta acreedores para mejorar condiciones de pago.")
        ],
        "investment": [
            ("📈", "Diversificación", "Invierte en distintos activos para reducir riesgos."),
            ("⌛", "Inversión a Largo Plazo", "Evita decisiones impulsivas por volatilidad a corto plazo."),
            ("🎓", "Educación Continua", "Edúcate sobre estrategias y opciones de inversión.")
        ],
    }

    return render(request, "educacion_financiera/tips.html", {
        "tab": tab,
        "tips": tips_data.get(tab, [])
    })
