from django.test import TestCase
from usuarios.models import Usuario
from usuarios.backends import EmailBackend
from cuentas.models import Moneda


class EmailBackendTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='auth_test@test.com',
            password='SecurePass123!',
            nombres='Auth',
            apellido_paterno='Test',
            apellido_materno='User',
            documento_identidad='12345678',
            telefono=987654321,
            id_moneda=self.moneda
        )
        self.backend = EmailBackend()

    def test_authenticate_success(self):
        user = self.backend.authenticate(
            request=None,
            correo='auth_test@test.com',
            password='SecurePass123!'
        )
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.usuario.id)

    def test_authenticate_wrong_password(self):
        user = self.backend.authenticate(
            request=None,
            correo='auth_test@test.com',
            password='WrongPassword!'
        )
        self.assertIsNone(user)

    def test_authenticate_nonexistent_user(self):
        user = self.backend.authenticate(
            request=None,
            correo='no_exist@test.com',
            password='AnyPass123!'
        )
        self.assertIsNone(user)

    def test_user_can_authenticate_inactive(self):
        self.usuario.is_active = False
        self.assertFalse(self.backend.user_can_authenticate(self.usuario))

    def test_get_user_success(self):
        user = self.backend.get_user(self.usuario.id)
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.usuario.id)

    def test_get_user_nonexistent(self):
        user = self.backend.get_user(99999)
        self.assertIsNone(user)

    def test_user_can_authenticate_active(self):
        self.assertTrue(self.backend.user_can_authenticate(self.usuario))

    def test_user_can_authenticate_inactive(self):
        self.usuario.is_active = False
        self.assertFalse(self.backend.user_can_authenticate(self.usuario))
