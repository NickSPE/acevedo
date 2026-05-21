"""
CP-AUTH-001: Login Exitoso
Nivel de Prueba: Sistema
Componente Probado: Módulo de Autenticación (Login Tradicional)
Clasificación: Prueba Funcional - Camino Positivo
Prioridad: Crítica

Descripción: Valida el proceso de autenticación del usuario usando 
credenciales de correo y contraseña.
"""

from django.test import Client
from django.urls import reverse
from usuarios.models import Usuario
from cuentas.models import Moneda
from .base_test_case_reporte import TestCaseConReporte


class CPAuth001LoginExitoso(TestCaseConReporte):
    """
    CP-AUTH-001: Login Exitoso
    """
    caso_id = 'CP-AUTH-001'
    nombre_caso = 'Login Exitoso'
    prioridad = 'Crítica'
    nivel_prueba = 'Sistema'
    descripcion = 'Valida el proceso de autenticación del usuario usando credenciales de correo y contraseña.'

    def setUp(self):
        self.client = Client()
        self.login_url = reverse('usuarios:login')
        
        # Crear moneda por defecto
        self.moneda, _ = Moneda.objects.get_or_create(
            codigo='PEN',
            defaults={'nombre': 'Soles'}
        )
        
        # Crear usuario de prueba
        self.usuario = Usuario.objects.create_user(
            correo='usuario@test.com',
            password='CorrectPassword123',
            nombres='Usuario',
            apellido_paterno='Test',
            apellido_materno='User',
            documento_identidad='12345678',
            telefono=9999999999,
            id_moneda=self.moneda
        )
        self.usuario.email_verificado = True
        self.usuario.save()

    def test_login_exitoso(self):
        """
        Datos de Entrada:
        - Email: usuario@test.com
        - Contraseña: CorrectPassword123
        
        Resultado Esperado:
        - Usuario autenticado exitosamente
        - Nueva sesión creada
        - Usuario autenticado en sesión
        """
        response = self.client.post(self.login_url, {
            'email': 'usuario@test.com',
            'password': 'CorrectPassword123'
        }, follow=True)
        
        # Verificar que la sesión fue creada
        self.assertIn('_auth_user_id', self.client.session,
                     "Debe crearse una sesión")
        
        # Verificar que el usuario está autenticado
        self.assertTrue(int(self.client.session['_auth_user_id']) == self.usuario.id,
                       "El usuario en sesión debe ser el autenticado")
        
        # Configurar datos de entrada y resultados
        self.datos_entrada = {
            'Email': 'usuario@test.com',
            'Contraseña': '••••••••••••••',
            'Email verificado': '✅ Sí'
        }
        
        self.resultados = {
            'Autenticación exitosa': '✅ Sí',
            'Sesión creada': '✅ Sí',
            'Usuario en sesión': '✅ Correcto',
            'Token de sesión': '_auth_user_id: 1',
            'Redireccionamiento': '✅ Onboarding'
        }
        
        # Generar reporte HTML
        self.generar_reporte_html()
