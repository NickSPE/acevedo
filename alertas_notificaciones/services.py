from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import transaction
from .models import Notificacion, TipoNotificacion, ConfiguracionNotificacion, PlantillaNotificacion
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """Servicio principal para gestión de notificaciones"""
    
    @staticmethod
    def crear_notificacion(usuario, tipo_notificacion, titulo, mensaje, categoria, **kwargs):
        """
        Crea y procesa una nueva notificación
        
        Args:
            usuario: Usuario destinatario
            tipo_notificacion: Nombre del tipo de notificación
            titulo: Título de la notificación
            mensaje: Mensaje de la notificación
            categoria: Categoría (ej: 'Metas', 'Saldo', 'Transacciones')
            **kwargs: Argumentos opcionales (prioridad, url_accion, datos_adicionales, etc.)
        
        Returns:
            Notificacion: Instancia de la notificación creada o None si está deshabilitada
        """
        try:
            # Obtener el tipo de notificación
            try:
                tipo_obj = TipoNotificacion.objects.get(nombre=tipo_notificacion, activo=True)
            except TipoNotificacion.DoesNotExist:
                logger.warning(f"Tipo de notificación no encontrado: {tipo_notificacion}")
                return None
            
            # Verificar configuración del usuario
            config = ConfiguracionNotificacion.objects.filter(
                usuario=usuario,
                tipo_notificacion=tipo_obj,
                activo=True
            ).first()
            
            # Si no hay configuración, usar valores por defecto
            if not config:
                config = NotificationService._crear_configuracion_default(usuario, tipo_obj)
            
            # Si las notificaciones están deshabilitadas, no crear
            if not config.activo:
                return None
            
            # Crear la notificación
            with transaction.atomic():
                notificacion = Notificacion.objects.create(
                    usuario=usuario,
                    tipo_notificacion=tipo_obj,
                    titulo=titulo,
                    mensaje=mensaje,
                    categoria=categoria,
                    modulo_origen=kwargs.get('modulo_origen', 'alertas_notificaciones'),
                    objeto_relacionado=kwargs.get('objeto_relacionado'),
                    prioridad=kwargs.get('prioridad', 'media'),
                    url_accion=kwargs.get('url_accion'),
                    datos_adicionales=kwargs.get('datos_adicionales', {}),
                    etiquetas=kwargs.get('etiquetas', [])
                )
                
                # Procesar envío según configuración
                NotificationProcessor.procesar_notificacion(notificacion, config)
                
                logger.info(f"Notificación creada: {notificacion.id} para usuario {usuario.id}")
                return notificacion
                
        except Exception as e:
            logger.error(f"Error creando notificación: {str(e)}")
            return None
    
    @staticmethod
    def _crear_configuracion_default(usuario, tipo_notificacion):
        """Crea configuración por defecto para un usuario y tipo de notificación"""
        return ConfiguracionNotificacion.objects.create(
            usuario=usuario,
            tipo_notificacion=tipo_notificacion,
            email_habilitado=True,
            push_habilitado=True,
            sms_habilitado=False,
            activo=True
        )
    
    @staticmethod
    def marcar_como_leida(notificacion_id, usuario):
        """Marca una notificación como leída"""
        try:
            notificacion = Notificacion.objects.get(id=notificacion_id, usuario=usuario)
            notificacion.estado = 'leida'
            notificacion.fecha_lectura = timezone.now()
            notificacion.save()
            logger.info(f"Notificación {notificacion_id} marcada como leída")
            return True
        except Notificacion.DoesNotExist:
            logger.warning(f"Notificación {notificacion_id} no encontrada para usuario {usuario.id}")
            return False
    
    @staticmethod
    def obtener_no_leidas(usuario):
        """Obtiene notificaciones no leídas del usuario"""
        return Notificacion.objects.filter(
            usuario=usuario,
            estado__in=['enviada', 'pendiente']
        ).order_by('-fecha_creacion')
    
    @staticmethod
    def obtener_contador_no_leidas(usuario):
        """Obtiene el contador de notificaciones no leídas"""
        return Notificacion.objects.filter(
            usuario=usuario,
            estado__in=['enviada', 'pendiente']
        ).count()
    
    @staticmethod
    def _format_currency(amount, usuario):
        """
        Formatea un monto con el símbolo de moneda del usuario
        
        Args:
            amount: Monto a formatear
            usuario: Usuario para obtener el símbolo de moneda
            
        Returns:
            str: Monto formateado con símbolo de moneda
        """
        try:
            # Obtener símbolo de moneda del usuario
            if usuario and hasattr(usuario, 'id_moneda') and usuario.id_moneda:
                symbol = usuario.id_moneda.simbolo
            else:
                symbol = "$"  # Por defecto
            
            # Formatear con comas para miles
            formatted_amount = f"{float(amount):,.2f}"
            return f"{symbol}{formatted_amount}"
        except:
            return f"${amount}"
    

