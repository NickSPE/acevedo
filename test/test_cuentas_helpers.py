from django.test import TestCase
from django.contrib.auth import get_user_model
from cuentas.models import Moneda, Cuenta, SubCuenta
from cuentas.helpers import (
    validar_permisos_subcuenta, validar_permisos_ambas_subcuentas,
    validar_password, validar_pin_cambio
)

Usuario = get_user_model()


class ValidarPermisosSubCuentaTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='perm_test@test.com', password='Password123!',
            nombres='Perm', apellido_paterno='Test',
            apellido_materno='User', documento_identidad='12345678',
            telefono=987654321, id_moneda=self.moneda
        )
        self.otro_usuario = Usuario.objects.create_user(
            correo='other@test.com', password='Password123!',
            nombres='Other', apellido_paterno='User',
            apellido_materno='Test', documento_identidad='87654321',
            telefono=999999999, id_moneda=self.moneda
        )
        self.cuenta = Cuenta.objects.create(
            nombre='Main', saldo_cuenta=1000.00, id_usuario=self.usuario
        )

    def test_propietario_directo(self):
        sub = SubCuenta.objects.create(
            nombre='Owned', saldo=100, tipo='ahorros', propietario=self.usuario
        )
        self.assertTrue(validar_permisos_subcuenta(self.usuario, sub))
        self.assertFalse(validar_permisos_subcuenta(self.otro_usuario, sub))

    def test_propietario_por_cuenta(self):
        sub = SubCuenta.objects.create(
            nombre='Via Cuenta', saldo=100, tipo='ahorros', id_cuenta=self.cuenta
        )
        self.assertTrue(validar_permisos_subcuenta(self.usuario, sub))
        self.assertFalse(validar_permisos_subcuenta(self.otro_usuario, sub))

    def test_validar_permisos_ambas(self):
        sub1 = SubCuenta.objects.create(
            nombre='Sub1', saldo=100, tipo='ahorros', id_cuenta=self.cuenta
        )
        sub2 = SubCuenta.objects.create(
            nombre='Sub2', saldo=200, tipo='emergencia', id_cuenta=self.cuenta
        )
        self.assertTrue(validar_permisos_ambas_subcuentas(self.usuario, sub1, sub2))
        self.assertFalse(validar_permisos_ambas_subcuentas(self.otro_usuario, sub1, sub2))


class ValidarPasswordTestCase(TestCase):
    def test_valid_password(self):
        self.assertIsNone(validar_password('oldPass', 'NewPass123', 'NewPass123'))

    def test_empty_fields(self):
        self.assertIsNotNone(validar_password('', '', ''))

    def test_mismatch_passwords(self):
        self.assertIsNotNone(validar_password('old', 'NewPass123', 'DifferentPass'))

    def test_short_password(self):
        self.assertIsNotNone(validar_password('old', 'Short1', 'Short1'))

    def test_same_as_current(self):
        self.assertIsNotNone(validar_password('SamePass1', 'SamePass1', 'SamePass1'))


class ValidarPinCambioTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='pin_val@test.com', password='Password123!',
            nombres='Pin', apellido_paterno='Val',
            apellido_materno='Test', documento_identidad='12345678',
            telefono=987654321, id_moneda=self.moneda,
            pin_acceso_rapido='123456'
        )

    def test_valid_pin_change(self):
        result = validar_pin_cambio(self.usuario, '123456', '654321', '654321')
        self.assertIsNone(result)

    def test_empty_fields(self):
        result = validar_pin_cambio(self.usuario, '', '', '')
        self.assertIsNotNone(result)

    def test_non_digit_pin(self):
        result = validar_pin_cambio(self.usuario, 'abc123', '654321', '654321')
        self.assertIsNotNone(result)

    def test_mismatch_new_pins(self):
        result = validar_pin_cambio(self.usuario, '123456', '654321', '111111')
        self.assertIsNotNone(result)

    def test_same_as_current(self):
        result = validar_pin_cambio(self.usuario, '123456', '123456', '123456')
        self.assertIsNotNone(result)
