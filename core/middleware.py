# core/middleware.py
import os
import time
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.core.cache import cache

class ServerRestartSessionMiddleware:
    """
    Middleware que limpia sesiones cuando el servidor se reinicia
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.server_start_time = time.time()
        
        # Limpiar sesiones al iniciar el servidor
        self.cleanup_sessions_on_startup()

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def cleanup_sessions_on_startup(self):
        """Limpia sesiones al inicio del servidor"""
        try:
            # Verificar si es un reinicio real del servidor
            cache_key = 'server_last_start'
            last_start = cache.get(cache_key)
            
            if not last_start or (time.time() - last_start) > 60:  # Más de 1 minuto
                print("🔄 Servidor reiniciado - Limpiando sesiones...")
                
                # Eliminar todas las sesiones activas
                deleted_count = Session.objects.all().delete()[0]
                print(f"🗑️  {deleted_count} sesiones eliminadas")
                
                # Guardar tiempo de inicio en cache
                cache.set(cache_key, time.time(), timeout=3600)  # 1 hora
                
        except Exception as e:
            print(f"❌ Error limpiando sesiones: {e}")
