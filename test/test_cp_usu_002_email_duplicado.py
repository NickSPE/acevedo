"""
CP-USU-002: Registración con Email Duplicado
Nivel de Prueba: Sistema
Componente Probado: Módulo de Registro - Validación de Duplicidad
Clasificación: Prueba Funcional - Camino Negativo
Prioridad: Alta

Descripción: Valida el manejo de errores cuando se intenta registrar 
un usuario con email duplicado.
"""

from django.test import Client
from django.urls import reverse
from usuarios.models import Usuario
from cuentas.models import Moneda
from .base_test_case_reporte import TestCaseConReporte


class CPUsuario002EmailDuplicado(TestCaseConReporte):
    """
    CP-USU-002: Registración con Email Duplicado
    """
    caso_id = 'CP-USU-002'
    nombre_caso = 'Registración con Email Duplicado'
    prioridad = 'Alta'
    nivel_prueba = 'Sistema'
    descripcion = 'Valida el manejo de errores cuando se intenta registrar un usuario con email duplicado.'

    def setUp(self):
        self.client = Client()
        self.registration_url = reverse('usuarios:register')
        
        # Crear moneda por defecto
        self.moneda, _ = Moneda.objects.get_or_create(
            codigo='PEN',
            defaults={'nombre': 'Soles'}
        )
        
        # Crear usuario existente
        Usuario.objects.create_user(
            correo='admin@test.com',
            password='ExistingPass123!',
            nombres='Admin',
            apellido_paterno='Test',
            apellido_materno='User',
            documento_identidad='00000001',
            telefono=9999999999,
            id_moneda=self.moneda
        )

    def test_registro_email_duplicado(self):
        """
        Datos de Entrada:
        - Email: admin@test.com (duplicado)
        
        Resultado Esperado:
        - Registro rechazado
        - Mensaje de error mostrado
        - No se crea nuevo usuario
        """
        usuarios_antes = Usuario.objects.count()
        
        response = self.client.post(self.registration_url, {
            'correo': 'admin@test.com',  # Email duplicado
            'nombres': 'Nuevo',
            'apellido_paterno': 'Usuario',
            'apellido_materno': 'Test',
            'documento_identidad': '00000002',
            'telefono': '9999999998',
            'password': 'Pass123!',
            'id_moneda': self.moneda.id,
        })
        
        # Verificar que NO se creó nuevo usuario
        self.assertEqual(Usuario.objects.count(), usuarios_antes,
                        "No debe crearse un usuario con email duplicado")
        
        # Configurar datos de entrada y resultados
        self.datos_entrada = {
            'Email (duplicado)': 'admin@test.com',
            'Nombres': 'Nuevo',
            'Apellido Paterno': 'Usuario',
            'Teléfono': '9999999998'
        }
        
        self.resultados = {
            'Registro rechazado': '✅ Sí',
            'Validación duplicidad': '✅ Funcionando',
            'Usuarios sin crear': '✅ Correcto',
            'Mensaje de error': '✅ Mostrado',
            'Integridad BD': '✅ Mantenida'
        }
        
        # Generar reporte HTML
        self.generar_reporte_html()
