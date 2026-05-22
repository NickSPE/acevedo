from rest_framework import serializers
from .models import Cuenta, SubCuenta, TransferenciaSubCuenta, TransferenciaCuentaPrincipal, Moneda
from usuarios.api_serializers import UsuarioSerializer

class MonedaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Moneda
        fields = ['id', 'codigo', 'nombre', 'simbolo']

class CuentaSerializer(serializers.ModelSerializer):
    saldo_total_subcuentas = serializers.ReadOnlyField()
    saldo_disponible = serializers.ReadOnlyField()
    id_usuario = UsuarioSerializer(read_only=True)

    class Meta:
        model = Cuenta
        fields = ['id', 'nombre', 'descripcion', 'saldo_cuenta', 'id_usuario', 'saldo_total_subcuentas', 'saldo_disponible']

class SubCuentaSerializer(serializers.ModelSerializer):
    progreso_meta = serializers.ReadOnlyField()
    dias_restantes_meta = serializers.ReadOnlyField()
    es_meta_alcanzada = serializers.ReadOnlyField()
    tipo_display_emoji = serializers.CharField(source='get_tipo_display_emoji', read_only=True)
    id_cuenta_detalle = CuentaSerializer(source='id_cuenta', read_only=True)

    class Meta:
        model = SubCuenta
        fields = [
            'id', 'nombre', 'descripcion', 'saldo', 'tipo', 'color', 
            'activa', 'fecha_creacion', 'fecha_modificacion', 'es_negocio', 
            'meta_objetivo', 'fecha_meta', 'id_cuenta', 'propietario',
            'progreso_meta', 'dias_restantes_meta', 'es_meta_alcanzada', 
            'tipo_display_emoji', 'id_cuenta_detalle'
        ]

class TransferenciaSubCuentaSerializer(serializers.ModelSerializer):
    subcuenta_origen_nombre = serializers.CharField(source='subcuenta_origen.nombre', read_only=True)
    subcuenta_destino_nombre = serializers.CharField(source='subcuenta_destino.nombre', read_only=True)

    class Meta:
        model = TransferenciaSubCuenta
        fields = [
            'id', 'subcuenta_origen', 'subcuenta_destino', 'monto', 
            'descripcion', 'fecha_transferencia', 'id_usuario',
            'subcuenta_origen_nombre', 'subcuenta_destino_nombre'
        ]
        read_only_fields = ['id_usuario', 'fecha_transferencia']

class TransferenciaCuentaPrincipalSerializer(serializers.ModelSerializer):
    subcuenta_nombre = serializers.CharField(source='subcuenta.nombre', read_only=True)
    cuenta_destino_nombre = serializers.CharField(source='cuenta_destino.nombre', read_only=True)

    class Meta:
        model = TransferenciaCuentaPrincipal
        fields = [
            'id', 'subcuenta', 'cuenta_destino', 'monto', 'tipo', 
            'descripcion', 'fecha_transferencia', 'id_usuario',
            'subcuenta_nombre', 'cuenta_destino_nombre'
        ]
        read_only_fields = ['id_usuario', 'fecha_transferencia']
