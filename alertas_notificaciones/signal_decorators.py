"""
Decorador para prevenir ejecución múltiple de signals
"""
import time
import hashlib
from django.core.cache import cache
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class SignalLock:
    """Sistema de locks para signals usando cache de Django"""
    
    @staticmethod
    def create_lock_key(signal_name, instance, user_id=None):
        """Crea una clave única para el lock basada en el signal y el objeto"""
        # Crear un hash único basado en los parámetros del signal
        lock_data = f"{signal_name}_{instance.__class__.__name__}_{instance.id}"
        
        if user_id:
            lock_data += f"_{user_id}"
            
        # Agregar timestamp redondeado a 5 segundos para agrupar ejecuciones cercanas
        rounded_time = int(time.time() // 5) * 5
        lock_data += f"_{rounded_time}"
        
        # Crear hash MD5
        return f"signal_lock_{hashlib.md5(lock_data.encode()).hexdigest()}"
    
    @staticmethod
    def acquire_lock(lock_key, timeout=30):
        """Intenta adquirir un lock"""
        try:
            # Usar cache.add que es atómico - solo crea si no existe
            acquired = cache.add(lock_key, True, timeout)
            if acquired:
                logger.debug(f"Lock adquirido: {lock_key}")
            else:
                logger.debug(f"Lock ya existe: {lock_key}")
            return acquired
        except Exception as e:
            logger.error(f"Error adquiriendo lock {lock_key}: {str(e)}")
            return False
    
    @staticmethod
    def release_lock(lock_key):
        """Libera un lock"""
        try:
            cache.delete(lock_key)
            logger.debug(f"Lock liberado: {lock_key}")
        except Exception as e:
            logger.error(f"Error liberando lock {lock_key}: {str(e)}")


def prevent_duplicate_signals(signal_name, timeout=30):
    """
    Decorador para prevenir ejecución múltiple de signals
    
    Args:
        signal_name: Nombre identificador del signal
        timeout: Tiempo en segundos que dura el lock
    """
    def decorator(func):
        @wraps(func)
        def wrapper(sender, instance, created=None, **kwargs):
            # Solo aplicar para creaciones nuevas
            if created is False:
                return func(sender, instance, created, **kwargs)
            
            # Determinar user_id si está disponible
            user_id = None
            if hasattr(instance, 'id_usuario'):
                user_id = instance.id_usuario.id
            elif hasattr(instance, 'usuario'):
                user_id = instance.usuario.id
            
            # Crear clave de lock
            lock_key = SignalLock.create_lock_key(signal_name, instance, user_id)
            
            # Intentar adquirir lock
            if SignalLock.acquire_lock(lock_key, timeout):
                try:
                    logger.info(f"Ejecutando signal {signal_name} para {instance.__class__.__name__}:{instance.id}")
                    result = func(sender, instance, created, **kwargs)
                    logger.info(f"Signal {signal_name} ejecutado exitosamente")
                    return result
                except Exception as e:
                    logger.error(f"Error en signal {signal_name}: {str(e)}")
                    raise
                finally:
                    # Liberar lock después de un breve delay para evitar race conditions
                    SignalLock.release_lock(lock_key)
            else:
                logger.warning(f"Signal {signal_name} ya en ejecución para {instance.__class__.__name__}:{instance.id}, saltando...")
                return None
        
        return wrapper
    return decorator
