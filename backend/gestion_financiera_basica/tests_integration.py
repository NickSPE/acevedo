from decimal import Decimal

from django.test import TestCase, override_settings
from django.utils import timezone

from alertas_notificaciones.models import TipoNotificacion, Notificacion
from cuentas.models import Moneda, Cuenta
from gestion_financiera_basica.models import Movimiento
from usuarios.models import Usuario


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="test@fingest.local",
)
class MovimientoNotificacionIntegrationTest(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(codigo="PEN", nombre="Sol", simbolo="S/")
        self.usuario = Usuario.objects.create_user(
            correo="test.user@fingest.local",
            password="pass1234",
            nombres="Test",
            apellido_paterno="User",
            apellido_materno="One",
            documento_identidad="12345678",
            telefono=999999999,
            id_moneda=self.moneda,
            email_verificado=True,
        )
        self.cuenta = Cuenta.objects.create(
            id_usuario=self.usuario,
            nombre="Cuenta principal",
            descripcion="Cuenta principal",
            saldo_cuenta=Decimal("1000.00"),
        )
        self.tipo_notificacion = TipoNotificacion.objects.create(
            nombre="movimiento_financiero",
            categoria="info",
            descripcion="Notificacion por movimiento financiero",
            icono="movement",
            color="#3B82F6",
            activo=True,
        )

    def test_movimiento_crea_notificacion(self):
        movimiento = Movimiento.objects.create(
            nombre="Ingreso de prueba",
            tipo="ingreso",
            categoria="salario",
            monto=Decimal("250.00"),
            fecha_movimiento=timezone.now(),
            descripcion="Ingreso para pruebas",
            id_cuenta=self.cuenta,
            id_usuario=self.usuario,
        )

        existe_notificacion = Notificacion.objects.filter(
            usuario=self.usuario,
            tipo_notificacion=self.tipo_notificacion,
            datos_adicionales__movimiento_id=movimiento.id,
        ).exists()

        self.assertTrue(existe_notificacion)
