from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from core.decorators import fast_access_pin_verified
from django.contrib.auth.decorators import login_required
from .models import CursoExterno, FavoritoCurso
from .ai_tips import get_ai_tips, get_personalized_tips

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
                retirement_age = int(request.POST.get("retirement_age", 65))
                current_savings = float(request.POST.get("current_savings", 0))
                monthly_contribution = float(request.POST.get("monthly_contribution", 0))
                expected_return = float(request.POST.get("expected_return", 7)) / 100
                
                years_to_retirement = retirement_age - current_age
                months_to_retirement = years_to_retirement * 12
                
                if expected_return > 0:
                    monthly_rate = expected_return / 12
                    future_value = current_savings * (1 + monthly_rate) ** months_to_retirement + \
                                   monthly_contribution * (((1 + monthly_rate) ** months_to_retirement - 1) / monthly_rate)
                else:
                    future_value = current_savings + (monthly_contribution * months_to_retirement)
                
                total_contributions = current_savings + (monthly_contribution * months_to_retirement)
                investment_growth = future_value - total_contributions
                
                result = {
                    'future_value': round(future_value, 2),
                    'total_contributions': round(total_contributions, 2),
                    'investment_growth': round(investment_growth, 2),
                    'years_to_retirement': years_to_retirement,
                    'monthly_income_estimate': round(future_value * 0.04 / 12, 2),  # Regla 4%
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
                investment_years = int(request.POST.get("investment_years", 0))
                
                months = investment_years * 12
                
                if annual_return > 0:
                    monthly_rate = annual_return / 12
                    future_value = initial_investment * (1 + monthly_rate) ** months + \
                                   monthly_investment * (((1 + monthly_rate) ** months - 1) / monthly_rate)
                else:
                    future_value = initial_investment + (monthly_investment * months)
                
                total_invested = initial_investment + (monthly_investment * months)
                total_return = future_value - total_invested
                roi_percentage = (total_return / total_invested * 100) if total_invested > 0 else 0
                
                result = {
                    'future_value': round(future_value, 2),
                    'total_invested': round(total_invested, 2),
                    'total_return': round(total_return, 2),
                    'roi_percentage': round(roi_percentage, 2),
                    'type': 'investment'
                }
                
                # Generar explicación con IA
                ai_explanation = generate_ai_explanation(result, tab)
                
            except:
                result = {"error": "Error en los valores ingresados"}

    return render(request, "educacion_financiera/calculators.html", {
        "tab": tab,
        "result": result,
        "ai_explanation": ai_explanation
    })


def generate_ai_explanation(result, calculator_type):
    """Generar explicación con IA para los resultados de las calculadoras"""
    try:
        import google.generativeai as genai
        import os
        
        # Configurar IA
        api_key = os.getenv("GOOGLE_API_KEY", "AIzaSyDnWhyD5zCArmmEzmRkQH4zuB2NxgtuEHc")
        genai.configure(api_key=api_key)
        
        # Lista de modelos para probar
        models_to_try = [
            'gemini-1.5-flash-latest',
            'gemini-1.5-flash', 
            'gemini-1.5-pro'
        ]
        
        # Crear prompt específico según el tipo de calculadora
        prompts = {
            'savings': f"""
            Analiza estos resultados de ahorro en máximo 3 puntos concisos:
            - Valor futuro: ${result.get('future_value', 0):,.2f}
            - Total contribuido: ${result.get('total_contributed', 0):,.2f}
            - Intereses ganados: ${result.get('interest_earned', 0):,.2f}
            
            Responde en formato de lista con máximo 3 puntos:
            1. [Evaluación del resultado - bueno/regular/malo]
            2. [Consejo principal para mejorar]
            3. [Dato interesante sobre el crecimiento]
            
            Sé directo y específico.
            """,
            
            'loan': f"""
            Analiza este préstamo en máximo 3 puntos concisos:
            - Pago mensual: ${result.get('monthly_payment', 0):,.2f}
            - Pago total: ${result.get('total_payment', 0):,.2f}
            - Interés total: ${result.get('total_interest', 0):,.2f}
            
            Responde en formato de lista con máximo 3 puntos:
            1. [Evaluación del costo del préstamo]
            2. [Estrategia principal para ahorro]
            3. [Comparación con el monto original]
            
            Sé directo y práctico.
            """,
            
            'budget': f"""
            Evalúa este presupuesto en máximo 3 puntos concisos:
            - Balance: ${result.get('remaining', 0):,.2f}
            - Necesidades: {result.get('needs_pct', 0)}% (ideal: 50%)
            - Ahorros: {result.get('savings_pct', 0)}% (ideal: 20%)
            
            Responde en formato de lista con máximo 3 puntos:
            1. [Estado general del presupuesto]
            2. [Área que más necesita ajuste]
            3. [Acción específica a tomar]
            
            Sé específico y accionable.
            """,
            
            'retirement': f"""
            Evalúa esta proyección de jubilación en máximo 3 puntos:
            - Valor al jubilarse: ${result.get('future_value', 0):,.2f}
            - Ingreso mensual: ${result.get('monthly_income_estimate', 0):,.2f}
            - Años restantes: {result.get('years_to_retirement', 0)}
            
            Responde en formato de lista con máximo 3 puntos:
            1. [¿Es suficiente para jubilarse cómodamente?]
            2. [Consejo principal para mejorar]
            3. [Ventaja del tiempo que queda]
            
            Sé directo y motivador.
            """,
            
            'investment': f"""
            Evalúa esta inversión en máximo 3 puntos concisos:
            - Valor futuro: ${result.get('future_value', 0):,.2f}
            - ROI: {result.get('roi_percentage', 0)}%
            - Ganancia: ${result.get('total_return', 0):,.2f}
            
            Responde en formato de lista con máximo 3 puntos:
            1. [Evaluación del ROI - bueno/promedio/bajo]
            2. [Consejo para optimizar]
            3. [Comparación con alternativas]
            
            Sé directo y específico.
            """
        }
        
        prompt = prompts.get(calculator_type, """
        Analiza estos resultados financieros en máximo 3 puntos:
        1. [Evaluación general]
        2. [Consejo principal]  
        3. [Próximo paso recomendado]
        
        Sé conciso y directo.
        """)
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"Modelo {model_name} falló: {e}")
                continue
                
        return None
        
    except Exception as e:
        print(f"Error generando explicación IA: {e}")
        return None

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
    use_ai = request.GET.get("ai", "false") == "true"
    
    # Si el usuario quiere consejos personalizados con IA
    if tab == "personalized":
        age_range = request.GET.get("age_range")
        employment = request.GET.get("employment") 
        goals = request.GET.get("goals")
        experience = request.GET.get("experience")
        
        tips_data = get_personalized_tips(
            user_age_range=age_range,
            employment_status=employment,
            financial_goals=goals,
            experience_level=experience
        )
    elif use_ai:
        # Usar IA para generar consejos dinámicos
        tips_data = get_ai_tips(tab)
    else:
        # Consejos estáticos tradicionales
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
        }.get(tab, [])

    return render(request, "educacion_financiera/tips.html", {
        "tab": tab,
        "tips": tips_data,
        "use_ai": use_ai,
    })

