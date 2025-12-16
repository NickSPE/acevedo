"""Funciones helpers para la app cuentas"""

from alertas_notificaciones.models import Notificacion, TipoNotificacion


def crear_notificacion_movimiento(usuario, titulo, mensaje, categoria='Transacciones', datos_adicionales=None):
    """Función auxiliar para crear notificaciones persistentes de movimientos financieros"""
    try:
        # Buscar o crear el tipo de notificación
        tipo_notificacion, created = TipoNotificacion.objects.get_or_create(
            nombre='Movimiento Financiero',
            defaults={
                'categoria': 'info',
                'descripcion': 'Notificaciones sobre movimientos en cuentas y subcuentas',
                'icono': '💰',
                'color': '#10b981'
            }
        )
        
        # Crear la notificación
        notificacion = Notificacion.objects.create(
            usuario=usuario,
            tipo_notificacion=tipo_notificacion,
            titulo=titulo,
            mensaje=mensaje,
            categoria=categoria,
            modulo_origen='cuentas',
            datos_adicionales=datos_adicionales or {},
            estado='enviada',
            prioridad='media'
        )
        
        return notificacion
        
    except Exception as e:
        print(f"Error creando notificación: {e}")
        return None


def validar_permisos_subcuenta(usuario, subcuenta):
    """Verifica si el usuario tiene permisos sobre la subcuenta"""
    return (subcuenta.propietario == usuario or 
            (subcuenta.id_cuenta and subcuenta.id_cuenta.id_usuario == usuario))


def validar_permisos_ambas_subcuentas(usuario, subcuenta1, subcuenta2):
    """Verifica si el usuario tiene permisos sobre ambas subcuentas"""
    return (validar_permisos_subcuenta(usuario, subcuenta1) and 
            validar_permisos_subcuenta(usuario, subcuenta2))


def procesar_imagen_perfil(usuario, imagen_archivo=None, solo_leer=False):
    """
    Procesa la imagen de perfil del usuario.
    Si imagen_archivo es None y solo_leer=True, retorna (base64, formato)
    Si imagen_archivo es proporcionado, guarda y retorna (success, mensaje)
    """
    import base64
    import io
    from PIL import Image
    
    if solo_leer:
        # Modo lectura: retorna imagen en base64 para mostrar
        if usuario.imagen_perfil:
            try:
                imagen_bytes = usuario.imagen_perfil
                imagen_base64 = base64.b64encode(imagen_bytes).decode('utf-8')
                formato = Image.open(io.BytesIO(imagen_bytes)).format
                return imagen_base64, formato
            except Exception as e:
                print(f"Error procesando imagen: {e}")
                usuario.imagen_perfil = None
                usuario.save()
                return None, None
        return None, None
    
    # Modo escritura: procesa archivo subido
    if not imagen_archivo:
        return False, "❌ No se seleccionó ninguna imagen."
    
    try:
        imagen_bytes = imagen_archivo.read()
        Image.open(io.BytesIO(imagen_bytes))  # Validar formato
        usuario.imagen_perfil = imagen_bytes
        usuario.save()
        return True, "✅ Foto de perfil actualizada correctamente."
    except Exception as e:
        return False, "❌ Error al procesar la imagen. Asegúrate de subir un archivo de imagen válido."


def validar_password(actual_password, new_password, confirm_password):
    """Valida cambio de contraseña. Retorna mensaje de error o None si es válido"""
    if not all([actual_password, new_password, confirm_password]):
        return "❌ Todos los campos de contraseña son obligatorios."
    
    if new_password != confirm_password:
        return "❌ Las nuevas contraseñas no coinciden."
    
    if len(new_password) < 8:
        return "❌ La nueva contraseña debe tener al menos 8 caracteres."
    
    if actual_password == new_password:
        return "⚠️ La nueva contraseña debe ser diferente a la actual."
    
    return None


def validar_pin_cambio(usuario, current_pin, new_pin, confirm_pin):
    """Valida cambio de PIN. Retorna mensaje de error o None si es válido"""
    from usuarios.models import Usuario
    
    if not all([current_pin, new_pin, confirm_pin]):
        return "❌ Todos los campos de PIN son obligatorios."
    
    if not all(pin.isdigit() for pin in [current_pin, new_pin, confirm_pin]):
        return "❌ Los PINs solo pueden contener números."
    
    if new_pin != confirm_pin:
        return "❌ Los nuevos PINs no coinciden."
    
    if current_pin == new_pin:
        return "⚠️ El nuevo PIN debe ser diferente al actual."
    
    if Usuario.objects.filter(pin_acceso_rapido=new_pin).exclude(id=usuario.id).exists():
        return "❌ Este PIN ya está siendo usado. Por favor, elige uno diferente."
    
    return None


def procesar_ajax_operacion(request, operacion, operacion_fn, validaciones_previas, usuario, titulo, datos_adicionales=None):
    """Helper para procesar operaciones AJAX comunes (depósitos, transferencias, etc.)"""
    from django.http import JsonResponse
    from decimal import Decimal
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        # Validaciones
        if not validaciones_previas():
            return JsonResponse({'success': False, 'error': 'Validación fallida'})
        
        # Ejecutar operación
        success, message = operacion_fn()
        
        if success:
            # Crear notificación
            crear_notificacion_movimiento(
                usuario=usuario,
                titulo=titulo,
                mensaje=message,
                datos_adicionales=datos_adicionales or {'tipo_movimiento': operacion}
            )
            return JsonResponse({'success': True, 'message': message})
        else:
            return JsonResponse({'success': False, 'error': message})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
