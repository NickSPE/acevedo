from django.contrib.auth.backends import BaseBackend
from usuarios.models import Usuario

class EmailBackend(BaseBackend):
    def authenticate(self, request, correo=None, password=None, **kwargs):
        try:
            user = Usuario.objects.get(correo=correo)
        except Usuario.DoesNotExist:
            return None
        if user.check_password(password):
            user.backend = 'usuarios.backends.EmailBackend'
            return user
        return None

    def get_user(self, user_id):
        try:
            return Usuario.objects.get(pk=user_id)
        except Usuario.DoesNotExist:
            return None

    def user_can_authenticate(self, user):
        """
        Método de seguridad opcional como el que usa Django por defecto.
        Evita login si el usuario está inactivo.
        """
        return getattr(user, 'is_active', False)