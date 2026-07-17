from django.test import TestCase
from django.urls import reverse


class AdminIndexViewTests(TestCase):
    def test_index_returns_200(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_index_contains_welcome_message(self):
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Bienvenido a la app del modulo Administracion del Sistema')

    def test_index_uses_correct_url(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
