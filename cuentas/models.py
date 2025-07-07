from django.db import models
from django.contrib.auth.models import AbstractUser

class Moneda(models.Model):
    codigo = models.CharField(max_length=5)
    nombre = models.CharField(max_length=50)
    simbolo = models.CharField(max_length=5)

    def __str__(self):
        return self.nombre


class Cuenta(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=300)
    saldo_cuenta = models.DecimalField(max_digits=15, decimal_places=2)
    id_usuario = models.ForeignKey("usuarios.Usuario", on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre

    def saldo_total_subcuentas(self):
        """Calcula el saldo total de todas las subcuentas"""
        total = self.subcuentas.aggregate(models.Sum('saldo'))['saldo__sum']
        return total if total is not None else 0

    def saldo_disponible(self):
        """Calcula el saldo disponible (saldo_cuenta - saldo en subcuentas)"""
        return self.saldo_cuenta - self.saldo_total_subcuentas()


class SubCuenta(models.Model):
    TIPOS_SUBCUENTA = (
        # Negocios y fuentes de ingreso
        ('tienda_online', 'Tienda Online'),
        ('tienda_fisica', 'Tienda Física'),
        ('servicios_profesionales', 'Servicios Profesionales'),
        ('freelance', 'Trabajo Freelance'),
        ('negocio_propio', 'Negocio Propio'),
        ('ingresos_pasivos', 'Ingresos Pasivos'),
        ('ventas_productos', 'Ventas de Productos'),
        ('consultoria', 'Consultoría'),
        ('alquiler_propiedades', 'Alquiler de Propiedades'),
        
        # Gestión personal tradicional
        ('ahorro_meta', 'Ahorro para Meta'),
        ('emergencia', 'Fondo de Emergencia'),
        ('inversion', 'Inversiones'),
        ('gastos_fijos', 'Gastos Fijos'),
        ('gastos_variables', 'Gastos Variables'),
        ('entretenimiento', 'Entretenimiento'),
        ('viajes', 'Viajes y Vacaciones'),
        ('educacion', 'Educación y Cursos'),
        ('salud', 'Salud y Bienestar'),
        ('familia', 'Gastos Familiares'),
        ('otros', 'Otros'),
    )

    COLORES_TIPO = {
        # Colores para negocios (tonos más profesionales)
        'tienda_online': '#1E40AF',      # Azul profesional
        'tienda_fisica': '#059669',       # Verde negocio
        'servicios_profesionales': '#7C3AED',  # Púrpura profesional
        'freelance': '#DC2626',          # Rojo energético
        'negocio_propio': '#EA580C',     # Naranja empresarial
        'ingresos_pasivos': '#10B981',   # Verde dinero
        'ventas_productos': '#2563EB',   # Azul comercial
        'consultoria': '#8B5CF6',       # Púrpura consultor
        'alquiler_propiedades': '#059669', # Verde inmobiliario
        
        # Colores para gestión personal
        'ahorro_meta': '#00b894',
        'emergencia': '#ff6b6b',
        'inversion': '#74b9ff',
        'gastos_fijos': '#636e72',
        'gastos_variables': '#a29bfe',
        'entretenimiento': '#fd79a8',
        'viajes': '#6c5ce7',
        'educacion': '#fdcb6e',
        'salud': '#55efc4',
        'familia': '#e17055',
        'otros': '#636e72',
    }

    nombre = models.CharField(max_length=50, help_text="Nombre descriptivo de la subcuenta")
    descripcion = models.CharField(max_length=300, blank=True, null=True, help_text="Propósito y objetivo de esta subcuenta")
    saldo = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Saldo actual en la subcuenta")
    tipo = models.CharField(max_length=30, choices=TIPOS_SUBCUENTA, default='otros', help_text="Categoría de la subcuenta")
    color = models.CharField(max_length=7, default='#3B82F6', help_text="Color para identificación visual")
    activa = models.BooleanField(default=True, help_text="Indica si la subcuenta está activa")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    # Campos para subcuentas de negocio
    es_negocio = models.BooleanField(default=False, help_text="Marca si es una subcuenta de negocio")
    meta_objetivo = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Meta de ahorro u objetivo financiero")
    fecha_meta = models.DateField(null=True, blank=True, help_text="Fecha límite para alcanzar la meta")
    
    # Relación con cuenta principal (OPCIONAL para subcuentas independientes)
    id_cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name='subcuentas', 
                                  null=True, blank=True, help_text="Cuenta principal (opcional para subcuentas independientes)")
    
    # Para subcuentas independientes se REQUIERE relación directa con usuario
    propietario = models.ForeignKey("usuarios.Usuario", on_delete=models.CASCADE, null=True, blank=True, 
                                   help_text="Propietario directo (requerido para subcuentas independientes)")

    def __str__(self):
        tipo_display = "💼" if self.es_negocio else "💰"
        return f"{tipo_display} {self.nombre} - ${self.saldo}"

    def save(self, *args, **kwargs):
        # Validar que tenga o cuenta principal o propietario directo
        if not self.id_cuenta and not self.propietario:
            raise ValueError("Una subcuenta debe tener una cuenta principal o un propietario directo")
        
        # Si tiene ambos, dar prioridad a la cuenta principal
        if self.id_cuenta and self.propietario:
            if self.id_cuenta.id_usuario != self.propietario:
                raise ValueError("El propietario debe coincidir con el usuario de la cuenta principal")
        
        # Asignar color automáticamente según el tipo si no se ha establecido uno personalizado
        if self.color == '#3B82F6':  # Color por defecto
            self.color = self.COLORES_TIPO.get(self.tipo, '#3B82F6')
        
        # Marcar automáticamente como negocio según el tipo
        tipos_negocio = ['tienda_online', 'tienda_fisica', 'servicios_profesionales', 
                        'freelance', 'negocio_propio', 'ingresos_pasivos', 
                        'ventas_productos', 'consultoria', 'alquiler_propiedades']
        if self.tipo in tipos_negocio:
            self.es_negocio = True
        
        super().save(*args, **kwargs)

    def get_color_tipo(self):
        """Obtiene el color correspondiente al tipo de subcuenta"""
        return self.COLORES_TIPO.get(self.tipo, '#3B82F6')
    
    def get_usuario(self):
        """Obtiene el usuario propietario de la subcuenta"""
        # Prioridad: propietario directo, luego usuario de la cuenta
        if self.propietario:
            return self.propietario
        elif self.id_cuenta:
            return self.id_cuenta.id_usuario
        return None
    
    def es_independiente(self):
        """Determina si la subcuenta es independiente (no vinculada a cuenta principal)"""
        return self.propietario is not None and self.id_cuenta is None
    
    def puede_transferir_a_cuenta_principal(self):
        """Determina si puede transferir dinero a una cuenta principal"""
        return self.id_cuenta is not None or (self.propietario and self.propietario.cuenta_set.exists())
    
    def progreso_meta(self):
        """Calcula el progreso hacia la meta objetivo"""
        if not self.meta_objetivo or self.meta_objetivo <= 0:
            return 0
        progreso = (float(self.saldo) / float(self.meta_objetivo)) * 100
        return min(progreso, 100)  # Máximo 100%
    
    def dias_restantes_meta(self):
        """Calcula los días restantes para alcanzar la fecha meta"""
        if not self.fecha_meta:
            return None
        from django.utils import timezone
        hoy = timezone.now().date()
        if self.fecha_meta <= hoy:
            return 0
        return (self.fecha_meta - hoy).days
    
    def es_meta_alcanzada(self):
        """Verifica si la meta ha sido alcanzada"""
        if not self.meta_objetivo:
            return False
        return self.saldo >= self.meta_objetivo
    
    def get_tipo_display_emoji(self):
        """Devuelve el tipo con emoji correspondiente"""
        emoji_map = {
            'tienda_online': '🛍️ Tienda Online',
            'tienda_fisica': '🏪 Tienda Física', 
            'servicios_profesionales': '💼 Servicios Profesionales',
            'freelance': '💻 Trabajo Freelance',
            'negocio_propio': '🏢 Negocio Propio',
            'ingresos_pasivos': '💸 Ingresos Pasivos',
            'ventas_productos': '📦 Ventas de Productos',
            'consultoria': '🎯 Consultoría',
            'alquiler_propiedades': '🏠 Alquiler de Propiedades',
            'ahorro_meta': '🎯 Ahorro para Meta',
            'emergencia': '🚨 Fondo de Emergencia',
            'inversion': '📈 Inversiones',
            'gastos_fijos': '🔒 Gastos Fijos',
            'gastos_variables': '📊 Gastos Variables',
            'entretenimiento': '🎭 Entretenimiento',
            'viajes': '✈️ Viajes y Vacaciones',
            'educacion': '📚 Educación y Cursos',
            'salud': '🏥 Salud y Bienestar',
            'familia': '👨‍👩‍👧‍👦 Gastos Familiares',
            'otros': '📁 Otros',
        }
        return emoji_map.get(self.tipo, f"📁 {self.get_tipo_display()}")

    class Meta:
        ordering = ['-fecha_creacion']


