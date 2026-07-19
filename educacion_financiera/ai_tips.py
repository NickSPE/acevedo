"""
Módulo para generar consejos financieros usando IA Gemini
"""
import os
from typing import List, Dict, Optional
import google.generativeai as genai


class FinancialTipsAI:
    """Generador de consejos financieros usando IA Gemini"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializar cliente de Gemini"""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
        except Exception as e:
            print(f"Error inicializando cliente Gemini: {e}")
            self.model = None
    
    @staticmethod
    def _generate_prompt(category: str, user_context: Optional[Dict] = None) -> str:
        """Generar prompt específico para cada categoría"""
        
        base_prompts = {
            "daily": """
            Genera 6 consejos financieros diarios prácticos y fáciles de implementar.
            Enfócate en hábitos cotidianos que mejoren la salud financiera.
            
            IMPORTANTE: Responde de manera estructurada y organizada.
            
            Para cada consejo usa este formato exacto:
            [Emoji] | [Título corto] | [Descripción práctica de 1-2 líneas]
            
            Ejemplo:
            💰 | Revisa gastos diarios | Anota todos tus gastos durante una semana para identificar fugas de dinero y patrones de consumo.
            
            Genera exactamente 6 consejos siguiendo este formato.
            """,
            
            "savings": """
            Genera 5 estrategias efectivas de ahorro personal de manera estructurada.
            Enfócate en métodos comprobados y técnicas psicológicas.
            
            Formato requerido para cada estrategia:
            [Emoji] | [Título] | [Descripción práctica y específica]
            
            Asegúrate de que cada consejo sea accionable y específico.
            """,
            
            "debt": """
            Genera 5 consejos estructurados para manejo inteligente de deudas.
            Incluye estrategias de pago, negociación y prevención.
            
            Formato requerido:
            [Emoji] | [Título] | [Descripción práctica con pasos específicos]
            
            Enfócate en soluciones realistas y aplicables.
            """,
            
            "investment": """
            Genera 5 consejos de inversión estructurados para principiantes.
            Enfócate en conceptos básicos, seguridad y diversificación.
            
            Formato requerido:
            [Emoji] | [Título] | [Descripción clara y educativa]
            
            Evita jerga técnica compleja y enfócate en lo fundamental.
            """,
            
            "personalized": """
            Genera consejos financieros personalizados y bien estructurados basados en:
            {user_info}
            
            Proporciona 5 consejos específicos y organizados para esta situación.
            
            Formato requerido:
            [Emoji] | [Título] | [Descripción personalizada y accionable]
            
            Asegúrate de que cada consejo sea relevante para el perfil del usuario.
            """
        }
        
        prompt = base_prompts.get(category, base_prompts["daily"])
        
        if category == "personalized" and user_context:
            user_info = f"""
            - Edad aproximada: {user_context.get('age_range', 'No especificada')}
            - Situación laboral: {user_context.get('employment', 'No especificada')}
            - Objetivos financieros: {user_context.get('goals', 'No especificados')}
            - Nivel de experiencia: {user_context.get('experience', 'Principiante')}
            """
            prompt = prompt.format(user_info=user_info)
        
        return prompt
    
    def generate_tips(self, category: str, user_context: Optional[Dict] = None) -> List[tuple]:
        """
        Generar consejos financieros usando IA
        
        Args:
            category: Categoría de consejos (daily, savings, debt, investment, personalized)
            user_context: Información del usuario para consejos personalizados
            Returns:
                Lista de tuplas (emoji, título, descripción)
        """
        if not self.model:
            return self._get_fallback_tips(category)
        
        try:
            prompt = self._generate_prompt(category, user_context)
            
            response = self.model.generate_content(prompt)
            
            # Procesar respuesta y convertir a formato esperado
            tips = self._parse_ai_response(response.text)
            
            # Si no se pudieron parsear, usar fallback
            if not tips:
                return self._get_fallback_tips(category)
                
            return tips
            
        except Exception as e:
            print(f"Error generando consejos con IA: {e}")
            return self._get_fallback_tips(category)
        
    @staticmethod
    def _parse_ai_response(response_text: str) -> List[tuple]:
        """Parsear respuesta de IA al formato esperado"""
        tips = []
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if '|' in line and len(line.split('|')) >= 3:
                parts = line.split('|')
                emoji = parts[0].strip()
                title = parts[1].strip()
                description = parts[2].strip()
                
                # Limpiar formato markdown si existe
                title = title.replace('*', '').replace('#', '').strip()
                description = description.replace('*', '').replace('#', '').strip()
                
                if emoji and title and description:
                    tips.append((emoji, title, description))
        
        return tips[:6]  # Máximo 6 consejos

    @staticmethod
    def _get_fallback_tips(category: str) -> List[tuple]:
        """Consejos de respaldo en caso de error con IA"""
        
        fallback_tips = {
            "daily": [
                ("📱", "App de Gastos", "Usa una app para registrar cada gasto y revisar patrones semanalmente."),
                ("💡", "Regla 24 Horas", "Espera 24 horas antes de compras no esenciales mayores a $50."),
                ("🏪", "Comparar Precios", "Compara precios en 3 tiendas antes de compras importantes."),
                ("💰", "Efectivo Semanal", "Usa efectivo para gastos variables y controla mejor tu presupuesto."),
                ("📊", "Revisión Nocturna", "Revisa tus gastos del día cada noche durante 5 minutos."),
                ("🎯", "Meta Diaria", "Establece un límite de gasto diario y apégate a él."),
            ],
            "savings": [
                ("🤖", "Ahorro Automático", "Configura transferencias automáticas el día de pago."),
                ("🏦", "Cuenta Separada", "Abre una cuenta de ahorros solo para emergencias."),
                ("💰", "Redondeo Inteligente", "Redondea compras y ahorra la diferencia."),
                ("📈", "Incremento Gradual", "Aumenta tu ahorro 1% cada mes."),
                ("🎁", "Ahorra Bonos", "Destina 50% de bonos/regalos monetarios al ahorro."),
            ],
            "debt": [
                ("❄️", "Método Avalancha", "Paga primero deudas con mayor tasa de interés."),
                ("⚡", "Método Bola de Nieve", "Paga primero la deuda más pequeña para motivación."),
                ("📞", "Negociar Intereses", "Llama para negociar tasas más bajas en tarjetas."),
                ("🚫", "Parar Nuevas Deudas", "No uses crédito mientras pagas deudas existentes."),
                ("📝", "Plan de Pagos", "Crea un calendario con fechas y montos específicos."),
            ],
            "investment": [
                ("🎯", "Diversificación", "No pongas todos los huevos en una canasta."),
                ("⏰", "Tiempo en Mercado", "El tiempo en el mercado supera al timing del mercado."),
                ("📚", "Educación Continua", "Invierte en tu educación financiera primero."),
                ("💵", "Fondo de Emergencia", "Ten 6 meses de gastos antes de invertir."),
                ("🐌", "Invierte Gradualmente", "Comienza con montos pequeños y aprende."),
            ],
        }
        
        return fallback_tips.get(category, fallback_tips["daily"])


# Instancia global del generador
ai_tips_generator = FinancialTipsAI()


def get_ai_tips(category: str, user_context: Optional[Dict] = None) -> List[tuple]:
    """
    Función helper para obtener consejos financieros
    
    Args:
        category: daily, savings, debt, investment, personalized
        user_context: Diccionario con información del usuario
        
    Returns:
        Lista de tuplas (emoji, título, descripción)
    """
    return ai_tips_generator.generate_tips(category, user_context)


def get_personalized_tips(user_age_range: str = None, 
                         employment_status: str = None,
                         financial_goals: str = None,
                         experience_level: str = None) -> List[tuple]:
    """
    Obtener consejos personalizados basados en información del usuario
    """
    user_context = {
        'age_range': user_age_range,
        'employment': employment_status, 
        'goals': financial_goals,
        'experience': experience_level
    }
    
    return get_ai_tips('personalized', user_context)
