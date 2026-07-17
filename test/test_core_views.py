from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from cuentas.models import Moneda, Cuenta
from gestion_financiera_basica.models import Movimiento

Usuario = get_user_model()


class InicioViewTestCase(TestCase):
    def setUp(self):
        self.index_url = reverse('core:index')
        self.moneda = Moneda.objects.create(
            nombre='Dolar', codigo='USD', simbolo='$'
        )
        self.usuario = Usuario.objects.create_user(
            correo='test@test.com', password='testpass123',
            nombres='Test', apellido_paterno='User',
            apellido_materno='Test', documento_identidad='12345678',
            telefono=987654321, id_moneda=self.moneda,
            onboarding_completed=True
        )

    def test_anonymous_user_gets_200(self):
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/index.html')

    def test_authenticated_user_redirects_to_dashboard(self):
        self.client.login(correo='test@test.com', password='testpass123')
        response = self.client.get(self.index_url)
        self.assertRedirects(response, reverse('core:dashboard'))


class DashboardViewTestCase(TestCase):
    def setUp(self):
        self.dashboard_url = reverse('core:dashboard')
        self.moneda = Moneda.objects.create(
            nombre='Dolar', codigo='USD', simbolo='$'
        )
        self.usuario = Usuario.objects.create_user(
            correo='test@test.com', password='testpass123',
            nombres='Test', apellido_paterno='User',
            apellido_materno='Test', documento_identidad='12345678',
            telefono=987654321, id_moneda=self.moneda,
            onboarding_completed=True
        )
        self.cuenta = Cuenta.objects.create(
            nombre='Test Account', descripcion='Test account description',
            saldo_cuenta=1000, id_usuario=self.usuario
        )
        self.movimiento = Movimiento.objects.create(
            nombre='Test Income', tipo='ingreso', categoria='salario',
            monto=500, fecha_movimiento=timezone.now(),
            descripcion='Test income', id_cuenta=self.cuenta,
            id_usuario=self.usuario
        )

    def test_redirect_if_not_authenticated(self):
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('usuarios:login'), response.url)

    def test_redirect_to_onboarding_if_not_completed(self):
        self.usuario.onboarding_completed = False
        self.usuario.save()
        self.client.login(correo='test@test.com', password='testpass123')
        response = self.client.get(self.dashboard_url)
        self.assertRedirects(response, reverse('usuarios:onboarding'))

    def test_dashboard_renders_for_authenticated_user(self):
        self.client.login(correo='test@test.com', password='testpass123')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/dashboard.html')


class LogoutViewTestCase(TestCase):
    def setUp(self):
        self.logout_url = reverse('core:logout')
        self.moneda = Moneda.objects.create(
            nombre='Dolar', codigo='USD', simbolo='$'
        )
        self.usuario = Usuario.objects.create_user(
            correo='test@test.com', password='testpass123',
            nombres='Test', apellido_paterno='User',
            apellido_materno='Test', documento_identidad='12345678',
            telefono=987654321, id_moneda=self.moneda,
            onboarding_completed=True
        )

    def test_logout_flushes_session(self):
        self.client.login(correo='test@test.com', password='testpass123')
        session = self.client.session
        session['test_key'] = 'test_value'
        session.save()
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, reverse('core:index'))
        session = self.client.session
        self.assertNotIn('test_key', session)


class TemporaryLogoutViewTestCase(TestCase):
    def setUp(self):
        self.temp_logout_url = reverse('core:temporary_logout')
        self.moneda = Moneda.objects.create(
            nombre='Dolar', codigo='USD', simbolo='$'
        )
        self.usuario = Usuario.objects.create_user(
            correo='test@test.com', password='testpass123',
            nombres='Test', apellido_paterno='User',
            apellido_materno='Test', documento_identidad='12345678',
            telefono=987654321, id_moneda=self.moneda,
            onboarding_completed=True
        )

    def test_temporary_logout_sets_pin_validated_to_false(self):
        self.client.login(correo='test@test.com', password='testpass123')
        session = self.client.session
        session['pin_acceso_rapido_validado'] = True
        session.save()
        response = self.client.get(self.temp_logout_url)
        self.assertRedirects(response, reverse('usuarios:acceso_rapido'))
        session = self.client.session
        self.assertFalse(session.get('pin_acceso_rapido_validado'))


class PrivacyPolicyViewTestCase(TestCase):
    def test_privacy_policy_returns_200(self):
        response = self.client.get(reverse('core:privacy'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/privacy.html')


class TermsOfServiceViewTestCase(TestCase):
    def test_terms_of_service_returns_200(self):
        response = self.client.get(reverse('core:terms'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/terms.html')


class HelpCenterViewTestCase(TestCase):
    def test_help_center_returns_200(self):
        response = self.client.get(reverse('core:help'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/help.html')


class ContactViewTestCase(TestCase):
    def setUp(self):
        self.contact_url = reverse('core:contact')

    def test_get_returns_200(self):
        response = self.client.get(self.contact_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/contact.html')

    def test_post_valid_data_redirects(self):
        response = self.client.post(self.contact_url, {
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'Test Subject',
            'message': 'This is a test message.',
        })
        self.assertRedirects(response, self.contact_url)

    def test_post_invalid_data_stays_on_page(self):
        response = self.client.post(self.contact_url, {
            'name': '',
            'email': 'test@example.com',
            'subject': '',
            'message': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/contact.html')
