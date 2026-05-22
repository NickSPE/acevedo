from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


# Create your models here.
class UsuarioManager(BaseUserManager):
    def create_user(self, correo, password=None, **extra_fields):
        if not correo:
            raise ValueError("El correo es obligatorio")
        correo = self.normalize_email(correo)
        user = self.model(correo=correo, **extra_fields)
        user.set_password(password)  # Usa hashing seguro
        user.save(using=self._db)
        return user

    def create_superuser(self, correo, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(correo, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    documento_identidad = models.CharField(max_length=25)
    nombres = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=50)
    apellido_materno = models.CharField(max_length=50)
    correo = models.EmailField(unique=True, max_length=100)
    telefono = models.BigIntegerField()
    pais = models.CharField(max_length=100, default="Peru", blank=True)
    imagen_perfil = models.BinaryField(null=True, blank=True)
    pin_acceso_rapido = models.CharField(max_length=6, default='000000')  # PIN de 6 dígitos exactos
    email_verificado = models.BooleanField(default=False)
    onboarding_completed = models.BooleanField(default=False)  # Nuevo campo para tracking de onboarding
    
    # Campos para recuperación de contraseña
    codigo_recuperacion = models.CharField(max_length=6, blank=True, null=True)  # Código de 6 dígitos
    codigo_expiracion = models.DateTimeField(blank=True, null=True)  # Cuando expira el código
    
    id_moneda = models.ForeignKey("cuentas.Moneda", on_delete=models.CASCADE)

    # Campos obligatorios para el sistema de autenticación
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'correo'
    REQUIRED_FIELDS = ['nombres', 'apellido_paterno', 'apellido_materno', 'documento_identidad', 'telefono']

    def __str__(self):
        return f"{self.nombres} {self.apellido_paterno}"

