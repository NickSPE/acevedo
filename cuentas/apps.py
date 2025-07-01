from django.apps import AppConfig


class CuentasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cuentas"
<<<<<<< HEAD
    
    def ready(self):
        import cuentas.signals
=======
>>>>>>> bba8140 (Corrige problemas con migraciones)
