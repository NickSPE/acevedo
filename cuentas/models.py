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
        ('emergencia', 'Emergencia'),
        ('objetivos', 'Objetivos'),
        ('inversion', 'Inversión'),
        ('gastos', 'Gastos'),
        ('ahorro', 'Ahorro'),
        ('entretenimiento', 'Entretenimiento'),
        ('transporte', 'Transporte'),
        ('alimentacion', 'Alimentación'),
        ('salud', 'Salud'),
        ('educacion', 'Educación'),
        ('otros', 'Otros'),
    )

    COLORES_TIPO = {
        'emergencia': '#ff6b6b',
        'objetivos': '#ffb84d',
        'inversion': '#74b9ff',
        'gastos': '#ff6b6b',
        'ahorro': '#00b894',
        'entretenimiento': '#a29bfe',
        'transporte': '#fd79a8',
        'alimentacion': '#e17055',
        'salud': '#55efc4',
        'educacion': '#6c5ce7',
        'otros': '#636e72',
    }

    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=300, blank=True, null=True)
    saldo = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tipo = models.CharField(max_length=20, choices=TIPOS_SUBCUENTA, default='otros')
    color = models.CharField(max_length=7, default='#3B82F6')  # Color hex para la UI
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    id_cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name='subcuentas')

    def __str__(self):
        return f"{self.nombre} - ${self.saldo}"

    def save(self, *args, **kwargs):
        # Asignar color automáticamente según el tipo si no se ha establecido uno personalizado
        if self.color == '#3B82F6':  # Color por defecto
            self.color = self.COLORES_TIPO.get(self.tipo, '#3B82F6')
        super().save(*args, **kwargs)

    def get_color_tipo(self):
        """Obtiene el color correspondiente al tipo de subcuenta"""
        return self.COLORES_TIPO.get(self.tipo, '#3B82F6')

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

# Create your models here.
