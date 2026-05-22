from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Sum
from decimal import Decimal

from usuarios.models import Usuario
from .models import Cuenta, SubCuenta, TransferenciaSubCuenta, TransferenciaCuentaPrincipal
from .api_serializers import CuentaSerializer, SubCuentaSerializer, TransferenciaSubCuentaSerializer, TransferenciaCuentaPrincipalSerializer

from .utils import (
    obtener_cuentas_usuario,
    obtener_estadisticas_subcuentas,
    obtener_balance_total,
    obtener_cuentas_con_subcuentas,
    obtener_subcuentas_independientes,
    obtener_transferencias_recientes,
    es_subcuenta_negocio
)
from .helpers import (
    crear_notificacion_movimiento,
    validar_permisos_subcuenta,
    validar_permisos_ambas_subcuentas,
    validar_password,
    validar_pin_cambio
)
from .services import (
    actualizar_perfil_usuario,
    actualizar_contacto_usuario,
    cambiar_password_usuario,
    cambiar_pin_usuario,
    procesar_transferencia_entre_subcuentas,
    procesar_deposito_subcuenta,
    procesar_transferencia_a_principal
)

class DashboardStatsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        stats = obtener_estadisticas_subcuentas(user)
        cuentas_con_subcuentas = obtener_cuentas_con_subcuentas(user)
        subcuentas_independientes = obtener_subcuentas_independientes(user)
        transferencias_recientes = obtener_transferencias_recientes(user)
        balance_total = obtener_balance_total(user)
        cuenta_principal = obtener_cuentas_usuario(user).first()

        # Serializar subcuentas vinculadas e independientes
        cuentas_data = []
        for cuenta in cuentas_con_subcuentas:
            cuentas_data.append({
                'cuenta': CuentaSerializer(cuenta).data,
                'subcuentas': SubCuentaSerializer(cuenta.subcuentas.filter(activa=True), many=True).data
            })

        return Response({
            'stats': {
                'total_subcuentas': stats['total'],
                'total_subcuentas_vinculadas': stats['total_vinculadas'],
                'total_subcuentas_independientes': stats['total_independientes'],
                'total_subcuentas_inactivas': stats['total_inactivas'],
                'total_saldo_subcuentas': stats['saldo_total'],
                'total_saldo_subcuentas_vinculadas': stats['saldo_vinculadas'],
                'total_saldo_subcuentas_independientes': stats['saldo_independientes'],
            },
            'cuentas_con_subcuentas': cuentas_data,
            'subcuentas_independientes_activas': SubCuentaSerializer(subcuentas_independientes['activas'], many=True).data,
            'subcuentas_independientes_inactivas': SubCuentaSerializer(subcuentas_independientes['inactivas'], many=True).data,
            'balance_total': balance_total,
            'cuenta_principal': CuentaSerializer(cuenta_principal).data if cuenta_principal else None,
        })

class SubCuentaListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubCuentaSerializer

    def get_queryset(self):
        return SubCuenta.objects.filter(
            Q(id_cuenta__id_usuario=self.request.user) | Q(propietario=self.request.user),
            activa=True
        )

    def perform_create(self, serializer):
        user = self.request.user
        tipo_subcuenta = self.request.data.get('tipo_subcuenta', 'personal') # 'personal' o 'business'
        
        cuenta_principal = Cuenta.objects.filter(id_usuario=user).first()
        if not cuenta_principal and tipo_subcuenta != 'business':
            raise serializers.ValidationError('Necesitas tener una cuenta principal para crear subcuentas personales.')

        with transaction.atomic():
            if tipo_subcuenta == 'business':
                serializer.save(
                    propietario=user,
                    id_cuenta=None,
                    es_negocio=True,
                    saldo=0,
                    activa=True
                )
            else:
                serializer.save(
                    id_cuenta=cuenta_principal,
                    propietario=None,
                    es_negocio=False,
                    saldo=0,
                    activa=True
                )

class SubCuentaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubCuentaSerializer

    def get_queryset(self):
        return SubCuenta.objects.filter(
            Q(id_cuenta__id_usuario=self.request.user) | Q(propietario=self.request.user)
        )

    def perform_destroy(self, instance):
        # Desactivación en lugar de borrado físico
        with transaction.atomic():
            if instance.saldo > 0:
                if instance.id_cuenta:
                    instance.id_cuenta.saldo_cuenta += instance.saldo
                    instance.id_cuenta.save()
                    instance.saldo = 0
            instance.activa = False
            instance.save()

class SubCuentaActivarAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        subcuenta = get_object_or_404(SubCuenta, id=pk, id_cuenta__id_usuario=request.user)
        subcuenta.activa = True
        subcuenta.save()
        return Response({'success': True, 'message': 'Subcuenta activada exitosamente.'})

# --- Transacciones ---

class TransferenciaSubCuentaListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransferenciaSubCuentaSerializer

    def get_queryset(self):
        return TransferenciaSubCuenta.objects.filter(id_usuario=self.request.user)

    def post(self, request, *args, **kwargs):
        subcuenta_origen_id = request.data.get('subcuenta_origen')
        subcuenta_destino_id = request.data.get('subcuenta_destino')
        monto = Decimal(str(request.data.get('monto', '0')))
        
        if monto <= 0:
            return Response({'error': 'El monto debe ser mayor a 0'}, status=status.HTTP_400_BAD_REQUEST)
        
        if subcuenta_origen_id == subcuenta_destino_id:
            return Response({'error': 'No puedes transferir a la misma subcuenta'}, status=status.HTTP_400_BAD_REQUEST)
            
        subcuenta_origen = get_object_or_404(SubCuenta, id=subcuenta_origen_id)
        subcuenta_destino = get_object_or_404(SubCuenta, id=subcuenta_destino_id)
        
        if not validar_permisos_ambas_subcuentas(request.user, subcuenta_origen, subcuenta_destino):
            return Response({'error': 'No tienes permisos sobre estas subcuentas'}, status=status.HTTP_403_FORBIDDEN)
            
        success, message = procesar_transferencia_entre_subcuentas(
            subcuenta_origen,
            subcuenta_destino,
            monto,
            request.user,
            request.data.get('descripcion', '')
        )
        
        if success:
            crear_notificacion_movimiento(
                usuario=request.user,
                titulo="🔄 Transferencia entre subcuentas",
                mensaje=message,
                datos_adicionales={
                    'tipo_movimiento': 'transferencia_entre_subcuentas',
                    'subcuenta_origen_id': subcuenta_origen.id,
                    'subcuenta_destino_id': subcuenta_destino.id,
                    'monto': float(monto)
                }
            )
            return Response({'success': True, 'message': message})
            
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

class TransferenciaCuentaPrincipalListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransferenciaCuentaPrincipalSerializer

    def get_queryset(self):
        return TransferenciaCuentaPrincipal.objects.filter(id_usuario=self.request.user)

    def post(self, request, *args, **kwargs):
        subcuenta_id = request.data.get('subcuenta')
        monto = Decimal(str(request.data.get('monto', '0')))
        tipo = request.data.get('tipo') # 'deposito' o 'retiro'
        descripcion = request.data.get('descripcion', '')

        if monto <= 0:
            return Response({'error': 'El monto debe ser mayor a 0'}, status=status.HTTP_400_BAD_REQUEST)

        subcuenta = get_object_or_404(SubCuenta, id=subcuenta_id)
        if not validar_permisos_subcuenta(request.user, subcuenta):
            return Response({'error': 'No tienes permisos sobre esta subcuenta'}, status=status.HTTP_403_FORBIDDEN)

        cuenta_principal = request.user.cuenta_set.first()
        if not cuenta_principal:
            return Response({'error': 'No tienes una cuenta principal'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if tipo == 'deposito': # De subcuenta a principal
                success, message = procesar_transferencia_a_principal(
                    subcuenta, cuenta_principal, monto, request.user, tipo='deposito', descripcion=descripcion
                )
            else: # De principal a subcuenta
                success, message = procesar_deposito_subcuenta(
                    subcuenta, monto, request.user, descripcion
                )

        if success:
            return Response({'success': True, 'message': message})
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

# --- Perfil y Seguridad de Cuentas ---

class UpdateProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        usuario = request.user
        nombres = request.data.get("nombres", "").strip()
        apellido_paterno = request.data.get("apellido_paterno", "").strip()
        apellido_materno = request.data.get("apellido_materno", "").strip()
        pais = request.data.get("pais", "").strip()

        if nombres and apellido_paterno and pais:
            actualizar_perfil_usuario(usuario, nombres, apellido_paterno, apellido_materno, pais)
            return Response({'success': True, 'message': 'Información personal actualizada correctamente.'})
        return Response({'error': 'Los campos Nombres, Apellido Paterno y País son obligatorios.'}, status=status.HTTP_400_BAD_REQUEST)

class UpdateContactAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        usuario = request.user
        email = request.data.get("email", "").strip()
        telefono = request.data.get("telefono", "").strip()

        if email:
            if Usuario.objects.filter(correo=email).exclude(id=usuario.id).exists():
                return Response({'error': 'Este correo electrónico ya está siendo usado por otro usuario.'}, status=status.HTTP_400_BAD_REQUEST)
            actualizar_contacto_usuario(usuario, email, telefono)
            return Response({'success': True, 'message': 'Información de contacto actualizada correctamente.'})
        return Response({'error': 'El correo electrónico es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        usuario = request.user
        actual_password = request.data.get("actual_password", "").strip()
        new_password = request.data.get("new_password", "").strip()
        confirm_password = request.data.get("confirm_password", "").strip()

        error_msg = validar_password(actual_password, new_password, confirm_password)
        if error_msg:
            return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)

        success, msg = cambiar_password_usuario(usuario, actual_password, new_password, request)
        if success:
            return Response({'success': True, 'message': msg})
        return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

class ChangePinAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        usuario = request.user
        current_pin = request.data.get("actual_pin", "").strip()
        new_pin = request.data.get("new_pin", "").strip()
        confirm_pin = request.data.get("confirm_pin", "").strip()

        error_msg = validar_pin_cambio(usuario, current_pin, new_pin, confirm_pin)
        if error_msg:
            return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)

        success, msg = cambiar_pin_usuario(usuario, current_pin, new_pin)
        if success:
            return Response({'success': True, 'message': msg})
        return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)
