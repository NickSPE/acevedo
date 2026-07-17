"""
Tests unitarios para los servicios de la aplicación educacion_financiera
Ubicación: test/test_educacion_financiera_services.py
"""

import unittest
from django.test import TestCase
from unittest.mock import patch, MagicMock
from educacion_financiera.services import (
    generate_ai_explanation,
    generate_ai_tips,
    process_ai_chat
)


class EducacionFinancieraServicesTestCase(TestCase):
    
    def setUp(self):
        self._patcher = patch('educacion_financiera.services._genai_client')
        self.mock_client = self._patcher.start()
        self.mock_client.models.generate_content.return_value = MagicMock(text="")
    
    def tearDown(self):
        self._patcher.stop()

    def test_generate_ai_explanation_savings(self):
        """Valida la generación de explicaciones de ahorro usando IA (Gemini mock)"""
        self.mock_client.models.generate_content.return_value = MagicMock(
            text="Explicación de ahorro de prueba."
        )

        result = {
            'future_value': 12000.00,
            'total_contributed': 10000.00,
            'interest_earned': 2000.00
        }

        explanation = generate_ai_explanation(result, 'savings')
        
        self.assertEqual(explanation, "Explicación de ahorro de prueba.")
        self.mock_client.models.generate_content.assert_called_once_with(
            model='gemini-2.0-flash',
            contents=unittest.mock.ANY
        )

    def test_generate_ai_explanation_loan(self):
        """Valida la generación de explicaciones de préstamos"""
        self.mock_client.models.generate_content.return_value = MagicMock(
            text="Explicación de préstamo."
        )

        result = {
            'monthly_payment': 500.00,
            'total_payment': 6000.00,
            'total_interest': 1000.00
        }

        explanation = generate_ai_explanation(result, 'loan')
        self.assertEqual(explanation, "Explicación de préstamo.")

    def test_generate_ai_explanation_budget(self):
        """Valida la generación de explicaciones de presupuesto"""
        self.mock_client.models.generate_content.return_value = MagicMock(
            text="Explicación de presupuesto."
        )

        result = {
            'income': 3000.00,
            'total_expenses': 2000.00,
            'remaining': 1000.00
        }

        explanation = generate_ai_explanation(result, 'budget')
        self.assertEqual(explanation, "Explicación de presupuesto.")

    def test_generate_ai_explanation_retirement(self):
        """Valida la generación de explicaciones de jubilación"""
        self.mock_client.models.generate_content.return_value = MagicMock(
            text="Explicación de jubilación."
        )

        result = {
            'total_at_retirement': 150000.00,
            'monthly_income': 800.00,
            'years_to_retirement': 25
        }

        explanation = generate_ai_explanation(result, 'retirement')
        self.assertEqual(explanation, "Explicación de jubilación.")

    def test_generate_ai_explanation_investment(self):
        """Valida la generación de explicaciones de inversión"""
        self.mock_client.models.generate_content.return_value = MagicMock(
            text="Explicación de inversión."
        )

        result = {
            'final_value': 25000.00,
            'total_profit': 5000.00,
            'roi_percentage': 25.0,
            'real_value': 22000.00
        }

        explanation = generate_ai_explanation(result, 'investment')
        self.assertEqual(explanation, "Explicación de inversión.")

    def test_generate_ai_explanation_failure(self):
        """Valida que devuelva un mensaje amigable por defecto si la API de Gemini falla"""
        self.mock_client.models.generate_content.side_effect = Exception("API connection timed out")

        result = {'future_value': 1000}
        explanation = generate_ai_explanation(result, 'savings')
        
        self.assertEqual(explanation, "No se pudo generar explicación con IA en este momento.")

    def test_generate_ai_tips_success_json_codeblock(self):
        """Valida la generación de tips estructurados parseando un bloque de código Markdown JSON"""
        self.mock_client.models.generate_content.return_value = MagicMock(text="""
        ```json
        [
          {
            "titulo": "Ahorra en compras",
            "descripcion": "Compara precios antes de comprar.",
            "prioridad": "alta"
          }
        ]
        ```
        """)

        tips = generate_ai_tips('savings')
        
        self.assertEqual(len(tips), 1)
        tip = tips[0]
        self.assertEqual(tip.titulo, "Ahorra en compras")
        self.assertEqual(tip.descripcion, "Compara precios antes de comprar.")
        self.assertEqual(tip.prioridad, "alta")
        self.assertTrue(tip.es_ai)

    def test_generate_ai_tips_success_raw_json(self):
        """Valida la generación de tips con JSON plano"""
        self.mock_client.models.generate_content.return_value = MagicMock(
            text='[{"titulo": "Inversión", "descripcion": "Diversifica", "prioridad": "media"}]'
        )

        tips = generate_ai_tips('investment')
        self.assertEqual(len(tips), 1)
        self.assertEqual(tips[0].titulo, "Inversión")
        self.assertEqual(tips[0].prioridad, "media")

    def test_generate_ai_tips_failure(self):
        """Valida que devuelva una lista vacía si hay un error en la API o el JSON es inválido"""
        self.mock_client.models.generate_content.return_value = MagicMock(
            text="Error interno o texto no estructurado en JSON"
        )

        tips = generate_ai_tips('savings')
        self.assertEqual(tips, [])

    def test_process_ai_chat_success(self):
        """Valida procesamiento de mensajes en chat conversacional de finanzas"""
        self.mock_client.models.generate_content.return_value = MagicMock(
            text="Hola, el presupuesto es importante."
        )

        chat_res = process_ai_chat("¿Cómo hago un presupuesto?")
        
        self.assertTrue(chat_res['success'])
        self.assertEqual(chat_res['response'], "Hola, el presupuesto es importante.")
        self.assertEqual(chat_res['model'], "gemini-2.0-flash")

    def test_process_ai_chat_failure(self):
        """Valida que el chat capture excepciones y devuelva un mensaje estructurado de error"""
        self.mock_client.models.generate_content.side_effect = Exception("General connection issue")

        chat_res = process_ai_chat("Hola")
        
        self.assertFalse(chat_res['success'])
        self.assertIn("error", chat_res)
        self.assertIn("No se pudo conectar", chat_res['error'])
