import os
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from django.shortcuts import get_object_or_404
import google.generativeai as genai

from .models import CursoExterno, FavoritoCurso
from .api_serializers import CursoExternoSerializer
from .views import generate_ai_explanation, generate_ai_tips

class CalculatorsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        tab = request.data.get('tab', 'savings')
        result = None
        ai_explanation = None

        if tab == "savings":
            try:
                initial = float(request.data.get("initial", 0))
                monthly = float(request.data.get("monthly", 0))
                rate = float(request.data.get("rate", 0)) / 100
                years = int(request.data.get("years", 0))
                months = years * 12
                
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
                
                ai_explanation = generate_ai_explanation(result, tab)
                
            except Exception as e:
                return Response({"error": "Error en los valores ingresados"}, status=status.HTTP_400_BAD_REQUEST)
        
        elif tab == "loan":
            try:
                amount = float(request.data.get("amount", 0))
                rate = float(request.data.get("rate", 0)) / 100
                years = int(request.data.get("years", 0))
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
                
                ai_explanation = generate_ai_explanation(result, tab)
                
            except Exception as e:
                return Response({"error": "Error en los valores ingresados"}, status=status.HTTP_400_BAD_REQUEST)
        
        elif tab == "budget":
            try:
                income = float(request.data.get("income", 0))
                needs = float(request.data.get("needs", 0))
                wants = float(request.data.get("wants", 0))
                savings = float(request.data.get("savings", 0))
                
                total_expenses = needs + wants + savings
                remaining = income - total_expenses
                
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
                
                ai_explanation = generate_ai_explanation(result, tab)
                
            except Exception as e:
                return Response({"error": "Error en los valores ingresados"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'tab': tab,
            'result': result,
            'ai_explanation': ai_explanation
        })

class CoursesListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CursoExternoSerializer
    queryset = CursoExterno.objects.all()

class ToggleFavoritoCursoAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, curso_id):
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
        
        return Response({
            'success': True,
            'es_favorito': es_favorito
        })

class FinancialTipsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tab = request.query_params.get('tab', 'savings')
        ai_enabled = request.query_params.get('ai', 'false').lower() == 'true'

        class TipObject:
            def __init__(self, categoria, titulo, descripcion, prioridad, es_ai=False, link_externo=None, tip_id=None):
                self.id = tip_id or f"{categoria}_{hash(titulo) % 1000}"
                self.categoria = categoria
                self.titulo = titulo
                self.descripcion = descripcion
                self.prioridad = prioridad
                self.es_ai = es_ai
                self.link_externo = link_externo

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

        tips_data = consejos_base.get(tab, consejos_base['savings'])
        tips_list = []

        for tip in tips_data:
            tips_list.append({
                'id': tip.id,
                'categoria': tip.categoria,
                'titulo': tip.titulo,
                'descripcion': tip.descripcion,
                'prioridad': tip.prioridad,
                'es_ai': tip.es_ai,
                'link_externo': tip.link_externo,
            })

        if ai_enabled:
            try:
                ai_tips = generate_ai_tips(tab)
                for tip in ai_tips:
                    tips_list.append({
                        'id': tip.id,
                        'categoria': tip.categoria,
                        'titulo': tip.titulo,
                        'descripcion': tip.descripcion,
                        'prioridad': tip.prioridad,
                        'es_ai': tip.es_ai,
                        'link_externo': tip.link_externo,
                    })
            except Exception as e:
                pass

        return Response({
            'tips': tips_list,
            'current_tab': tab,
            'ai_enabled': ai_enabled
        })

class AIChatAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user_message = request.data.get('message', '')
        if not user_message:
            return Response({'error': 'Mensaje no proveído'}, status=status.HTTP_400_BAD_REQUEST)

        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)

        prompt = f"""
        Eres un asistente financiero experto y amigable. El usuario te pregunta: "{user_message}"
        
        Responde de manera útil, práctica y conversacional. Puedes hablar de cualquier tema financiero sin restricciones.
        Si no es sobre finanzas, redirige amablemente hacia temas financieros.
        
        Sé específico, da ejemplos prácticos y mantén un tono amigable.
        """

        models = ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-pro']
        for model_name in models:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return Response({
                    'success': True,
                    'response': response.text,
                    'model': model_name
                })
            except Exception as e:
                continue

        return Response({'error': 'No se pudo conectar con la IA. Intenta de nuevo.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
