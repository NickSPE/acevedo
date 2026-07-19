from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from cuentas.models import Moneda, Cuenta, SubCuenta
from gestion_financiera_basica.models import Movimiento, MetaAhorro, AporteMetaAhorro

Usuario = get_user_model()


class GestionFinancieraBasicaViewsTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='gf_test@test.com',
            password='Password123!',
            nombres='Gf',
            apellido_paterno='Test',
            apellido_materno='User',
            documento_identidad='87654321',
            telefono=987654321,
            id_moneda=self.moneda,
            email_verificado=True,
            onboarding_completed=True
        )
        self.cuenta = Cuenta.objects.create(
            nombre='Cuenta Principal',
            saldo_cuenta=Decimal('5000.00'),
            id_usuario=self.usuario
        )
        self.client.force_login(self.usuario)

    def test_savings_goals_view_no_goals(self):
        response = self.client.get(reverse('gestion_financiera_basica:savings_goals'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gestion_financiera_basica/savings_goals.html')
        self.assertEqual(len(response.context['goals']), 0)
        self.assertEqual(response.context['estadisticas']['total_objetivo'], 0.0)

    def test_savings_goals_view_with_various_goals(self):
        # 1. Meta completada
        meta_completa = MetaAhorro.objects.create(
            nombre='Viaje Europa',
            descripcion='Ahorro para viaje',
            monto_objetivo=Decimal('1000.00'),
            fecha_inicio=date.today(),
            fecha_limite=date.today() + timedelta(days=30),
            frecuencia_aporte='mensual',
            id_usuario=self.usuario,
            id_cuenta=self.cuenta
        )
        AporteMetaAhorro.objects.create(
            id_meta_ahorro=meta_completa,
            monto=Decimal('1000.00'),
            descripcion='Aporte final',
            id_usuario=self.usuario
        )

        # 2. Meta al 90% (casi completa)
        meta_casi_completa = MetaAhorro.objects.create(
            nombre='Laptop',
            descripcion='Nueva laptop',
            monto_objetivo=Decimal('2000.00'),
            fecha_inicio=date.today(),
            fecha_limite=date.today() + timedelta(days=60),
            frecuencia_aporte='quincenal',
            id_usuario=self.usuario,
            id_cuenta=self.cuenta
        )
        AporteMetaAhorro.objects.create(
            id_meta_ahorro=meta_casi_completa,
            monto=Decimal('1900.00'),
            id_usuario=self.usuario
        )

        # 3. Meta al 10% (atencion)
        meta_baja = MetaAhorro.objects.create(
            nombre='Fondo Emergencia',
            monto_objetivo=Decimal('10000.00'),
            fecha_inicio=date.today(),
            fecha_limite=date.today() + timedelta(days=365),
            frecuencia_aporte='mensual',
            id_usuario=self.usuario,
            id_cuenta=self.cuenta
        )
        AporteMetaAhorro.objects.create(
            id_meta_ahorro=meta_baja,
            monto=Decimal('1000.00'),
            id_usuario=self.usuario
        )

        response = self.client.get(reverse('gestion_financiera_basica:savings_goals'))
        self.assertEqual(response.status_code, 200)
        goals = response.context['goals']
        self.assertEqual(len(goals), 3)
        self.assertEqual(response.context['estadisticas']['metas_completadas'], 1)
        self.assertGreater(len(response.context['tips_dinamicos']), 0)

    def test_transactions_view_all_and_filters(self):
        # Crear movimientos
        m1 = Movimiento.objects.create(
            nombre='Sueldo Freelance',
            tipo='ingreso',
            monto=Decimal('1500.00'),
            fecha_movimiento=timezone.now(),
            id_cuenta=self.cuenta,
            id_usuario=self.usuario
        )
        m2 = Movimiento.objects.create(
            nombre='Supermercado Semanal',
            tipo='egreso',
            monto=Decimal('250.00'),
            fecha_movimiento=timezone.now() - timedelta(days=2),
            id_cuenta=self.cuenta,
            id_usuario=self.usuario
        )

        # 1. Sin filtros
        response = self.client.get(reverse('gestion_financiera_basica:transactions'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['transactions'].count(), 2)

        # 2. Filtrar ingresos
        response = self.client.get(reverse('gestion_financiera_basica:transactions') + '?filter=income')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['transactions'].count(), 1)
        self.assertEqual(response.context['transactions'][0].nombre, 'Sueldo Freelance')

        # 3. Filtrar egresos
        response = self.client.get(reverse('gestion_financiera_basica:transactions') + '?filter=expenses')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['transactions'].count(), 1)
        self.assertEqual(response.context['transactions'][0].nombre, 'Supermercado Semanal')

        # 4. Búsqueda por query
        response = self.client.get(reverse('gestion_financiera_basica:transactions') + '?search=Freelance')
        self.assertEqual(response.context['transactions'].count(), 1)

        # 5. Ordenación
        response = self.client.get(reverse('gestion_financiera_basica:transactions') + '?sort=highest')
        self.assertEqual(response.context['transactions'][0].monto, Decimal('1500.00'))

        response = self.client.get(reverse('gestion_financiera_basica:transactions') + '?sort=lowest')
        self.assertEqual(response.context['transactions'][0].monto, Decimal('250.00'))

        response = self.client.get(reverse('gestion_financiera_basica:transactions') + '?sort=oldest')
        self.assertEqual(response.context['transactions'][0].nombre, 'Supermercado Semanal')

    def test_agregar_movimiento_get(self):
        response = self.client.get(reverse('gestion_financiera_basica:agregar_movimiento'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gestion_financiera_basica/add_transaction.html')

    def test_agregar_movimiento_post_ingreso(self):
        saldo_inicial = self.cuenta.saldo_cuenta
        data = {
            'nombre': 'Venta de Gadget',
            'tipo': 'ingreso',
            'monto': '120.50',
            'id_cuenta': self.cuenta.id,
            'fecha_movimiento': date.today().isoformat(),
            'descripcion': 'Vendido por Marketplace'
        }
        response = self.client.post(reverse('gestion_financiera_basica:agregar_movimiento'), data)
        self.assertRedirects(response, reverse('gestion_financiera_basica:transactions'))
        
        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.saldo_cuenta, saldo_inicial + Decimal('120.50'))
        
        movimiento = Movimiento.objects.get(nombre='Venta de Gadget')
        self.assertEqual(movimiento.tipo, 'ingreso')
        self.assertEqual(movimiento.monto, Decimal('120.50'))

    def test_agregar_movimiento_post_egreso_exitoso(self):
        saldo_inicial = self.cuenta.saldo_cuenta
        data = {
            'nombre': 'Restaurante',
            'tipo': 'egreso',
            'monto': '75.00',
            'id_cuenta': self.cuenta.id,
            'fecha_movimiento': date.today().isoformat(),
            'descripcion': 'Cena de negocios'
        }
        response = self.client.post(reverse('gestion_financiera_basica:agregar_movimiento'), data)
        self.assertRedirects(response, reverse('gestion_financiera_basica:transactions'))

        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.saldo_cuenta, saldo_inicial - Decimal('75.00'))

    def test_agregar_movimiento_post_egreso_saldo_insuficiente(self):
        saldo_inicial = self.cuenta.saldo_cuenta
        data = {
            'nombre': 'Viaje Espacial',
            'tipo': 'egreso',
            'monto': '10000.00',  # Excede los 5000.00 de saldo inicial
            'id_cuenta': self.cuenta.id,
            'fecha_movimiento': date.today().isoformat()
        }
        response = self.client.post(reverse('gestion_financiera_basica:agregar_movimiento'), data)
        self.assertEqual(response.status_code, 200)  # Vuelve a renderizar el form
        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.saldo_cuenta, saldo_inicial)
        # El formulario fue rechazado, saldo intacto

    def test_agregar_movimiento_post_cuenta_no_existe(self):
        data = {
            'nombre': 'Ingreso inválido',
            'tipo': 'ingreso',
            'monto': '100.00',
            'id_cuenta': 9999,  # Cuenta inexistente
            'fecha_movimiento': date.today().isoformat()
        }
        response = self.client.post(reverse('gestion_financiera_basica:agregar_movimiento'), data)
        self.assertEqual(response.status_code, 200)

    def test_agregar_movimiento_ajax_success(self):
        data = {
            'nombre': 'Ingreso Ajax',
            'tipo': 'ingreso',
            'monto': '50.00',
            'id_cuenta': self.cuenta.id,
            'fecha_movimiento': date.today().isoformat()
        }
        response = self.client.post(
            reverse('gestion_financiera_basica:agregar_movimiento'),
            data,
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertTrue(res_json['success'])

    def test_agregar_movimiento_ajax_validation_failure(self):
        data = {
            'nombre': '',  # Inválido
            'tipo': 'ingreso',
            'monto': '50.00',
            'id_cuenta': self.cuenta.id,
            'fecha_movimiento': date.today().isoformat()
        }
        response = self.client.post(
            reverse('gestion_financiera_basica:agregar_movimiento'),
            data,
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertFalse(res_json['success'])

    def test_agregar_movimiento_ajax_saldo_insuficiente(self):
        data = {
            'nombre': 'Gasto Gigante Ajax',
            'tipo': 'egreso',
            'monto': '10000.00',
            'id_cuenta': self.cuenta.id,
            'fecha_movimiento': date.today().isoformat()
        }
        response = self.client.post(
            reverse('gestion_financiera_basica:agregar_movimiento'),
            data,
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertFalse(res_json['success'])
        self.assertIn('Saldo insuficiente', res_json['message'])

    def test_agregar_meta_ahorro_get_and_post(self):
        # 1. GET agregar meta
        response = self.client.get(reverse('gestion_financiera_basica:agregar_meta_ahorro'))
        self.assertEqual(response.status_code, 200)

        # 2. POST agregar meta
        data = {
            'nombre': 'Meta Vacaciones',
            'descripcion': 'Ahorro para fin de año',
            'monto_objetivo': '3000.00',
            'fecha_inicio': date.today().isoformat(),
            'fecha_limite': (date.today() + timedelta(days=120)).isoformat(),
            'frecuencia_aporte': 'mensual',
            'id_cuenta': self.cuenta.id
        }
        response = self.client.post(reverse('gestion_financiera_basica:agregar_meta_ahorro'), data)
        self.assertRedirects(response, reverse('gestion_financiera_basica:savings_goals'))

        meta = MetaAhorro.objects.get(nombre='Meta Vacaciones')
        self.assertEqual(meta.monto_objetivo, Decimal('3000.00'))

    def test_agregar_meta_ahorro_post_invalid_account(self):
        data = {
            'nombre': 'Meta Inválida',
            'monto_objetivo': '1000.00',
            'fecha_inicio': date.today().isoformat(),
            'fecha_limite': (date.today() + timedelta(days=30)).isoformat(),
            'frecuencia_aporte': 'mensual',
            'id_cuenta': 9999  # Cuenta inexistente
        }
        response = self.client.post(reverse('gestion_financiera_basica:agregar_meta_ahorro'), data)
        self.assertEqual(response.status_code, 200)

    def test_aportar_meta_ahorro_get_and_post_exitoso(self):
        meta = MetaAhorro.objects.create(
            nombre='Fondo Laptop',
            monto_objetivo=Decimal('2000.00'),
            fecha_inicio=date.today(),
            fecha_limite=date.today() + timedelta(days=60),
            frecuencia_aporte='mensual',
            id_usuario=self.usuario,
            id_cuenta=self.cuenta
        )

        # GET
        response = self.client.get(reverse('gestion_financiera_basica:aportar_meta_ahorro', args=[meta.id]))
        self.assertEqual(response.status_code, 200)

        # POST aporte válido
        saldo_inicial = self.cuenta.saldo_cuenta
        data = {
            'monto': '200.00',
            'fecha_aporte': date.today().isoformat(),
            'descripcion': 'Primer aporte'
        }
        response = self.client.post(reverse('gestion_financiera_basica:aportar_meta_ahorro', args=[meta.id]), data)
        self.assertRedirects(response, reverse('gestion_financiera_basica:savings_goals'))

        # Validar saldo de cuenta reducido
        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.saldo_cuenta, saldo_inicial - Decimal('200.00'))

        # Validar aporte creado
        aporte = AporteMetaAhorro.objects.get(id_meta_ahorro=meta)
        self.assertEqual(aporte.monto, Decimal('200.00'))

        # Validar movimiento automático de egreso creado
        movimiento = Movimiento.objects.get(nombre=f"Aporte a meta: {meta.nombre}")
        self.assertEqual(movimiento.tipo, 'egreso')
        self.assertEqual(movimiento.monto, Decimal('200.00'))

    def test_aportar_meta_ahorro_saldo_insuficiente(self):
        meta = MetaAhorro.objects.create(
            nombre='Fondo Viaje',
            monto_objetivo=Decimal('10000.00'),
            fecha_inicio=date.today(),
            fecha_limite=date.today() + timedelta(days=60),
            frecuencia_aporte='mensual',
            id_usuario=self.usuario,
            id_cuenta=self.cuenta
        )
        data = {
            'monto': '6000.00',  # Excede saldo de 5000.00
            'fecha_aporte': date.today().isoformat(),
            'descripcion': 'Aporte excesivo'
        }
        response = self.client.post(reverse('gestion_financiera_basica:aportar_meta_ahorro', args=[meta.id]), data)
        self.assertEqual(response.status_code, 200)
        # Saldo sigue igual
        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.saldo_cuenta, Decimal('5000.00'))

    def test_aportar_meta_ahorro_sin_cuenta(self):
        # Crear usuario sin cuenta asociada
        usuario_sin_cuenta = Usuario.objects.create_user(
            correo='gf_no_cuenta@test.com',
            password='Password123!',
            nombres='No',
            apellido_paterno='Cuenta',
            documento_identidad='11223344',
            telefono=987654321,
            id_moneda=self.moneda,
            email_verificado=True,
            onboarding_completed=True
        )
        # Crear una cuenta temporal para asociar la meta al crearla
        temp_cuenta = Cuenta.objects.create(
            nombre='Temp',
            saldo_cuenta=Decimal('500.00'),
            id_usuario=usuario_sin_cuenta
        )
        meta = MetaAhorro.objects.create(
            nombre='Meta Sin Cuenta',
            monto_objetivo=Decimal('1000.00'),
            fecha_inicio=date.today(),
            fecha_limite=date.today() + timedelta(days=60),
            frecuencia_aporte='mensual',
            id_usuario=usuario_sin_cuenta,
            id_cuenta=temp_cuenta
        )
        # Eliminar la cuenta temporal para forzar el flujo de error
        temp_cuenta.delete()

        self.client.force_login(usuario_sin_cuenta)
        data = {
            'monto': '100.00',
            'fecha_aporte': date.today().isoformat(),
        }
        response = self.client.post(reverse('gestion_financiera_basica:aportar_meta_ahorro', args=[meta.id]), data)
        # La meta fue eliminada junto con la cuenta (CASCADE), por lo que la vista devuelve 404
        self.assertIn(response.status_code, [200, 404])

    def test_editar_meta_ahorro_get_and_post(self):
        meta = MetaAhorro.objects.create(
            nombre='Meta Editar',
            monto_objetivo=Decimal('1000.00'),
            fecha_inicio=date.today(),
            fecha_limite=date.today() + timedelta(days=60),
            frecuencia_aporte='mensual',
            id_usuario=self.usuario,
            id_cuenta=self.cuenta
        )

        # GET
        response = self.client.get(reverse('gestion_financiera_basica:editar_meta_ahorro', args=[meta.id]))
        self.assertEqual(response.status_code, 200)

        # POST edición válida
        data = {
            'nombre': 'Meta Modificada',
            'descripcion': 'Descripcion actualizada',
            'monto_objetivo': '1200.00',
            'fecha_inicio': date.today().isoformat(),
            'fecha_limite': (date.today() + timedelta(days=90)).isoformat(),
            'frecuencia_aporte': 'mensual',
            'id_cuenta': self.cuenta.id
        }
        response = self.client.post(reverse('gestion_financiera_basica:editar_meta_ahorro', args=[meta.id]), data)
        self.assertRedirects(response, reverse('gestion_financiera_basica:savings_goals'))

        meta.refresh_from_db()
        self.assertEqual(meta.nombre, 'Meta Modificada')
        self.assertEqual(meta.monto_objetivo, Decimal('1200.00'))

    def test_editar_meta_ahorro_post_invalid(self):
        meta = MetaAhorro.objects.create(
            nombre='Meta Editar Inválida',
            monto_objetivo=Decimal('1000.00'),
            fecha_inicio=date.today(),
            fecha_limite=date.today() + timedelta(days=60),
            frecuencia_aporte='mensual',
            id_usuario=self.usuario,
            id_cuenta=self.cuenta
        )
        data = {
            'nombre': '',  # Inválido
            'monto_objetivo': '1200.00',
            'fecha_inicio': date.today().isoformat(),
            'fecha_limite': (date.today() + timedelta(days=90)).isoformat(),
            'frecuencia_aporte': 'semanal',
            'id_cuenta': self.cuenta.id
        }
        response = self.client.post(reverse('gestion_financiera_basica:editar_meta_ahorro', args=[meta.id]), data)
        self.assertEqual(response.status_code, 200)

    def test_eliminar_meta_ahorro_post(self):
        meta = MetaAhorro.objects.create(
            nombre='Meta Eliminar',
            monto_objetivo=Decimal('1000.00'),
            fecha_inicio=date.today(),
            fecha_limite=date.today() + timedelta(days=60),
            frecuencia_aporte='mensual',
            id_usuario=self.usuario,
            id_cuenta=self.cuenta
        )
        # GET redirecciona
        response = self.client.get(reverse('gestion_financiera_basica:eliminar_meta_ahorro', args=[meta.id]))
        self.assertRedirects(response, reverse('gestion_financiera_basica:savings_goals'))

        # POST elimina
        response = self.client.post(reverse('gestion_financiera_basica:eliminar_meta_ahorro', args=[meta.id]))
        self.assertRedirects(response, reverse('gestion_financiera_basica:savings_goals'))
        self.assertFalse(MetaAhorro.objects.filter(id=meta.id).exists())

    def test_detalle_meta_ahorro(self):
        meta = MetaAhorro.objects.create(
            nombre='Meta Detalle',
            monto_objetivo=Decimal('1000.00'),
            fecha_inicio=date.today(),
            fecha_limite=date.today() + timedelta(days=60),
            frecuencia_aporte='mensual',
            id_usuario=self.usuario,
            id_cuenta=self.cuenta
        )
        aporte = AporteMetaAhorro.objects.create(
            id_meta_ahorro=meta,
            monto=Decimal('150.00'),
            descripcion='Detalle aporte',
            id_usuario=self.usuario
        )
        response = self.client.get(reverse('gestion_financiera_basica:detalle_meta_ahorro', args=[meta.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['meta'].id, meta.id)
        self.assertIn(aporte, list(response.context['aportes']))
