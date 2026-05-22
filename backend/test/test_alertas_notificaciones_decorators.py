"""
Tests unitarios para los decoradores de señales y locks de caché
Ubicación: test/test_alertas_notificaciones_decorators.py
"""

from django.test import TestCase
from unittest.mock import MagicMock, patch
from django.core.cache import cache
from alertas_notificaciones.signal_decorators import (
    SignalLock,
    prevent_duplicate_signals
)


class SignalDecoratorsTestCase(TestCase):
    def setUp(self):
        # Crear un mock de instancia del modelo
        self.mock_instance = MagicMock()
        self.mock_instance.__class__.__name__ = "Cuenta"
        self.mock_instance.id = 123
        
        # Mock de relación de usuario
        self.mock_user = MagicMock()
        self.mock_user.id = 456
        self.mock_instance.id_usuario = self.mock_user

    def test_signal_lock_create_key(self):
        """Valida que la clave de lock generada contenga el hash MD5 adecuado"""
        key1 = SignalLock.create_lock_key("test_signal", self.mock_instance, user_id=456)
        key2 = SignalLock.create_lock_key("test_signal", self.mock_instance, user_id=456)
        
        # Puesto que agrupa por 5 segundos, deben ser iguales en la misma ejecución
        self.assertEqual(key1, key2)
        self.assertTrue(key1.startswith("signal_lock_"))
        
        # Con diferente usuario debe ser diferente clave
        key3 = SignalLock.create_lock_key("test_signal", self.mock_instance, user_id=999)
        self.assertNotEqual(key1, key3)

    @patch('alertas_notificaciones.signal_decorators.cache')
    def test_signal_lock_acquire_and_release(self, mock_cache):
        """Valida adquisición atómica y liberación del lock"""
        mock_cache.add.return_value = True
        
        acquired = SignalLock.acquire_lock("some_key", timeout=15)
        self.assertTrue(acquired)
        mock_cache.add.assert_called_with("some_key", True, 15)
        
        # Liberar
        SignalLock.release_lock("some_key")
        mock_cache.delete.assert_called_with("some_key")

    @patch('alertas_notificaciones.signal_decorators.cache')
    def test_signal_lock_acquire_failure(self, mock_cache):
        """Valida retorno False si el lock ya existe o si ocurre excepción en caché"""
        mock_cache.add.return_value = False
        acquired = SignalLock.acquire_lock("some_key")
        self.assertFalse(acquired)
        
        # Lanzar excepción
        mock_cache.add.side_effect = Exception("Cache down")
        acquired_exc = SignalLock.acquire_lock("some_key")
        self.assertFalse(acquired_exc)

    @patch('alertas_notificaciones.signal_decorators.SignalLock')
    def test_prevent_duplicate_signals_decorator_executed(self, mock_signal_lock):
        """Valida que ejecute la señal decorada si adquiere el lock exitosamente"""
        mock_signal_lock.create_lock_key.return_value = "lock_test_key"
        mock_signal_lock.acquire_lock.return_value = True
        
        # Función receptora simulada
        mock_receiver = MagicMock()
        mock_receiver.__name__ = "dummy_receiver"
        
        decorated_func = prevent_duplicate_signals("dummy_signal")(mock_receiver)
        
        # Ejecución
        result = decorated_func(sender=None, instance=self.mock_instance, created=True)
        
        mock_receiver.assert_called_once_with(None, self.mock_instance, True)
        mock_signal_lock.release_lock.assert_called_with("lock_test_key")

    @patch('alertas_notificaciones.signal_decorators.SignalLock')
    def test_prevent_duplicate_signals_decorator_blocked(self, mock_signal_lock):
        """Valida que no ejecute la señal y retorne None si no puede adquirir el lock"""
        mock_signal_lock.create_lock_key.return_value = "lock_test_key"
        mock_signal_lock.acquire_lock.return_value = False
        
        mock_receiver = MagicMock()
        mock_receiver.__name__ = "dummy_receiver"
        
        decorated_func = prevent_duplicate_signals("dummy_signal")(mock_receiver)
        
        result = decorated_func(sender=None, instance=self.mock_instance, created=True)
        
        self.assertIsNone(result)
        mock_receiver.assert_not_called()
        mock_signal_lock.release_lock.assert_not_called()

    def test_prevent_duplicate_signals_not_created(self):
        """Valida que si created=False (actualización), pase directo sin adquirir locks"""
        mock_receiver = MagicMock()
        mock_receiver.__name__ = "dummy_receiver"
        
        with patch('alertas_notificaciones.signal_decorators.SignalLock') as mock_signal_lock:
            decorated_func = prevent_duplicate_signals("dummy_signal")(mock_receiver)
            
            # created=False
            decorated_func(sender=None, instance=self.mock_instance, created=False)
            
            mock_receiver.assert_called_once_with(None, self.mock_instance, False)
            mock_signal_lock.acquire_lock.assert_not_called()
