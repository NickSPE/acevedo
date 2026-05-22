"""
Tests unitarios y de integración para los triggers y señales de notificaciones financieras
Ubicación: test/test_gestion_financiera_signals.py
"""

from django.test import TestCase
from decimal import Decimal
from django.utils import timezone
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from cuentas.models import Moneda, Cuenta
from gestion_financiera_basica.models import MetaAhorro, AporteMetaAhorro, Movimiento
from alertas_notificaciones.models import TipoNotificacion, Notificacion
from gestion_financiera_basica.signals import verificar_metas_vencidas

Usuario = get_user_model()


class GestionFinancieraSignalsTestCase(TestCase):
    def setUp(self):
        # Crear moneda de prueba
        self.moneda = Moneda.objects.create(
            codigo='USD',
            nombre='Dólares',
            simbolo='$'
        )

        # Crear usuario
        self.usuario = Usuario.objects.create_user(
            correo='test_signals@test.com',
            password='Password123!',
            nombres='Carlos',
            apellido_paterno='Mendoza',
            documento_identidad='12345679',
            telefono=999999998,
            id_moneda=self.moneda
        )

        # Crear cuenta principal
        self.cuenta = Cuenta.objects.create(
            nombre='Cuenta Corriente',
            saldo_cuenta=Decimal('5000.00'),
            id_usuario=self.usuario
        )

        # Crear todos los TipoNotificacion requeridos por las señales
        self.tipos_notificaciones = {}
        nombres_tipos = [
            "aporte_realizado", "progreso_meta", "meta_alcanzada",
            "movimiento_financiero", "saldo_bajo", "saldo_negativo",
            "nueva_meta", "meta_por_vencer"
        ]
        for nombre in nombres_tipos:
            self.tipos_notificaciones[nombre] = TipoNotificacion.objects.create(
                nombre=nombre,
                categoria='info' if 'bajo' not in nombre else 'warning',
                descripcion=f'Descripción de {nombre}',
                icono='🔔',
                activo=True
            )

        # Limpiar cualquier notificación creada durante el setup
        Notificacion.objects.all().delete()

    def test_notificar_nueva_meta_ahorro(self):
        """Valida que al crear una nueva meta de ahorro se dispare la señal y cree la notificación"""
        meta = MetaAhorro.objects.create(
            fecha_inicio=timezone.now().date(),
            fecha_limite=timezone.now().date() + timedelta(days=30),
            monto_objetivo=Decimal('1000.00'),
            frecuencia_aporte='mensual',
            descripcion='Ahorro para laptop',
            nombre='Laptop 2026',
            id_usuario=self.usuario,
            id_cuenta=self.cuenta
        )

        # Debe existir una notificación para 'nueva_meta'
        notif = Notificacion.objects.filter(usuario=self.usuario, tipo_notificacion__nombre="nueva_meta").first()
        self.assertIsNotNone(notif)
        self.assertIn("Laptop 2026", notif.mensaje)
        self.assertEqual(notif.datos_adicionales['meta_id'], meta.id)

    def test_notificar_nuevo_aporte_normal(self):
        """Valida señal de nuevo aporte con progreso normal (< 75%)"""
        meta = MetaAhorro.objects.create(
            fecha_inicio=timezone.now().date(),
            fecha_limite=timezone.now().date() + timedelta(days=30),
            monto_objetivo=Decimal('1000.00'),
            frecuencia_aporte='mensual',
            descripcion='Meta Ahorro',
            nombre='Mi Meta',
            id_usuario=self.usuario,
            id_cuenta=self.cuenta
        )
        
        # Limpiar notificaciones previas
        Notificacion.objects.all().delete()

        # Crear un aporte del 10% (monto 100)
        aporte = AporteMetaAhorro.objects.create(
            id_meta_ahorro=meta,
            monto=Decimal('100.00'),
            descripcion='Primer Aporte',
            id_usuario=self.usuario
        )

        # Verificar que se generó la notificación del aporte realizado
        notif = Notificacion.objects.filter(usuario=self.usuario, tipo_notificacion__nombre="aporte_realizado").first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.prioridad, 'media')
        self.assertIn("Mi Meta", notif.mensaje)

    def test_notificar_nuevo_aporte_alcanzado(self):
        """Valida que si el aporte completa el monto objetivo se notifique meta_alcanzada"""
        meta = MetaAhorro.objects.create(
            fecha_inicio=timezone.now().date(),
            fecha_limite=timezone.now().date() + timedelta(days=30),
            monto_objetivo=Decimal('500.00'),
            frecuencia_aporte='mensual',
            descripcion='Meta Ahorro',
            nombre='Meta Vacaciones',
            id_usuario=self.usuario,
            id_cuenta=self.cuenta
        )
        
        Notificacion.objects.all().delete()

        # Aporte del total (monto 500)
        aporte = AporteMetaAhorro.objects.create(
            id_meta_ahorro=meta,
            monto=Decimal('500.00'),
            descripcion='Aporte final',
            id_usuario=self.usuario
        )

        notif = Notificacion.objects.filter(usuario=self.usuario, tipo_notificacion__nombre="meta_alcanzada").first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.prioridad, 'alta')
        self.assertIn("Felicidades", notif.mensaje)

    def test_notificar_movimiento_financiero_ingreso(self):
        """Valida que al registrar un ingreso se genere notificación adecuada"""
        mov = Movimiento.objects.create(
            nombre='Freelance Project',
            tipo='ingreso',
            monto=Decimal('1200.00'),
            fecha_movimiento=timezone.now(),
            descripcion='Desarrollo Web Django',
            id_cuenta=self.cuenta,
            id_usuario=self.usuario
        )

        notif = Notificacion.objects.filter(usuario=self.usuario, tipo_notificacion__nombre="movimiento_financiero").first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.prioridad, 'alta') # >= 1000 es alta prioridad
        self.assertIn("patrimonio", notif.mensaje)
        self.assertEqual(notif.datos_adicionales['movimiento_nombre'], 'Freelance Project')

    def test_notificar_movimiento_financiero_egreso(self):
        """Valida que al registrar un egreso se genere notificación de gasto"""
        mov = Movimiento.objects.create(
            nombre='Supermercado',
            tipo='egreso',
            monto=Decimal('150.00'),
            fecha_movimiento=timezone.now(),
            id_cuenta=self.cuenta,
            id_usuario=self.usuario
        )

        notif = Notificacion.objects.filter(usuario=self.usuario, tipo_notificacion__nombre="movimiento_financiero").first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.prioridad, 'baja') # < 500 es baja prioridad
        self.assertIn("Gasto registrado correctamente", notif.mensaje)

    def test_notificar_cambio_saldo_cuenta_bajo_y_negativo(self):
        """Valida alertas ante saldos bajos y números rojos al actualizar cuentas"""
        # Saldo bajo (< 50)
        self.cuenta.saldo_cuenta = Decimal('30.00')
        self.cuenta.save()

        notif = Notificacion.objects.filter(usuario=self.usuario, tipo_notificacion__nombre="saldo_bajo").first()
        self.assertIsNotNone(notif)
        self.assertIn("saldo bajo", notif.mensaje)

        # Saldo negativo (< 0)
        self.cuenta.saldo_cuenta = Decimal('-10.00')
        self.cuenta.save()

        notif_neg = Notificacion.objects.filter(usuario=self.usuario, tipo_notificacion__nombre="saldo_negativo").first()
        self.assertIsNotNone(notif_neg)
        self.assertIn("saldo negativo", notif_neg.mensaje)

    def test_verificar_metas_vencidas(self):
        """Valida la verificación periódica de metas próximas a vencer"""
        # Crear meta que vence en 3 días (próxima a vencer)
        meta = MetaAhorro.objects.create(
            fecha_inicio=timezone.now().date() - timedelta(days=10),
            fecha_limite=timezone.now().date() + timedelta(days=3),
            monto_objetivo=Decimal('1000.00'),
            frecuencia_aporte='mensual',
            descripcion='Ahorro vencido',
            nombre='Próxima a expirar',
            id_usuario=self.usuario,
            id_cuenta=self.cuenta
        )

        # Ejecutar función
        verificar_metas_vencidas()

        notif = Notificacion.objects.filter(usuario=self.usuario, tipo_notificacion__nombre="meta_por_vencer").first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.prioridad, 'alta') # 3 días = prioridad 'alta'
        self.assertIn("vencer en 3 días", notif.titulo)
