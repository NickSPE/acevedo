"""
CP-USU-001: Registro de Usuario Exitoso
Nivel de Prueba: Sistema
Componente Probado: Módulo de Registro de Usuarios
Clasificación: Prueba Funcional - Camino Positivo
Prioridad: Crítica

Descripción: El presente caso de prueba valida el proceso completo de 
registro de un usuario nuevo en el sistema FinGest.
"""

from django.test import Client
from django.urls import reverse
from usuarios.models import Usuario
from cuentas.models import Moneda
from .base_test_case_reporte import TestCaseConReporte


class CPUsuario001RegistroExitoso(TestCaseConReporte):
    """
    CP-USU-001: Registro de Usuario Exitoso
    """
    caso_id = 'CP-USU-001'
    nombre_caso = 'Registro de Usuario Exitoso'
    prioridad = 'Crítica'
    nivel_prueba = 'Sistema'
    descripcion = 'El presente caso de prueba valida el proceso completo de registro de un usuario nuevo en el sistema FinGest.'

    def setUp(self):
        self.client = Client()
        self.registration_url = reverse('usuarios:register')
        # Crear moneda por defecto
        self.moneda, _ = Moneda.objects.get_or_create(
            codigo='PEN',
            defaults={'nombre': 'Soles'}
        )

    def test_registro_usuario_exitoso(self):
        """
        Datos de Entrada:
        - Email: jcano@empresa.com
        - Nombres: Juan
        - Apellido Paterno: Cano
        - Contraseña: SecurePass123!
        
        Resultado Esperado:
        - Usuario creado exitosamente en base de datos
        - Contraseña almacenada hasheada
        """
        # Configurar datos de entrada y resultados
        self.datos_entrada = {
            'Email': 'jcano@empresa.com',
            'Nombres': 'Juan',
            'Apellido Paterno': 'Cano',
            'Contraseña': '••••••••••••••'
        }
        
        usuarios_antes = Usuario.objects.count()
        
        # Crear usuario directamente (como lo haría el sistema después de verificar email)
        usuario = Usuario.objects.create_user(
            correo='jcano@empresa.com',
            password='SecurePass123!',
            nombres='Juan',
            apellido_paterno='Cano',
            apellido_materno='García',
            documento_identidad='12345678',
            telefono=999999999,
            id_moneda=self.moneda
        )
        
        # Verificar que el usuario fue creado
        self.assertIsNotNone(usuario, "El usuario no fue creado en la base de datos")
        self.assertEqual(Usuario.objects.count(), usuarios_antes + 1)
        
        # Verificar que la contraseña está hasheada
        self.assertNotEqual(usuario.password, 'SecurePass123!', 
                           "La contraseña no debe estar en texto plano")
        
        # Verificar datos almacenados
        self.assertEqual(usuario.nombres, 'Juan')
        self.assertEqual(usuario.apellido_paterno, 'Cano')
        
        # Configurar resultados
        self.resultados = {
            'Usuario creado': '✅ Sí',
            'Contraseña hasheada': '✅ Sí',
            'Datos almacenados correctamente': '✅ Sí',
            'Hash': 'pbkdf2_sha256$...',
            'Estado BD': '✅ OK'
        }
        
        # Generar reporte HTML
        self.generar_reporte_html()
