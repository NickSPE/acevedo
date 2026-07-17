from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.hashers import make_password, check_password
from django.db import models


class UsuarioManager(BaseUserManager):
    def create_user(self, correo, password=None, **extra_fields):
        if not correo:
            raise ValueError("El correo es obligatorio")
        correo = self.normalize_email(correo)
        if 'pin_acceso_rapido' in extra_fields:
            extra_fields['pin_acceso_rapido'] = make_password(extra_fields['pin_acceso_rapido'])
        user = self.model(correo=correo, **extra_fields)
        user.set_password(password)
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
    pin_acceso_rapido = models.CharField(max_length=128, default='000000')
    email_verificado = models.BooleanField(default=False)
    onboarding_completed = models.BooleanField(default=False)
    
    codigo_recuperacion = models.CharField(max_length=6, blank=True, null=True)
    codigo_expiracion = models.DateTimeField(blank=True, null=True)
    
    id_moneda = models.ForeignKey("cuentas.Moneda", on_delete=models.CASCADE)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'correo'
    REQUIRED_FIELDS = ['nombres', 'apellido_paterno', 'apellido_materno', 'documento_identidad', 'telefono']

    def set_pin(self, pin):
        self.pin_acceso_rapido = make_password(pin)

    def check_pin(self, pin):
        stored = str(self.pin_acceso_rapido) if not isinstance(self.pin_acceso_rapido, str) else self.pin_acceso_rapido
        if stored.startswith('pbkdf2_'):
            return check_password(str(pin), stored)
        return stored == str(pin)

    def __str__(self):
        return f"{self.nombres} {self.apellido_paterno}"

