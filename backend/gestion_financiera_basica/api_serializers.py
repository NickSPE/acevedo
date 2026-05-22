from rest_framework import serializers
from .models import Movimiento, MetaAhorro, AporteMetaAhorro
from cuentas.api_serializers import CuentaSerializer

class MovimientoSerializer(serializers.ModelSerializer):
    categoria_display_emoji = serializers.CharField(source='get_categoria_display_emoji', read_only=True)
    cuenta_detalle = CuentaSerializer(source='id_cuenta', read_only=True)

    class Meta:
        model = Movimiento
        fields = [
            'id', 'nombre', 'tipo', 'categoria', 'monto', 'fecha_movimiento', 
            'descripcion', 'id_cuenta', 'id_usuario', 'categoria_display_emoji',
            'cuenta_detalle'
        ]
        read_only_fields = ['id_usuario']

class AporteMetaAhorroSerializer(serializers.ModelSerializer):
    class Meta:
        model = AporteMetaAhorro
        fields = ['id', 'id_meta_ahorro', 'monto', 'fecha_aporte', 'descripcion', 'id_usuario']
        read_only_fields = ['id_usuario', 'fecha_aporte']

class MetaAhorroSerializer(serializers.ModelSerializer):
    monto_ahorrado = serializers.ReadOnlyField()
    porcentaje_progreso = serializers.ReadOnlyField()
    falta_por_ahorrar = serializers.ReadOnlyField()
    meta_alcanzada = serializers.ReadOnlyField()
    aportes = AporteMetaAhorroSerializer(many=True, read_only=True)
    cuenta_detalle = CuentaSerializer(source='id_cuenta', read_only=True)

    class Meta:
        model = MetaAhorro
        fields = [
            'id', 'fecha_inicio', 'fecha_limite', 'monto_objetivo', 
            'frecuencia_aporte', 'descripcion', 'nombre', 'id_usuario', 
            'id_cuenta', 'monto_ahorrado', 'porcentaje_progreso', 
            'falta_por_ahorrar', 'meta_alcanzada', 'aportes', 'cuenta_detalle'
        ]
        read_only_fields = ['id_usuario']