class NotificationProcessor:
    """Procesador de notificaciones para diferentes canales"""
    
    @staticmethod
    def procesar_notificacion(notificacion, config):
        """Procesa el envío de una notificación según configuración"""
        try:
            # Email
            if config.email_habilitado:
                EmailService.enviar_notificacion(notificacion)
                
            # Push notification (por ahora solo marcar como enviado)
            if config.push_habilitado:
                notificacion.push_enviado = True
                
            # SMS (futuro)
            if config.sms_habilitado:
                # TODO: Implementar SMS
                pass
            
            # Actualizar estado
            notificacion.estado = 'enviada'
            notificacion.fecha_envio = timezone.now()
            notificacion.save()
            
            logger.info(f"Notificación {notificacion.id} procesada correctamente")
            
        except Exception as e:
            notificacion.estado = 'error'
            notificacion.save()
            logger.error(f"Error procesando notificación {notificacion.id}: {str(e)}")


class EmailService:
    """Servicio para envío de emails"""
    
    @staticmethod
    def enviar_notificacion(notificacion):
        """Envía notificación por email"""
        try:
            # Buscar plantilla específica
            plantilla = PlantillaNotificacion.objects.filter(
                tipo_notificacion=notificacion.tipo_notificacion,
                activa=True
            ).first()
            
            if plantilla:
                # Usar plantilla personalizada
                asunto = EmailService._renderizar_plantilla(plantilla.asunto_email, notificacion)
                contenido = EmailService._renderizar_plantilla(plantilla.plantilla_email, notificacion)
            else:
                # Generar asunto dinámico basado en el contenido
                datos = notificacion.datos_adicionales or {}
                if datos.get('movimiento_nombre'):
                    asunto = f"FinGest - {notificacion.titulo}: {datos.get('movimiento_nombre')}"
                elif datos.get('meta_nombre'):
                    asunto = f"FinGest - {notificacion.titulo}: {datos.get('meta_nombre')}"
                else:
                    asunto = f"FinGest - {notificacion.titulo}"
                contenido = EmailService._generar_contenido_default(notificacion)
            
            # Enviar email
            send_mail(
                subject=asunto,
                message=contenido,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notificacion.usuario.correo],
                html_message=contenido,
                fail_silently=False
            )
            
            notificacion.email_enviado = True
            notificacion.save()
            
            logger.info(f"Email enviado para notificación {notificacion.id}")
            
        except Exception as e:
            logger.error(f"Error enviando email para notificación {notificacion.id}: {str(e)}")
            raise
    
    @staticmethod
    def _renderizar_plantilla(plantilla_texto, notificacion):
        """Renderiza una plantilla con los datos de la notificación"""
        # Variables disponibles para las plantillas
        contexto = {
            'usuario': notificacion.usuario,
            'notificacion': notificacion,
            'titulo': notificacion.titulo,
            'mensaje': notificacion.mensaje,
            'categoria': notificacion.categoria,
            'fecha': notificacion.fecha_creacion,
            'url_accion': notificacion.url_accion,
            **notificacion.datos_adicionales
        }
        
        # Reemplazar variables en la plantilla
        contenido = plantilla_texto
        for key, value in contexto.items():
            if value is not None:
                contenido = contenido.replace(f'{{{key}}}', str(value))
        
        return contenido
    
    @staticmethod
    def _generar_contenido_default(notificacion):
        """Genera contenido HTML por defecto para el email"""
        # Obtener el usuario de la notificación
        usuario = notificacion.usuario
        # Determinar el color del icono basado en el tipo de notificación
        icon_color = "#3B82F6"  # Azul por defecto
        if "gasto" in notificacion.titulo.lower() or "egreso" in notificacion.titulo.lower():
            icon_color = "#EF4444"  # Rojo para gastos
        elif "ingreso" in notificacion.titulo.lower():
            icon_color = "#10B981"  # Verde para ingresos
        elif "meta" in notificacion.titulo.lower():
            icon_color = "#8B5CF6"  # Morado para metas
        elif "saldo" in notificacion.titulo.lower():
            icon_color = "#F59E0B"  # Naranja para alertas de saldo
        
        # Obtener datos adicionales
        datos = notificacion.datos_adicionales or {}
        
        # Crear secciones de información adicional
        info_adicional = ""
        if datos.get('movimiento_tipo'):
            tipo_mov = "Ingreso" if datos.get('movimiento_tipo') == 'ingreso' else "Gasto"
            emoji_tipo = "💰" if datos.get('movimiento_tipo') == 'ingreso' else "💸"
            info_adicional += f"""
            <div style="background-color: #f8fafc; border-radius: 8px; padding: 16px; margin: 20px 0;">
                <h4 style="margin: 0 0 10px 0; color: #1f2937; font-size: 16px;">📋 Detalles de la Transacción</h4>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #6b7280;"><strong>Tipo:</strong></span>
                    <span style="color: {icon_color}; font-weight: bold;">{emoji_tipo} {tipo_mov}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #6b7280;"><strong>Monto:</strong></span>
                    <span style="color: #1f2937; font-weight: bold; font-size: 18px;">{NotificationService._format_currency(datos.get('monto', 0), usuario)}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #6b7280;"><strong>Cuenta:</strong></span>
                    <span style="color: #1f2937;">{datos.get('cuenta_nombre', 'N/A')}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #6b7280;"><strong>Saldo actual:</strong></span>
                    <span style="color: #059669; font-weight: bold;">{NotificationService._format_currency(datos.get('saldo_actual', 0), usuario)}</span>
                </div>
            </div>
            """
        
        # Información para metas de ahorro
        if datos.get('meta_nombre'):
            info_adicional += f"""
            <div style="background-color: #f0f9ff; border-radius: 8px; padding: 16px; margin: 20px 0;">
                <h4 style="margin: 0 0 10px 0; color: #1f2937; font-size: 16px;">🎯 Información de la Meta</h4>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #6b7280;"><strong>Meta:</strong></span>
                    <span style="color: #1f2937; font-weight: bold;">{datos.get('meta_nombre')}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #6b7280;"><strong>Progreso:</strong></span>
                    <span style="color: #8B5CF6; font-weight: bold;">{datos.get('progreso_porcentaje', 0):.1f}%</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #6b7280;"><strong>Objetivo:</strong></span>
                    <span style="color: #1f2937; font-weight: bold;">{NotificationService._format_currency(datos.get('monto_objetivo', 0), usuario)}</span>
                </div>
            </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>FinGest - {notificacion.titulo}</title>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{ 
                    max-width: 600px; 
                    margin: 0 auto; 
                    background-color: white; 
                    border-radius: 16px; 
                    padding: 0; 
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{ 
                    background: linear-gradient(135deg, {icon_color} 0%, {icon_color}dd 100%);
                    color: white;
                    text-align: center; 
                    padding: 30px 20px;
                }}
                .logo {{ 
                    font-size: 28px; 
                    font-weight: 800; 
                    margin-bottom: 10px;
                    letter-spacing: -0.5px;
                }}
                .notification-icon {{ 
                    font-size: 64px; 
                    margin: 15px 0;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .header-subtitle {{
                    font-size: 14px;
                    opacity: 0.9;
                    margin: 0;
                }}
                .content {{
                    padding: 30px;
                }}
                .title {{ 
                    color: #1f2937; 
                    font-size: 24px; 
                    font-weight: 700; 
                    margin-bottom: 20px;
                    line-height: 1.3;
                }}
                .message {{ 
                    color: #4b5563; 
                    line-height: 1.6; 
                    margin-bottom: 25px;
                    font-size: 16px;
                }}
                .category {{ 
                    background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
                    color: #374151; 
                    padding: 8px 16px; 
                    border-radius: 20px; 
                    font-size: 12px; 
                    font-weight: 600; 
                    display: inline-block; 
                    margin-bottom: 20px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .action-button {{ 
                    display: inline-block; 
                    background: linear-gradient(135deg, {icon_color} 0%, {icon_color}dd 100%);
                    color: white; 
                    padding: 14px 28px; 
                    text-decoration: none; 
                    border-radius: 8px; 
                    font-weight: 600;
                    margin: 20px 0;
                    transition: transform 0.2s ease;
                }}
                .action-button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }}
                .footer {{ 
                    margin-top: 40px; 
                    padding-top: 20px; 
                    border-top: 2px solid #e5e7eb; 
                    text-align: center; 
                    color: #6b7280; 
                    font-size: 14px;
                }}
                .footer a {{
                    color: {icon_color};
                    text-decoration: none;
                    font-weight: 600;
                }}
                .timestamp {{
                    background-color: #f9fafb;
                    border-radius: 8px;
                    padding: 12px;
                    margin: 20px 0;
                    text-align: center;
                    color: #6b7280;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">FinGest</div>
                    <div class="notification-icon">{notificacion.tipo_notificacion.icono}</div>
                    <p class="header-subtitle">Tu asistente financiero personal</p>
                </div>
                
                <div class="content">
                    <div class="category">{notificacion.categoria}</div>
                    <div class="title">{notificacion.titulo}</div>
                    <div class="message">{notificacion.mensaje}</div>
                    
                    {info_adicional}
                    
                    <div class="timestamp">
                        📅 {notificacion.fecha_creacion.strftime('%d de %B de %Y a las %H:%M')}
                    </div>
                    
                    {f'<a href="{notificacion.url_accion}" class="action-button">🔍 Ver Detalles</a>' if notificacion.url_accion else ''}
                    
                    <div class="footer">
                        <p>📧 Has recibido esta notificación porque tienes habilitadas las notificaciones por email en FinGest.</p>
                        <p>🔧 Si no deseas recibir estas notificaciones, puedes <a href="#">modificar tu configuración</a>.</p>
                        <br>
                        <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                            © 2025 FinGest - Tu compañero en el camino hacia la libertad financiera
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """


