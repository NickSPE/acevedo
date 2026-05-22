from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import TipoNotificacion, ConfiguracionNotificacion, Notificacion
from .api_serializers import TipoNotificacionSerializer, ConfiguracionNotificacionSerializer, NotificacionSerializer
from .services import NotificationService, ConfigurationNotificationService

class ConfiguracionesNotificacionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tipos = TipoNotificacion.objects.filter(activo=True)
        configuraciones = []
        for t in tipos:
            config, _ = ConfiguracionNotificacion.objects.get_or_create(
                usuario=request.user,
                tipo_notificacion=t,
                defaults={
                    'email_habilitado': True,
                    'push_habilitado': True,
                    'sms_habilitado': False,
                    'activo': True
                }
            )
            configuraciones.append(ConfiguracionNotificacionSerializer(config).data)
        return Response(configuraciones)

    def post(self, request):
        tipos = TipoNotificacion.objects.filter(activo=True)
        cambios_realizados = []

        for t in tipos:
            config, _ = ConfiguracionNotificacion.objects.get_or_create(
                usuario=request.user,
                tipo_notificacion=t
            )

            email_anterior = config.email_habilitado
            push_anterior = config.push_habilitado

            # Tomar campos enviados
            config.email_habilitado = request.data.get(f'email_{t.nombre}', config.email_habilitado)
            config.push_habilitado = request.data.get(f'push_{t.nombre}', config.push_habilitado)
            config.activo = request.data.get(f'activo_{t.nombre}', config.activo)

            umbral_val = request.data.get(f'umbral_{t.nombre}')
            if umbral_val is not None:
                try:
                    config.umbral_monto = float(umbral_val)
                except ValueError:
                    pass

            config.save()

            if email_anterior != config.email_habilitado:
                cambios_realizados.append({
                    'tipo': 'email_habilitado',
                    'tipo_notificacion': t.nombre,
                    'valor_anterior': email_anterior,
                    'nuevo_valor': config.email_habilitado
                })

            if push_anterior != config.push_habilitado:
                cambios_realizados.append({
                    'tipo': 'push_habilitado',
                    'tipo_notificacion': t.nombre,
                    'valor_anterior': push_anterior,
                    'nuevo_valor': config.push_habilitado
                })

        if cambios_realizados:
            ConfigurationNotificationService.notificar_cambio_configuracion(
                request.user,
                cambios_realizados
            )
            return Response({'success': True, 'message': 'Configuraciones actualizadas exitosamente y notificación enviada.'})

        return Response({'success': True, 'message': 'No se detectaron cambios.'})

class HistorialNotificacionesAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificacionSerializer

    def get_queryset(self):
        return Notificacion.objects.filter(usuario=self.request.user).order_by('-fecha_creacion')

    def list(self, request, *args, **kwargs):
        show_all = request.query_params.get('show_all', 'false').lower() == 'true'
        queryset = self.get_queryset()
        
        if not show_all:
            queryset = queryset[:3]
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'notifications': serializer.data,
                'total_notificaciones': self.get_queryset().count(),
                'unread_in_page': sum(1 for n in serializer.data if n['estado'] != 'leida'),
                'is_limited': True
            })

        return super().list(request, *args, **kwargs)

class MarcarNotificacionLeidaAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        success = NotificationService.marcar_como_leida(pk, request.user)
        if success:
            return Response({'success': True, 'message': 'Notificación marcada como leída.'})
        return Response({'error': 'Notificación no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

class MarcarTodasLeidasAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        count = Notificacion.objects.filter(
            usuario=request.user,
            estado__in=['enviada', 'pendiente']
        ).update(
            estado='leida',
            fecha_lectura=timezone.now()
        )
        return Response({'success': True, 'message': f'{count} notificaciones marcadas como leídas.'})

class ObtenerContadorNotificacionesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = NotificationService.obtener_contador_no_leidas(request.user)
        return Response({'count': count})

class TestNotificationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        notificacion = NotificationService.crear_notificacion(
            usuario=request.user,
            tipo_notificacion='configuracion_actualizada',
            titulo='Prueba de Notificación',
            mensaje='Esta es una notificación de prueba para verificar que el sistema funciona correctamente.',
            categoria='Pruebas',
            prioridad='media'
        )
        if notificacion:
            return Response({'success': True, 'message': 'Notificación de prueba enviada correctamente.'})
        return Response({'success': False, 'message': 'No se pudo enviar la notificación (posiblemente deshabilitada).'})
