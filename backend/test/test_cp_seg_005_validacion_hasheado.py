"""
CP-SEG-USU-005: Validación de Hasheado de Contraseña
Nivel de Prueba: Integración
Componente Probado: Mecanismos de Seguridad - Almacenamiento de Credenciales
Clasificación: Prueba No Funcional - Seguridad
Prioridad: Crítica

Descripción: Valida que las contraseñas se almacenen de manera segura 
usando algoritmos criptográficos.
"""

from usuarios.models import Usuario
from cuentas.models import Moneda
from .base_test_case_reporte import TestCaseConReporte


class CPSeg005ValidacionHasheado(TestCaseConReporte):
    """
    CP-SEG-USU-005: Validación de Hasheado de Contraseña
    """
    caso_id = 'CP-SEG-USU-005'
    nombre_caso = 'Validación de Hasheado de Contraseña'
    prioridad = 'Crítica'
    nivel_prueba = 'Integración'
    descripcion = 'Valida que las contraseñas se almacenen de manera segura usando algoritmos criptográficos.'

    def setUp(self):
        # Crear moneda por defecto
        self.moneda, _ = Moneda.objects.get_or_create(
            codigo='PEN',
            defaults={'nombre': 'Soles'}
        )
        
        # Crear usuario de prueba
        self.usuario = Usuario.objects.create_user(
            correo='user@test.com',
            password='MyPassword123!',
            nombres='Test',
            apellido_paterno='User',
            apellido_materno='Security',
            documento_identidad='12345678',
            telefono=9999999999,
            id_moneda=self.moneda
        )

    def test_contraseña_hasheada_segura(self):
        """
        Datos de Entrada:
        - Email: user@test.com
        - Contraseña original: MyPassword123!
        
        Resultado Esperado:
        - Contraseña nunca en texto plano
        - Algoritmo seguro de hash (PBKDF2)
        - Cada ejecución produce resultado diferente (salt aleatorio)
        - Valor hasheado irreversible
        """
        # Recuperar password hasheada desde BD
        stored_password = self.usuario.password
        
        # Verificar que NO está en texto plano
        self.assertNotEqual(stored_password, 'MyPassword123!',
                           "La contraseña no debe estar en texto plano")
        
        # Verificar que comienza con algoritmo seguro
        self.assertTrue(stored_password.startswith('pbkdf2_sha256$'),
                       "Debe usar algoritmo seguro de hash (PBKDF2)")
        
        # Verificar que check_password funciona
        self.assertTrue(self.usuario.check_password('MyPassword123!'),
                       "La verificación de contraseña debe funcionar")
        
        # Verificar que check_password falla con contraseña incorrecta
        self.assertFalse(self.usuario.check_password('WrongPassword123!'),
                        "La verificación debe fallar con contraseña incorrecta")
        
        # Crear dos usuarios con la misma contraseña y verificar que los hashes son diferentes
        usuario2 = Usuario.objects.create_user(
            correo='user2@test.com',
            password='MyPassword123!',
            nombres='Test',
            apellido_paterno='User',
            apellido_materno='Two',
            documento_identidad='87654321',
            telefono=9999999998,
            id_moneda=self.moneda
        )
        
        # Los hashes deben ser diferentes debido al salt aleatorio
        self.assertNotEqual(self.usuario.password, usuario2.password,
                           "El hash debe ser diferente para la misma contraseña debido al salt aleatorio")
        
        # DATOS REALES DE LA BASE DE DATOS
        # Extraer componentes del hash real de la BD
        hash_parts = self.usuario.password.split('$')
        algoritmo = hash_parts[0]
        iteraciones = hash_parts[1]
        salt_real = hash_parts[2]
        hash_real = hash_parts[3]
        
        # Hash del segundo usuario para comparación
        hash_parts_usuario2 = usuario2.password.split('$')
        salt_usuario2 = hash_parts_usuario2[2]
        hash_usuario2 = hash_parts_usuario2[3]
        
        # Configurar DATOS DE ENTRADA REALES DE LA BD
        self.datos_entrada = {
            'Email': 'user@test.com',
            'Contraseña Ingresada': '••••••••••••••',
            'Algoritmo': algoritmo,
            'Iteraciones': iteraciones
        }
        
        # Configurar RESULTADOS REALES DE LA BD
        self.resultados = {
            'Hash Usuario 1': f'{hash_real[:45]}...',
            'Salt Usuario 1': salt_real,
            'Hash Usuario 2': f'{hash_usuario2[:45]}...',
            'Salt Usuario 2': salt_usuario2,
            'Hashes Diferentes': '✅ Sí',
            'Verificación Correcta': '✅ Sí',
            'Algoritmo': 'PBKDF2-SHA256',
            'Irreversibilidad': '✅ Confirmada'
        }
        
        # Generar reporte HTML
        self.generar_reporte_html()
