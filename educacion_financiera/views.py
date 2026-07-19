from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from core.decorators import fast_access_pin_verified
from django.contrib.auth.decorators import login_required
from .models import CursoExterno, FavoritoCurso
from .utils import marcar_favoritos, paginar_cursos
from .services import generate_ai_explanation, generate_ai_tips, process_ai_chat
from .constants import CONSEJOS_BASE
import json

# Views App EDUCACION_FINANCIERA


@login_required
@fast_access_pin_verified
# Constantes para evitar duplicados de literales
ERROR_VALORES_INGRESADOS = "Error en los valores ingresados"
METODO_NO_PERMITIDO = "Método no permitido"

# Helpers de cálculo para reducir complejidad cognitiva
def _calculate_savings(post_data):
    try:
        initial = float(post_data.get("initial", 0))
        monthly = float(post_data.get("monthly", 0))
        rate = float(post_data.get("rate", 0)) / 100
        years = int(post_data.get("years", 0))
        months = years * 12
        
        # Cálculo con interés compuesto
        if rate > 0:
            future_value = initial * (1 + rate/12) ** months + monthly * (((1 + rate/12) ** months - 1) / (rate/12))
        else:
            future_value = initial + (monthly * months)
        
        total_contributed = initial + (monthly * months)
        interest_earned = future_value - total_contributed
        
        return {
            'future_value': round(future_value, 2),
            'total_contributed': round(total_contributed, 2),
            'interest_earned': round(interest_earned, 2),
            'type': 'savings'
        }
        }
    except Exception:
        return {"error": ERROR_VALORES_INGRESADOS}

def _calculate_loan(post_data):
    try:
        amount = float(post_data.get("amount", 0))
        rate = float(post_data.get("rate", 0)) / 100
        years = int(post_data.get("years", 0))
        months = years * 12
        
        if rate > 0:
            monthly_rate = rate / 12
            monthly_payment = amount * monthly_rate / (1 - (1 + monthly_rate) ** -months)
        else:
            monthly_payment = amount / months
        
        total_payment = monthly_payment * months
        total_interest = total_payment - amount
        
        return {
            'monthly_payment': round(monthly_payment, 2),
            'total_payment': round(total_payment, 2),
            'total_interest': round(total_interest, 2),
            'loan_amount': amount,
            'type': 'loan'
        }
    except Exception:
        return {"error": ERROR_VALORES_INGRESADOS}

def _calculate_budget(post_data):
    try:
        income = float(post_data.get("income", 0))
        needs = float(post_data.get("needs", 0))
        wants = float(post_data.get("wants", 0))
        savings = float(post_data.get("savings", 0))
        
        total_expenses = needs + wants + savings
        remaining = income - total_expenses
        
        # Regla 50/30/20
        recommended_needs = income * 0.5
        recommended_wants = income * 0.3
        recommended_savings = income * 0.2
        
        return {
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
    except Exception:
        return {"error": ERROR_VALORES_INGRESADOS}

def _calculate_retirement(post_data):
    try:
        current_age = int(post_data.get("current_age", 0))
        retirement_age = int(post_data.get("retirement_age", 0))
        current_savings = float(post_data.get("current_savings", 0))
        monthly_contribution = float(post_data.get("monthly_contribution", 0))
        expected_return = float(post_data.get("expected_return", 0)) / 100
        desired_income = float(post_data.get("desired_income", 0))
        
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
        
        return {
            'total_at_retirement': round(total_at_retirement, 2),
            'monthly_income': round(monthly_income, 2),
            'total_contributions': round(total_contributions, 2),
            'years_to_retirement': years_to_retirement,
            'shortfall': round(max(0, desired_income - monthly_income), 2) if desired_income > 0 else 0,
            'type': 'retirement'
        }
    except Exception:
        return {"error": ERROR_VALORES_INGRESADOS}

def _calculate_investment(post_data):
    try:
        initial_investment = float(post_data.get("initial_investment", 0))
        monthly_investment = float(post_data.get("monthly_investment", 0))
        annual_return = float(post_data.get("annual_return", 0)) / 100
        years = int(post_data.get("years", 0))
        inflation_rate = float(post_data.get("inflation_rate", 3.0)) / 100
        
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
        
        return {
            'final_value': round(final_value, 2),
            'total_profit': round(total_profit, 2),
            'total_invested': round(total_invested, 2),
            'roi_percentage': round(roi_percentage, 2),
            'real_value': round(real_value, 2),
            'type': 'investment'
        }
    except Exception:
        return {"error": ERROR_VALORES_INGRESADOS}


@login_required
@fast_access_pin_verified
def calculators(request):
    tab = request.GET.get("tab", "savings")  # default tab
    result = None
    ai_explanation = None

    if request.method == "POST":
        calc_funcs = {
            "savings": _calculate_savings,
            "loan": _calculate_loan,
            "budget": _calculate_budget,
            "retirement": _calculate_retirement,
            "investment": _calculate_investment,
        }
        calc_func = calc_funcs.get(tab)
        if calc_func:
            result = calc_func(request.POST)
            if result and "error" not in result:
                # Generar explicación con IA
                ai_explanation = generate_ai_explanation(result, tab)

    return render(request, 'educacion_financiera/calculators_new.html', {
        'tab': tab,
        'result': result,
        'ai_explanation': ai_explanation
    })

@login_required
@fast_access_pin_verified
def courses(request):
    # Obtener cursos ordenados
    todos_cursos = CursoExterno.objects.all().order_by('orden', 'titulo')
    
    # Marcar favoritos del usuario
    todos_cursos = marcar_favoritos(todos_cursos, request.user)
    
    # Paginar cursos
    page = request.GET.get('page')
    paginator, cursos_pagina = paginar_cursos(todos_cursos, page)
    
    return render(request, 'educacion_financiera/courses.html', {
        'cursos': cursos_pagina,
        'paginator': paginator,
        'page_obj': cursos_pagina,
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
    
    return JsonResponse({'success': False, 'error': METODO_NO_PERMITIDO})

@login_required
@fast_access_pin_verified
def tips(request):
    """Vista principal de consejos financieros"""
    tab = request.GET.get('tab', 'savings')
    ai_enabled = request.GET.get('ai', 'false').lower() == 'true'
    
    # Obtener consejos base para la categoría
    tips_data = CONSEJOS_BASE.get(tab, CONSEJOS_BASE['savings']).copy()
    
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
            
            # Procesar con servicio de IA
            result = process_ai_chat(user_message)
            return JsonResponse(result)
            
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
