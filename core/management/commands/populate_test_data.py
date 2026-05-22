from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import secrets
crypto_random = secrets.SystemRandom()

from usuarios.models import Usuario
from cuentas.models import Cuenta, SubCuenta, Moneda
from gestion_financiera_basica.models import Movimiento, MetaAhorro, AporteMetaAhorro
from educacion_financiera.models import CursoExterno


class Command(BaseCommand):
    help = 'Rellena la base de datos con datos de prueba para subcuentas, transacciones y cursos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--correo',
            type=str,
            help='Correo del usuario para asociar los datos (si no existe, se crea)',
        )
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Limpia los datos existentes antes de crear nuevos',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🚀 Iniciando población de datos de prueba...'))
        
        # Obtener o crear usuario
        correo = options.get('correo') or 'demo@test.com'
        usuario = self.get_or_create_usuario(correo)
        
        # Limpiar si se especifica
        if options.get('limpiar'):
            self.limpiar_datos(usuario)
        
        # Crear cuenta principal
        cuenta = self.crear_cuenta_principal(usuario)
        
        # Crear subcuentas
        self.crear_subcuentas(usuario, cuenta)
        
        # Crear transacciones/movimientos
        self.crear_movimientos(usuario, cuenta)
        
        # Crear metas de ahorro
        self.crear_metas_ahorro(usuario, cuenta)
        
        # Crear cursos externos
        self.crear_cursos()
        
        self.stdout.write(self.style.SUCCESS('✅ Datos de prueba creados exitosamente!'))

    def get_or_create_usuario(self, correo):
        """Obtiene o crea un usuario de prueba"""
        try:
            usuario = Usuario.objects.get(correo=correo)
            self.stdout.write(f'  📧 Usuario encontrado: {correo}')
        except Usuario.DoesNotExist:
            # Primero crear moneda si no existe
            moneda = self.crear_moneda()
            
            usuario = Usuario.objects.create_user(
                correo=correo,
                password='demo1234',
                nombres='Usuario',
                apellido_paterno='Demo',
                apellido_materno='Prueba',
                documento_identidad='12345678',
                telefono=999999999,
                id_moneda=moneda,
            )
            self.stdout.write(self.style.SUCCESS(f'  📧 Usuario creado: {correo} (contraseña: demo1234)'))
        return usuario

    def limpiar_datos(self, usuario):
        """Limpia datos existentes del usuario"""
        self.stdout.write('  🗑️ Limpiando datos existentes...')
        Movimiento.objects.filter(id_usuario=usuario).delete()
        AporteMetaAhorro.objects.filter(id_usuario=usuario).delete()
        MetaAhorro.objects.filter(id_usuario=usuario).delete()
        SubCuenta.objects.filter(propietario=usuario).delete()
        Cuenta.objects.filter(id_usuario=usuario).delete()

    def crear_moneda(self):
        """Crea moneda por defecto si no existe"""
        moneda, created = Moneda.objects.get_or_create(
            codigo='PEN', 
            defaults={'nombre': 'Sol Peruano', 'simbolo': 'S/'}
        )
        if created:
            Moneda.objects.get_or_create(codigo='USD', defaults={'nombre': 'Dólar Americano', 'simbolo': '$'})
            self.stdout.write('  💰 Monedas creadas')
        return moneda

    def crear_cuenta_principal(self, usuario):
        """Crea cuenta principal para el usuario"""
        cuenta, created = Cuenta.objects.get_or_create(
            id_usuario=usuario,
            defaults={
                'nombre': 'Cuenta Principal',
                'descripcion': 'Cuenta principal para gestión financiera',
                'saldo_cuenta': Decimal('15000.00')
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  🏦 Cuenta principal creada'))
        else:
            self.stdout.write('  🏦 Cuenta principal existente')
        return cuenta

    def crear_subcuentas(self, usuario, cuenta):
        """Crea subcuentas de prueba"""
        self.stdout.write('  📁 Creando subcuentas...')
        
        subcuentas_data = [
            # Subcuentas de negocio
            {
                'nombre': 'Tienda Online - Shopify',
                'descripcion': 'Ingresos de mi tienda de dropshipping',
                'saldo': Decimal('3500.00'),
                'tipo': 'tienda_online',
                'es_negocio': True,
                'meta_objetivo': Decimal('10000.00'),
            },
            {
                'nombre': 'Servicios de Consultoría',
                'descripcion': 'Ingresos por asesorías financieras',
                'saldo': Decimal('2800.00'),
                'tipo': 'consultoria',
                'es_negocio': True,
            },
            {
                'nombre': 'Freelance Desarrollo Web',
                'descripcion': 'Proyectos de desarrollo freelance',
                'saldo': Decimal('1500.00'),
                'tipo': 'freelance',
                'es_negocio': True,
            },
            {
                'nombre': 'Alquiler Departamento',
                'descripcion': 'Ingresos por alquiler mensual',
                'saldo': Decimal('4200.00'),
                'tipo': 'alquiler_propiedades',
                'es_negocio': True,
                'meta_objetivo': Decimal('50000.00'),
            },
            
            # Subcuentas personales
            {
                'nombre': 'Fondo de Emergencia',
                'descripcion': 'Para imprevistos y emergencias',
                'saldo': Decimal('5000.00'),
                'tipo': 'emergencia',
                'meta_objetivo': Decimal('10000.00'),
            },
            {
                'nombre': 'Ahorro para Viaje',
                'descripcion': 'Vacaciones en Europa 2026',
                'saldo': Decimal('2500.00'),
                'tipo': 'viajes',
                'meta_objetivo': Decimal('8000.00'),
                'fecha_meta': timezone.now().date() + timedelta(days=365),
            },
            {
                'nombre': 'Inversiones',
                'descripcion': 'Capital para invertir en bolsa',
                'saldo': Decimal('3000.00'),
                'tipo': 'inversion',
            },
            {
                'nombre': 'Gastos del Hogar',
                'descripcion': 'Servicios, alquiler, mantenimiento',
                'saldo': Decimal('1200.00'),
                'tipo': 'gastos_fijos',
            },
            {
                'nombre': 'Educación y Cursos',
                'descripcion': 'Cursos online y libros',
                'saldo': Decimal('800.00'),
                'tipo': 'educacion',
                'meta_objetivo': Decimal('2000.00'),
            },
            {
                'nombre': 'Entretenimiento',
                'descripcion': 'Salidas, streaming, hobbies',
                'saldo': Decimal('450.00'),
                'tipo': 'entretenimiento',
            },
        ]
        
        for data in subcuentas_data:
            SubCuenta.objects.get_or_create(
                nombre=data['nombre'],
                propietario=usuario,
                defaults={
                    'descripcion': data.get('descripcion', ''),
                    'saldo': data.get('saldo', Decimal('0')),
                    'tipo': data.get('tipo', 'otros'),
                    'es_negocio': data.get('es_negocio', False),
                    'meta_objetivo': data.get('meta_objetivo'),
                    'fecha_meta': data.get('fecha_meta'),
                    'id_cuenta': cuenta,
                    'activa': True,
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'    ✅ {len(subcuentas_data)} subcuentas creadas'))

    def crear_movimientos(self, usuario, cuenta):
        """Crea movimientos/transacciones de prueba"""
        self.stdout.write('  💳 Creando transacciones...')
        
        # Categorías de gastos con montos típicos
        gastos = [
            ('alimentacion', 'Supermercado Plaza Vea', 150, 350),
            ('alimentacion', 'Almuerzo restaurante', 25, 60),
            ('transporte', 'Gasolina', 80, 150),
            ('transporte', 'Uber/Taxi', 15, 45),
            ('entretenimiento', 'Netflix y Spotify', 35, 50),
            ('entretenimiento', 'Cine con amigos', 40, 80),
            ('salud', 'Farmacia', 30, 100),
            ('salud', 'Gimnasio mensual', 100, 150),
            ('educacion', 'Curso Udemy', 30, 80),
            ('compras', 'Ropa y accesorios', 100, 300),
            ('servicios', 'Luz y agua', 80, 150),
            ('servicios', 'Internet y teléfono', 100, 180),
            ('vivienda', 'Alquiler mensual', 1200, 1500),
            ('otros', 'Gastos varios', 20, 100),
        ]
        
        # Categorías de ingresos
        ingresos = [
            ('salario', 'Sueldo mensual', 3500, 5000),
            ('freelance', 'Proyecto web', 500, 2000),
            ('negocio', 'Ventas tienda online', 300, 1500),
            ('inversion', 'Dividendos', 50, 300),
            ('regalo', 'Cumpleaños', 100, 500),
            ('otros', 'Ingreso extra', 50, 200),
        ]
        
        movimientos_creados = 0
        hoy = timezone.now()
        
        # Crear movimientos de los últimos 3 meses
        for dias_atras in range(90):
            fecha = hoy - timedelta(days=dias_atras)
            
            # 2-4 gastos por día
            num_gastos = crypto_random.randint(1, 4)
            for _ in range(num_gastos):
                categoria, nombre_base, min_monto, max_monto = crypto_random.choice(gastos)
                monto = Decimal(str(crypto_random.randint(min_monto, max_monto)))
                
                Movimiento.objects.create(
                    nombre=nombre_base,
                    tipo='egreso',
                    categoria=categoria,
                    monto=monto,
                    fecha_movimiento=fecha,
                    descripcion=f'{nombre_base} - {fecha.strftime("%d/%m")}',
                    id_cuenta=cuenta,
                    id_usuario=usuario,
                )
                movimientos_creados += 1
            
            # 0-2 ingresos por día (menos frecuentes)
            if crypto_random.random() < 0.3:  # 30% de probabilidad
                categoria, nombre_base, min_monto, max_monto = crypto_random.choice(ingresos)
                monto = Decimal(str(crypto_random.randint(min_monto, max_monto)))
                
                Movimiento.objects.create(
                    nombre=nombre_base,
                    tipo='ingreso',
                    categoria=categoria,
                    monto=monto,
                    fecha_movimiento=fecha,
                    descripcion=f'{nombre_base} - {fecha.strftime("%d/%m")}',
                    id_cuenta=cuenta,
                    id_usuario=usuario,
                )
                movimientos_creados += 1
        
        self.stdout.write(self.style.SUCCESS(f'    ✅ {movimientos_creados} transacciones creadas'))

    def crear_metas_ahorro(self, usuario, cuenta):
        """Crea metas de ahorro de prueba"""
        self.stdout.write('  🎯 Creando metas de ahorro...')
        
        metas_data = [
            {
                'nombre': 'Viaje a Europa',
                'descripcion': 'Vacaciones soñadas en Europa',
                'monto_objetivo': Decimal('8000.00'),
                'frecuencia_aporte': 'mensual',
                'dias_duracion': 365,
            },
            {
                'nombre': 'Fondo de Emergencia',
                'descripcion': '6 meses de gastos cubiertos',
                'monto_objetivo': Decimal('15000.00'),
                'frecuencia_aporte': 'quincenal',
                'dias_duracion': 548,
            },
            {
                'nombre': 'Nueva Laptop',
                'descripcion': 'MacBook Pro para trabajo',
                'monto_objetivo': Decimal('5000.00'),
                'frecuencia_aporte': 'mensual',
                'dias_duracion': 180,
            },
            {
                'nombre': 'Curso de Inversiones',
                'descripcion': 'Masterclass de trading',
                'monto_objetivo': Decimal('1500.00'),
                'frecuencia_aporte': 'semanal',
                'dias_duracion': 90,
            },
        ]
        
        for data in metas_data:
            hoy = timezone.now().date()
            meta, created = MetaAhorro.objects.get_or_create(
                nombre=data['nombre'],
                id_usuario=usuario,
                defaults={
                    'descripcion': data['descripcion'],
                    'monto_objetivo': data['monto_objetivo'],
                    'frecuencia_aporte': data['frecuencia_aporte'],
                    'fecha_inicio': hoy - timedelta(days=30),
                    'fecha_limite': hoy + timedelta(days=data['dias_duracion']),
                    'id_cuenta': cuenta,
                }
            )
            
            if created:
                # Crear algunos aportes para la meta
                num_aportes = crypto_random.randint(3, 8)
                for i in range(num_aportes):
                    monto_aporte = data['monto_objetivo'] / Decimal(str(crypto_random.randint(10, 20)))
                    AporteMetaAhorro.objects.create(
                        id_meta_ahorro=meta,
                        monto=monto_aporte.quantize(Decimal('0.01')),
                        descripcion=f'Aporte #{i+1}',
                        id_usuario=usuario,
                    )
        
        self.stdout.write(self.style.SUCCESS(f'    ✅ {len(metas_data)} metas de ahorro creadas'))

    def crear_cursos(self):
        """Crea cursos externos de prueba"""
        self.stdout.write('  📚 Creando cursos externos...')
        
        cursos_data = [
            # YouTube - Español
            {
                'titulo': 'Finanzas Personales desde Cero',
                'descripcion': 'Aprende los fundamentos de las finanzas personales: presupuestos, ahorro, inversión y más. Ideal para principiantes.',
                'nivel': 'basico',
                'plataforma': 'youtube',
                'url_externa': 'https://www.youtube.com/watch?v=ejemplo1',
                'imagen_url': 'https://img.youtube.com/vi/ejemplo1/maxresdefault.jpg',
                'duracion_estimada': '2 horas (12 videos)',
                'instructor': 'Juan Ramón Rallo',
                'idioma': 'Español',
                'gratis': True,
                'orden': 1,
            },
            {
                'titulo': 'Cómo Invertir en la Bolsa de Valores',
                'descripcion': 'Guía completa para comenzar a invertir en acciones. Análisis técnico y fundamental explicado de forma sencilla.',
                'nivel': 'intermedio',
                'plataforma': 'youtube',
                'url_externa': 'https://www.youtube.com/watch?v=ejemplo2',
                'imagen_url': 'https://img.youtube.com/vi/ejemplo2/maxresdefault.jpg',
                'duracion_estimada': '4 horas (20 videos)',
                'instructor': 'Inversiones con Sentido',
                'idioma': 'Español',
                'gratis': True,
                'orden': 2,
            },
            {
                'titulo': 'Criptomonedas y Blockchain Explicado',
                'descripcion': 'Entiende cómo funcionan Bitcoin, Ethereum y las principales criptomonedas. Incluye análisis de riesgos.',
                'nivel': 'intermedio',
                'plataforma': 'youtube',
                'url_externa': 'https://www.youtube.com/watch?v=ejemplo3',
                'imagen_url': 'https://img.youtube.com/vi/ejemplo3/maxresdefault.jpg',
                'duracion_estimada': '3 horas (15 videos)',
                'instructor': 'Crypto España',
                'idioma': 'Español',
                'gratis': True,
                'orden': 3,
            },
            
            # Udemy
            {
                'titulo': 'Curso Completo de Trading',
                'descripcion': 'Domina el trading desde cero hasta nivel avanzado. Incluye estrategias probadas y gestión del riesgo.',
                'nivel': 'avanzado',
                'plataforma': 'udemy',
                'url_externa': 'https://www.udemy.com/course/trading-completo',
                'imagen_url': 'https://img-c.udemycdn.com/course/480x270/trading.jpg',
                'duracion_estimada': '25 horas',
                'instructor': 'Carlos Martínez',
                'idioma': 'Español',
                'gratis': False,
                'orden': 4,
            },
            {
                'titulo': 'Excel para Finanzas',
                'descripcion': 'Aprende a usar Excel como un profesional de las finanzas. Fórmulas, tablas dinámicas y dashboards.',
                'nivel': 'intermedio',
                'plataforma': 'udemy',
                'url_externa': 'https://www.udemy.com/course/excel-finanzas',
                'imagen_url': 'https://img-c.udemycdn.com/course/480x270/excel.jpg',
                'duracion_estimada': '15 horas',
                'instructor': 'Ana García',
                'idioma': 'Español',
                'gratis': False,
                'orden': 5,
            },
            
            # Coursera
            {
                'titulo': 'Fundamentos de Finanzas Empresariales',
                'descripcion': 'Curso de la Universidad de Pennsylvania sobre finanzas corporativas y toma de decisiones financieras.',
                'nivel': 'intermedio',
                'plataforma': 'coursera',
                'url_externa': 'https://www.coursera.org/learn/finanzas-empresariales',
                'imagen_url': 'https://d3njjcbhbojbot.cloudfront.net/finanzas.jpg',
                'duracion_estimada': '20 horas (4 semanas)',
                'instructor': 'Wharton School',
                'idioma': 'Español',
                'gratis': True,
                'orden': 6,
            },
            {
                'titulo': 'Mercados Financieros',
                'descripcion': 'Curso del premio Nobel Robert Shiller sobre mercados financieros, bonos, acciones y derivados.',
                'nivel': 'avanzado',
                'plataforma': 'coursera',
                'url_externa': 'https://www.coursera.org/learn/financial-markets',
                'imagen_url': 'https://d3njjcbhbojbot.cloudfront.net/markets.jpg',
                'duracion_estimada': '33 horas (7 semanas)',
                'instructor': 'Robert Shiller - Yale',
                'idioma': 'Inglés',
                'gratis': True,
                'orden': 7,
            },
            
            # Khan Academy
            {
                'titulo': 'Economía y Finanzas',
                'descripcion': 'Serie completa sobre conceptos económicos y financieros básicos. Perfecto para estudiantes.',
                'nivel': 'basico',
                'plataforma': 'khan_academy',
                'url_externa': 'https://es.khanacademy.org/economics-finance-domain',
                'imagen_url': 'https://cdn.kastatic.org/economics.png',
                'duracion_estimada': '10+ horas',
                'instructor': 'Khan Academy',
                'idioma': 'Español',
                'gratis': True,
                'orden': 8,
            },
            
            # Platzi
            {
                'titulo': 'Curso de Inversión en Bolsa',
                'descripcion': 'Aprende a invertir en la bolsa de valores con estrategias prácticas y análisis de casos reales.',
                'nivel': 'intermedio',
                'plataforma': 'platzi',
                'url_externa': 'https://platzi.com/cursos/inversion-bolsa',
                'imagen_url': 'https://static.platzi.com/bolsa.png',
                'duracion_estimada': '4 horas',
                'instructor': 'Platzi',
                'idioma': 'Español',
                'gratis': False,
                'orden': 9,
            },
            {
                'titulo': 'Finanzas para Emprendedores',
                'descripcion': 'Todo lo que necesitas saber sobre finanzas para manejar tu negocio exitosamente.',
                'nivel': 'basico',
                'plataforma': 'platzi',
                'url_externa': 'https://platzi.com/cursos/finanzas-emprendedores',
                'imagen_url': 'https://static.platzi.com/emprendedores.png',
                'duracion_estimada': '3 horas',
                'instructor': 'Platzi',
                'idioma': 'Español',
                'gratis': False,
                'orden': 10,
            },
            
            # Más cursos de YouTube
            {
                'titulo': 'Cómo Ahorrar Dinero - Métodos Comprobados',
                'descripcion': 'Técnicas y estrategias para ahorrar dinero efectivamente. Incluye el método del sobre y el 50/30/20.',
                'nivel': 'basico',
                'plataforma': 'youtube',
                'url_externa': 'https://www.youtube.com/watch?v=ejemplo4',
                'imagen_url': 'https://img.youtube.com/vi/ejemplo4/maxresdefault.jpg',
                'duracion_estimada': '1 hora (6 videos)',
                'instructor': 'Educación Financiera',
                'idioma': 'Español',
                'gratis': True,
                'orden': 11,
            },
            {
                'titulo': 'Libertad Financiera - El Camino',
                'descripcion': 'Aprende los pasos para alcanzar la independencia financiera y retirarte temprano.',
                'nivel': 'intermedio',
                'plataforma': 'youtube',
                'url_externa': 'https://www.youtube.com/watch?v=ejemplo5',
                'imagen_url': 'https://img.youtube.com/vi/ejemplo5/maxresdefault.jpg',
                'duracion_estimada': '5 horas (25 videos)',
                'instructor': 'Dinero y Libertad',
                'idioma': 'Español',
                'gratis': True,
                'orden': 12,
            },
        ]
        
        cursos_creados = 0
        for data in cursos_data:
            _, created = CursoExterno.objects.get_or_create(
                titulo=data['titulo'],
                defaults=data
            )
            if created:
                cursos_creados += 1
        
        self.stdout.write(self.style.SUCCESS(f'    ✅ {cursos_creados} cursos creados'))
