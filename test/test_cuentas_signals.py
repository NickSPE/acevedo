"""
Tests unitarios para la señal de post_migrate de cuentas
Ubicación: test/test_cuentas_signals.py
"""

from django.test import TestCase
from unittest.mock import MagicMock
from cuentas.models import Moneda
from cuentas.signals import crear_monedas_por_defecto


class CuentasSignalsTestCase(TestCase):
    def setUp(self):
        # Limpiar todas las monedas existentes para asegurar un estado limpio
        Moneda.objects.all().delete()

    def test_crear_monedas_por_defecto_success(self):
        """Valida que cree exitosamente las monedas por defecto al recibir la señal del emisor 'cuentas'"""
        self.assertEqual(Moneda.objects.count(), 0)

        # Crear un emisor mock que represente la aplicación cuentas
        mock_sender = MagicMock()
        mock_sender.name = "cuentas"

        # Invocar la función receptora manualmente
        crear_monedas_por_defecto(mock_sender)

        # Deben haberse creado las 3 monedas
        self.assertEqual(Moneda.objects.count(), 3)
        self.assertTrue(Moneda.objects.filter(codigo="USD").exists())
        self.assertTrue(Moneda.objects.filter(codigo="PEN").exists())
        self.assertTrue(Moneda.objects.filter(codigo="EUR").exists())

        # Probar re-ejecución (get_or_create no debe duplicar ni lanzar error)
        crear_monedas_por_defecto(mock_sender)
        self.assertEqual(Moneda.objects.count(), 3)

    def test_crear_monedas_por_defecto_other_sender(self):
        """Valida que no haga nada si el emisor de la señal no es de la aplicación 'cuentas'"""
        self.assertEqual(Moneda.objects.count(), 0)

        # Crear un emisor de otra app
        mock_sender = MagicMock()
        mock_sender.name = "otra_aplicacion"

        crear_monedas_por_defecto(mock_sender)

        # No debe haber creado monedas
        self.assertEqual(Moneda.objects.count(), 0)
