"""
Tests unitarios para los servicios de la aplicación educacion_financiera
Ubicación: test/test_educacion_financiera_services.py
"""

from django.test import TestCase
from unittest.mock import patch, MagicMock
from educacion_financiera.services import (
    generate_ai_explanation,
    generate_ai_tips,
    process_ai_chat
)


class EducacionFinancieraServicesTestCase(TestCase):
    
    @patch('educacion_financiera.services.genai.GenerativeModel')
    def test_generate_ai_explanation_savings(self, mock_generative_model):
        """Valida la generación de explicaciones de ahorro usando IA (Gemini mock)"""
        # Configurar Mock
        mock_model_instance = MagicMock()
        mock_generative_model.return_value = mock_model_instance
        
        mock_response = MagicMock()
        mock_response.text = "Explicación de ahorro de prueba."
        mock_model_instance.generate_content.return_value = mock_response

        result = {
            'future_value': 12000.00,
            'total_contributed': 10000.00,
            'interest_earned': 2000.00
        }

        explanation = generate_ai_explanation(result, 'savings')
        
        self.assertEqual(explanation, "Explicación de ahorro de prueba.")
        # Verificar que se llamó al modelo
        mock_generative_model.assert_called_with('gemini-2.0-flash')
        mock_model_instance.generate_content.assert_called()

    @patch('educacion_financiera.services.genai.GenerativeModel')
    def test_generate_ai_explanation_loan(self, mock_generative_model):
        """Valida la generación de explicaciones de préstamos"""
        mock_model_instance = MagicMock()
        mock_generative_model.return_value = mock_model_instance
        mock_response = MagicMock()
        mock_response.text = "Explicación de préstamo."
        mock_model_instance.generate_content.return_value = mock_response

        result = {
            'monthly_payment': 500.00,
            'total_payment': 6000.00,
            'total_interest': 1000.00
        }

        explanation = generate_ai_explanation(result, 'loan')
        self.assertEqual(explanation, "Explicación de préstamo.")

    @patch('educacion_financiera.services.genai.GenerativeModel')
    def test_generate_ai_explanation_budget(self, mock_generative_model):
        """Valida la generación de explicaciones de presupuesto"""
        mock_model_instance = MagicMock()
        mock_generative_model.return_value = mock_model_instance
        mock_response = MagicMock()
        mock_response.text = "Explicación de presupuesto."
        mock_model_instance.generate_content.return_value = mock_response

        result = {
            'income': 3000.00,
            'total_expenses': 2000.00,
            'remaining': 1000.00
        }

        explanation = generate_ai_explanation(result, 'budget')
        self.assertEqual(explanation, "Explicación de presupuesto.")

    @patch('educacion_financiera.services.genai.GenerativeModel')
    def test_generate_ai_explanation_retirement(self, mock_generative_model):
        """Valida la generación de explicaciones de jubilación"""
        mock_model_instance = MagicMock()
        mock_generative_model.return_value = mock_model_instance
        mock_response = MagicMock()
        mock_response.text = "Explicación de jubilación."
        mock_model_instance.generate_content.return_value = mock_response

        result = {
            'total_at_retirement': 150000.00,
            'monthly_income': 800.00,
            'years_to_retirement': 25
        }

        explanation = generate_ai_explanation(result, 'retirement')
        self.assertEqual(explanation, "Explicación de jubilación.")

    @patch('educacion_financiera.services.genai.GenerativeModel')
    def test_generate_ai_explanation_investment(self, mock_generative_model):
        """Valida la generación de explicaciones de inversión"""
        mock_model_instance = MagicMock()
        mock_generative_model.return_value = mock_model_instance
        mock_response = MagicMock()
        mock_response.text = "Explicación de inversión."
        mock_model_instance.generate_content.return_value = mock_response

        result = {
            'final_value': 25000.00,
            'total_profit': 5000.00,
            'roi_percentage': 25.0,
            'real_value': 22000.00
        }

        explanation = generate_ai_explanation(result, 'investment')
        self.assertEqual(explanation, "Explicación de inversión.")

    @patch('educacion_financiera.services.genai.GenerativeModel')
    def test_generate_ai_explanation_failure(self, mock_generative_model):
        """Valida que devuelva un mensaje amigable por defecto si la API de Gemini falla"""
        mock_model_instance = MagicMock()
        mock_generative_model.return_value = mock_model_instance
        
        # Simular error lanzando excepción
        mock_model_instance.generate_content.side_effect = Exception("API connection timed out")

        result = {'future_value': 1000}
        explanation = generate_ai_explanation(result, 'savings')
        
        # Debe recuperar el mensaje por defecto amigable
        self.assertEqual(explanation, "No se pudo generar explicación con IA en este momento.")

    @patch('educacion_financiera.services.genai.GenerativeModel')
    def test_generate_ai_tips_success_json_codeblock(self, mock_generative_model):
        """Valida la generación de tips estructurados parseando un bloque de código Markdown JSON"""
        mock_model_instance = MagicMock()
        mock_generative_model.return_value = mock_model_instance
        
        mock_response = MagicMock()
        # Formato común que devuelve la IA con comillas e inicio json
        mock_response.text = """
        ```json
        [
          {
            "titulo": "Ahorra en compras",
            "descripcion": "Compara precios antes de comprar.",
            "prioridad": "alta"
          }
        ]
        ```
        """
        mock_model_instance.generate_content.return_value = mock_response

        tips = generate_ai_tips('savings')
        
        self.assertEqual(len(tips), 1)
        tip = tips[0]
        self.assertEqual(tip.titulo, "Ahorra en compras")
        self.assertEqual(tip.descripcion, "Compara precios antes de comprar.")
        self.assertEqual(tip.prioridad, "alta")
        self.assertTrue(tip.es_ai)

    @patch('educacion_financiera.services.genai.GenerativeModel')
    def test_generate_ai_tips_success_raw_json(self, mock_generative_model):
        """Valida la generación de tips con JSON plano"""
        mock_model_instance = MagicMock()
        mock_generative_model.return_value = mock_model_instance
        
        mock_response = MagicMock()
        mock_response.text = '[{"titulo": "Inversión", "descripcion": "Diversifica", "prioridad": "media"}]'
        mock_model_instance.generate_content.return_value = mock_response

        tips = generate_ai_tips('investment')
        self.assertEqual(len(tips), 1)
        self.assertEqual(tips[0].titulo, "Inversión")
        self.assertEqual(tips[0].prioridad, "media")

    @patch('educacion_financiera.services.genai.GenerativeModel')
    def test_generate_ai_tips_failure(self, mock_generative_model):
        """Valida que devuelva una lista vacía si hay un error en la API o el JSON es inválido"""
        mock_model_instance = MagicMock()
        mock_generative_model.return_value = mock_model_instance
        
        mock_response = MagicMock()
        mock_response.text = "Error interno o texto no estructurado en JSON"
        mock_model_instance.generate_content.return_value = mock_response

        tips = generate_ai_tips('savings')
        self.assertEqual(tips, [])

    @patch('educacion_financiera.services.genai.GenerativeModel')
    def test_process_ai_chat_success(self, mock_generative_model):
        """Valida procesamiento de mensajes en chat conversacional de finanzas"""
        mock_model_instance = MagicMock()
        mock_generative_model.return_value = mock_model_instance
        
        mock_response = MagicMock()
        mock_response.text = "Hola, el presupuesto es importante."
        mock_model_instance.generate_content.return_value = mock_response

        chat_res = process_ai_chat("¿Cómo hago un presupuesto?")
        
        self.assertTrue(chat_res['success'])
        self.assertEqual(chat_res['response'], "Hola, el presupuesto es importante.")
        self.assertEqual(chat_res['model'], "gemini-2.0-flash")

    @patch('educacion_financiera.services.genai.GenerativeModel')
    def test_process_ai_chat_failure(self, mock_generative_model):
        """Valida que el chat capture excepciones y devuelva un mensaje estructurado de error"""
        mock_model_instance = MagicMock()
        mock_generative_model.return_value = mock_model_instance
        mock_model_instance.generate_content.side_effect = Exception("General connection issue")

        chat_res = process_ai_chat("Hola")
        
        self.assertFalse(chat_res['success'])
        self.assertIn("error", chat_res)
        self.assertIn("No se pudo conectar", chat_res['error'])
