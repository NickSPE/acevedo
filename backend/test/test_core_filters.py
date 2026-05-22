"""
Tests unitarios para los filtros y tags de plantilla de monedas
Ubicación: test/test_core_filters.py
"""

from django.test import TestCase
from decimal import Decimal
from django.contrib.auth import get_user_model
from cuentas.models import Moneda
from core.templatetags.currency_filters import (
    currency_symbol,
    format_currency,
    user_currency_symbol,
    format_money
)

Usuario = get_user_model()


class CurrencyFiltersTestCase(TestCase):
    def setUp(self):
        # Crear moneda de prueba
        self.moneda = Moneda.objects.create(
            codigo='PEN',
            nombre='Soles',
            simbolo='S/.'
        )

        # Crear usuario con moneda
        self.usuario = Usuario.objects.create_user(
            correo='test_filters@test.com',
            password='Password123!',
            nombres='Juan',
            apellido_paterno='Perez',
            documento_identidad='87654321',
            telefono=987654321,
            id_moneda=self.moneda
        )

    def test_currency_symbol_valid_user(self):
        """Valida que retorne el símbolo de la moneda asignada al usuario"""
        simbolo = currency_symbol(self.usuario)
        self.assertEqual(simbolo, "S/.")

    def test_currency_symbol_user_without_currency(self):
        """Valida que retorne el símbolo por defecto si el usuario no tiene moneda asignada"""
        class MockUserNoCurrency:
            id_moneda = None
        simbolo = currency_symbol(MockUserNoCurrency())
        self.assertEqual(simbolo, "$")

    def test_currency_symbol_none_user(self):
        """Valida que retorne el símbolo por defecto si el usuario es None"""
        simbolo = currency_symbol(None)
        self.assertEqual(simbolo, "$")

    def test_currency_symbol_exception(self):
        """Valida que retorne el símbolo por defecto si ocurre alguna excepción al evaluar"""
        # Objeto falso para forzar error o comportamiento anormal
        class FakeUser:
            @property
            def id_moneda(self):
                raise AttributeError("Error simulado")

        simbolo = currency_symbol(FakeUser())
        self.assertEqual(simbolo, "$")

    def test_format_currency_conversions(self):
        """Valida que formatee correctamente los montos pasados como int, float, str y Decimal"""
        # Caso 1: float con usuario con moneda
        val_float = format_currency(1234.56, self.usuario)
        self.assertEqual(val_float, "S/.1,234.56")

        # Caso 2: int sin usuario (usa default $)
        val_int = format_currency(500, None)
        self.assertEqual(val_int, "$500.00")

        # Caso 3: str
        val_str = format_currency("1000000", self.usuario)
        self.assertEqual(val_str, "S/.1,000,000.00")

        # Caso 4: Decimal
        val_decimal = format_currency(Decimal("99.99"), self.usuario)
        self.assertEqual(val_decimal, "S/.99.99")

    def test_format_currency_exception(self):
        """Valida que retorne el fallback formateado ante cualquier excepción de casteo"""
        res = format_currency("invalido", self.usuario)
        self.assertEqual(res, "$invalido")

    def test_user_currency_symbol_tag(self):
        """Valida el simple_tag para obtener el símbolo de moneda"""
        simbolo = user_currency_symbol(self.usuario)
        self.assertEqual(simbolo, "S/.")

        simbolo_sin = user_currency_symbol(None)
        self.assertEqual(simbolo_sin, "$")

    def test_format_money_tag(self):
        """Valida el simple_tag para formatear dinero"""
        res = format_money(150.5, self.usuario)
        self.assertEqual(res, "S/.150.50")

        res_sin = format_money(2500, None)
        self.assertEqual(res_sin, "$2,500.00")

        # Excepción
        res_error = format_money("invalido", None)
        self.assertEqual(res_error, "$invalido")
