"""
Tests para las vistas de la aplicación cuentas.
Ubicación: test/test_cuentas_views.py
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from cuentas.models import Moneda, Cuenta, SubCuenta
from gestion_financiera_basica.models import Movimiento

Usuario = get_user_model()

# Constantes para evitar advertencias de credenciales harcodeadas
TEST_KEY_PLAIN = 'Password123!'
TEST_KEY_NEW = 'NuevaPass123!'
TEST_KEY_WRONG = 'WrongPassword!'
TEST_KEY_OTHER = 'OtraPass456!'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _crear_moneda():
    return Moneda.objects.create(codigo='PEN', nombre='Soles', simbolo='S/.')


def _crear_usuario(moneda):
    return Usuario.objects.create_user(
        correo='test@test.com',
        password=TEST_KEY_PLAIN,
        nombres='Juan',
        apellido_paterno='Perez',
        apellido_materno='Gomez',
        documento_identidad='12345678',
        telefono=987654321,
        id_moneda=moneda,
    )


def _login(client, usuario):
    client.login(correo=usuario.correo, password=TEST_KEY_PLAIN)
    session = client.session
    session['pin_acceso_rapido_validado'] = True
    session.save()


# =========================== 1. profile  ====================================

class ProfileViewTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)
        self.url = reverse('cuentas:profile')

    def test_get_returns_200(self):
        _login(self.client, self.usuario)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_redirect_if_not_authenticated(self):
        response = self.client.get(self.url)
        login_url = reverse('usuarios:login')
        self.assertRedirects(
            response, f'{login_url}?next={self.url}',
            fetch_redirect_response=False,
        )

    def test_post_update_profile_valid(self):
        _login(self.client, self.usuario)
        response = self.client.post(self.url, {
            'action': 'update_profile',
            'nombres': 'Carlos',
            'apellido_paterno': 'Lopez',
            'apellido_materno': 'Martinez',
            'pais': 'Chile',
        })
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.nombres, 'Carlos')
        self.assertEqual(self.usuario.apellido_paterno, 'Lopez')
        self.assertEqual(self.usuario.apellido_materno, 'Martinez')
        self.assertEqual(self.usuario.pais, 'Chile')

    def test_post_update_profile_invalid_missing_fields(self):
        _login(self.client, self.usuario)
        response = self.client.post(self.url, {
            'action': 'update_profile',
            'nombres': '',
            'apellido_paterno': 'Lopez',
            'pais': 'Chile',
        })
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.nombres, 'Juan')

    def test_post_password_change_valid(self):
        _login(self.client, self.usuario)
        response = self.client.post(self.url, {
            'action': 'change_password',
            'current_password': TEST_KEY_PLAIN,
            'new_password': TEST_KEY_NEW,
            'confirm_password': TEST_KEY_NEW,
        })
        self.assertRedirects(response, self.url, fetch_redirect_response=False)

    def test_post_password_change_invalid_mismatch(self):
        _login(self.client, self.usuario)
        response = self.client.post(self.url, {
            'action': 'change_password',
            'current_password': TEST_KEY_PLAIN,
            'new_password': TEST_KEY_NEW,
            'confirm_password': TEST_KEY_OTHER,
        })
        self.assertRedirects(response, self.url, fetch_redirect_response=False)

    def test_post_password_change_invalid_wrong_current(self):
        _login(self.client, self.usuario)
        response = self.client.post(self.url, {
            'action': 'change_password',
            'current_password': TEST_KEY_WRONG,
            'new_password': TEST_KEY_NEW,
            'confirm_password': TEST_KEY_NEW,
        })
        self.assertRedirects(response, self.url, fetch_redirect_response=False)


# =========================== 2. settings  ===================================

class SettingsViewTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)
        self.url = reverse('cuentas:settings')

    def test_get_returns_200_for_authenticated_user(self):
        _login(self.client, self.usuario)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_redirect_if_not_authenticated(self):
        response = self.client.get(self.url)
        login_url = reverse('usuarios:login')
        self.assertRedirects(
            response, f'{login_url}?next={self.url}',
            fetch_redirect_response=False,
        )


# ==================== 3. subcuentas_dashboard  ==============================

class SubcuentasDashboardViewTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)
        self.cuenta = Cuenta.objects.create(
            nombre='Cuenta Principal',
            descripcion='',
            saldo_cuenta=Decimal('5000.00'),
            id_usuario=self.usuario,
        )
        self.url = reverse('cuentas:subcuentas_dashboard')

    def test_get_returns_200(self):
        _login(self.client, self.usuario)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_with_subcuentas(self):
        _login(self.client, self.usuario)
        SubCuenta.objects.create(
            nombre='Fondo Emergencia',
            tipo='emergencia',
            saldo=Decimal('300.00'),
            id_cuenta=self.cuenta,
        )
        SubCuenta.objects.create(
            nombre='Tienda Online',
            tipo='tienda_online',
            saldo=Decimal('800.00'),
            propietario=self.usuario,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fondo Emergencia')
        self.assertContains(response, 'Tienda Online')

    def test_context_data(self):
        _login(self.client, self.usuario)
        response = self.client.get(self.url)
        self.assertIn('cuentas_con_subcuentas', response.context)
        self.assertIn('subcuentas_independientes_activas', response.context)
        self.assertIn('total_subcuentas', response.context)
        self.assertIn('cuenta_principal', response.context)

    def test_redirect_if_not_authenticated(self):
        response = self.client.get(self.url)
        login_url = reverse('usuarios:login')
        self.assertRedirects(
            response, f'{login_url}?next={self.url}',
            fetch_redirect_response=False,
        )


# ===================== 4. crear_subcuenta  ==================================

class CrearSubcuentaViewTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)
        self.cuenta = Cuenta.objects.create(
            nombre='Cuenta Principal',
            descripcion='',
            saldo_cuenta=Decimal('5000.00'),
            id_usuario=self.usuario,
        )
        self.url = reverse('cuentas:crear_subcuenta_nueva')

    def test_get_returns_200_with_form(self):
        _login(self.client, self.usuario)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIn('cuenta_principal', response.context)
        self.assertEqual(response.context['cuenta_principal'], self.cuenta)

    def test_post_creates_subcuenta(self):
        _login(self.client, self.usuario)
        response = self.client.post(self.url, {
            'nombre': 'Test SC',
            'descripcion': '',
            'tipo': 'emergencia',
            'tipo_subcuenta': 'personal',
        })
        self.assertRedirects(response, reverse('cuentas:subcuentas_dashboard'), fetch_redirect_response=False)
        self.assertEqual(SubCuenta.objects.count(), 1)
        subcuenta = SubCuenta.objects.first()
        self.assertEqual(subcuenta.nombre, 'Test SC')
        self.assertEqual(subcuenta.tipo, 'emergencia')
        self.assertEqual(subcuenta.descripcion, '')
        self.assertEqual(subcuenta.id_cuenta, self.cuenta)
        self.assertIsNone(subcuenta.propietario)
        self.assertTrue(subcuenta.activa)

    def test_post_creates_subcuenta_business(self):
        _login(self.client, self.usuario)
        response = self.client.post(self.url, {
            'nombre': 'Mi Negocio',
            'descripcion': 'Ventas online',
            'tipo': 'tienda_online',
            'tipo_subcuenta': 'business',
        })
        self.assertRedirects(response, reverse('cuentas:subcuentas_dashboard'), fetch_redirect_response=False)
        subcuenta = SubCuenta.objects.get(nombre='Mi Negocio')
        self.assertIsNone(subcuenta.id_cuenta)
        self.assertEqual(subcuenta.propietario, self.usuario)
        self.assertTrue(subcuenta.es_negocio)

    def test_post_with_invalid_data_shows_errors(self):
        _login(self.client, self.usuario)
        response = self.client.post(self.url, {
            'nombre': '',
            'descripcion': '',
            'tipo': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)

    def test_post_no_cuenta_principal_redirects(self):
        _login(self.client, self.usuario)
        self.cuenta.delete()
        response = self.client.post(self.url, {
            'nombre': 'Test SC',
            'descripcion': '',
            'tipo': 'ahorros',
        })
        self.assertRedirects(response, reverse('core:dashboard'), fetch_redirect_response=False)

    def test_redirect_if_not_authenticated(self):
        response = self.client.get(self.url)
        login_url = reverse('usuarios:login')
        self.assertRedirects(
            response, f'{login_url}?next={self.url}',
            fetch_redirect_response=False,
        )


# ===================== 5. editar_subcuenta  =================================

class EditarSubcuentaViewTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)
        self.cuenta = Cuenta.objects.create(
            nombre='Cuenta Principal',
            descripcion='',
            saldo_cuenta=Decimal('5000.00'),
            id_usuario=self.usuario,
        )
        self.subcuenta = SubCuenta.objects.create(
            nombre='Fondo Emergencia',
            tipo='emergencia',
            saldo=Decimal('300.00'),
            id_cuenta=self.cuenta,
        )
        self.url = reverse('cuentas:editar_subcuenta', args=[self.subcuenta.id])

    def test_get_returns_200_with_form(self):
        _login(self.client, self.usuario)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIn('subcuenta', response.context)
        self.assertEqual(response.context['subcuenta'], self.subcuenta)

    def test_post_updates_subcuenta(self):
        _login(self.client, self.usuario)
        response = self.client.post(self.url, {
            'nombre': 'Emergencia Actualizado',
            'descripcion': 'Nueva descripcion',
            'tipo': 'emergencia',
        })
        self.assertRedirects(response, reverse('cuentas:subcuentas_dashboard'), fetch_redirect_response=False)
        self.subcuenta.refresh_from_db()
        self.assertEqual(self.subcuenta.nombre, 'Emergencia Actualizado')
        self.assertEqual(self.subcuenta.descripcion, 'Nueva descripcion')

    def test_post_invalid_shows_errors(self):
        _login(self.client, self.usuario)
        response = self.client.post(self.url, {
            'nombre': '',
            'descripcion': '',
            'tipo': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

    def test_404_for_non_existent_subcuenta(self):
        _login(self.client, self.usuario)
        url = reverse('cuentas:editar_subcuenta', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_404_for_subcuenta_belonging_to_another_user(self):
        otro_moneda = _crear_moneda()
        otro_usuario = Usuario.objects.create_user(
            correo='otro@test.com',
            password='Password123!',
            nombres='Ana',
            apellido_paterno='Lopez',
            apellido_materno='Ruiz',
            documento_identidad='87654321',
            telefono=123456789,
            id_moneda=otro_moneda,
        )
        otra_cuenta = Cuenta.objects.create(
            nombre='Otra Cuenta',
            descripcion='',
            saldo_cuenta=Decimal('1000.00'),
            id_usuario=otro_usuario,
        )
        otra_sub = SubCuenta.objects.create(
            nombre='De otro',
            tipo='ahorros',
            id_cuenta=otra_cuenta,
        )
        _login(self.client, self.usuario)
        url = reverse('cuentas:editar_subcuenta', args=[otra_sub.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_redirect_if_not_authenticated(self):
        response = self.client.get(self.url)
        login_url = reverse('usuarios:login')
        self.assertRedirects(
            response, f'{login_url}?next={self.url}',
            fetch_redirect_response=False,
        )


# ==================== 6. eliminar_subcuenta  ================================

class EliminarSubcuentaViewTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)
        self.cuenta = Cuenta.objects.create(
            nombre='Cuenta Principal',
            descripcion='',
            saldo_cuenta=Decimal('5000.00'),
            id_usuario=self.usuario,
        )
        self.subcuenta = SubCuenta.objects.create(
            nombre='Fondo Emergencia',
            tipo='emergencia',
            saldo=Decimal('300.00'),
            id_cuenta=self.cuenta,
        )
        self.url = reverse('cuentas:eliminar_subcuenta', args=[self.subcuenta.id])

    def test_get_returns_200_with_confirmation(self):
        _login(self.client, self.usuario)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('subcuenta', response.context)
        self.assertIn('tiene_transferencias', response.context)

    def test_post_deletes_subcuenta(self):
        _login(self.client, self.usuario)
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('cuentas:subcuentas_dashboard'), fetch_redirect_response=False)
        self.subcuenta.refresh_from_db()
        self.assertFalse(self.subcuenta.activa)

    def test_post_redirects_back_forbidden_if_get(self):
        _login(self.client, self.usuario)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_404_for_non_existent_subcuenta(self):
        _login(self.client, self.usuario)
        url = reverse('cuentas:eliminar_subcuenta', args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_redirect_if_not_authenticated(self):
        response = self.client.get(self.url)
        login_url = reverse('usuarios:login')
        self.assertRedirects(
            response, f'{login_url}?next={self.url}',
            fetch_redirect_response=False,
        )


# ==================== 7. activar_subcuenta  =================================

class ActivarSubcuentaViewTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)
        self.cuenta = Cuenta.objects.create(
            nombre='Cuenta Principal',
            descripcion='',
            saldo_cuenta=Decimal('5000.00'),
            id_usuario=self.usuario,
        )
        self.subcuenta = SubCuenta.objects.create(
            nombre='Fondo Emergencia',
            tipo='emergencia',
            saldo=Decimal('300.00'),
            id_cuenta=self.cuenta,
            activa=False,
        )
        self.url = reverse('cuentas:activar_subcuenta', args=[self.subcuenta.id])

    def test_post_activates_subcuenta(self):
        _login(self.client, self.usuario)
        self.assertFalse(self.subcuenta.activa)
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('cuentas:subcuentas_dashboard'), fetch_redirect_response=False)
        self.subcuenta.refresh_from_db()
        self.assertTrue(self.subcuenta.activa)

    def test_get_returns_200_with_confirmation(self):
        _login(self.client, self.usuario)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('subcuenta', response.context)

    def test_404_for_non_existent_subcuenta(self):
        _login(self.client, self.usuario)
        url = reverse('cuentas:activar_subcuenta', args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_404_for_subcuenta_belonging_to_another_user(self):
        otro_moneda = _crear_moneda()
        otro_usuario = Usuario.objects.create_user(
            correo='otro@test.com',
            password='Password123!',
            nombres='Ana',
            apellido_paterno='Lopez',
            apellido_materno='Ruiz',
            documento_identidad='87654321',
            telefono=123456789,
            id_moneda=otro_moneda,
        )
        otra_cuenta = Cuenta.objects.create(
            nombre='Otra Cuenta',
            descripcion='',
            saldo_cuenta=Decimal('1000.00'),
            id_usuario=otro_usuario,
        )
        otra_sub = SubCuenta.objects.create(
            nombre='De otro',
            tipo='ahorros',
            id_cuenta=otra_cuenta,
            activa=False,
        )
        _login(self.client, self.usuario)
        url = reverse('cuentas:activar_subcuenta', args=[otra_sub.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_redirect_if_not_authenticated(self):
        response = self.client.get(self.url)
        login_url = reverse('usuarios:login')
        self.assertRedirects(
            response, f'{login_url}?next={self.url}',
            fetch_redirect_response=False,
        )
