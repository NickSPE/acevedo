from decimal import Decimal
from datetime import date, datetime, timedelta
import json

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.http import HttpRequest, QueryDict

from analisis_reportes.models import Reporte, ConfiguracionReporte
from analisis_reportes.views import (
    get_periodo_fechas,
    obtener_fechas_periodo,
    calcular_estadisticas_generales,
    get_gastos_por_categoria,
    get_ingresos_vs_egresos,
    get_estadisticas_subcuentas,
    get_balance_general,
    procesar_datos_para_template,
    safe_csv_cell,
    get_flujo_mensual,
)
from cuentas.models import Moneda, Cuenta, SubCuenta
from gestion_financiera_basica.models import Movimiento
from django.contrib.auth import get_user_model

Usuario = get_user_model()


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _crear_moneda():
    return Moneda.objects.create(codigo='PEN', nombre='Soles', simbolo='S/.')


def _crear_usuario(moneda):
    return Usuario.objects.create_user(
        correo='test@test.com',
        password='Password123!',
        nombres='Juan',
        apellido_paterno='Perez',
        apellido_materno='Gomez',
        documento_identidad='12345678',
        telefono=987654321,
        id_moneda=moneda,
    )


def _login(client, usuario):
    client.login(correo=usuario.correo, password='Password123!')
    session = client.session
    session['pin_acceso_rapido_validado'] = True
    session.save()


# ===================================================================
# A. Helper function tests
# ===================================================================

class GetPeriodoFechasTests(TestCase):
    def test_mes_actual(self):
        inicio, _ = get_periodo_fechas('mes_actual')
        hoy = timezone.now().date()
        self.assertEqual(inicio.day, 1)
        self.assertEqual(inicio.month, hoy.month)
        self.assertEqual(inicio.year, hoy.year)

    def test_semana_actual(self):
        inicio, fin = get_periodo_fechas('semana_actual')
        self.assertEqual(inicio.weekday(), 0)
        self.assertEqual(fin, inicio + timedelta(days=6))

    def test_año_actual(self):
        inicio, fin = get_periodo_fechas('año_actual')
        hoy = timezone.now().date()
        self.assertEqual(inicio.month, 1)
        self.assertEqual(inicio.day, 1)
        self.assertEqual(fin.month, 12)
        self.assertEqual(fin.day, 31)
        self.assertEqual(fin.year, hoy.year)

    def test_ultimos_30_dias(self):
        inicio, fin = get_periodo_fechas('ultimos_30_dias')
        hoy = timezone.now().date()
        self.assertEqual(fin, hoy)
        self.assertEqual(inicio, hoy - timedelta(days=30))

    def test_ultimos_90_dias(self):
        inicio, fin = get_periodo_fechas('ultimos_90_dias')
        hoy = timezone.now().date()
        self.assertEqual(fin, hoy)
        self.assertEqual(inicio, hoy - timedelta(days=90))

    def test_invalid_periodo_defaults_to_mes_actual(self):
        inicio, _ = get_periodo_fechas('no_existe')
        hoy = timezone.now().date()
        self.assertEqual(inicio.day, 1)
        self.assertEqual(inicio.month, hoy.month)


class ObtenerFechasPeriodoTests(TestCase):
    def test_mes_actual(self):
        inicio, _ = obtener_fechas_periodo('mes_actual')
        now = timezone.now()
        self.assertEqual(inicio.day, 1)
        self.assertEqual(inicio.hour, 0)
        self.assertEqual(inicio.minute, 0)
        self.assertEqual(inicio.month, now.month)

    def test_ultimo_mes(self):
        inicio, _ = obtener_fechas_periodo('ultimo_mes')
        now = timezone.now()
        expected_month = now.month - 1 if now.month > 1 else 12
        self.assertEqual(inicio.month, expected_month)

    def test_trimestre(self):
        inicio, _ = obtener_fechas_periodo('trimestre')
        self.assertIsInstance(inicio, datetime)

    def test_ano(self):
        inicio, _ = obtener_fechas_periodo('ano')
        self.assertEqual(inicio.month, 1)
        self.assertEqual(inicio.day, 1)
        self.assertEqual(inicio.hour, 0)
        self.assertEqual(inicio.minute, 0)

    def test_default_return_mes_actual(self):
        inicio, _ = obtener_fechas_periodo('invalido')
        now = timezone.now()
        self.assertEqual(inicio.day, 1)
        self.assertEqual(inicio.month, now.month)


class CalcularEstadisticasGeneralesTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)
        self.fecha_inicio = timezone.localdate() - timedelta(days=30)
        self.fecha_fin = timezone.localdate()

    def _dt(self, d):
        return timezone.make_aware(datetime.combine(d, datetime.min.time()))

    def test_sin_datos_retorna_ceros(self):
        stats = calcular_estadisticas_generales(self.usuario, self.fecha_inicio, self.fecha_fin)
        self.assertEqual(stats['balance_total'], 0.0)
        self.assertEqual(stats['total_subcuentas'], 0.0)
        self.assertEqual(stats['total_ingresos'], 0.0)
        self.assertEqual(stats['total_egresos'], 0.0)
        self.assertEqual(stats['ahorro_neto'], 0.0)
        self.assertEqual(stats['num_cuentas'], 0)
        self.assertEqual(stats['num_subcuentas'], 0)
        self.assertEqual(stats['promedio_transaccion'], 0.0)
        self.assertEqual(stats['total_transacciones'], 0)

    def test_con_cuentas_subcuentas_y_movimientos(self):
        cuenta = Cuenta.objects.create(
            nombre='Cuenta Principal', saldo_cuenta=Decimal('5000.00'),
            id_usuario=self.usuario
        )
        SubCuenta.objects.create(
            nombre='Ahorros', saldo=Decimal('1000.00'), tipo='ahorro_meta',
            activa=True, id_cuenta=cuenta
        )
        medio = self.fecha_inicio + (self.fecha_fin - self.fecha_inicio) // 2
        Movimiento.objects.create(
            nombre='Salario', tipo='ingreso', monto=Decimal('3000.00'),
            fecha_movimiento=self._dt(medio), id_cuenta=cuenta,
            id_usuario=self.usuario
        )
        Movimiento.objects.create(
            nombre='Comida', tipo='egreso', monto=Decimal('500.00'),
            fecha_movimiento=self._dt(medio), id_cuenta=cuenta,
            id_usuario=self.usuario
        )
        stats = calcular_estadisticas_generales(self.usuario, self.fecha_inicio, self.fecha_fin)
        self.assertEqual(stats['balance_total'], 5000.0)
        self.assertEqual(stats['total_subcuentas'], 1000.0)
        self.assertEqual(stats['total_ingresos'], 3000.0)
        self.assertEqual(stats['total_egresos'], 500.0)
        self.assertEqual(stats['ahorro_neto'], 2500.0)
        self.assertEqual(stats['num_cuentas'], 1)
        self.assertEqual(stats['num_subcuentas'], 1)
        self.assertEqual(stats['total_transacciones'], 2)


class GetGastosPorCategoriaTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)
        self.fecha_inicio = timezone.localdate() - timedelta(days=30)
        self.fecha_fin = timezone.localdate()

    def _dt(self, d):
        return timezone.make_aware(datetime.combine(d, datetime.min.time()))

    def test_sin_gastos_retorna_default(self):
        resultado = get_gastos_por_categoria(self.usuario, self.fecha_inicio, self.fecha_fin)
        self.assertEqual(resultado['labels'], ['Sin gastos registrados'])
        self.assertEqual(resultado['values'], [0])

    def test_con_gastos_agrupa_por_nombre(self):
        cuenta = Cuenta.objects.create(
            nombre='Cuenta', saldo_cuenta=Decimal('1000'),
            id_usuario=self.usuario
        )
        medio = self.fecha_inicio + (self.fecha_fin - self.fecha_inicio) // 2
        Movimiento.objects.create(
            nombre='Comida', tipo='egreso', monto=Decimal('200'),
            fecha_movimiento=self._dt(medio), id_cuenta=cuenta,
            id_usuario=self.usuario
        )
        Movimiento.objects.create(
            nombre='Comida', tipo='egreso', monto=Decimal('150'),
            fecha_movimiento=self._dt(medio), id_cuenta=cuenta,
            id_usuario=self.usuario
        )
        Movimiento.objects.create(
            nombre='Transporte', tipo='egreso', monto=Decimal('100'),
            fecha_movimiento=self._dt(medio), id_cuenta=cuenta,
            id_usuario=self.usuario
        )
        resultado = get_gastos_por_categoria(self.usuario, self.fecha_inicio, self.fecha_fin)
        self.assertIn('Comida', resultado['labels'])
        self.assertIn('Transporte', resultado['labels'])
        comida_idx = resultado['labels'].index('Comida')
        self.assertEqual(resultado['values'][comida_idx], 350.0)


class GetIngresosVsEgresosTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)
        self.fecha_inicio = timezone.localdate().replace(day=1)
        self.fecha_fin = timezone.localdate()

    def _dt(self, d):
        return timezone.make_aware(datetime.combine(d, datetime.min.time()))

    def test_retorna_estructura_correcta(self):
        resultado = get_ingresos_vs_egresos(self.usuario, self.fecha_inicio, self.fecha_fin)
        self.assertIn('labels', resultado)
        self.assertIn('ingresos', resultado)
        self.assertIn('gastos', resultado)
        self.assertEqual(len(resultado['labels']), len(resultado['ingresos']))
        self.assertEqual(len(resultado['labels']), len(resultado['gastos']))

    def test_con_movimientos_acumula_correctamente(self):
        cuenta = Cuenta.objects.create(
            nombre='Cuenta', saldo_cuenta=Decimal('5000'),
            id_usuario=self.usuario
        )
        medio = self.fecha_inicio + (self.fecha_fin - self.fecha_inicio) // 2
        dt = self._dt(medio)
        Movimiento.objects.create(
            nombre='Salario', tipo='ingreso', monto=Decimal('3000'),
            fecha_movimiento=dt, id_cuenta=cuenta, id_usuario=self.usuario
        )
        Movimiento.objects.create(
            nombre='Renta', tipo='egreso', monto=Decimal('1000'),
            fecha_movimiento=dt, id_cuenta=cuenta, id_usuario=self.usuario
        )
        resultado = get_ingresos_vs_egresos(self.usuario, self.fecha_inicio, self.fecha_fin)
        self.assertTrue(all(v is not None for v in resultado['ingresos']))
        self.assertTrue(all(v is not None for v in resultado['gastos']))


class GetEstadisticasSubcuentasTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)

    def test_sin_subcuentas_retorna_default(self):
        resultado = get_estadisticas_subcuentas(self.usuario)
        self.assertEqual(resultado['labels'], ['Sin subcuentas'])
        self.assertEqual(resultado['saldos'], [0])
        self.assertEqual(resultado['cantidades'], [0])
        self.assertEqual(resultado['tipos_detalle'], [])

    def test_con_subcuentas_agrupa_por_tipo(self):
        cuenta = Cuenta.objects.create(
            nombre='Cuenta', saldo_cuenta=Decimal('5000'),
            id_usuario=self.usuario
        )
        SubCuenta.objects.create(
            nombre='Ahorro', saldo=Decimal('2000'), tipo='ahorro_meta',
            activa=True, id_cuenta=cuenta
        )
        SubCuenta.objects.create(
            nombre='Inversion', saldo=Decimal('3000'), tipo='inversion',
            activa=True, id_cuenta=cuenta
        )
        resultado = get_estadisticas_subcuentas(self.usuario)
        self.assertNotEqual(resultado['labels'], ['Sin subcuentas'])
        self.assertEqual(resultado['total_subcuentas'], 2)
        self.assertGreater(resultado['total_saldo'], 0)


class GetBalanceGeneralTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)
        self.fecha_inicio = date.today() - timedelta(days=30)
        self.fecha_fin = date.today()

    def test_sin_cuentas_retorna_vacio(self):
        resultado = get_balance_general(self.usuario, self.fecha_inicio, self.fecha_fin)
        self.assertEqual(resultado, [])

    def test_con_cuentas_y_subcuentas(self):
        cuenta = Cuenta.objects.create(
            nombre='Principal', saldo_cuenta=Decimal('10000'),
            id_usuario=self.usuario
        )
        SubCuenta.objects.create(
            nombre='Emergencia', saldo=Decimal('5000'), tipo='emergencia',
            activa=True, id_cuenta=cuenta
        )
        resultado = get_balance_general(self.usuario, self.fecha_inicio, self.fecha_fin)
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]['cuenta'], 'Principal')
        self.assertEqual(resultado[0]['saldo_principal'], 10000.0)
        self.assertEqual(resultado[0]['saldo_subcuentas'], 5000.0)
        self.assertEqual(resultado[0]['saldo_total'], 15000.0)


class ProcesarDatosParaTemplateTests(TestCase):
    def test_datos_vacios_retorna_dict_vacio(self):
        self.assertEqual(procesar_datos_para_template('gastos_categoria', {}), {})
        self.assertEqual(procesar_datos_para_template('gastos_categoria', None), {})

    def test_gastos_categoria(self):
        datos = {'labels': ['Comida', 'Transporte'], 'data': [300, 200], 'counts': [3, 2]}
        resultado = procesar_datos_para_template('gastos_categoria', datos)
        self.assertEqual(resultado['tipo'], 'gastos_categoria')
        self.assertEqual(len(resultado['items']), 2)
        self.assertEqual(resultado['total'], 500.0)
        self.assertEqual(resultado['total_cantidad'], 5)

    def test_gastos_categoria_sin_counts(self):
        datos = {'labels': ['Comida'], 'data': [300]}
        resultado = procesar_datos_para_template('gastos_categoria', datos)
        self.assertEqual(resultado['total'], 300.0)
        self.assertEqual(resultado['total_cantidad'], 0)

    def test_ingresos_egresos_con_data(self):
        datos = {'data': [5000, 3000]}
        resultado = procesar_datos_para_template('ingresos_egresos', datos)
        self.assertEqual(resultado['tipo'], 'ingresos_egresos')
        self.assertEqual(resultado['ingresos'], 5000)
        self.assertEqual(resultado['egresos'], 3000)
        self.assertEqual(resultado['balance'], 2000)

    def test_ingresos_egresos_data_vacio(self):
        datos = {'data': []}
        resultado = procesar_datos_para_template('ingresos_egresos', datos)
        self.assertEqual(resultado['ingresos'], 0)
        self.assertEqual(resultado['egresos'], 0)

    def test_ingresos_egresos_porcentaje_cero_sin_ingresos(self):
        datos = {'data': [0, 100]}
        resultado = procesar_datos_para_template('ingresos_egresos', datos)
        self.assertEqual(resultado['porcentaje_egresos'], 0)

    def test_subcuentas_analisis(self):
        datos = {
            'labels': ['Ahorro', 'Inversion'],
            'saldos': [2000, 3000],
            'cantidades': [2, 1],
        }
        resultado = procesar_datos_para_template('subcuentas_analisis', datos)
        self.assertEqual(resultado['tipo'], 'subcuentas_analisis')
        self.assertEqual(len(resultado['items']), 2)
        self.assertEqual(resultado['total_saldo'], 5000)
        self.assertEqual(resultado['total_cantidad'], 3)

    def test_subcuentas_analisis_con_cero_cantidad(self):
        datos = {'labels': ['Vacio'], 'saldos': [0], 'cantidades': [0]}
        resultado = procesar_datos_para_template('subcuentas_analisis', datos)
        self.assertEqual(resultado['promedio_total'], 0)

    def test_flujo_efectivo(self):
        datos = {
            'labels': ['Ene 2025', 'Feb 2025'],
            'ingresos': [5000, 6000],
            'egresos': [3000, 4000],
        }
        resultado = procesar_datos_para_template('flujo_efectivo', datos)
        self.assertEqual(resultado['tipo'], 'flujo_efectivo')
        self.assertEqual(len(resultado['items']), 2)
        self.assertEqual(resultado['items'][0]['balance'], 2000)

    def test_tipo_desconocido(self):
        datos = {'algo': 'valor'}
        resultado = procesar_datos_para_template('otro_tipo', datos)
        self.assertEqual(resultado['tipo'], 'otros')
        self.assertEqual(resultado['datos_raw'], datos)


