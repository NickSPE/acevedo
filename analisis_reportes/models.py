from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
import json

User = get_user_model()

class Reporte(models.Model):
    TIPOS_REPORTE = (
        ('gastos_categoria', 'Gastos por Categoría'),
        ('ingresos_egresos', 'Ingresos vs Egresos'),
        ('subcuentas_analisis', 'Análisis de Subcuentas'),
        ('balance_general', 'Balance General'),
        ('flujo_efectivo', 'Flujo de Efectivo'),
    )
    
    tipo_reporte = models.CharField(max_length=25, choices=TIPOS_REPORTE)
    titulo = models.CharField(max_length=200, default='Reporte Financiero')
    descripcion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(auto_now_add=True)
    datos_json = models.TextField(blank=True, null=True)  # Para almacenar datos del reporte en JSON
    id_usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    id_cuenta = models.ForeignKey("cuentas.Cuenta", on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_tipo_reporte_display()} - {self.fecha_creacion.strftime('%d/%m/%Y')}"
    
    def get_datos(self):
        """Devuelve los datos del reporte como diccionario"""
        if self.datos_json:
            return json.loads(self.datos_json)
        return {}
    
    def set_datos(self, datos):
        """Guarda los datos del reporte como JSON"""
        self.datos_json = json.dumps(datos, default=str)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'


class ConfiguracionReporte(models.Model):
    """Configuraciones personalizadas para reportes del usuario"""
    FORMATOS_EXPORT = (
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    )
    
    id_usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    periodo_default = models.CharField(max_length=20, default='mes_actual')
    incluir_subcuentas_inactivas = models.BooleanField(default=False)
    formato_export_default = models.CharField(max_length=10, choices=FORMATOS_EXPORT, default='pdf')
    moneda_display = models.CharField(max_length=10, default='USD')
    
    def __str__(self):
        return f"Configuración de {self.id_usuario.username}"
    
    class Meta:
        verbose_name = 'Configuración de Reporte'
        verbose_name_plural = 'Configuraciones de Reportes'
