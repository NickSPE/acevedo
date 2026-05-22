from django.db import models
from django.db.models import Sum

# Create your models here.

class MetaAhorro(models.Model):
    FRECUENCIAS = (
        ('diaria', 'Diaria'),
        ('semanal', 'Semanal'),
        ('quincenal', 'Quincenal'),
        ('mensual', 'Mensual'),
        ('bimestral', 'Bimestral'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('anual', 'Anual'),
    )

    fecha_inicio = models.DateField()
    fecha_limite = models.DateField()
    monto_objetivo = models.DecimalField(max_digits=15, decimal_places=2)
    frecuencia_aporte = models.CharField(max_length=20, choices=FRECUENCIAS, default='mensual')
    descripcion = models.CharField(max_length=255)
    nombre = models.CharField(max_length=50)
    id_usuario = models.ForeignKey("usuarios.Usuario", on_delete=models.CASCADE)
    id_cuenta = models.ForeignKey("cuentas.Cuenta", on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre

    def monto_ahorrado(self):
        """Calcula el monto total ahorrado hasta la fecha"""
        total = self.aportes.aggregate(Sum('monto'))['monto__sum']
        return float(total) if total is not None else 0.0

    def porcentaje_progreso(self):
        """Calcula el porcentaje de progreso hacia la meta"""
        if self.monto_objetivo <= 0:
            return 0.0
        monto_actual = self.monto_ahorrado()
        objetivo = float(self.monto_objetivo)
        return min((monto_actual / objetivo) * 100, 100.0)

    def falta_por_ahorrar(self):
        """Calcula cuánto falta para alcanzar la meta"""
        falta = float(self.monto_objetivo) - self.monto_ahorrado()
        return max(falta, 0.0)

    def meta_alcanzada(self):
        """Verifica si la meta ya fue alcanzada"""
        return self.monto_ahorrado() >= float(self.monto_objetivo)


class MoldeAhorro(models.Model):
    nombre = models.CharField(max_length=50)
    porcentaje_ahorro = models.DecimalField(max_digits=3, decimal_places=2)
    id_meta_ahorro = models.ForeignKey(MetaAhorro, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre


class AporteMetaAhorro(models.Model):
    """Modelo para registrar los aportes individuales a una meta de ahorro"""
    id_meta_ahorro = models.ForeignKey(MetaAhorro, on_delete=models.CASCADE, related_name='aportes')
    monto = models.DecimalField(max_digits=15, decimal_places=2)
    fecha_aporte = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField(blank=True, default='')
    id_usuario = models.ForeignKey("usuarios.Usuario", on_delete=models.CASCADE)

    def __str__(self):
        return f"Aporte ${self.monto} a {self.id_meta_ahorro.nombre}"

    class Meta:
        ordering = ['-fecha_aporte']


class Movimiento(models.Model):
    TIPOS_MOVIMIENTO = (
        ('ingreso', 'Ingreso'),
        ('egreso', 'Egreso'),
    )
    
    CATEGORIAS_GASTOS = (
        ('alimentacion', '🍽️ Alimentación'),
        ('transporte', '🚗 Transporte'),
        ('entretenimiento', '🎬 Entretenimiento'),
        ('salud', '🏥 Salud'),
        ('educacion', '📚 Educación'),
        ('compras', '🛒 Compras'),
        ('servicios', '🔧 Servicios'),
        ('vivienda', '🏠 Vivienda'),
        ('trabajo', '💼 Trabajo'),
        ('ahorros', '🎯 Ahorros/Metas'),
        ('otros', '📦 Otros'),
    )

    CATEGORIAS_INGRESOS = (
        ('salario', '💰 Salario'),
        ('freelance', '💻 Freelance'),
        ('negocio', '🏢 Negocio'),
        ('inversion', '📈 Inversión'),
        ('regalo', '🎁 Regalo'),
        ('otros', '📦 Otros'),
    )

    nombre = models.CharField(max_length=50)
    tipo = models.CharField(max_length=25, choices=TIPOS_MOVIMIENTO)
    categoria = models.CharField(max_length=25, blank=True, default='', help_text="Categoría del movimiento")
    monto = models.DecimalField(max_digits=15, decimal_places=2)
    fecha_movimiento = models.DateTimeField()
    descripcion = models.TextField(blank=True, default='')
    id_cuenta = models.ForeignKey("cuentas.Cuenta", on_delete=models.CASCADE)
    id_usuario = models.ForeignKey("usuarios.Usuario", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.tipo} - {self.monto}"

    def get_categoria_display_emoji(self):
        """Retorna la categoría con emoji"""
        if self.tipo == 'egreso':
            for cat_key, cat_display in self.CATEGORIAS_GASTOS:
                if cat_key == self.categoria:
                    return cat_display
        elif self.tipo == 'ingreso':
            for cat_key, cat_display in self.CATEGORIAS_INGRESOS:
                if cat_key == self.categoria:
                    return cat_display
        return '📦 Otros'