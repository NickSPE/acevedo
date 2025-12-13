from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from core.decorators import fast_access_pin_verified
from django.contrib.auth.decorators import login_required
from .models import CursoExterno, FavoritoCurso
import json
import google.generativeai as genai

""" Views App EDUCACION_FINANCIERA """


@login_required
@fast_access_pin_verified
def calculators(request):
    tab = request.GET.get("tab", "savings")  # default tab
    result = None
    ai_explanation = None

    if request.method == "POST":
        if tab == "savings":
            try:
                initial = float(request.POST.get("initial", 0))
                monthly = float(request.POST.get("monthly", 0))
                rate = float(request.POST.get("rate", 0)) / 100
                years = int(request.POST.get("years", 0))
                months = years * 12
                
                # Cálculo con interés compuesto
                if rate > 0:
                    future_value = initial * (1 + rate/12) ** months + monthly * (((1 + rate/12) ** months - 1) / (rate/12))
                else:
                    future_value = initial + (monthly * months)
                
                total_contributed = initial + (monthly * months)
                interest_earned = future_value - total_contributed
                
                result = {
                    'future_value': round(future_value, 2),
                    'total_contributed': round(total_contributed, 2),
                    'interest_earned': round(interest_earned, 2),
                    'type': 'savings'
                }
                
                # Generar explicación con IA
                ai_explanation = generate_ai_explanation(result, tab)
                
            except:
                result = {"error": "Error en los valores ingresados"}
        
        elif tab == "loan":
            try:
                amount = float(request.POST.get("amount", 0))
                rate = float(request.POST.get("rate", 0)) / 100
                years = int(request.POST.get("years", 0))
                months = years * 12
                
                if rate > 0:
                    monthly_rate = rate / 12
                    monthly_payment = amount * monthly_rate / (1 - (1 + monthly_rate) ** -months)
                else:
                    monthly_payment = amount / months
                
                total_payment = monthly_payment * months
                total_interest = total_payment - amount
                
                result = {
                    'monthly_payment': round(monthly_payment, 2),
                    'total_payment': round(total_payment, 2),
                    'total_interest': round(total_interest, 2),
                    'loan_amount': amount,
                    'type': 'loan'
                }
                
                # Generar explicación con IA
                ai_explanation = generate_ai_explanation(result, tab)
                
            except:
                result = {"error": "Error en los valores ingresados"}
        
        elif tab == "budget":
            try:
                income = float(request.POST.get("income", 0))
                needs = float(request.POST.get("needs", 0))
                wants = float(request.POST.get("wants", 0))
                savings = float(request.POST.get("savings", 0))
                
                total_expenses = needs + wants + savings
                remaining = income - total_expenses
                
                # Regla 50/30/20
                recommended_needs = income * 0.5
                recommended_wants = income * 0.3
                recommended_savings = income * 0.2
                
                result = {
                    'income': income,
                    'total_expenses': round(total_expenses, 2),
                    'remaining': round(remaining, 2),
                    'needs_pct': round((needs/income)*100, 1) if income > 0 else 0,
                    'wants_pct': round((wants/income)*100, 1) if income > 0 else 0,
                    'savings_pct': round((savings/income)*100, 1) if income > 0 else 0,
                    'recommended_needs': round(recommended_needs, 2),
                    'recommended_wants': round(recommended_wants, 2),
                    'recommended_savings': round(recommended_savings, 2),
                    'type': 'budget'
                }
                
                # Generar explicación con IA
                ai_explanation = generate_ai_explanation(result, tab)
                
            except:
                result = {"error": "Error en los valores ingresados"}
        
        elif tab == "retirement":
            try:
                current_age = int(request.POST.get("current_age", 0))
                retirement_age = int(request.POST.get("retirement_age", 0))
                current_savings = float(request.POST.get("current_savings", 0))
                monthly_contribution = float(request.POST.get("monthly_contribution", 0))
                expected_return = float(request.POST.get("expected_return", 0)) / 100
                desired_income = float(request.POST.get("desired_income", 0))
                
                years_to_retirement = retirement_age - current_age
                months_to_retirement = years_to_retirement * 12
                
                # Cálculo del valor futuro con aportaciones
                if expected_return > 0:
                    monthly_rate = expected_return / 12
                    # Valor futuro del dinero actual
                    future_current = current_savings * (1 + monthly_rate) ** months_to_retirement
                    # Valor futuro de las aportaciones mensuales
                    future_contributions = monthly_contribution * (((1 + monthly_rate) ** months_to_retirement - 1) / monthly_rate)
                    total_at_retirement = future_current + future_contributions
                else:
                    total_at_retirement = current_savings + (monthly_contribution * months_to_retirement)
                
                # Ingreso mensual sostenible (regla del 4%)
                monthly_income = (total_at_retirement * 0.04) / 12
                total_contributions = current_savings + (monthly_contribution * months_to_retirement)
                
                result = {
                    'total_at_retirement': round(total_at_retirement, 2),
                    'monthly_income': round(monthly_income, 2),
                    'total_contributions': round(total_contributions, 2),
                    'years_to_retirement': years_to_retirement,
                    'shortfall': round(max(0, desired_income - monthly_income), 2) if desired_income > 0 else 0,
                    'type': 'retirement'
                }
                
                # Generar explicación con IA
                ai_explanation = generate_ai_explanation(result, tab)
                
            except:
                result = {"error": "Error en los valores ingresados"}
        
        elif tab == "investment":
            try:
                initial_investment = float(request.POST.get("initial_investment", 0))
                monthly_investment = float(request.POST.get("monthly_investment", 0))
                annual_return = float(request.POST.get("annual_return", 0)) / 100
                years = int(request.POST.get("years", 0))
                inflation_rate = float(request.POST.get("inflation_rate", 3.0)) / 100
                
                months = years * 12
                
                # Cálculo del valor futuro
                if annual_return > 0:
                    monthly_rate = annual_return / 12
                    # Valor futuro de la inversión inicial
                    future_initial = initial_investment * (1 + monthly_rate) ** months
                    # Valor futuro de las inversiones mensuales
                    future_monthly = monthly_investment * (((1 + monthly_rate) ** months - 1) / monthly_rate)
                    final_value = future_initial + future_monthly
                else:
                    final_value = initial_investment + (monthly_investment * months)
                
                total_invested = initial_investment + (monthly_investment * months)
                total_profit = final_value - total_invested
                roi_percentage = (total_profit / total_invested * 100) if total_invested > 0 else 0
                
                # Valor real ajustado por inflación
                real_rate = ((1 + annual_return) / (1 + inflation_rate)) - 1
                if real_rate > 0:
                    real_monthly_rate = real_rate / 12
                    real_future_initial = initial_investment * (1 + real_monthly_rate) ** months
                    real_future_monthly = monthly_investment * (((1 + real_monthly_rate) ** months - 1) / real_monthly_rate)
                    real_value = real_future_initial + real_future_monthly
                else:
                    real_value = final_value / ((1 + inflation_rate) ** years)
                
                result = {
                    'final_value': round(final_value, 2),
                    'total_profit': round(total_profit, 2),
                    'total_invested': round(total_invested, 2),
                    'roi_percentage': round(roi_percentage, 2),
                    'real_value': round(real_value, 2),
                    'type': 'investment'
                }
                
                # Generar explicación con IA
                ai_explanation = generate_ai_explanation(result, tab)
                
            except:
                result = {"error": "Error en los valores ingresados"}

    return render(request, 'educacion_financiera/calculators_new.html', {
        'tab': tab,
        'result': result,
        'ai_explanation': ai_explanation
    })

