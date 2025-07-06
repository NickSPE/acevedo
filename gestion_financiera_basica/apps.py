from django.apps import AppConfig


class GestionFinancieraBasicaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gestion_financiera_basica"
    
    def ready(self):
        """Importar señales cuando la aplicación esté lista"""
        import gestion_financiera_basica.signals