@login_required
@fast_access_pin_verified
def ai_chat(request):
    """Vista para chat interactivo con IA - Completamente libre"""
    if request.method == 'POST':
        user_question = request.POST.get('question', '').strip()
        
        if user_question:
            try:
                import google.generativeai as genai
                import os
                
                # Configurar IA directamente sin restricciones
                api_key = os.getenv("GOOGLE_API_KEY", "AIzaSyDnWhyD5zCArmmEzmRkQH4zuB2NxgtuEHc")
                genai.configure(api_key=api_key)
                
                # Lista de modelos para probar en orden de preferencia
                models_to_try = [
                    'gemini-1.5-flash-latest',
                    'gemini-1.5-flash', 
                    'gemini-1.5-pro',
                    'gemini-pro-latest',
                    'gemini-pro'
                ]
                
                ai_response = None
                last_error = None
                
                for model_name in models_to_try:
                    try:
                        model = genai.GenerativeModel(model_name)
                        
                        # Crear un prompt estructurado para respuestas organizadas
                        structured_prompt = f"""
Responde de manera clara, ordenada y estructurada a la siguiente pregunta/mensaje:

"{user_question}"

Por favor, estructura tu respuesta usando:
- Títulos claros si es necesario
- Puntos organizados
- Información paso a paso cuando sea apropiado
- Ejemplos prácticos si aplica
- Un tono amigable y profesional

Hazlo de forma natural y conversacional, pero bien organizada.
"""
                        
                        response = model.generate_content(structured_prompt)
                        ai_response = response.text
                        break  # Si llegamos aquí, el modelo funcionó
                    except Exception as e:
                        last_error = e
                        print(f"Modelo {model_name} falló: {e}")
                        continue
                
                if not ai_response:
                    # Si ningún modelo funcionó, usar respuesta de fallback
                    ai_response = f"¡Hola! 👋 Gracias por tu mensaje: '{user_question}'. Actualmente tengo un problema técnico con la conexión a la IA, pero estoy trabajando para solucionarlo. Mientras tanto, puedes probar con los consejos financieros tradicionales en la sección de Tips."
                    
                return JsonResponse({
                    'success': True,
                    'response': ai_response,
                    'question': user_question
                })
                
            except Exception as e:
                print(f"Error en AI chat: {e}")
                return JsonResponse({
                    'success': True,
                    'response': f'¡Hola! 👋 Hubo un problema técnico, pero puedo intentar ayudarte de otra manera. Error: {str(e)}',
                    'question': user_question
                })
        
        return JsonResponse({
            'success': False,
            'error': 'Escribe algo para comenzar la conversación'
        })
    
    return render(request, "educacion_financiera/ai_chat.html")
