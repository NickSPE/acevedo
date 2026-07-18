from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from cuentas.models import Moneda, Cuenta

Usuario = get_user_model()

# Constantes para evitar advertencias de credenciales harcodeadas
TEST_PWD_CORRECT = 'CorrectPassword123'
TEST_PWD_WRONG = 'WrongPassword'
TEST_PWD_OLD = 'OldPass123'


class LoginViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('usuarios:login')
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='login_test@test.com',
            password=TEST_PWD_CORRECT,
            nombres='Login',
            apellido_paterno='Test',
            apellido_materno='User',
            documento_identidad='12345678',
            telefono=987654321,
            id_moneda=self.moneda,
            email_verificado=True,
            onboarding_completed=True
        )

    def test_login_page_renders(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/login.html')

    def test_login_success_verified_email(self):
        response = self.client.post(self.login_url, {
            'email': 'login_test@test.com',
            'password': TEST_PWD_CORRECT
        }, follow=True)
        self.assertRedirects(response, reverse('core:dashboard'))

    def test_login_success_redirects_onboarding(self):
        self.usuario.onboarding_completed = False
        self.usuario.save()
        response = self.client.post(self.login_url, {
            'email': 'login_test@test.com',
            'password': TEST_PWD_CORRECT
        }, follow=True)
        self.assertRedirects(response, reverse('usuarios:onboarding'))

    def test_login_failure_wrong_password(self):
        response = self.client.post(self.login_url, {
            'email': 'login_test@test.com',
            'password': TEST_PWD_WRONG
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Credenciales no validas')

    def test_login_unverified_email(self):
        self.usuario.email_verificado = False
        self.usuario.save()
        response = self.client.post(self.login_url, {
            'email': 'login_test@test.com',
            'password': 'CorrectPassword123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('usuarios:pagina_verificar_correo'))


class PinLoginViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.pin_login_url = reverse('usuarios:pin_login')
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='pin_login@test.com',
            password='Password123!',
            nombres='Pin',
            apellido_paterno='Login',
            apellido_materno='Test',
            documento_identidad='12345678',
            telefono=987654321,
            id_moneda=self.moneda,
            pin_acceso_rapido='123456',
            email_verificado=True,
            onboarding_completed=True
        )

    def test_pin_login_page_renders(self):
        response = self.client.get(self.pin_login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/pin_login.html')

    def test_pin_login_success(self):
        response = self.client.post(self.pin_login_url, {
            'pin_input': '123456'
        }, follow=True)
        self.assertRedirects(response, reverse('core:dashboard'))

    def test_pin_login_invalid_pin(self):
        response = self.client.post(self.pin_login_url, {
            'pin_input': '000000'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PIN incorrecto')

    def test_pin_login_empty_pin(self):
        response = self.client.post(self.pin_login_url, {'pin_input': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No se recibió ningún PIN')

    def test_pin_login_non_digit(self):
        response = self.client.post(self.pin_login_url, {'pin_input': 'abc123'})
        self.assertEqual(response.status_code, 200)


class PasswordResetTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.reset_url = reverse('usuarios:password_reset_request')
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='reset_test@test.com',
            password=TEST_PWD_OLD,
            nombres='Reset',
            apellido_paterno='Test',
            apellido_materno='User',
            documento_identidad='12345678',
            telefono=987654321,
            id_moneda=self.moneda
        )

    def test_password_reset_page_renders(self):
        response = self.client.get(self.reset_url)
        self.assertEqual(response.status_code, 200)

    def test_password_reset_invalid_action(self):
        response = self.client.post(self.reset_url, {
            'email': 'reset_test@test.com',
            'action': 'invalid_action'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])

    def test_password_reset_nonexistent_email(self):
        response = self.client.post(self.reset_url, {
            'email': 'no_exist@test.com',
            'action': 'send_code'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])


class OnboardingViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.onboarding_url = reverse('usuarios:onboarding')
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='onboard_test@test.com',
            password='Password123!',
            nombres='Onboard',
            apellido_paterno='Test',
            apellido_materno='User',
            documento_identidad='12345678',
            telefono=987654321,
            id_moneda=self.moneda,
            onboarding_completed=False
        )

    def test_onboarding_redirects_if_not_authenticated(self):
        response = self.client.get(self.onboarding_url)
        self.assertRedirects(response, reverse('usuarios:login'))

    def test_onboarding_redirects_if_completed(self):
        self.usuario.onboarding_completed = True
        self.usuario.save()
        self.client.force_login(self.usuario)
        response = self.client.get(self.onboarding_url)
        self.assertRedirects(response, reverse('core:dashboard'))

    def test_onboarding_renders_for_incomplete(self):
        self.client.force_login(self.usuario)
        response = self.client.get(self.onboarding_url)
        self.assertEqual(response.status_code, 200)


class CompleteOnboardingTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.complete_url = reverse('usuarios:complete_onboarding')
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='complete_onboard@test.com',
            password='Password123!',
            nombres='Complete',
            apellido_paterno='Onboard',
            apellido_materno='Test',
            documento_identidad='12345678',
            telefono=987654321,
            id_moneda=self.moneda,
            onboarding_completed=False
        )
        self.cuenta = Cuenta.objects.create(
            nombre='Test Account',
            saldo_cuenta=1000.00,
            id_usuario=self.usuario
        )

    def test_complete_onboarding_requires_auth(self):
        response = self.client.post(self.complete_url, {}, content_type='application/json')
        data = response.json()
        self.assertFalse(data['success'])

    def test_complete_onboarding_skip(self):
        self.client.force_login(self.usuario)
        response = self.client.post(self.complete_url, {'skipped': True}, content_type='application/json')
        data = response.json()
        self.assertTrue(data['success'])
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.onboarding_completed)

    def test_complete_onboarding_updates_pin(self):
        self.client.force_login(self.usuario)
        response = self.client.post(self.complete_url, {
            'pin_acceso_rapido': '654321'
        }, content_type='application/json')
        data = response.json()
        self.assertTrue(data['success'])
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_pin('654321'))

    def test_complete_onboarding_updates_telefono(self):
        self.client.force_login(self.usuario)
        response = self.client.post(self.complete_url, {
            'telefono': '999888777'
        }, content_type='application/json')
        self.assertTrue(response.json()['success'])
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.telefono, 999888777)

    def test_complete_onboarding_updates_saldo(self):
        self.client.force_login(self.usuario)
        response = self.client.post(self.complete_url, {
            'saldo_inicial': '2500'
        }, content_type='application/json')
        self.assertTrue(response.json()['success'])
        self.cuenta.refresh_from_db()
        self.assertEqual(float(self.cuenta.saldo_cuenta), 2500.0)

    def test_complete_onboarding_not_allowed_get(self):
        self.client.force_login(self.usuario)
        response = self.client.get(self.complete_url)
        data = response.json()
        self.assertFalse(data['success'])
