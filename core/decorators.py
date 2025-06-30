""" from django.shortcuts import redirect
from functools import wraps

def email_verified_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Verifica si el PIN fue validado en la sesión
        if not request.session.get('pin_validado'):
            return redirect('usuarios:login')  # nombre de tu vista de verificación
        return view_func(request, *args, **kwargs)
    return _wrapped_view """