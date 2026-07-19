from django.test import TestCase
from unittest.mock import patch
from django.contrib.auth import get_user_model
from alertas_notificaciones.models import (
    Notificacion, TipoNotificacion, ConfiguracionNotificacion, PlantillaNotificacion
)
from alertas_notificaciones.services import (
    NotificationService, NotificationProcessor, EmailService,
    ConfigurationNotificationService
)
from cuentas.models import Moneda

Usuario = get_user_model()


class NotificationServiceTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.')
        self.usuario = Usuario.objects.create_user(
            correo='notif_test@test.com', password='Password123!',
            nombres='Notif', apellido_paterno='Test',
            apellido_materno='User', documento_identidad='12345678',
            telefono=987654321, id_moneda=self.moneda
        )
        self.tipo = TipoNotificacion.objects.create(
            nombre='TestType', categoria='info',
            descripcion='Test', icono='🔔', activo=True
        )

    def test_crear_notificacion_success(self):
        notif = NotificationService.crear_notificacion(
            usuario=self.usuario, tipo_notificacion='TestType',
            titulo='Test Title', mensaje='Test Message', categoria='Test'
        )
        self.assertIsNotNone(notif)
        self.assertEqual(notif.titulo, 'Test Title')
        self.assertEqual(notif.mensaje, 'Test Message')
        self.assertEqual(notif.usuario, self.usuario)

    def test_crear_notificacion_disabled_type(self):
        self.tipo.activo = False
        self.tipo.save()
        notif = NotificationService.crear_notificacion(
            usuario=self.usuario, tipo_notificacion='TestType',
            titulo='Test', mensaje='Test', categoria='Test'
        )
        self.assertIsNone(notif)

    def test_crear_notificacion_nonexistent_type(self):
        notif = NotificationService.crear_notificacion(
            usuario=self.usuario, tipo_notificacion='NonExistent',
            titulo='Test', mensaje='Test', categoria='Test'
        )
        self.assertIsNone(notif)

    def test_crear_notificacion_with_config_disabled(self):
        ConfiguracionNotificacion.objects.create(
            usuario=self.usuario, tipo_notificacion=self.tipo,
            activo=False
        )
        notif = NotificationService.crear_notificacion(
            usuario=self.usuario, tipo_notificacion='TestType',
            titulo='Test', mensaje='Test', categoria='Test'
        )
        self.assertIsNone(notif)

    @patch('alertas_notificaciones.services.NotificationProcessor.procesar_notificacion')
    def test_crear_notificacion_triggers_processor(self, mock_process):
        NotificationService.crear_notificacion(
            usuario=self.usuario, tipo_notificacion='TestType',
            titulo='Test', mensaje='Test', categoria='Test'
        )
        mock_process.assert_called_once()

    def test_marcar_como_leida_success(self):
        notif = Notificacion.objects.create(
            usuario=self.usuario, tipo_notificacion=self.tipo,
            titulo='Test', mensaje='Test', categoria='Test',
            estado='enviada'
        )
        result = NotificationService.marcar_como_leida(notif.id, self.usuario)
        self.assertTrue(result)
        notif.refresh_from_db()
        self.assertEqual(notif.estado, 'leida')

    def test_marcar_como_leida_not_found(self):
        result = NotificationService.marcar_como_leida(99999, self.usuario)
        self.assertFalse(result)

    def test_obtener_no_leidas(self):
        Notificacion.objects.create(
            usuario=self.usuario, tipo_notificacion=self.tipo,
            titulo='Unread', mensaje='Test', categoria='Test',
            estado='enviada'
        )
        Notificacion.objects.create(
            usuario=self.usuario, tipo_notificacion=self.tipo,
            titulo='Read', mensaje='Test', categoria='Test',
            estado='leida'
        )
        no_leidas = NotificationService.obtener_no_leidas(self.usuario)
        self.assertEqual(no_leidas.count(), 1)
        self.assertEqual(no_leidas.first().titulo, 'Unread')

    def test_obtener_contador_no_leidas(self):
        Notificacion.objects.create(
            usuario=self.usuario, tipo_notificacion=self.tipo,
            titulo='Test', mensaje='Test', categoria='Test',
            estado='pendiente'
        )
        count = NotificationService.obtener_contador_no_leidas(self.usuario)
        self.assertEqual(count, 1)

    def test_format_currency_with_user(self):
        result = NotificationService._format_currency(1234.56, self.usuario)
        self.assertEqual(result, 'S/.1,234.56')

    def test_format_currency_without_user(self):
        result = NotificationService._format_currency(1234.56, None)
        self.assertEqual(result, '$1,234.56')

    def test_format_currency_exception(self):
        class BadUser:
            pass
        result = NotificationService._format_currency('invalid', BadUser())
        self.assertEqual(result, '$invalid')


class NotificationProcessorTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='processor_test@test.com', password='Password123!',
            nombres='Proc', apellido_paterno='Test',
            apellido_materno='User', documento_identidad='12345678',
            telefono=987654321, id_moneda=self.moneda
        )
        self.tipo = TipoNotificacion.objects.create(
            nombre='ProcType', categoria='info',
            descripcion='Test', icono='🔔', activo=True
        )
        self.config = ConfiguracionNotificacion.objects.create(
            usuario=self.usuario, tipo_notificacion=self.tipo,
            email_habilitado=False, push_habilitado=False, activo=True
        )
        self.notificacion = Notificacion.objects.create(
            usuario=self.usuario, tipo_notificacion=self.tipo,
            titulo='Test', mensaje='Test', categoria='Test',
            estado='pendiente'
        )

    @patch('alertas_notificaciones.services.EmailService.enviar_notificacion')
    def test_procesar_notificacion_email(self, mock_email):
        self.config.email_habilitado = True
        self.config.save()
        NotificationProcessor.procesar_notificacion(self.notificacion, self.config)
        mock_email.assert_called_once_with(self.notificacion)
        self.notificacion.refresh_from_db()
        self.assertEqual(self.notificacion.estado, 'enviada')

    def test_procesar_notificacion_push_flag(self):
        self.config.push_habilitado = True
        self.config.save()
        NotificationProcessor.procesar_notificacion(self.notificacion, self.config)
        self.notificacion.refresh_from_db()
        self.assertTrue(self.notificacion.push_enviado)

    def test_procesar_notificacion_error_sets_error_state(self):
        bad_notif = Notificacion.objects.create(
            usuario=self.usuario, tipo_notificacion=self.tipo,
            titulo='Bad', mensaje='Test', categoria='Test',
            estado='pendiente'
        )
        with patch('alertas_notificaciones.services.logger'):
            with patch.object(bad_notif, 'save', side_effect=[Exception("DB Error"), None]):
                NotificationProcessor.procesar_notificacion(bad_notif, self.config)
                self.assertEqual(bad_notif.estado, 'error')


class EmailServiceTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='email_test@test.com', password='Password123!',
            nombres='Email', apellido_paterno='Test',
            apellido_materno='User', documento_identidad='12345678',
            telefono=987654321, id_moneda=self.moneda
        )
        self.tipo = TipoNotificacion.objects.create(
            nombre='EmailType', categoria='info',
            descripcion='Test', icono='🔔', activo=True
        )
        self.notificacion = Notificacion.objects.create(
            usuario=self.usuario, tipo_notificacion=self.tipo,
            titulo='Test Title', mensaje='Test Message', categoria='Test',
            estado='pendiente',
            datos_adicionales={'movimiento_nombre': 'Test Movement'}
        )

    @patch('alertas_notificaciones.services.send_mail')
    def test_enviar_notificacion_success(self, mock_send_mail):
        EmailService.enviar_notificacion(self.notificacion)
        mock_send_mail.assert_called_once()
        self.notificacion.refresh_from_db()
        self.assertTrue(self.notificacion.email_enviado)

    @patch('alertas_notificaciones.services.send_mail')
    def test_enviar_notificacion_with_template(self, mock_send_mail):
        PlantillaNotificacion.objects.create(
            tipo_notificacion=self.tipo, nombre='Test Template',
            asunto_email='Custom Subject {titulo}',
            plantilla_email='Custom Body {mensaje}',
            plantilla_push='', activa=True
        )
        EmailService.enviar_notificacion(self.notificacion)
        _, kwargs = mock_send_mail.call_args
        self.assertIn('Custom Subject', kwargs['subject'])

    def test_renderizar_plantilla(self):
        resultado = EmailService._renderizar_plantilla(
            'Hola {titulo}, {mensaje}',
            self.notificacion
        )
        self.assertIn('Test Title', resultado)
        self.assertIn('Test Message', resultado)

    def test_generar_contenido_default_includes_title(self):
        html = EmailService._generar_contenido_default(self.notificacion)
        self.assertIn('Test Title', html)
        self.assertIn('Test Message', html)


class ConfigurationNotificationServiceTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='config_notif@test.com', password='Password123!',
            nombres='Config', apellido_paterno='Test',
            apellido_materno='User', documento_identidad='12345678',
            telefono=987654321, id_moneda=self.moneda
        )

    @patch('alertas_notificaciones.services.EmailService.enviar_email_configuracion')
    def test_notificar_cambio_configuracion_with_email(self, mock_email):
        tipo = TipoNotificacion.objects.create(
            nombre='ConfigType', categoria='info',
            descripcion='Test', icono='🔔', activo=True
        )
        ConfiguracionNotificacion.objects.create(
            usuario=self.usuario, tipo_notificacion=tipo,
            email_habilitado=True
        )
        ConfigurationNotificationService.notificar_cambio_configuracion(
            self.usuario,
            [{'tipo': 'email_habilitado', 'nuevo_valor': True}]
        )
        mock_email.assert_called_once()