def generate_ai_explanation(result, calculation_type):
    """Genera explicación usando IA de Gemini"""
    try:
        # Configurar Gemini
        model = genai.GenerativeModel(model_name='gemini-2.0-flash', api_key="AIzaSyCGNpJrqFn8gjWU3-DKMl05s-cgaMket2A")
        
        prompt = "Explica estos resultados financieros."  # Default prompt
        
        if calculation_type == 'savings':
            prompt = f"""
            Explica de manera simple estos resultados de ahorro:
            - Valor futuro: ${result['future_value']:,.2f}
            - Total aportado: ${result['total_contributed']:,.2f}
            - Intereses ganados: ${result['interest_earned']:,.2f}
            
            Da 2-3 consejos prácticos sobre ahorro.
            """
        elif calculation_type == 'loan':
            prompt = f"""
            Explica estos resultados de préstamo:
            - Pago mensual: ${result['monthly_payment']:,.2f}
            - Total a pagar: ${result['total_payment']:,.2f}
            - Intereses totales: ${result['total_interest']:,.2f}
            
            Da consejos para manejar mejor las deudas.
            """
        elif calculation_type == 'budget':
            prompt = f"""
            Analiza este presupuesto:
            - Ingresos: ${result['income']:,.2f}
            - Gastos totales: ${result['total_expenses']:,.2f}
            - Remanente: ${result['remaining']:,.2f}
            
            Da consejos para optimizar el presupuesto.
            """
        elif calculation_type == 'retirement':
            prompt = f"""
            Analiza este plan de jubilación:
            - Total al jubilarte: ${result['total_at_retirement']:,.2f}
            - Ingreso mensual sostenible: ${result['monthly_income']:,.2f}
            - Años para jubilación: {result['years_to_retirement']}
            
            Da consejos específicos para mejorar el plan de jubilación.
            """
        elif calculation_type == 'investment':
            prompt = f"""
            Analiza esta proyección de inversión:
            - Valor final: ${result['final_value']:,.2f}
            - Ganancia total: ${result['total_profit']:,.2f}
            - ROI: {result['roi_percentage']:.1f}%
            - Valor real: ${result['real_value']:,.2f}
            
            Da consejos sobre estrategias de inversión y diversificación.
            """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        print(f"Error generando explicación IA: {e}")
        return "No se pudo generar explicación con IA en este momento."