class TransferenciaSubCuenta(models.Model):
    """Modelo para registrar transferencias entre subcuentas"""
    subcuenta_origen = models.ForeignKey(SubCuenta, on_delete=models.CASCADE, related_name='transferencias_enviadas')
    subcuenta_destino = models.ForeignKey(SubCuenta, on_delete=models.CASCADE, related_name='transferencias_recibidas')
    monto = models.DecimalField(max_digits=15, decimal_places=2)
    descripcion = models.CharField(max_length=300, blank=True, null=True)
    fecha_transferencia = models.DateTimeField(auto_now_add=True)
    id_usuario = models.ForeignKey("usuarios.Usuario", on_delete=models.CASCADE)

    def __str__(self):
        return f"${self.monto} de {self.subcuenta_origen.nombre} a {self.subcuenta_destino.nombre}"

    class Meta:
        ordering = ['-fecha_transferencia']


class TransferenciaCuentaPrincipal(models.Model):
    """Modelo para registrar transferencias desde subcuentas hacia cuenta principal"""
    TIPO_TRANSFERENCIA = (
        ('deposito', 'Depósito hacia cuenta principal'),
        ('retiro', 'Retiro hacia subcuenta'),
    )
    
    subcuenta = models.ForeignKey(SubCuenta, on_delete=models.CASCADE, related_name='transferencias_cuenta_principal')
    cuenta_destino = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name='transferencias_desde_subcuentas')
    monto = models.DecimalField(max_digits=15, decimal_places=2)
    tipo = models.CharField(max_length=20, choices=TIPO_TRANSFERENCIA, default='deposito')
    descripcion = models.CharField(max_length=300, blank=True, null=True)
    fecha_transferencia = models.DateTimeField(auto_now_add=True)
    id_usuario = models.ForeignKey("usuarios.Usuario", on_delete=models.CASCADE)

    def __str__(self):
        direccion = "hacia" if self.tipo == 'deposito' else "desde"
        return f"${self.monto} {direccion} cuenta principal - {self.subcuenta.nombre}"

    class Meta:
        ordering = ['-fecha_transferencia']

# Create your models here.
