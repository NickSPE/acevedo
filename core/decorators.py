from django.shortcuts import redirect
from functools import wraps

def fast_access_pin_verified(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Solo verificar PIN si el usuario llegó desde acceso rápido con PIN
        # Si hizo login normal con email/contraseña, no necesita verificación de PIN
        if request.session.get('login_method') == 'pin' and not request.session.get('pin_acceso_rapido_validado'):
            return redirect('usuarios:acceso_rapido')
        return view_func(request, *args, **kwargs)
    return _wrapped_view