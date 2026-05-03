from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from cuentas.models import Moneda, Cuenta
from gestion_financiera_basica.models import Movimiento
from usuarios.models import Usuario
from analisis_reportes.models import Reporte


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="test@fingest.local",
)
class SistemaFlujosTest(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(codigo="PEN", nombre="Sol", simbolo="S/")
        self.usuario = Usuario.objects.create_user(
            correo="system.user@fingest.local",
            password="pass1234",
            nombres="System",
            apellido_paterno="User",
            apellido_materno="One",
            documento_identidad="11223344",
            telefono=999999997,
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

    def test_flujo_registro_movimiento_y_dashboard(self):
        self.client.force_login(self.usuario)

        fecha_movimiento = timezone.now().date().isoformat()
        response = self.client.post(
            reverse("gestion_financiera_basica:agregar_movimiento"),
            data={
                "nombre": "Ingreso sistema",
                "tipo": "ingreso",
                "categoria": "salario",
                "monto": "250.00",
                "fecha_movimiento": fecha_movimiento,
                "descripcion": "Ingreso desde flujo de sistema",
                "id_cuenta": str(self.cuenta.id),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Movimiento.objects.filter(
                id_usuario=self.usuario,
                nombre="Ingreso sistema",
            ).exists()
        )

        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.saldo_cuenta, Decimal("1250.00"))

        dashboard_response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(dashboard_response.status_code, 200)

    def test_flujo_generar_y_ver_reporte(self):
        Movimiento.objects.create(
            nombre="Ingreso reporte",
            tipo="ingreso",
            categoria="salario",
            monto=Decimal("500.00"),
            fecha_movimiento=timezone.now(),
            id_cuenta=self.cuenta,
            id_usuario=self.usuario,
        )

        self.client.force_login(self.usuario)

        fecha_inicio = (timezone.now().date() - timedelta(days=7)).isoformat()
        fecha_fin = timezone.now().date().isoformat()

        response = self.client.post(
            reverse("analisis_reportes:generar_reporte"),
            data={
                "tipo_reporte": "ingresos_egresos",
                "titulo": "Reporte Sistema",
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reporte.objects.count(), 1)
        self.assertIn("reporte", response.context)
