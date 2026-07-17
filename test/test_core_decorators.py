from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from core.decorators import fast_access_pin_verified
from cuentas.models import Moneda

Usuario = get_user_model()


class FastAccessPinVerifiedDecoratorTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='decorator_test@test.com', password='Password123!',
            nombres='Decorator', apellido_paterno='Test',
            apellido_materno='User', documento_identidad='12345678',
            telefono=987654321, id_moneda=self.moneda
        )

        @fast_access_pin_verified
        def test_view(request):
            return HttpResponse('OK')

        self.test_view = test_view

    def test_normal_login_passes(self):
        request = self.factory.get('/test/')
        request.user = self.usuario
        request.session = {}
        response = self.test_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'OK')

    def test_pin_login_validated_passes(self):
        request = self.factory.get('/test/')
        request.user = self.usuario
        request.session = {
            'login_method': 'pin',
            'pin_acceso_rapido_validado': True
        }
        response = self.test_view(request)
        self.assertEqual(response.status_code, 200)

    def test_pin_login_not_validated_redirects(self):
        from django.shortcuts import redirect
        from django.urls import reverse

        request = self.factory.get('/test/')
        request.user = self.usuario
        request.session = {
            'login_method': 'pin',
            'pin_acceso_rapido_validado': False
        }
        response = self.test_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('usuarios:acceso_rapido'), response.url)
