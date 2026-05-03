from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from cuentas.models import Moneda, Cuenta
from gestion_financiera_basica.models import Movimiento
from usuarios.models import Usuario
from .models import Reporte


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="test@fingest.local",
)
class ReporteGeneracionIntegrationTest(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(codigo="PEN", nombre="Sol", simbolo="S/")
        self.usuario = Usuario.objects.create_user(
            correo="report.user@fingest.local",
            password="pass1234",
            nombres="Report",
            apellido_paterno="User",
            apellido_materno="One",
            documento_identidad="87654321",
            telefono=999999998,
            id_moneda=self.moneda,
            email_verificado=True,
            onboarding_completed=True,
        )
        self.cuenta = Cuenta.objects.create(
            id_usuario=self.usuario,
            nombre="Cuenta principal",
            descripcion="Cuenta principal",
            saldo_cuenta=Decimal("1000.00"),
        )

    def test_generar_reporte_ingresos_egresos(self):
        fecha_movimiento = timezone.now()
        Movimiento.objects.create(
            nombre="Ingreso base",
            tipo="ingreso",
            categoria="salario",
            monto=Decimal("500.00"),
            fecha_movimiento=fecha_movimiento,
            id_cuenta=self.cuenta,
            id_usuario=self.usuario,
        )
        Movimiento.objects.create(
            nombre="Gasto base",
            tipo="egreso",
            categoria="alimentacion",
            monto=Decimal("200.00"),
            fecha_movimiento=fecha_movimiento,
            id_cuenta=self.cuenta,
            id_usuario=self.usuario,
        )

        self.client.force_login(self.usuario)

        fecha_inicio = (fecha_movimiento.date() - timedelta(days=1)).isoformat()
        fecha_fin = (fecha_movimiento.date() + timedelta(days=1)).isoformat()

        response = self.client.post(
            reverse("analisis_reportes:generar_reporte"),
            data={
                "tipo_reporte": "ingresos_egresos",
                "titulo": "Reporte Ingresos y Egresos",
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Reporte.objects.count(), 1)

        reporte = Reporte.objects.first()
        datos = reporte.get_datos()

        self.assertEqual(reporte.tipo_reporte, "ingresos_egresos")
        self.assertIn("labels", datos)
        self.assertIn("ingresos", datos)
        self.assertIn("gastos", datos)
