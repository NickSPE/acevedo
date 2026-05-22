"""
Tests unitarios para los servicios de la aplicación cuentas
Ubicación: test/test_cuentas_services.py
"""

from django.test import TestCase
from decimal import Decimal
from django.contrib.auth import get_user_model
from cuentas.models import Moneda, Cuenta, SubCuenta, TransferenciaSubCuenta, TransferenciaCuentaPrincipal
from cuentas.services import (
    actualizar_perfil_usuario,
    actualizar_contacto_usuario,
    cambiar_password_usuario,
    cambiar_pin_usuario,
    procesar_transferencia_entre_subcuentas,
    procesar_deposito_subcuenta,
    procesar_retiro_subcuenta,
    procesar_transferencia_a_principal
)

Usuario = get_user_model()


class CuentasServicesTestCase(TestCase):
    def setUp(self):
        # Crear moneda de prueba
        self.moneda = Moneda.objects.create(
            codigo='PEN',
            nombre='Soles',
            simbolo='S/.'
        )
        
        # Crear usuario de prueba
        self.usuario = Usuario.objects.create_user(
            correo='test_services@test.com',
            password='Password123!',
            nombres='Juan',
            apellido_paterno='Perez',
            apellido_materno='Gomez',
            documento_identidad='87654321',
            telefono=987654321,
            id_moneda=self.moneda
        )
        # Asignar PIN inicial
        self.usuario.pin_acceso_rapido = 1234
        self.usuario.save()

        # Crear cuenta principal
        self.cuenta = Cuenta.objects.create(
            nombre='Cuenta Ahorro Principal',
            descripcion='Cuenta para ahorros generales',
            saldo_cuenta=Decimal('1000.00'),
            id_usuario=self.usuario
        )

        # Crear subcuentas de prueba
        # 1. Subcuenta personal (vinculada a cuenta principal)
        self.subcuenta_personal_1 = SubCuenta.objects.create(
            nombre='Viaje Cusco',
            descripcion='Ahorro para vacaciones',
            saldo=Decimal('200.00'),
            tipo='viajes',
            id_cuenta=self.cuenta
        )
        
        self.subcuenta_personal_2 = SubCuenta.objects.create(
            nombre='Curso Python',
            descripcion='Educacion',
            saldo=Decimal('100.00'),
            tipo='educacion',
            id_cuenta=self.cuenta
        )

        # 2. Subcuenta de negocio (independiente, sin cuenta principal)
        self.subcuenta_negocio = SubCuenta.objects.create(
            nombre='Tienda de Ropa Online',
            descripcion='Negocio independiente',
            saldo=Decimal('500.00'),
            tipo='tienda_online',
            propietario=self.usuario
        )

    def test_actualizar_perfil_usuario(self):
        """Valida la actualización de datos personales del usuario"""
        actualizar_perfil_usuario(
            usuario=self.usuario,
            nombres='Carlos',
            apellido_paterno='Sanchez',
            apellido_materno='Ruiz',
            pais='Perú'
        )
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.nombres, 'Carlos')
        self.assertEqual(self.usuario.apellido_paterno, 'Sanchez')
        self.assertEqual(self.usuario.apellido_materno, 'Ruiz')
        self.assertEqual(self.usuario.pais, 'Perú')

    def test_actualizar_contacto_usuario(self):
        """Valida la actualización de contacto (correo y opcionalmente teléfono)"""
        # Actualización con teléfono
        actualizar_contacto_usuario(
            usuario=self.usuario,
            email='carlos.contacto@test.com',
            telefono=911111111
        )
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.correo, 'carlos.contacto@test.com')
        self.assertEqual(self.usuario.telefono, 911111111)

        # Actualización sin teléfono (mantiene el anterior)
        actualizar_contacto_usuario(
            usuario=self.usuario,
            email='carlos.nuevo@test.com'
        )
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.correo, 'carlos.nuevo@test.com')
        self.assertEqual(self.usuario.telefono, 911111111)

    def test_cambiar_password_usuario_success(self):
        """Valida cambio de contraseña con contraseña actual correcta"""
        success, msg = cambiar_password_usuario(
            usuario=self.usuario,
            actual_password='Password123!',
            new_password='NewPassword456!'
        )
        self.assertTrue(success)
        self.assertIn("exitosamente", msg)
        self.assertTrue(self.usuario.check_password('NewPassword456!'))

    def test_cambiar_password_usuario_incorrect_password(self):
        """Valida que falle el cambio de contraseña si la clave actual es incorrecta"""
        success, msg = cambiar_password_usuario(
            usuario=self.usuario,
            actual_password='WrongPassword!',
            new_password='NewPassword456!'
        )
        self.assertFalse(success)
        self.assertIn("incorrecta", msg)
        self.assertFalse(self.usuario.check_password('NewPassword456!'))

    def test_cambiar_pin_usuario_success(self):
        """Valida cambio exitoso del PIN de acceso rápido"""
        success, msg = cambiar_pin_usuario(
            usuario=self.usuario,
            current_pin='1234',
            new_pin='5678'
        )
        self.assertTrue(success)
        self.assertEqual(self.usuario.pin_acceso_rapido, '5678')

    def test_cambiar_pin_usuario_incorrect_pin(self):
        """Valida que falle el cambio de PIN si el PIN actual no coincide"""
        success, msg = cambiar_pin_usuario(
            usuario=self.usuario,
            current_pin='9999',
            new_pin='5678'
        )
        self.assertFalse(success)
        self.assertIn("incorrecto", msg)
        self.assertEqual(self.usuario.pin_acceso_rapido, 1234)

    def test_procesar_transferencia_entre_subcuentas_success(self):
        """Valida transferencia exitosa entre dos subcuentas"""
        saldo_orig = self.subcuenta_personal_1.saldo
        saldo_dest = self.subcuenta_personal_2.saldo
        monto = Decimal('50.00')

        success, msg = procesar_transferencia_entre_subcuentas(
            subcuenta_origen=self.subcuenta_personal_1,
            subcuenta_destino=self.subcuenta_personal_2,
            monto=monto,
            usuario=self.usuario,
            descripcion="Pago de prueba"
        )
        
        self.assertTrue(success)
        self.subcuenta_personal_1.refresh_from_db()
        self.subcuenta_personal_2.refresh_from_db()
        
        self.assertEqual(self.subcuenta_personal_1.saldo, saldo_orig - monto)
        self.assertEqual(self.subcuenta_personal_2.saldo, saldo_dest + monto)
        
        # Verificar que se creó el registro de transferencia
        self.assertTrue(TransferenciaSubCuenta.objects.filter(
            subcuenta_origen=self.subcuenta_personal_1,
            subcuenta_destino=self.subcuenta_personal_2,
            monto=monto,
            id_usuario=self.usuario
        ).exists())

    def test_procesar_transferencia_entre_subcuentas_insufficient_funds(self):
        """Valida rechazo de transferencia entre subcuentas por fondos insuficientes"""
        saldo_orig = self.subcuenta_personal_1.saldo
        monto = Decimal('300.00') # Excede el saldo de 200

        success, msg = procesar_transferencia_entre_subcuentas(
            subcuenta_origen=self.subcuenta_personal_1,
            subcuenta_destino=self.subcuenta_personal_2,
            monto=monto,
            usuario=self.usuario
        )
        
        self.assertFalse(success)
        self.assertIn("insuficiente", msg)
        self.subcuenta_personal_1.refresh_from_db()
        self.assertEqual(self.subcuenta_personal_1.saldo, saldo_orig)

    def test_procesar_deposito_subcuenta_negocio(self):
        """Valida depósito directo a una subcuenta comercial/de negocio"""
        saldo_orig = self.subcuenta_negocio.saldo
        monto = Decimal('150.00')

        success, msg = procesar_deposito_subcuenta(
            subcuenta=self.subcuenta_negocio,
            monto=monto,
            usuario=self.usuario
        )
        
        self.assertTrue(success)
        self.subcuenta_negocio.refresh_from_db()
        self.assertEqual(self.subcuenta_negocio.saldo, saldo_orig + monto)

    def test_procesar_deposito_subcuenta_personal_success(self):
        """Valida depósito en subcuenta personal (transfiere desde cuenta principal)"""
        saldo_cuenta_orig = self.cuenta.saldo_cuenta
        saldo_sub_orig = self.subcuenta_personal_1.saldo
        monto = Decimal('100.00')

        success, msg = procesar_deposito_subcuenta(
            subcuenta=self.subcuenta_personal_1,
            monto=monto,
            usuario=self.usuario
        )
        
        self.assertTrue(success)
        self.cuenta.refresh_from_db()
        self.subcuenta_personal_1.refresh_from_db()
        
        self.assertEqual(self.cuenta.saldo_cuenta, saldo_cuenta_orig - monto)
        self.assertEqual(self.subcuenta_personal_1.saldo, saldo_sub_orig + monto)

    def test_procesar_deposito_subcuenta_personal_insufficient_funds(self):
        """Valida que falle el depósito si la cuenta principal no tiene saldo disponible suficiente"""
        # Saldo cuenta: 1000. Subcuentas ocupan: 300. Disponible: 700.
        # Intentamos depositar 800
        monto = Decimal('800.00')

        success, msg = procesar_deposito_subcuenta(
            subcuenta=self.subcuenta_personal_1,
            monto=monto,
            usuario=self.usuario
        )
        
        self.assertFalse(success)
        self.assertIn("Saldo insuficiente", msg)

    def test_procesar_retiro_subcuenta_negocio(self):
        """Valida retiro directo de una subcuenta de negocio"""
        saldo_orig = self.subcuenta_negocio.saldo
        monto = Decimal('50.00')

        success, msg = procesar_retiro_subcuenta(
            subcuenta=self.subcuenta_negocio,
            monto=monto,
            usuario=self.usuario
        )
        
        self.assertTrue(success)
        self.subcuenta_negocio.refresh_from_db()
        self.assertEqual(self.subcuenta_negocio.saldo, saldo_orig - monto)

    def test_procesar_retiro_subcuenta_personal(self):
        """Valida retiro de subcuenta personal (transfiere de regreso a cuenta principal)"""
        saldo_cuenta_orig = self.cuenta.saldo_cuenta
        saldo_sub_orig = self.subcuenta_personal_1.saldo
        monto = Decimal('80.00')

        success, msg = procesar_retiro_subcuenta(
            subcuenta=self.subcuenta_personal_1,
            monto=monto,
            usuario=self.usuario,
            descripcion="Retiro para emergencias"
        )
        
        self.assertTrue(success)
        self.cuenta.refresh_from_db()
        self.subcuenta_personal_1.refresh_from_db()
        
        self.assertEqual(self.cuenta.saldo_cuenta, saldo_cuenta_orig + monto)
        self.assertEqual(self.subcuenta_personal_1.saldo, saldo_sub_orig - monto)
        
        # Verificar registro de transferencia
        self.assertTrue(TransferenciaCuentaPrincipal.objects.filter(
            subcuenta=self.subcuenta_personal_1,
            cuenta_destino=self.cuenta,
            monto=monto,
            tipo='deposito',
            id_usuario=self.usuario
        ).exists())

    def test_procesar_retiro_subcuenta_insufficient_funds(self):
        """Valida que falle el retiro de subcuenta si el saldo de la subcuenta es insuficiente"""
        monto = Decimal('250.00') # Saldo es de 200

        success, msg = procesar_retiro_subcuenta(
            subcuenta=self.subcuenta_personal_1,
            monto=monto,
            usuario=self.usuario
        )
        
        self.assertFalse(success)
        self.assertIn("insuficiente", msg)

    def test_procesar_transferencia_a_principal_deposito_success(self):
        """Valida transferencia tipo deposito (de subcuenta a principal)"""
        saldo_cuenta_orig = self.cuenta.saldo_cuenta
        saldo_sub_orig = self.subcuenta_personal_1.saldo
        monto = Decimal('60.00')

        success, msg = procesar_transferencia_a_principal(
            subcuenta=self.subcuenta_personal_1,
            cuenta_principal=self.cuenta,
            monto=monto,
            usuario=self.usuario,
            tipo='deposito',
            descripcion="Retorno"
        )
        
        self.assertTrue(success)
        self.cuenta.refresh_from_db()
        self.subcuenta_personal_1.refresh_from_db()
        
        self.assertEqual(self.cuenta.saldo_cuenta, saldo_cuenta_orig + monto)
        self.assertEqual(self.subcuenta_personal_1.saldo, saldo_sub_orig - monto)
        self.assertIn("desde", msg)

    def test_procesar_transferencia_a_principal_retiro_success(self):
        """Valida transferencia tipo retiro (de principal a subcuenta)"""
        saldo_cuenta_orig = self.cuenta.saldo_cuenta
        saldo_sub_orig = self.subcuenta_personal_1.saldo
        monto = Decimal('120.00')

        success, msg = procesar_transferencia_a_principal(
            subcuenta=self.subcuenta_personal_1,
            cuenta_principal=self.cuenta,
            monto=monto,
            usuario=self.usuario,
            tipo='retiro',
            descripcion="Aporte"
        )
        
        self.assertTrue(success)
        self.cuenta.refresh_from_db()
        self.subcuenta_personal_1.refresh_from_db()
        
        self.assertEqual(self.cuenta.saldo_cuenta, saldo_cuenta_orig - monto)
        self.assertEqual(self.subcuenta_personal_1.saldo, saldo_sub_orig + monto)
        self.assertIn("desde tu cuenta principal", msg)

    def test_procesar_transferencia_a_principal_invalid_type(self):
        """Valida rechazo de transferencia ante un tipo inválido"""
        success, msg = procesar_transferencia_a_principal(
            subcuenta=self.subcuenta_personal_1,
            cuenta_principal=self.cuenta,
            monto=Decimal('10.00'),
            usuario=self.usuario,
            tipo='invalido'
        )
        self.assertFalse(success)
        self.assertIn("inválido", msg)

    def test_procesar_transferencia_a_principal_insufficient_funds(self):
        """Valida rechazo de transferencia por fondos insuficientes en origen según el tipo"""
        # Caso depósito: saldo subcuenta insuficiente
        success, msg = procesar_transferencia_a_principal(
            subcuenta=self.subcuenta_personal_1,
            cuenta_principal=self.cuenta,
            monto=Decimal('500.00'), # Excede los 200 de saldo de la subcuenta
            usuario=self.usuario,
            tipo='deposito'
        )
        self.assertFalse(success)
        self.assertIn("insuficiente", msg)

        # Caso retiro: disponible en cuenta principal insuficiente
        # Disponible actual: 1000 - 300 = 700. Intentamos retirar 800
        success, msg = procesar_transferencia_a_principal(
            subcuenta=self.subcuenta_personal_1,
            cuenta_principal=self.cuenta,
            monto=Decimal('800.00'),
            usuario=self.usuario,
            tipo='retiro'
        )
        self.assertFalse(success)
        self.assertIn("insuficiente", msg)
