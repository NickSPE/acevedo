"""
Tests unitarios para las utilidades de la aplicación cuentas
Ubicación: test/test_cuentas_utils.py
"""

from django.utils import timezone
from django.test import TestCase
from decimal import Decimal
from django.contrib.auth import get_user_model
from cuentas.models import Moneda, Cuenta, SubCuenta, TransferenciaSubCuenta
from gestion_financiera_basica.models import Movimiento
from cuentas.utils import (
    obtener_cuentas_usuario,
    obtener_estadisticas_subcuentas,
    obtener_balance_total,
    obtener_cuentas_con_subcuentas,
    obtener_subcuentas_independientes,
    obtener_transferencias_recientes,
    es_subcuenta_negocio
)

Usuario = get_user_model()


class CuentasUtilsTestCase(TestCase):
    def setUp(self):
        # Crear moneda de prueba
        self.moneda = Moneda.objects.create(
            codigo='PEN',
            nombre='Soles',
            simbolo='S/.'
        )

        # Crear usuario de prueba
        self.usuario = Usuario.objects.create_user(
            correo='test_utils@test.com',
            password='Password123!',
            nombres='Juan',
            apellido_paterno='Perez',
            apellido_materno='Gomez',
            documento_identidad='87654321',
            telefono=987654321,
            id_moneda=self.moneda
        )

        # Crear cuenta principal
        self.cuenta = Cuenta.objects.create(
            nombre='Cuenta General',
            descripcion='Cuenta principal',
            saldo_cuenta=Decimal('2000.00'),
            id_usuario=self.usuario
        )

        # Crear subcuentas vinculadas (personales)
        self.sub_vinculada_1 = SubCuenta.objects.create(
            nombre='Fondo Emergencia',
            saldo=Decimal('300.00'),
            tipo='emergencia',
            id_cuenta=self.cuenta
        )

        self.sub_vinculada_2 = SubCuenta.objects.create(
            nombre='Vacaciones Cusco',
            saldo=Decimal('150.00'),
            tipo='viajes',
            id_cuenta=self.cuenta,
            activa=False # Subcuenta inactiva para probar filtros
        )

        # Crear subcuentas independientes (de negocio)
        self.sub_independiente_1 = SubCuenta.objects.create(
            nombre='Tienda Ropa',
            saldo=Decimal('800.00'),
            tipo='tienda_online',
            propietario=self.usuario
        )

        self.sub_independiente_2 = SubCuenta.objects.create(
            nombre='Consultoría TI',
            saldo=Decimal('400.00'),
            tipo='consultoria',
            propietario=self.usuario,
            activa=False # Subcuenta inactiva
        )

    def test_obtener_cuentas_usuario(self):
        """Valida que se filtren correctamente las cuentas del usuario"""
        cuentas = obtener_cuentas_usuario(self.usuario)
        self.assertEqual(cuentas.count(), 1)
        self.assertEqual(cuentas.first(), self.cuenta)

    def test_obtener_estadisticas_subcuentas(self):
        """Valida los conteos y suma de saldos de las estadísticas de subcuentas"""
        stats = obtener_estadisticas_subcuentas(self.usuario)
        
        # Subcuentas activas:
        # Vinculadas activas: 1 (Fondo Emergencia - 300)
        # Independientes activas: 1 (Tienda Ropa - 800)
        self.assertEqual(stats['total_vinculadas'], 1)
        self.assertEqual(stats['total_independientes'], 1)
        self.assertEqual(stats['total'], 2)
        
        # Subcuentas inactivas:
        # Vinculadas inactivas: 1 (Vacaciones - 150)
        # Independientes inactivas: 1 (Consultoría - 400)
        self.assertEqual(stats['total_inactivas'], 2)

        # Saldos totales:
        # Vinculadas (todas): 300 + 150 = 450
        # Independientes (todas): 800 + 400 = 1200
        # Total: 1650
        self.assertEqual(stats['saldo_vinculadas'], Decimal('450.00'))
        self.assertEqual(stats['saldo_independientes'], Decimal('1200.00'))
        self.assertEqual(stats['saldo_total'], Decimal('1650.00'))

    def test_obtener_balance_total(self):
        """Valida el cálculo del balance total incorporando saldo inicial y movimientos"""
        # Saldo inicial cuenta: 2000.00
        # Crear movimientos (ingreso y egreso)
        Movimiento.objects.create(
            nombre="Salario",
            tipo="ingreso",
            monto=Decimal('1500.00'),
            fecha_movimiento=timezone.now(),
            id_cuenta=self.cuenta,
            id_usuario=self.usuario
        )

        Movimiento.objects.create(
            nombre="Pago Alquiler",
            tipo="egreso",
            monto=Decimal('600.00'),
            fecha_movimiento=timezone.now(),
            id_cuenta=self.cuenta,
            id_usuario=self.usuario
        )

        # Balance esperado: 2000.00 (inicial) + 1500.00 (ingreso) - 600.00 (egreso) = 2900.00
        balance = obtener_balance_total(self.usuario)
        self.assertEqual(balance, 2900.0)

    def test_obtener_cuentas_con_subcuentas(self):
        """Valida la estructura de datos que asocia cuentas con sus respectivas subcuentas"""
        cuentas_con_sub = obtener_cuentas_con_subcuentas(self.usuario)
        self.assertEqual(len(cuentas_con_sub), 1)
        
        item = cuentas_con_sub[0]
        self.assertEqual(item['cuenta'], self.cuenta)
        
        # Subcuentas activas e inactivas de la cuenta principal
        self.assertIn(self.sub_vinculada_1, item['subcuentas'])
        self.assertNotIn(self.sub_vinculada_2, item['subcuentas']) # es inactiva
        self.assertIn(self.sub_vinculada_2, item['subcuentas_inactivas'])
        
        # Saldo disponible esperado: 2000.00 - (300.00 + 150.00) = 1550.00
        self.assertEqual(item['saldo_disponible'], Decimal('1550.00'))

    def test_obtener_subcuentas_independientes(self):
        """Valida la clasificación de subcuentas independientes del usuario"""
        indep = obtener_subcuentas_independientes(self.usuario)
        
        self.assertIn(self.sub_independiente_1, indep['activas'])
        self.assertNotIn(self.sub_independiente_2, indep['activas'])
        
        self.assertIn(self.sub_independiente_2, indep['inactivas'])
        self.assertEqual(len(indep['todas']), 2)

    def test_obtener_transferencias_recientes(self):
        """Valida la consulta de transferencias recientes de subcuentas"""
        # Crear transferencia de prueba
        trans = TransferenciaSubCuenta.objects.create(
            subcuenta_origen=self.sub_independiente_1,
            subcuenta_destino=self.sub_vinculada_1,
            monto=Decimal('100.00'),
            id_usuario=self.usuario
        )

        recientes = obtener_transferencias_recientes(self.usuario)
        self.assertEqual(recientes.count(), 1)
        self.assertEqual(recientes.first(), trans)

    def test_es_subcuenta_negocio(self):
        """Valida la correcta lógica de discriminación comercial/negocio"""
        # Caso 1: Marcada explícitamente o por tipo comercial (Tienda Ropa es tienda_online, es_negocio = True)
        self.assertTrue(es_subcuenta_negocio(self.sub_independiente_1))

        # Caso 2: Subcuenta de uso personal tradicional (Fondo Emergencia)
        self.assertFalse(es_subcuenta_negocio(self.sub_vinculada_1))
