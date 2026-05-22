"""
Tests unitarios para el middleware ServerRestartSessionMiddleware de core
Ubicación: test/test_core_middleware.py
"""

import time
from django.test import TestCase
from unittest.mock import MagicMock, patch
from core.middleware import ServerRestartSessionMiddleware


class ServerRestartSessionMiddlewareTestCase(TestCase):
    
    @patch('core.middleware.cache')
    @patch('core.middleware.Session.objects')
    def test_middleware_cleanup_sessions_on_startup_first_time(self, mock_session_objects, mock_cache):
        """Valida que en el primer inicio (o tras expiración) elimine las sesiones y actualice el caché"""
        mock_cache.get.return_value = None  # No hay registro previo de arranque en caché
        
        # Mock de delete() que retorna un tuple (deleted_count, {...})
        mock_delete = MagicMock()
        mock_delete.return_value = (5, {})
        mock_session_objects.all.return_value.delete = mock_delete
        
        # Inicializar el middleware
        get_response_mock = MagicMock()
        middleware = ServerRestartSessionMiddleware(get_response_mock)
        
        # Verificar que se llamó a cache.get con la clave correcta
        mock_cache.get.assert_called_with('server_last_start')
        
        # Verificar que se eliminaron sesiones
        mock_session_objects.all.assert_called_once()
        mock_delete.assert_called_once()
        
        # Verificar que guardó en cache el nuevo timestamp con timeout de 3600
        mock_cache.set.assert_called_once()
        called_args = mock_cache.set.call_args[0]
        self.assertEqual(called_args[0], 'server_last_start')
        self.assertAlmostEqual(called_args[1], time.time(), delta=2)
        self.assertEqual(mock_cache.set.call_args[1]['timeout'], 3600)

    @patch('core.middleware.cache')
    @patch('core.middleware.Session.objects')
    def test_middleware_cleanup_sessions_on_startup_already_running(self, mock_session_objects, mock_cache):
        """Valida que no limpie sesiones si el servidor arrancó recientemente (menos de 60 segundos)"""
        # Simular que el servidor arrancó hace 10 segundos
        mock_cache.get.return_value = time.time() - 10
        
        get_response_mock = MagicMock()
        middleware = ServerRestartSessionMiddleware(get_response_mock)
        
        # No se debe haber llamado a all() ni delete() en Session
        mock_session_objects.all.assert_not_called()
        mock_cache.set.assert_not_called()

    @patch('core.middleware.cache')
    def test_middleware_cleanup_sessions_exception(self, mock_cache):
        """Valida que si ocurre una excepción de base de datos o caché, se capture silenciosamente"""
        mock_cache.get.side_effect = Exception("Cache Connection Failed")
        
        get_response_mock = MagicMock()
        # No debe lanzar excepción
        middleware = ServerRestartSessionMiddleware(get_response_mock)

    @patch('core.middleware.cache')
    def test_middleware_call(self, mock_cache):
        """Valida que la llamada al middleware procese correctamente el request y devuelva la respuesta"""
        mock_cache.get.return_value = time.time()
        
        # Mock de request y response
        mock_request = MagicMock()
        mock_response = MagicMock()
        
        get_response_mock = MagicMock()
        get_response_mock.return_value = mock_response
        
        middleware = ServerRestartSessionMiddleware(get_response_mock)
        
        # Ejecución
        response = middleware(mock_request)
        
        self.assertEqual(response, mock_response)
        get_response_mock.assert_called_with(mock_request)
