import os
import json
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
_genai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

AVAILABLE_MODELS = ['gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-pro-latest']


NO_IA_MSG = "No se pudo generar explicación con IA en este momento."


def generate_ai_explanation(result, calculation_type):
    """Genera explicación usando IA de Gemini"""
    if _genai_client is None:
        return NO_IA_MSG

    try:
        prompt = _build_explanation_prompt(result, calculation_type)
        
        for model_name in AVAILABLE_MODELS:
            try:
                response = _genai_client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                print(f"Error con modelo {model_name}: {e}")
                continue
        
        return NO_IA_MSG
        
    except Exception as e:
        print(f"Error generando explicación IA: {e}")
        return NO_IA_MSG


def _build_explanation_prompt(result, calculation_type):
    """Construye el prompt según el tipo de cálculo"""
    
    if calculation_type == 'savings':
        return f"""
        Explica de manera simple estos resultados de ahorro:
        - Valor futuro: ${result['future_value']:,.2f}
        - Total aportado: ${result['total_contributed']:,.2f}
        - Intereses ganados: ${result['interest_earned']:,.2f}
        
        Da 2-3 consejos prácticos sobre ahorro.
        """
    
    elif calculation_type == 'loan':
        return f"""
        Explica estos resultados de préstamo:
        - Pago mensual: ${result['monthly_payment']:,.2f}
        - Total a pagar: ${result['total_payment']:,.2f}
        - Intereses totales: ${result['total_interest']:,.2f}
        
        Da consejos para manejar mejor las deudas.
        """
    
    elif calculation_type == 'budget':
        return f"""
        Analiza este presupuesto:
        - Ingresos: ${result['income']:,.2f}
        - Gastos totales: ${result['total_expenses']:,.2f}
        - Remanente: ${result['remaining']:,.2f}
        
        Da consejos para optimizar el presupuesto.
        """
    
    elif calculation_type == 'retirement':
        return f"""
        Analiza este plan de jubilación:
        - Total al jubilarte: ${result['total_at_retirement']:,.2f}
        - Ingreso mensual sostenible: ${result['monthly_income']:,.2f}
        - Años para jubilación: {result['years_to_retirement']}
        
        Da consejos específicos para mejorar el plan de jubilación.
        """
    
    elif calculation_type == 'investment':
        return f"""
        Analiza esta proyección de inversión:
        - Valor final: ${result['final_value']:,.2f}
        - Ganancia total: ${result['total_profit']:,.2f}
        - ROI: {result['roi_percentage']:.1f}%
        - Valor real: ${result['real_value']:,.2f}
        
        Da consejos sobre estrategias de inversión y diversificación.
        """
    
    return "Explica estos resultados financieros."


def generate_ai_tips(categoria):
    """Genera consejos financieros usando Gemini AI"""
    if _genai_client is None:
        return []

    from .models_helpers import TipObject
    
    try:
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
        
        for model_name in AVAILABLE_MODELS:
            try:
                response = _genai_client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                
                # Limpiar respuesta
                ai_tips_raw = response.text.strip()
                if "```json" in ai_tips_raw:
                    ai_tips_raw = ai_tips_raw.split("```json")[1].split("```")[0]
                elif "```" in ai_tips_raw:
                    ai_tips_raw = ai_tips_raw.split("```")[1]
                
                ai_tips_data = json.loads(ai_tips_raw.strip())
                
                # Convertir a objetos TipObject
                ai_tips = []
                for i, tip_data in enumerate(ai_tips_data):
                    tip_obj = TipObject(
                        id=f"ai_{categoria}_{i}",
                        categoria=categoria,
                        titulo=tip_data['titulo'],
                        descripcion=tip_data['descripcion'],
                        prioridad=tip_data['prioridad'],
                        es_ai=True,
                    )
                    ai_tips.append(tip_obj)
                
                return ai_tips
                
            except Exception as e:
                print(f"Error con modelo {model_name}: {e}")
                continue
        
        return []
        
    except Exception as e:
        print(f"Error general en generate_ai_tips: {e}")
        return []


def process_ai_chat(user_message):
    """Procesa mensaje de chat con IA"""
    if _genai_client is None:
        return {
            'success': False,
            'error': 'No se pudo conectar con la IA. Intenta de nuevo.'
        }

    try:
        prompt = f"""
Eres un asistente financiero experto y amigable. El usuario te pregunta: "{user_message}"

Responde de manera útil, práctica y conversacional. Puedes hablar de cualquier tema financiero sin restricciones.
Si no es sobre finanzas, redirige amablemente hacia temas financieros.

Sé específico, da ejemplos prácticos y mantén un tono amigable.
"""
        
        for model_name in AVAILABLE_MODELS:
            try:
                response = _genai_client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                
                return {
                    'success': True,
                    'response': response.text,
                    'model': model_name
                }
                
            except Exception as e:
                print(f"Error con modelo {model_name}: {e}")
                continue
        
        return {
            'success': False,
            'error': 'No se pudo conectar con la IA. Intenta de nuevo.'
        }
        
    except Exception as e:
        print(f"Error en process_ai_chat: {e}")
        return {
            'success': False,
            'error': f'Error procesando tu mensaje: {str(e)}'
        }
