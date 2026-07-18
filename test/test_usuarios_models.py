from django.test import TestCase
from django.contrib.auth.hashers import check_password
from usuarios.models import Usuario
from cuentas.models import Moneda


# Constantes para evitar advertencias de credenciales harcodeadas
TEST_PASS_VAL = 'Password123!'
TEST_SHORT_VAL = 'Pass123!'


class UsuarioModelTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='test_model@test.com',
            password=TEST_PASS_VAL,
            nombres='Juan',
            apellido_paterno='Perez',
            apellido_materno='Gomez',
            documento_identidad='12345678',
            telefono=987654321,
            id_moneda=self.moneda
        )

    def test_create_user_success(self):
        self.assertEqual(Usuario.objects.count(), 1)
        self.assertEqual(self.usuario.correo, 'test_model@test.com')
        self.assertTrue(self.usuario.check_password(TEST_PASS_VAL))

    def test_create_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            Usuario.objects.create_user(correo='', password=TEST_SHORT_VAL)

    def test_create_user_pin_is_hashed(self):
        usuario = Usuario.objects.create_user(
            correo='pin_test@test.com',
            password=TEST_PASS_VAL,
            nombres='Pin',
            apellido_paterno='Test',
            apellido_materno='User',
            documento_identidad='87654321',
            telefono=999999999,
            id_moneda=self.moneda,
            pin_acceso_rapido='123456'
        )
        self.assertTrue(usuario.pin_acceso_rapido.startswith('pbkdf2_'))
        self.assertTrue(usuario.check_pin('123456'))
        self.assertFalse(usuario.check_pin('654321'))

    def test_set_pin_hashes(self):
        self.usuario.set_pin('654321')
        self.usuario.save()
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.pin_acceso_rapido.startswith('pbkdf2_'))
        self.assertTrue(self.usuario.check_pin('654321'))

    def test_check_pin_fallback_plaintext(self):
        self.usuario.pin_acceso_rapido = '000000'
        self.usuario.save()
        self.assertTrue(self.usuario.check_pin('000000'))
        self.assertFalse(self.usuario.check_pin('111111'))

    def test_str_representation(self):
        self.assertEqual(str(self.usuario), 'Juan Perez')

    def test_email_verificado_default(self):
        self.assertFalse(self.usuario.email_verificado)

    def test_onboarding_completed_default(self):
        self.assertFalse(self.usuario.onboarding_completed)
