from datetime import date, datetime, timedelta
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.hashers import make_password
from cuentas.models import Moneda, Cuenta
from usuarios.models import Usuario
from gestion_financiera_basica.models import Movimiento, MetaAhorro, AporteMetaAhorro
from gestion_financiera_basica.forms import MovimientoForm, MetaAhorroForm, AporteMetaAhorroForm


class MovimientoFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.moneda = Moneda.objects.create(nombre='Dolar', codigo='USD', simbolo='$')
        cls.usuario = Usuario.objects.create_user(
            correo='test@test.com', password='testpass123',
            nombres='Test', apellido_paterno='Test', apellido_materno='User',
            documento_identidad='12345678', telefono=123456789,
            id_moneda=cls.moneda,
        )
        cls.cuenta = Cuenta.objects.create(
            nombre='Test Account', descripcion='', saldo_cuenta=1000,
            id_usuario=cls.usuario,
        )

    def test_valid_form_with_all_required_fields(self):
        form = MovimientoForm(
            data={
                'nombre': 'Test Movement',
                'tipo': 'ingreso',
                'monto': '100.00',
                'fecha_movimiento': '2026-07-17',
                'id_cuenta': self.cuenta.pk,
            },
            user=self.usuario,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_form_with_all_fields_including_optional(self):
        form = MovimientoForm(
            data={
                'nombre': 'Test Movement',
                'tipo': 'egreso',
                'categoria': 'alimentacion',
                'monto': '250.50',
                'fecha_movimiento': '2026-07-17',
                'descripcion': 'Test description',
                'id_cuenta': self.cuenta.pk,
            },
            user=self.usuario,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_requires_user_kwarg_to_filter_accounts(self):
        otro_usuario = Usuario.objects.create_user(
            correo='otro@test.com', password='testpass123',
            nombres='Otro', apellido_paterno='Test', apellido_materno='User',
            documento_identidad='87654321', telefono=987654321,
            id_moneda=self.moneda,
        )
        otra_cuenta = Cuenta.objects.create(
            nombre='Other Account', descripcion='', saldo_cuenta=500,
            id_usuario=otro_usuario,
        )
        form = MovimientoForm(user=self.usuario)
        self.assertIn(self.cuenta, form.fields['id_cuenta'].queryset)
        self.assertNotIn(otra_cuenta, form.fields['id_cuenta'].queryset)

    def test_empty_description_defaults_to_empty_string(self):
        form = MovimientoForm(
            data={
                'nombre': 'Test Movement',
                'tipo': 'ingreso',
                'monto': '100.00',
                'fecha_movimiento': '2026-07-17',
                'id_cuenta': self.cuenta.pk,
            },
            user=self.usuario,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['descripcion'], '')

    def test_missing_nombre_is_invalid(self):
        form = MovimientoForm(
            data={
                'tipo': 'ingreso',
                'monto': '100.00',
                'fecha_movimiento': '2026-07-17',
                'id_cuenta': self.cuenta.pk,
            },
            user=self.usuario,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_invalid_monto_rejected(self):
        form = MovimientoForm(
            data={
                'nombre': 'Test Movement',
                'tipo': 'ingreso',
                'monto': 'abc',
                'fecha_movimiento': '2026-07-17',
                'id_cuenta': self.cuenta.pk,
            },
            user=self.usuario,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('monto', form.errors)

    def test_descripcion_is_optional(self):
        form = MovimientoForm(
            data={
                'nombre': 'Test Movement',
                'tipo': 'egreso',
                'monto': '50.00',
                'fecha_movimiento': '2026-07-17',
                'id_cuenta': self.cuenta.pk,
            },
            user=self.usuario,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['descripcion'], '')

    def test_categoria_is_optional(self):
        form = MovimientoForm(
            data={
                'nombre': 'Test Movement',
                'tipo': 'ingreso',
                'monto': '75.00',
                'fecha_movimiento': '2026-07-17',
                'id_cuenta': self.cuenta.pk,
            },
            user=self.usuario,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data.get('categoria', ''), '')


class MetaAhorroFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.moneda = Moneda.objects.create(nombre='Dolar', codigo='USD', simbolo='$')
        cls.usuario = Usuario.objects.create_user(
            correo='test@test.com', password='testpass123',
            nombres='Test', apellido_paterno='Test', apellido_materno='User',
            documento_identidad='12345678', telefono=123456789,
            id_moneda=cls.moneda,
        )
        cls.cuenta = Cuenta.objects.create(
            nombre='Test Account', descripcion='', saldo_cuenta=1000,
            id_usuario=cls.usuario,
        )

    def test_valid_form_with_all_fields(self):
        form = MetaAhorroForm(
            data={
                'nombre': 'Test Goal',
                'descripcion': 'My savings goal',
                'monto_objetivo': '1000.00',
                'fecha_inicio': date.today().isoformat(),
                'fecha_limite': (date.today() + timedelta(days=30)).isoformat(),
                'frecuencia_aporte': 'mensual',
                'id_cuenta': self.cuenta.pk,
            },
            user=self.usuario,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_requires_user_kwarg(self):
        otro_usuario = Usuario.objects.create_user(
            correo='otro2@test.com', password='testpass123',
            nombres='Otro', apellido_paterno='Test', apellido_materno='User',
            documento_identidad='11111111', telefono=111111111,
            id_moneda=self.moneda,
        )
        otra_cuenta = Cuenta.objects.create(
            nombre='Other Account', descripcion='', saldo_cuenta=500,
            id_usuario=otro_usuario,
        )
        form = MetaAhorroForm(
            data={
                'nombre': 'Test Goal',
                'descripcion': 'desc',
                'monto_objetivo': '1000.00',
                'fecha_inicio': date.today().isoformat(),
                'fecha_limite': (date.today() + timedelta(days=30)).isoformat(),
                'frecuencia_aporte': 'mensual',
                'id_cuenta': self.cuenta.pk,
            },
            user=self.usuario,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIn(self.cuenta, form.fields['id_cuenta'].queryset)
        self.assertNotIn(otra_cuenta, form.fields['id_cuenta'].queryset)

    def test_clean_validates_fecha_limite_after_fecha_inicio(self):
        form = MetaAhorroForm(
            data={
                'nombre': 'Bad Goal',
                'descripcion': 'Reversed dates',
                'monto_objetivo': '1000.00',
                'fecha_inicio': (date.today() + timedelta(days=30)).isoformat(),
                'fecha_limite': date.today().isoformat(),
                'frecuencia_aporte': 'mensual',
                'id_cuenta': self.cuenta.pk,
            },
            user=self.usuario,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'La fecha límite debe ser posterior a la fecha de inicio.',
            str(form.errors),
        )

    def test_clean_validates_monto_objetivo_positive(self):
        form = MetaAhorroForm(
            data={
                'nombre': 'Bad Goal',
                'descripcion': 'Negative amount',
                'monto_objetivo': '-100.00',
                'fecha_inicio': date.today().isoformat(),
                'fecha_limite': (date.today() + timedelta(days=30)).isoformat(),
                'frecuencia_aporte': 'mensual',
                'id_cuenta': self.cuenta.pk,
            },
            user=self.usuario,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'El monto objetivo debe ser mayor a cero.',
            str(form.errors),
        )

    def test_future_dates_are_valid(self):
        form = MetaAhorroForm(
            data={
                'nombre': 'Future Goal',
                'descripcion': 'Future savings',
                'monto_objetivo': '5000.00',
                'fecha_inicio': (date.today() + timedelta(days=10)).isoformat(),
                'fecha_limite': (date.today() + timedelta(days=40)).isoformat(),
                'frecuencia_aporte': 'semanal',
                'id_cuenta': self.cuenta.pk,
            },
            user=self.usuario,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_reversed_dates_are_invalid(self):
        form = MetaAhorroForm(
            data={
                'nombre': 'Reversed Goal',
                'descripcion': 'Start after limit',
                'monto_objetivo': '2000.00',
                'fecha_inicio': date.today().isoformat(),
                'fecha_limite': (date.today() - timedelta(days=1)).isoformat(),
                'frecuencia_aporte': 'diaria',
                'id_cuenta': self.cuenta.pk,
            },
            user=self.usuario,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'La fecha límite debe ser posterior a la fecha de inicio.',
            str(form.errors),
        )

    def test_same_date_is_invalid(self):
        today = date.today().isoformat()
        form = MetaAhorroForm(
            data={
                'nombre': 'Same Day Goal',
                'descripcion': 'Equal dates',
                'monto_objetivo': '1000.00',
                'fecha_inicio': today,
                'fecha_limite': today,
                'frecuencia_aporte': 'mensual',
                'id_cuenta': self.cuenta.pk,
            },
            user=self.usuario,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'La fecha límite debe ser posterior a la fecha de inicio.',
            str(form.errors),
        )


class AporteMetaAhorroFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.moneda = Moneda.objects.create(nombre='Dolar', codigo='USD', simbolo='$')
        cls.usuario = Usuario.objects.create_user(
            correo='test@test.com', password='testpass123',
            nombres='Test', apellido_paterno='Test', apellido_materno='User',
            documento_identidad='12345678', telefono=123456789,
            id_moneda=cls.moneda,
        )
        cls.cuenta = Cuenta.objects.create(
            nombre='Test Account', descripcion='', saldo_cuenta=1000,
            id_usuario=cls.usuario,
        )
        cls.meta = MetaAhorro.objects.create(
            nombre='Test Goal', monto_objetivo=1000,
            fecha_inicio=date.today(),
            fecha_limite=date.today() + timedelta(days=30),
            frecuencia_aporte='mensual', descripcion='Test goal description',
            id_usuario=cls.usuario, id_cuenta=cls.cuenta,
        )

    def test_valid_monto(self):
        form = AporteMetaAhorroForm(
            data={'monto': '100.00', 'descripcion': 'Aporte mensual'},
            meta_ahorro=self.meta,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_clean_monto_rejects_negative_monto(self):
        form = AporteMetaAhorroForm(
            data={'monto': '-50.00', 'descripcion': 'invalido'},
            meta_ahorro=self.meta,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('monto', form.errors)

    def test_clean_monto_accepts_zero_monto(self):
        form = AporteMetaAhorroForm(
            data={'monto': '0.00', 'descripcion': 'cero'},
            meta_ahorro=self.meta,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_descripcion_is_optional(self):
        form = AporteMetaAhorroForm(
            data={'monto': '75.00'},
            meta_ahorro=self.meta,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_accepts_meta_ahorro_kwarg(self):
        form = AporteMetaAhorroForm(
            data={'monto': '200.00', 'descripcion': 'Kwarg test'},
            meta_ahorro=self.meta,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.meta_ahorro, self.meta)

    def test_with_meta_ahorro_falta_por_ahorrar(self):
        falta = self.meta.falta_por_ahorrar()
        form = AporteMetaAhorroForm(
            data={'monto': '50.00'},
            meta_ahorro=self.meta,
        )
        self.assertTrue(form.is_valid(), form.errors)
        expected = f'Cantidad a aportar. Falta: ${falta:.2f} para alcanzar la meta'
        self.assertEqual(form.fields['monto'].help_text, expected)

    def test_clean_monto_accepts_decimals(self):
        form = AporteMetaAhorroForm(
            data={'monto': '99.99'},
            meta_ahorro=self.meta,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['monto'], Decimal('99.99'))
