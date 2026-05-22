from rest_framework import serializers
from .models import Usuario
from cuentas.models import Moneda, Cuenta

class MonedaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Moneda
        fields = ['id', 'codigo', 'nombre', 'simbolo']

class UsuarioSerializer(serializers.ModelSerializer):
    moneda_detalle = MonedaSerializer(source='id_moneda', read_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'documento_identidad', 'nombres', 'apellido_paterno', 
            'apellido_materno', 'correo', 'telefono', 'pais', 
            'email_verificado', 'onboarding_completed', 'pin_acceso_rapido', 
            'moneda_detalle', 'id_moneda'
        ]
        extra_kwargs = {
            'pin_acceso_rapido': {'write_only': True}
        }

class RegistroUsuarioSerializer(serializers.Serializer):
    documento_identidad = serializers.CharField(max_length=25, required=False, default='00000000')
    nombres = serializers.CharField(max_length=100)
    apellido_paterno = serializers.CharField(max_length=50)
    apellido_materno = serializers.CharField(max_length=50)
    correo = serializers.EmailField(max_length=100)
    contrasena = serializers.CharField(write_only=True)
    telefono = serializers.IntegerField(required=False, default=0)
    pin_acceso_rapido = serializers.CharField(max_length=6, required=False, default='000000')
    id_moneda = serializers.IntegerField()
    
    # Datos de cuenta principal inicial
    nombre_cuenta = serializers.CharField(max_length=50, required=False, default='Cuenta principal')
    saldo_inicial = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, default=0.0)
    descripcion_cuenta = serializers.CharField(max_length=300, required=False, allow_blank=True, default='')

    def validate_correo(self, value):
        if Usuario.objects.filter(correo=value).exists():
            raise serializers.ValidationError("El correo ya está registrado.")
        return value

    def validate_id_moneda(self, value):
        if not Moneda.objects.filter(id=value).exists():
            raise serializers.ValidationError("La moneda seleccionada no es válida.")
        return value

    def create(self, validated_data):
        moneda_obj = Moneda.objects.get(id=validated_data['id_moneda'])
        
        nuevo_usuario = Usuario.objects.create_user(
            documento_identidad=validated_data.get('documento_identidad', '00000000'),
            nombres=validated_data['nombres'],
            apellido_paterno=validated_data['apellido_paterno'],
            apellido_materno=validated_data['apellido_materno'],
            correo=validated_data['correo'],
            password=validated_data['contrasena'],
            telefono=validated_data.get('telefono', 0),
            pin_acceso_rapido=validated_data.get('pin_acceso_rapido', '000000'),
            email_verificado=True, # Verificado via flow
            id_moneda=moneda_obj
        )
        
        # Crear la cuenta principal
        Cuenta.objects.create(
            id_usuario=nuevo_usuario,
            nombre=validated_data.get('nombre_cuenta', 'Cuenta principal'),
            saldo_cuenta=validated_data.get('saldo_inicial', 0.0),
            descripcion=validated_data.get('descripcion_cuenta', '')
        )
        
        return nuevo_usuario
