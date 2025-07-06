from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class TipoNotificacion(models.Model):
    """Tipos de notificaciones del sistema"""
    CATEGORIAS = (
        ('critical', 'Crítica'),
        ('warning', 'Advertencia'), 
        ('info', 'Informativa'),
    )
    
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    descripcion = models.TextField()
    icono = models.CharField(max_length=50)  # Clase CSS o emoji
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre


class ConfiguracionNotificacion(models.Model):
    """Configuraciones personalizadas por usuario"""
    FRECUENCIAS = (
        ('instant', 'Instantáneo'),
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
    )
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo_notificacion = models.ForeignKey(TipoNotificacion, on_delete=models.CASCADE)
    
    # Canales habilitados
    email_habilitado = models.BooleanField(default=True)
    push_habilitado = models.BooleanField(default=True)
    sms_habilitado = models.BooleanField(default=False)
    
    # Configuraciones específicas
    frecuencia_resumen = models.CharField(max_length=20, choices=FRECUENCIAS, default='weekly')
    umbral_monto = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    horario_envio = models.TimeField(default='09:00:00')
    dias_anticipacion = models.IntegerField(default=3)
    
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['usuario', 'tipo_notificacion']
    
    def __str__(self):
        return f"{self.usuario.nombres} - {self.tipo_notificacion.nombre}"


class Notificacion(models.Model):
    """Registro de notificaciones enviadas"""
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('enviada', 'Enviada'),
        ('leida', 'Leída'),
        ('archivada', 'Archivada'),
        ('error', 'Error'),
    )
    
    PRIORIDADES = (
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    )
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo_notificacion = models.ForeignKey(TipoNotificacion, on_delete=models.CASCADE)
    
    # Contenido
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    datos_adicionales = models.JSONField(default=dict, blank=True)  # Datos contextuales
    
    # Metadatos
    categoria = models.CharField(max_length=50)  # ej: 'Saldo', 'Metas', 'Transacciones'
    modulo_origen = models.CharField(max_length=50)  # ej: 'gestion_financiera_basica'
    objeto_relacionado = models.CharField(max_length=100, null=True, blank=True)  # ID del objeto que generó la notificación
    
    # Estado y control
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    prioridad = models.CharField(max_length=20, choices=PRIORIDADES, default='media')
    
    # Canales y entrega
    email_enviado = models.BooleanField(default=False)
    push_enviado = models.BooleanField(default=False)
    sms_enviado = models.BooleanField(default=False)
    
    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    fecha_expiracion = models.DateTimeField(null=True, blank=True)
    
    # Acciones
    url_accion = models.URLField(null=True, blank=True)  # URL para acción relacionada
    etiquetas = models.JSONField(default=list, blank=True)  # Tags para filtrado
    
    class Meta:
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['usuario', 'estado']),
            models.Index(fields=['categoria', 'fecha_creacion']),
            models.Index(fields=['tipo_notificacion', 'fecha_creacion']),
        ]
    
    def __str__(self):
        return f"{self.titulo} - {self.usuario.nombres}"


class PlantillaNotificacion(models.Model):
    """Plantillas para diferentes tipos de notificaciones"""
    tipo_notificacion = models.ForeignKey(TipoNotificacion, on_delete=models.CASCADE)
    
    nombre = models.CharField(max_length=100)
    asunto_email = models.CharField(max_length=200)
    plantilla_email = models.TextField()
    plantilla_push = models.TextField()
    plantilla_sms = models.CharField(max_length=160, blank=True)
    
    # Variables disponibles en las plantillas
    variables_disponibles = models.JSONField(default=list)
    
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nombre} - {self.tipo_notificacion.nombre}"