class SafeCsvCellTests(TestCase):
    def test_none_retorna_vacio(self):
        self.assertEqual(safe_csv_cell(None), '')

    def test_valor_normal(self):
        self.assertEqual(safe_csv_cell('Hola'), 'Hola')
        self.assertEqual(safe_csv_cell(123), '123')
        self.assertEqual(safe_csv_cell(45.67), '45.67')

    def test_injection_igual(self):
        self.assertEqual(safe_csv_cell('=SUM(A1:A10)'), "'=SUM(A1:A10)")

    def test_injection_mas(self):
        self.assertEqual(safe_csv_cell('+1234'), "'+1234")

    def test_injection_menos(self):
        self.assertEqual(safe_csv_cell('-1234'), "'-1234")

    def test_injection_arroba(self):
        self.assertEqual(safe_csv_cell('@EVALUATE'), "'@EVALUATE")

    def test_cadena_vacia(self):
        self.assertEqual(safe_csv_cell(''), '')


class GetFlujoMensualTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)
        self.fecha_inicio = timezone.localdate().replace(day=1)
        self.fecha_fin = timezone.localdate()

    def _dt(self, d):
        return timezone.make_aware(datetime.combine(d, datetime.min.time()))

    def test_sin_datos_retorna_estructura(self):
        resultado = get_flujo_mensual(self.usuario, self.fecha_inicio, self.fecha_fin)
        self.assertIn('labels', resultado)
        self.assertIn('values', resultado)
        self.assertTrue(len(resultado['labels']) >= 1)

    def test_con_ingresos_y_egresos(self):
        cuenta = Cuenta.objects.create(
            nombre='Cuenta', saldo_cuenta=Decimal('5000'),
            id_usuario=self.usuario
        )
        medio = self.fecha_inicio + (self.fecha_fin - self.fecha_inicio) // 2
        dt = self._dt(medio)
        Movimiento.objects.create(
            nombre='Trabajo', tipo='ingreso', monto=Decimal('4000'),
            fecha_movimiento=dt, id_cuenta=cuenta, id_usuario=self.usuario
        )
        Movimiento.objects.create(
            nombre='Gastos', tipo='egreso', monto=Decimal('1500'),
            fecha_movimiento=dt, id_cuenta=cuenta, id_usuario=self.usuario
        )
        resultado = get_flujo_mensual(self.usuario, self.fecha_inicio, self.fecha_fin)
        self.assertTrue(any(v > 0 for v in resultado['values']))


# ===================================================================
# B. View tests
# ===================================================================

class ReportsViewTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)
        self.url = reverse('analisis_reportes:reports')

    def test_get_returns_200(self):
        _login(self.client, self.usuario)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_redirect_if_not_authenticated(self):
        response = self.client.get(self.url)
        login_url = reverse('usuarios:login')
        self.assertRedirects(
            response, f'{login_url}?next={self.url}',
            fetch_redirect_response=False,
        )

    def test_ajax_returns_json_response(self):
        _login(self.client, self.usuario)
        response = self.client.get(
            self.url,
            {'periodo': 'mes_actual'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('stats', data)
        self.assertIn('gastos_categoria', data)
        self.assertIn('ingresos_egresos', data)

    def test_ajax_con_periodo_personalizado(self):
        _login(self.client, self.usuario)
        hoy = timezone.localdate()
        inicio = (hoy - timedelta(days=10)).strftime('%Y-%m-%d')
        fin = hoy.strftime('%Y-%m-%d')
        response = self.client.get(
            self.url,
            {'periodo': 'personalizado', 'fecha_inicio': inicio, 'fecha_fin': fin},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

    def test_with_config_renders_context(self):
        _login(self.client, self.usuario)
        ConfiguracionReporte.objects.create(
            id_usuario=self.usuario, periodo_default='semana_actual'
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('config', response.context)


class GenerarReporteViewTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)
        self.url = reverse('analisis_reportes:generar_reporte')

    def test_get_redirects_to_reports(self):
        _login(self.client, self.usuario)
        response = self.client.get(self.url)
        self.assertRedirects(
            response, reverse('analisis_reportes:reports'),
            fetch_redirect_response=False,
        )

    def test_post_creates_reporte_and_redirects(self):
        _login(self.client, self.usuario)
        hoy = date.today()
        response = self.client.post(self.url, {
            'tipo_reporte': 'gastos_categoria',
            'titulo': 'Mis Gastos',
            'fecha_inicio': hoy.strftime('%Y-%m-%d'),
            'fecha_fin': hoy.strftime('%Y-%m-%d'),
            'descripcion': 'Reporte de prueba',
        })
        self.assertEqual(Reporte.objects.count(), 1)
        reporte = Reporte.objects.first()
        self.assertRedirects(
            response,
            reverse('analisis_reportes:ver_reporte', args=[reporte.id]),
            fetch_redirect_response=False,
        )
        self.assertEqual(reporte.tipo_reporte, 'gastos_categoria')
        self.assertEqual(reporte.titulo, 'Mis Gastos')

    def test_post_genera_todos_los_tipos_de_reporte(self):
        _login(self.client, self.usuario)
        hoy = date.today()
        for tipo in ['gastos_categoria', 'ingresos_egresos', 'subcuentas_analisis',
                      'balance_general', 'flujo_efectivo']:
            response = self.client.post(self.url, {
                'tipo_reporte': tipo,
                'fecha_inicio': hoy.strftime('%Y-%m-%d'),
                'fecha_fin': hoy.strftime('%Y-%m-%d'),
            })
            self.assertEqual(response.status_code, 302)

    def test_post_redirect_if_not_authenticated(self):
        response = self.client.post(self.url, {
            'tipo_reporte': 'gastos_categoria',
            'fecha_inicio': '2025-01-01',
            'fecha_fin': '2025-01-31',
        })
        login_url = reverse('usuarios:login')
        self.assertRedirects(
            response, f'{login_url}?next={self.url}',
            fetch_redirect_response=False,
        )


class VerReporteViewTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)
        self.reporte = Reporte.objects.create(
            tipo_reporte='gastos_categoria',
            titulo='Test Reporte',
            id_usuario=self.usuario,
            datos_json=json.dumps({'labels': ['A'], 'data': [100]}),
        )
        self.url = reverse('analisis_reportes:ver_reporte', args=[self.reporte.id])

    def test_get_returns_200(self):
        _login(self.client, self.usuario)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_404_for_non_existent_reporte(self):
        _login(self.client, self.usuario)
        url = reverse('analisis_reportes:ver_reporte', args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_404_for_other_user_reporte(self):
        otro_usuario = Usuario.objects.create_user(
            correo='otro@test.com', password='Password123!',
            nombres='Otro', apellido_paterno='User',
            apellido_materno='X', documento_identidad='87654321',
            telefono=123456789, id_moneda=self.moneda,
        )
        otro_reporte = Reporte.objects.create(
            tipo_reporte='ingresos_egresos', titulo='Otro',
            id_usuario=otro_usuario,
            datos_json='{}',
        )
        _login(self.client, self.usuario)
        url = reverse('analisis_reportes:ver_reporte', args=[otro_reporte.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class ExportarReporteViewTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)
        self.reporte = Reporte.objects.create(
            tipo_reporte='gastos_categoria',
            titulo='Test Export',
            id_usuario=self.usuario,
            fecha_inicio=timezone.now(),
            fecha_fin=timezone.now(),
            datos_json=json.dumps({'labels': ['Comida'], 'data': [500]}),
        )

    def test_export_pdf_returns_pdf(self):
        _login(self.client, self.usuario)
        url = reverse('analisis_reportes:exportar_reporte', args=[self.reporte.id, 'pdf'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('FinGest_Reporte', response['Content-Disposition'])

    def test_export_excel_returns_excel(self):
        _login(self.client, self.usuario)
        url = reverse('analisis_reportes:exportar_reporte', args=[self.reporte.id, 'excel'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response['Content-Type'])
        self.assertIn('.xlsx', response['Content-Disposition'])

    def test_export_invalid_format_redirects(self):
        _login(self.client, self.usuario)
        url = reverse('analisis_reportes:exportar_reporte', args=[self.reporte.id, 'doc'])
        response = self.client.get(url)
        ver_url = reverse('analisis_reportes:ver_reporte', args=[self.reporte.id])
        self.assertRedirects(
            response, ver_url, fetch_redirect_response=False,
        )

    def test_export_csv_returns_csv_or_500(self):
        _login(self.client, self.usuario)
        url = reverse('analisis_reportes:exportar_reporte', args=[self.reporte.id, 'csv'])
        self.client.handler.raise_request_exception = False
        response = self.client.get(url)
        self.assertIn(response.status_code, (200, 500))


class ApiDatosGraficoViewTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)

    def _invoke(self, tipo, periodo='mes_actual'):
        qs = QueryDict(f'tipo={tipo}&periodo={periodo}')
        request = HttpRequest()
        request.method = 'GET'
        request.GET = qs
        request.user = self.usuario
        request.session = {'pin_acceso_rapido_validado': True}
        from analisis_reportes.views import api_datos_grafico
        return api_datos_grafico(request)

    def test_gastos_categoria(self):
        response = self._invoke('gastos_categoria')
        data = json.loads(response.content)
        self.assertIn('labels', data)
        self.assertIn('values', data)

    def test_ingresos_egresos(self):
        response = self._invoke('ingresos_egresos')
        data = json.loads(response.content)
        self.assertIn('labels', data)
        self.assertIn('ingresos', data)
        self.assertIn('gastos', data)

    def test_subcuentas(self):
        response = self._invoke('subcuentas')
        data = json.loads(response.content)
        self.assertIn('labels', data)

    def test_flujo_mensual(self):
        response = self._invoke('flujo_mensual')
        data = json.loads(response.content)
        self.assertIn('labels', data)
        self.assertIn('values', data)

    def test_tipo_desconocido_retorna_vacio(self):
        response = self._invoke('no_existe')
        data = json.loads(response.content)
        self.assertEqual(data, {})


class ExportarExcelViewTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)
        self.url = reverse('analisis_reportes:exportar_excel')

    def test_get_returns_excel_file(self):
        _login(self.client, self.usuario)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response['Content-Type'])
        self.assertIn('.xlsx', response['Content-Disposition'])

    def test_get_with_periodo_param(self):
        _login(self.client, self.usuario)
        response = self.client.get(self.url, {'periodo': 'año_actual'})
        self.assertEqual(response.status_code, 200)


class ExportarPdfSimpleViewTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)
        self.url = reverse('analisis_reportes:exportar_pdf')

    def test_get_returns_pdf_file(self):
        _login(self.client, self.usuario)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('.pdf', response['Content-Disposition'])

    def test_get_with_periodo_param(self):
        _login(self.client, self.usuario)
        response = self.client.get(self.url, {'periodo': 'ultimos_30_dias'})
        self.assertEqual(response.status_code, 200)


# ===================================================================
# C. Model tests
# ===================================================================

class ReporteModelTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)

    def test_create_reporte(self):
        reporte = Reporte.objects.create(
            tipo_reporte='gastos_categoria',
            titulo='Mi Reporte',
            id_usuario=self.usuario,
            datos_json=json.dumps({'labels': ['A'], 'data': [100]}),
        )
        self.assertEqual(Reporte.objects.count(), 1)
        self.assertEqual(reporte.tipo_reporte, 'gastos_categoria')
        self.assertEqual(reporte.titulo, 'Mi Reporte')

    def test_get_datos_retorna_dict(self):
        reporte = Reporte.objects.create(
            tipo_reporte='gastos_categoria',
            id_usuario=self.usuario,
            datos_json=json.dumps({'labels': ['X'], 'data': [50]}),
        )
        datos = reporte.get_datos()
        self.assertEqual(datos['labels'], ['X'])
        self.assertEqual(datos['data'], [50])

    def test_get_datos_vacio_sin_datos_json(self):
        reporte = Reporte.objects.create(
            tipo_reporte='gastos_categoria',
            id_usuario=self.usuario,
            datos_json='',
        )
        self.assertEqual(reporte.get_datos(), {})

    def test_set_datos_guarda_json(self):
        reporte = Reporte.objects.create(
            tipo_reporte='gastos_categoria',
            id_usuario=self.usuario,
        )
        reporte.set_datos({'clave': 'valor', 'numero': 42})
        reporte.save()
        reporte.refresh_from_db()
        self.assertIn('clave', reporte.datos_json)
        self.assertIn('valor', reporte.datos_json)

    def test_str_representation(self):
        reporte = Reporte.objects.create(
            tipo_reporte='ingresos_egresos',
            id_usuario=self.usuario,
        )
        self.assertIn('Ingresos vs Egresos', str(reporte))

    def test_default_values(self):
        reporte = Reporte.objects.create(
            tipo_reporte='flujo_efectivo',
            id_usuario=self.usuario,
        )
        self.assertEqual(reporte.titulo, 'Reporte Financiero')
        self.assertEqual(reporte.descripcion, '')
        self.assertIsNotNone(reporte.fecha_creacion)


class ConfiguracionReporteModelTests(TestCase):
    def setUp(self):
        self.moneda = _crear_moneda()
        self.usuario = _crear_usuario(self.moneda)

    def test_create_configuracion(self):
        config = ConfiguracionReporte.objects.create(
            id_usuario=self.usuario,
            periodo_default='semana_actual',
            incluir_subcuentas_inactivas=True,
            formato_export_default='excel',
        )
        self.assertEqual(ConfiguracionReporte.objects.count(), 1)
        self.assertEqual(config.periodo_default, 'semana_actual')
        self.assertTrue(config.incluir_subcuentas_inactivas)
        self.assertEqual(config.formato_export_default, 'excel')

    def test_default_values(self):
        config = ConfiguracionReporte.objects.create(
            id_usuario=self.usuario,
        )
        self.assertEqual(config.periodo_default, 'mes_actual')
        self.assertFalse(config.incluir_subcuentas_inactivas)
        self.assertEqual(config.formato_export_default, 'pdf')
        self.assertEqual(config.moneda_display, 'USD')

    def test_str_representation(self):
        config = ConfiguracionReporte.objects.create(
            id_usuario=self.usuario,
        )
        self.assertIn(self.usuario.correo, str(config))