class ConfigurationNotificationService:
    """Servicio para notificar cambios en configuraciones"""
    
    @staticmethod
    def notificar_cambio_configuracion(usuario, cambios_realizados):
        """
        Envía notificación cuando el usuario cambia sus configuraciones de notificación
        """
        # Crear un mensaje descriptivo de los cambios
        mensaje_cambios = []
        
        for cambio in cambios_realizados:
            if cambio['tipo'] == 'email_habilitado':
                if cambio['nuevo_valor']:
                    mensaje_cambios.append("✅ Notificaciones por email activadas")
                else:
                    mensaje_cambios.append("❌ Notificaciones por email desactivadas")
            elif cambio['tipo'] == 'push_habilitado':
                if cambio['nuevo_valor']:
                    mensaje_cambios.append("🔔 Notificaciones push activadas")
                else:
                    mensaje_cambios.append("🔕 Notificaciones push desactivadas")
        
        mensaje_final = "Hemos actualizado tus preferencias de notificación:\n\n" + "\n".join(mensaje_cambios)
        
        # Solo enviar por email si tiene email habilitado
        config_email = ConfiguracionNotificacion.objects.filter(
            usuario=usuario,
            email_habilitado=True
        ).exists()
        
        if config_email:
            try:
                # Enviar email de confirmación directamente
                EmailService.enviar_email_configuracion(usuario, mensaje_final)
                logger.info(f"Email de confirmación de configuración enviado a {usuario.correo}")
            except Exception as e:
                logger.error(f"Error enviando email de configuración: {str(e)}")
    
    @staticmethod
    def enviar_email_configuracion(usuario, mensaje):
        """Envía email específico de cambio de configuración"""
        asunto = "FinGest - Configuración de Notificaciones Actualizada"
        
        contenido_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Configuración Actualizada</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .logo {{ font-size: 24px; font-weight: bold; color: #3B82F6; }}
                .icon {{ font-size: 48px; margin: 20px 0; }}
                .title {{ color: #1f2937; font-size: 20px; font-weight: bold; margin-bottom: 15px; }}
                .message {{ color: #4b5563; line-height: 1.6; margin-bottom: 25px; white-space: pre-line; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; text-align: center; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">FinGest</div>
                    <div class="icon">⚙️</div>
                </div>
                
                <div class="title">Configuración Actualizada</div>
                <div class="message">Hola {usuario.nombres},

{mensaje}

Estos cambios son efectivos inmediatamente. Puedes modificar tu configuración en cualquier momento desde tu panel de configuración.</div>
                
                <div class="footer">
                    <p>Si no realizaste estos cambios, por favor contacta con nuestro soporte.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.correo],
            html_message=contenido_html,
            fail_silently=False
        )

# Añadir método al EmailService
EmailService.enviar_email_configuracion = ConfigurationNotificationService.enviar_email_configuracion
