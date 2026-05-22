from rest_framework import serializers
from .models import Reporte, ConfiguracionReporte

class ReporteSerializer(serializers.ModelSerializer):
    datos = serializers.ReadOnlyField(source='get_datos')

    class Meta:
        model = Reporte
        fields = [
            'id', 'tipo_reporte', 'titulo', 'descripcion', 
            'fecha_inicio', 'fecha_fin', 'fecha_creacion', 
            'id_usuario', 'datos'
        ]
        read_only_fields = ['id_usuario', 'fecha_creacion']

class ConfiguracionReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracionReporte
        fields = ['id', 'id_usuario', 'periodo_default', 'mostrar_graficos_default']
        read_only_fields = ['id_usuario']
