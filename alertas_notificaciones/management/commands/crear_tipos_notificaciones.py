from django.core.management.base import BaseCommand
from alertas_notificaciones.models import TipoNotificacion, PlantillaNotificacion

class Command(BaseCommand):
    help = 'Crea los tipos de notificaciones iniciales del sistema'

    def handle(self, *args, **options):
        self.stdout.write('Creando tipos de notificaciones iniciales...')
        
        # Tipos de notificaciones básicos
        tipos_notificaciones = [
            # GESTIÓN FINANCIERA
            {
                'nombre': 'meta_alcanzada',
                'categoria': 'info',
                'descripcion': 'Se envía cuando el usuario completa una meta de ahorro',
                'icono': '🎯',
                'color': '#10B981'
            },
            {
                'nombre': 'saldo_bajo',
                'categoria': 'critical',
                'descripcion': 'Alerta cuando el saldo de una cuenta está por debajo del límite',
                'icono': '🚨',
                'color': '#EF4444'
            },
            {
                'nombre': 'recordatorio_aporte',
                'categoria': 'warning',
                'descripcion': 'Recordatorio para realizar un aporte a meta de ahorro',
                'icono': '⏰',
                'color': '#F59E0B'
            },
            {
                'nombre': 'aporte_realizado',
                'categoria': 'info',
                'descripcion': 'Confirmación de aporte realizado a meta de ahorro',
                'icono': '💰',
                'color': '#3B82F6'
            },
            {
                'nombre': 'transaccion_registrada',
                'categoria': 'info',
                'descripcion': 'Confirmación de registro de ingreso o gasto',
                'icono': '💳',
                'color': '#3B82F6'
            },
            {
                'nombre': 'progreso_meta',
                'categoria': 'info',
                'descripcion': 'Notificación de progreso en meta de ahorro (25%, 50%, 75%)',
                'icono': '📈',
                'color': '#8B5CF6'
            },
            {
                'nombre': 'presupuesto_excedido',
                'categoria': 'warning',
                'descripcion': 'Alerta cuando se supera el presupuesto en una categoría',
                'icono': '📊',
                'color': '#F59E0B'
            },
            {
                'nombre': 'gasto_grande',
                'categoria': 'warning',
                'descripcion': 'Alerta por gasto significativo detectado',
                'icono': '⚠️',
                'color': '#F59E0B'
            },
            # CUENTAS Y SUBCUENTAS
            {
                'nombre': 'transferencia_realizada',
                'categoria': 'info',
                'descripcion': 'Confirmación de transferencia entre subcuentas',
                'icono': '🔄',
                'color': '#3B82F6'
            },
            {
                'nombre': 'deposito_subcuenta',
                'categoria': 'info',
                'descripcion': 'Confirmación de depósito en subcuenta',
                'icono': '📥',
                'color': '#10B981'
            },
            {
                'nombre': 'retiro_subcuenta',
                'categoria': 'info',
                'descripcion': 'Confirmación de retiro de subcuenta',
                'icono': '📤',
                'color': '#F59E0B'
            },
            {
                'nombre': 'fondo_emergencia_bajo',
                'categoria': 'critical',
                'descripcion': 'Alerta cuando el fondo de emergencia está bajo',
                'icono': '🛡️',
                'color': '#DC2626'
            },
            # SEGURIDAD
            {
                'nombre': 'configuracion_actualizada',
                'categoria': 'info',
                'descripcion': 'Confirmación de cambio en configuración de notificaciones',
                'icono': '⚙️',
                'color': '#6366F1'
            },
            {
                'nombre': 'cambio_contraseña',
                'categoria': 'info',
                'descripcion': 'Confirmación de cambio de contraseña',
                'icono': '🔑',
                'color': '#6366F1'
            },
            {
                'nombre': 'acceso_sospechoso',
                'categoria': 'critical',
                'descripcion': 'Alerta por intento de acceso desde ubicación no reconocida',
                'icono': '🔐',
                'color': '#DC2626'
            },
            # EDUCACIÓN
            {
                'nombre': 'tip_personalizado',
                'categoria': 'info',
                'descripcion': 'Notificación de nuevos consejos financieros personalizados',
                'icono': '💡',
                'color': '#8B5CF6'
            },
            {
                'nombre': 'reporte_mensual',
                'categoria': 'info',
                'descripcion': 'Notificación de reporte mensual disponible',
                'icono': '📊',
                'color': '#3B82F6'
            },
            # GESTIÓN FINANCIERA BÁSICA - INTEGRACIÓN
            {
                'nombre': 'movimiento_financiero',
                'categoria': 'info',
                'descripcion': 'Notificación por nuevos ingresos o gastos registrados',
                'icono': '💰',
                'color': '#3B82F6'
            },
            {
                'nombre': 'nueva_meta',
                'categoria': 'info',
                'descripcion': 'Confirmación de creación de nueva meta de ahorro',
                'icono': '🎯',
                'color': '#8B5CF6'
            },
            {
                'nombre': 'meta_por_vencer',
                'categoria': 'warning',
                'descripcion': 'Alerta cuando una meta de ahorro está próxima a vencer',
                'icono': '⏰',
                'color': '#F59E0B'
            },
            {
                'nombre': 'saldo_negativo',
                'categoria': 'critical',
                'descripcion': 'Alerta crítica cuando una cuenta tiene saldo negativo',
                'icono': '🚨',
                'color': '#DC2626'
            }
        ]
        
        # Crear tipos de notificaciones
        for tipo_data in tipos_notificaciones:
            tipo, created = TipoNotificacion.objects.get_or_create(
                nombre=tipo_data['nombre'],
                defaults=tipo_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Creado tipo de notificación: {tipo.nombre}')
                )
            else:
                self.stdout.write(f'- Tipo de notificación ya existe: {tipo.nombre}')
        
        # Crear plantillas básicas para algunos tipos importantes
        plantillas = [
            {
                'tipo_nombre': 'configuracion_actualizada',
                'nombre': 'Configuración Actualizada',
                'asunto_email': 'FinGest - Configuración de Notificaciones Actualizada',
                'plantilla_email': '''
Hola {usuario.nombres},

Hemos actualizado tu configuración de notificaciones según tus preferencias.

{mensaje}

Estos cambios son efectivos inmediatamente. Puedes modificar tu configuración en cualquier momento desde tu panel de cuenta.

Si no realizaste estos cambios, por favor contacta con nuestro soporte.

Saludos,
El equipo de FinGest
                ''',
                'plantilla_push': 'Configuración de notificaciones actualizada',
                'variables_disponibles': ['usuario.nombres', 'mensaje', 'fecha']
            },
            {
                'tipo_nombre': 'meta_alcanzada',
                'nombre': 'Meta de Ahorro Alcanzada',
                'asunto_email': '🎉 ¡Meta Alcanzada en FinGest!',
                'plantilla_email': '''
¡Felicidades {usuario.nombres}!

Has alcanzado tu meta de ahorro "{meta_nombre}" por un monto de ${meta_objetivo}.

Este es un gran logro en tu camino hacia la estabilidad financiera. ¡Sigue así!

¿Ya tienes tu próxima meta en mente?

Saludos,
El equipo de FinGest
                ''',
                'plantilla_push': '🎉 ¡Meta "{meta_nombre}" completada!',
                'variables_disponibles': ['usuario.nombres', 'meta_nombre', 'meta_objetivo', 'fecha']
            },
            {
                'tipo_nombre': 'aporte_realizado',
                'nombre': 'Aporte a Meta Registrado',
                'asunto_email': 'FinGest - Aporte Registrado',
                'plantilla_email': '''
Hola {usuario.nombres},

Hemos registrado tu aporte de ${aporte_monto} a tu meta "{meta_nombre}".

Progreso actual: {progreso_actual}%
Monto faltante: ${monto_faltante}

¡Cada aporte te acerca más a tu objetivo!

Saludos,
El equipo de FinGest
                ''',
                'plantilla_push': 'Aporte de ${aporte_monto} registrado en {meta_nombre}',
                'variables_disponibles': ['usuario.nombres', 'aporte_monto', 'meta_nombre', 'progreso_actual', 'monto_faltante']
            },
            {
                'tipo_nombre': 'saldo_bajo',
                'nombre': 'Alerta de Saldo Bajo',
                'asunto_email': '🚨 FinGest - Alerta de Saldo Bajo',
                'plantilla_email': '''
Hola {usuario.nombres},

Te informamos que el saldo de tu cuenta "{cuenta_nombre}" está por debajo del límite establecido.

Saldo actual: ${saldo_actual}
Límite configurado: ${limite_configurado}

Te recomendamos revisar tus finanzas y considerar hacer un depósito.

Saludos,
El equipo de FinGest
                ''',
                'plantilla_push': '🚨 Saldo bajo en {cuenta_nombre}: ${saldo_actual}',
                'variables_disponibles': ['usuario.nombres', 'cuenta_nombre', 'saldo_actual', 'limite_configurado']
            }
        ]
        
        # Crear plantillas
        for plantilla_data in plantillas:
            try:
                tipo = TipoNotificacion.objects.get(nombre=plantilla_data['tipo_nombre'])
                plantilla, created = PlantillaNotificacion.objects.get_or_create(
                    tipo_notificacion=tipo,
                    nombre=plantilla_data['nombre'],
                    defaults={
                        'asunto_email': plantilla_data['asunto_email'],
                        'plantilla_email': plantilla_data['plantilla_email'],
                        'plantilla_push': plantilla_data['plantilla_push'],
                        'variables_disponibles': plantilla_data['variables_disponibles']
                    }
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Creada plantilla: {plantilla.nombre}')
                    )
                else:
                    self.stdout.write(f'- Plantilla ya existe: {plantilla.nombre}')
            except TipoNotificacion.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'✗ Tipo de notificación no encontrado: {plantilla_data["tipo_nombre"]}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Tipos de notificaciones y plantillas creados exitosamente!')
        )
