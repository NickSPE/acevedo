from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import monthrange
from decimal import Decimal

from cuentas.models import Cuenta
from .models import Movimiento, MetaAhorro, AporteMetaAhorro
from .api_serializers import MovimientoSerializer, MetaAhorroSerializer, AporteMetaAhorroSerializer
from .views import generar_consejos_dinamicos

class MovimientoListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MovimientoSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Movimiento.objects.filter(id_cuenta__id_usuario=user)

        # Filtros
        filter_type = self.request.query_params.get('filter', 'all')
        search_query = self.request.query_params.get('search', '').strip()
        sort_by = self.request.query_params.get('sort', 'newest')

        if filter_type == 'income':
            queryset = queryset.filter(tipo='ingreso')
        elif filter_type == 'expenses':
            queryset = queryset.filter(tipo='egreso')

        if search_query:
            queryset = queryset.filter(
                Q(nombre__icontains=search_query) |
                Q(descripcion__icontains=search_query) |
                Q(id_cuenta__nombre__icontains=search_query)
            )

        if sort_by == 'newest':
            queryset = queryset.order_by('-fecha_movimiento')
        elif sort_by == 'oldest':
            queryset = queryset.order_by('fecha_movimiento')
        elif sort_by == 'highest':
            queryset = queryset.order_by('-monto')
        elif sort_by == 'lowest':
            queryset = queryset.order_by('monto')
        else:
            queryset = queryset.order_by('-fecha_movimiento')

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        cuenta_id = self.request.data.get('id_cuenta')
        cuenta = Cuenta.objects.get(id=cuenta_id, id_usuario=user)

        monto = Decimal(str(self.request.data.get('monto', 0)))
        tipo = self.request.data.get('tipo')

        # Actualizar saldo de la cuenta principal
        if tipo == 'ingreso':
            cuenta.saldo_cuenta += monto
        elif tipo == 'egreso':
            if cuenta.saldo_disponible() < monto:
                raise serializers.ValidationError('No hay suficiente saldo disponible en la cuenta.')
            cuenta.saldo_cuenta -= monto
        cuenta.save()

        serializer.save(id_usuario=user)

class MovimientoRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MovimientoSerializer

    def get_queryset(self):
        return Movimiento.objects.filter(id_cuenta__id_usuario=self.request.user)

    def perform_destroy(self, instance):
        # Revertir saldo en la cuenta al eliminar movimiento
        cuenta = instance.id_cuenta
        if instance.tipo == 'ingreso':
            cuenta.saldo_cuenta -= instance.monto
        elif instance.tipo == 'egreso':
            cuenta.saldo_cuenta += instance.monto
        cuenta.save()
        instance.delete()

class MetaAhorroListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MetaAhorroSerializer

    def get_queryset(self):
        return MetaAhorro.objects.filter(id_usuario=self.request.user).order_by('-fecha_inicio')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Calcular estadísticas y consejos dinámicos
        goals = []
        total_objetivo = 0
        total_ahorrado = 0
        metas_completadas = 0

        for meta in queryset:
            monto_ahorrado = float(meta.monto_ahorrado())
            objetivo = float(meta.monto_objetivo)
            porcentaje = meta.porcentaje_progreso()
            
            total_objetivo += objetivo
            total_ahorrado += monto_ahorrado
            if meta.meta_alcanzada():
                metas_completadas += 1
            
            goals.append({
                'id': meta.id,
                'nombre': meta.nombre,
                'porcentaje_num': porcentaje,
                'falta_por_ahorrar': float(meta.falta_por_ahorrar())
            })

        promedio_progreso = sum([g['porcentaje_num'] for g in goals]) / len(goals) if goals else 0
        tips_dinamicos = generar_consejos_dinamicos(goals, promedio_progreso, metas_completadas)

        return Response({
            'goals': serializer.data,
            'tips_dinamicos': tips_dinamicos,
            'estadisticas': {
                'total_objetivo': total_objetivo,
                'total_ahorrado': total_ahorrado,
                'falta_ahorrar': total_objetivo - total_ahorrado,
                'porcentaje_total': (total_ahorrado / total_objetivo * 100) if total_objetivo > 0 else 0,
                'metas_completadas': metas_completadas,
                'total_metas': len(goals),
                'promedio_progreso': promedio_progreso
            }
        })

    def perform_create(self, serializer):
        user = self.request.user
        cuenta_id = self.request.data.get('id_cuenta')
        # Verificar que la cuenta pertenece al usuario
        Cuenta.objects.get(id=cuenta_id, id_usuario=user)
        serializer.save(id_usuario=user)

class MetaAhorroRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MetaAhorroSerializer

    def get_queryset(self):
        return MetaAhorro.objects.filter(id_usuario=self.request.user)

class AporteMetaAhorroCreateAPIView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AporteMetaAhorroSerializer

    def perform_create(self, serializer):
        user = self.request.user
        meta_id = self.request.data.get('id_meta_ahorro')
        meta = MetaAhorro.objects.get(id=meta_id, id_usuario=user)
        
        monto = Decimal(str(self.request.data.get('monto', 0)))
        
        # Verificar que la cuenta principal tiene saldo suficiente para aportar a la meta
        cuenta = meta.id_cuenta
        if cuenta.saldo_disponible() < monto:
            raise serializers.ValidationError('No hay suficiente saldo disponible en la cuenta para realizar el aporte.')
            
        # Descontar saldo de la cuenta e ingresar el aporte
        cuenta.saldo_cuenta -= monto
        cuenta.save()
        
        serializer.save(id_usuario=user)
