from django.test import TestCase
from django.contrib.auth import get_user_model
from cuentas.models import Moneda, Cuenta, SubCuenta
from cuentas.forms import (
    SubCuentaForm, TransferenciaSubCuentaForm, DepositoSubCuentaForm,
    RetiroSubCuentaForm, TransferenciaCuentaPrincipalForm
)

Usuario = get_user_model()


class SubCuentaFormTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='form_test@test.com', password='Password123!',
            nombres='Form', apellido_paterno='Test',
            apellido_materno='User', documento_identidad='12345678',
            telefono=987654321, id_moneda=self.moneda
        )
        self.cuenta = Cuenta.objects.create(
            nombre='Test Account', saldo_cuenta=1000.00, id_usuario=self.usuario
        )

    def test_subcuenta_form_valid(self):
        form = SubCuentaForm(data={
            'nombre': 'Test Sub',
            'tipo': 'ahorros',
        }, user=self.usuario)
        self.assertFalse(form.is_valid())

    def test_subcuenta_form_required_fields(self):
        form = SubCuentaForm(data={}, user=self.usuario)
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_subcuenta_form_valid_with_valid_tipo(self):
        form = SubCuentaForm(data={
            'nombre': 'Test',
            'tipo': 'emergencia',
            'descripcion': 'Optional description',
        }, user=self.usuario)
        self.assertTrue(form.is_valid(), form.errors)

    def test_subcuenta_form_init_sets_user(self):
        form = SubCuentaForm(user=self.usuario)
        self.assertEqual(form.user, self.usuario)


class TransferenciaSubCuentaFormTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='transf_form@test.com', password='Password123!',
            nombres='Transf', apellido_paterno='Form',
            apellido_materno='Test', documento_identidad='12345678',
            telefono=987654321, id_moneda=self.moneda
        )
        self.cuenta = Cuenta.objects.create(
            nombre='Account', saldo_cuenta=1000.00, id_usuario=self.usuario
        )
        self.sub1 = SubCuenta.objects.create(
            nombre='Source', saldo=500.00, tipo='ahorros', id_cuenta=self.cuenta
        )
        self.sub2 = SubCuenta.objects.create(
            nombre='Dest', saldo=100.00, tipo='emergencia', id_cuenta=self.cuenta
        )

    def test_transferencia_form_valid(self):
        form = TransferenciaSubCuentaForm(data={
            'subcuenta_origen': self.sub1.id,
            'subcuenta_destino': self.sub2.id,
            'monto': '50.00'
        }, user=self.usuario)
        self.assertTrue(form.is_valid())

    def test_transferencia_form_required_fields(self):
        form = TransferenciaSubCuentaForm(data={}, user=self.usuario)
        self.assertFalse(form.is_valid())
        self.assertIn('subcuenta_origen', form.errors)
        self.assertIn('subcuenta_destino', form.errors)
        self.assertIn('monto', form.errors)

    def test_transferencia_form_init_filters_subcuentas(self):
        form = TransferenciaSubCuentaForm(user=self.usuario)
        self.assertIsNotNone(form.fields['subcuenta_origen'].choices)


class DepositoSubCuentaFormTestCase(TestCase):
    def test_deposito_form_valid(self):
        form = DepositoSubCuentaForm(data={'monto': '100.00'})
        self.assertTrue(form.is_valid())

    def test_deposito_form_invalid_monto_empty(self):
        form = DepositoSubCuentaForm(data={})
        self.assertFalse(form.is_valid())

    def test_deposito_form_valid_monto_50(self):
        form = DepositoSubCuentaForm(data={'monto': '50.00'})
        self.assertTrue(form.is_valid())

    def test_deposito_form_optional_descripcion(self):
        form = DepositoSubCuentaForm(data={'monto': '50.00', 'descripcion': 'Test deposit'})
        self.assertTrue(form.is_valid())


class RetiroSubCuentaFormTestCase(TestCase):
    def test_retiro_form_valid(self):
        form = RetiroSubCuentaForm(data={'monto': '100.00'})
        self.assertTrue(form.is_valid())

    def test_retiro_form_invalid_monto_empty(self):
        form = RetiroSubCuentaForm(data={})
        self.assertFalse(form.is_valid())

    def test_retiro_form_optional_descripcion(self):
        form = RetiroSubCuentaForm(data={'monto': '50.00', 'descripcion': 'Test retiro'})
        self.assertTrue(form.is_valid())


class TransferenciaCuentaPrincipalFormTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='principal_form@test.com', password='Password123!',
            nombres='Principal', apellido_paterno='Form',
            apellido_materno='Test', documento_identidad='12345678',
            telefono=987654321, id_moneda=self.moneda
        )
        self.cuenta = Cuenta.objects.create(
            nombre='Main', saldo_cuenta=1000.00, id_usuario=self.usuario
        )
        self.subcuenta = SubCuenta.objects.create(
            nombre='Sub', saldo=500.00, tipo='ahorros', id_cuenta=self.cuenta
        )

    def test_transferencia_principal_form_valid(self):
        form = TransferenciaCuentaPrincipalForm(
            data={'tipo': 'deposito', 'monto': '100.00'},
            subcuenta=self.subcuenta
        )
        self.assertTrue(form.is_valid())

    def test_transferencia_principal_form_clean_monto_negative(self):
        form = TransferenciaCuentaPrincipalForm(
            data={'tipo': 'deposito', 'monto': '-10.00'},
            subcuenta=self.subcuenta
        )
        self.assertFalse(form.is_valid())

    def test_transferencia_principal_form_clean_monto_exceeds_balance(self):
        form = TransferenciaCuentaPrincipalForm(
            data={'tipo': 'deposito', 'monto': '1000.00'},
            subcuenta=self.subcuenta
        )
        self.assertFalse(form.is_valid())
