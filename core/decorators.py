from django.shortcuts import redirect
from functools import wraps

def fast_access_pin_verified(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Verifica si el PIN fue validado en la sesión
        if not request.session.get('pin_acceso_rapido_validado'):
            return redirect('usuarios:login')  # nombre de tu vista de verificación
        return view_func(request, *args, **kwargs)
    return _wrapped_view