@login_required
@fast_access_pin_verified
def courses(request):
    # Obtener todos los cursos
    todos_cursos = CursoExterno.objects.all().order_by('orden', 'titulo')
    
    # Marcar favoritos para el usuario actual
    favoritos_ids = FavoritoCurso.objects.filter(usuario=request.user).values_list('curso_id', flat=True)
    
    for curso in todos_cursos:
        curso.es_favorito = curso.id in favoritos_ids
    
    # Configurar paginación: 6 cursos por página
    paginator = Paginator(todos_cursos, 6)
    page = request.GET.get('page')
    
    try:
        cursos = paginator.page(page)
    except PageNotAnInteger:
        # Si page no es un entero, mostrar la primera página
        cursos = paginator.page(1)
    except EmptyPage:
        # Si page está fuera de rango, mostrar la última página
        cursos = paginator.page(paginator.num_pages)
    
    return render(request, 'educacion_financiera/courses.html', {
        'cursos': cursos,
        'paginator': paginator,
        'page_obj': cursos,
    })

@login_required
def toggle_favorito_curso(request, curso_id):
    """Toggle favorito de curso via AJAX"""
    if request.method == 'POST':
        try:
            curso = get_object_or_404(CursoExterno, id=curso_id)
            favorito, created = FavoritoCurso.objects.get_or_create(
                usuario=request.user,
                curso=curso
            )
            
            if not created:
                # Si ya existía, eliminarlo
                favorito.delete()
                es_favorito = False
            else:
                es_favorito = True
            
            return JsonResponse({
                'success': True,
                'es_favorito': es_favorito
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
@fast_access_pin_verified
def tips(request):
    """Vista principal de consejos financieros"""
    tab = request.GET.get('tab', 'savings')
    ai_enabled = request.GET.get('ai', 'false').lower() == 'true'
    
    # Clase para estructurar consejos
    class TipObject:
        def __init__(self, categoria, titulo, descripcion, prioridad, es_ai=False, link_externo=None, id=None):
            self.id = id or f"{categoria}_{hash(titulo) % 1000}"
            self.categoria = categoria
            self.titulo = titulo
            self.descripcion = descripcion
            self.prioridad = prioridad
            self.es_ai = es_ai
            self.link_externo = link_externo
        
        def get_categoria_display(self):
            category_map = {
                'savings': '💰 Ahorros',
                'investment': '📈 Inversiones',
                'budget': '📊 Presupuesto',
                'debt': '💳 Deudas',
                'insurance': '🛡️ Seguros',
                'retirement': '🏖️ Jubilación'
            }
            return category_map.get(self.categoria, self.categoria.title())
        
        def get_prioridad_display(self):
            prioridad_map = {
                'high': 'Alta',
                'medium': 'Media',
                'low': 'Baja'
            }
            return prioridad_map.get(self.prioridad, self.prioridad.title())
    
    # Consejos base por categoría
    consejos_base = {
        'savings': [
            TipObject('savings', 'Automatiza tus Ahorros', 'Configura transferencias automáticas del 20% de tus ingresos a una cuenta separada el día que cobras.', 'high'),
            TipObject('savings', 'Regla del 50/30/20', 'Destina 50% para necesidades, 30% para deseos y 20% para ahorros e inversiones.', 'medium'),
            TipObject('savings', 'Fondo de Emergencia', 'Mantén al menos 3-6 meses de gastos en una cuenta de fácil acceso para emergencias.', 'high'),
        ],
        'investment': [
            TipObject('investment', 'Diversifica tu Portafolio', 'Invierte en diferentes tipos de activos (acciones, bonos, bienes raíces) para reducir riesgos.', 'high'),
            TipObject('investment', 'Inversión a Largo Plazo', 'El tiempo es tu mejor aliado. Invierte consistentemente y deja que el interés compuesto haga su magia.', 'medium'),
            TipObject('investment', 'Edúcate Antes de Invertir', 'Nunca inviertas en algo que no entiendes. Lee, estudia y consulta con expertos.', 'high'),
        ],
        'budget': [
            TipObject('budget', 'Rastrea Todos tus Gastos', 'Anota cada peso que gastas durante un mes para identificar patrones y áreas de mejora.', 'high'),
            TipObject('budget', 'Presupuesto Base Cero', 'Cada peso debe tener un propósito antes de gastarlo. Asigna todo tu ingreso a categorías específicas.', 'medium'),
            TipObject('budget', 'Revisa Mensualmente', 'Evalúa tu presupuesto cada mes y ajusta según tus necesidades y objetivos cambiantes.', 'medium'),
        ],
        'debt': [
            TipObject('debt', 'Método Avalancha de Deudas', 'Paga primero las deudas con mayor tasa de interés mientras mantienes pagos mínimos en otras.', 'high'),
            TipObject('debt', 'Evita Deudas de Consumo', 'No uses tarjetas de crédito para compras que no puedes pagar inmediatamente.', 'high'),
            TipObject('debt', 'Negocia con Acreedores', 'Si tienes problemas para pagar, contacta a tus acreedores para negociar planes de pago.', 'medium'),
        ],
        'insurance': [
            TipObject('insurance', 'Seguro de Vida', 'Si tienes dependientes, necesitas un seguro de vida equivalente a 10 veces tu ingreso anual.', 'high'),
            TipObject('insurance', 'Seguro de Salud', 'Un seguro médico puede protegerte de gastos catastróficos que podrían arruinar tus finanzas.', 'high'),
            TipObject('insurance', 'Revisa Coberturas Anualmente', 'Evalúa tus seguros cada año para asegurar que cubran tus necesidades actuales.', 'medium'),
        ],
        'retirement': [
            TipObject('retirement', 'Comienza Temprano', 'Incluso $50 mensuales a los 25 años valen más que $500 mensuales a los 45 por el interés compuesto.', 'high'),
            TipObject('retirement', 'Contribuye al Máximo', 'Si tu empleador ofrece plan de jubilación con aportación patronal, contribuye al menos hasta el límite del match.', 'high'),
            TipObject('retirement', 'Calcula tu Número', 'Determina cuánto necesitas para jubilarte cómodamente y trabaja hacia esa meta específica.', 'medium'),
        ]
    }
    
    # Obtener consejos para la categoría seleccionada
    tips_data = consejos_base.get(tab, consejos_base['savings'])
    
    # Si AI está habilitada, generar consejos adicionales
    if ai_enabled:
        try:
            ai_tips = generate_ai_tips(tab)
            tips_data.extend(ai_tips)
        except Exception as e:
            print(f"Error generando consejos IA: {e}")
    
    return render(request, 'educacion_financiera/tips.html', {
        'tips': tips_data,
        'current_tab': tab,
        'ai_enabled': ai_enabled
    })

def generate_ai_tips(categoria):
    """Genera consejos financieros usando Gemini AI"""
    try:
        # Prompt para generar consejos
        prompt = f"""
Genera 3 consejos financieros muy específicos y prácticos sobre {categoria} para el año 2025.

Cada consejo debe incluir:
- Un título claro y directo
- Una descripción práctica de 2-3 líneas con pasos específicos
- Una prioridad (alta/media/baja)

Responde SOLO con un JSON array en este formato:
[
  {{
    "titulo": "Título del consejo",
    "descripcion": "Descripción práctica con pasos específicos",
    "prioridad": "alta"
  }}
]
"""
        
        # Intentar con diferentes modelos
        models = ['gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-pro-latest']
        
        for model_name in models:
            try:
                model = genai.GenerativeModel(model_name, api_key="AIzaSyCGNpJrqFn8gjWU3-DKMl05s-cgaMket2A")
                response = model.generate_content(prompt)
                
                # Limpiar respuesta
                ai_tips_raw = response.text.strip()
                if "```json" in ai_tips_raw:
                    ai_tips_raw = ai_tips_raw.split("```json")[1].split("```")[0]
                elif "```" in ai_tips_raw:
                    ai_tips_raw = ai_tips_raw.split("```")[1]
                
                ai_tips_data = json.loads(ai_tips_raw.strip())
                
                # Convertir a objetos TipObject
                class TipObject:
                    def __init__(self, categoria, titulo, descripcion, prioridad, es_ai=False, link_externo=None, id=None):
                        self.id = id or f"{categoria}_{hash(titulo) % 1000}"
                        self.categoria = categoria
                        self.titulo = titulo
                        self.descripcion = descripcion
                        self.prioridad = prioridad
                        self.es_ai = es_ai
                        self.link_externo = link_externo
                    
                    def get_categoria_display(self):
                        category_map = {
                            'savings': '💰 Ahorros',
                            'investment': '📈 Inversiones',
                            'budget': '📊 Presupuesto',
                            'debt': '💳 Deudas',
                            'insurance': '🛡️ Seguros',
                            'retirement': '🏖️ Jubilación'
                        }
                        return category_map.get(self.categoria, self.categoria.title())
                    
                    def get_prioridad_display(self):
                        prioridad_map = {
                            'alta': 'Alta',
                            'media': 'Media',
                            'baja': 'Baja',
                            'high': 'Alta',
                            'medium': 'Media',
                            'low': 'Baja'
                        }
                        return prioridad_map.get(self.prioridad, self.prioridad.title())
                
                ai_tips = []
                for i, tip_data in enumerate(ai_tips_data):
                    tip_obj = TipObject(
                        id=f"ai_{categoria}_{i}",
                        categoria=categoria,
                        titulo=tip_data['titulo'],
                        descripcion=tip_data['descripcion'],
                        prioridad=tip_data['prioridad'],
                        es_ai=True,
                        link_externo=None
                    )
                    ai_tips.append(tip_obj)
                
                return ai_tips
                
            except Exception as e:
                print(f"Error con modelo {model_name}: {e}")
                continue
        
        # Si falla, retornar lista vacía
        return []
        
    except Exception as e:
        print(f"Error general en generate_ai_tips: {e}")
        return []

@login_required
@fast_access_pin_verified
def ai_chat(request):
    """Chat interactivo con IA financiera sin restricciones"""
    # Si es GET, renderizar el template del chat
    if request.method == 'GET':
        return render(request, 'educacion_financiera/ai_chat.html')
    
    if request.method == 'POST':
        try:
            # Intentar leer como JSON o como FormData
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                user_message = data.get('message', '')
            else:
                user_message = request.POST.get('question', '')
            
            # Prompt básico sin restricciones
            prompt = f"""
Eres un asistente financiero experto y amigable. El usuario te pregunta: "{user_message}"

Responde de manera útil, práctica y conversacional. Puedes hablar de cualquier tema financiero sin restricciones.
Si no es sobre finanzas, redirige amablemente hacia temas financieros.

Sé específico, da ejemplos prácticos y mantén un tono amigable.
"""
            
            # Intentar con diferentes modelos
            models = ['gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-pro-latest']
            
            for model_name in models:
                try:
                    model = genai.GenerativeModel(model_name, api_key="AIzaSyCGNpJrqFn8gjWU3-DKMl05s-cgaMket2A")
                    response = model.generate_content(prompt)
                    
                    return JsonResponse({
                        'success': True,
                        'response': response.text,
                        'model': model_name
                    })
                    
                except Exception as e:
                    print(f"Error con modelo {model_name}: {e}")
                    continue
            
            # Si todos los modelos fallan
            return JsonResponse({
                'success': False,
                'error': 'No se pudo conectar con la IA. Intenta de nuevo.'
            })
            
        except Exception as e:
            print(f"Error en ai_chat: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Error procesando tu mensaje: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def generar_consejos_ia(request):
    """Genera consejos IA para una categoría específica"""
    if request.method == 'POST':
        categoria = request.POST.get('categoria', 'savings')
        
        try:
            ai_tips = generate_ai_tips(categoria)
            
            return JsonResponse({
                'success': True,
                'message': f'Se generaron {len(ai_tips)} consejos con IA para {categoria}',
                'tips': [tip.__dict__ for tip in ai_tips]
            })
            
        except Exception as e:
            print(f"Error generando consejos IA: {e}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})
