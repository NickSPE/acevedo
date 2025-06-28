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
    id_usuario = models.ForeignKey("usuarios.Usuario" , on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre
# Create your models here.
