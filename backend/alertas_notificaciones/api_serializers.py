from rest_framework import serializers
from .models import TipoNotificacion, ConfiguracionNotificacion, Notificacion

class TipoNotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoNotificacion
        fields = ['id', 'nombre', 'descripcion', 'activo']

class ConfiguracionNotificacionSerializer(serializers.ModelSerializer):
    tipo_notificacion_detalle = TipoNotificacionSerializer(source='tipo_notificacion', read_only=True)

    class Meta:
        model = ConfiguracionNotificacion
        fields = [
            'id', 'usuario', 'tipo_notificacion', 'tipo_notificacion_detalle',
            'email_habilitado', 'push_habilitado', 'sms_habilitado', 
            'activo', 'umbral_monto', 'frecuencia_resumen'
        ]
        read_only_fields = ['usuario']

class NotificacionSerializer(serializers.ModelSerializer):
    tipo_notificacion_detalle = TipoNotificacionSerializer(source='tipo_notificacion', read_only=True)
    relative_time = serializers.SerializerMethodField()

    class Meta:
        model = Notificacion
        fields = [
            'id', 'usuario', 'tipo_notificacion', 'tipo_notificacion_detalle',
            'titulo', 'mensaje', 'estado', 'prioridad', 'categoria', 
            'fecha_creacion', 'fecha_lectura', 'url_accion', 
            'email_enviado', 'push_enviado', 'relative_time'
        ]
        read_only_fields = ['usuario', 'fecha_creacion', 'fecha_lectura', 'email_enviado', 'push_enviado']

    def get_relative_time(self, obj):
        from .utils import get_relative_time
        return get_relative_time(obj.fecha_creacion)
