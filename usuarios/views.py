from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate , login
from django.core.mail import send_mail
from django.conf import settings

from django.shortcuts import redirect

from cuentas.models import Moneda, Cuenta
from .models import Usuario
import random

def Generar_Pin():
    return str(random.randint(100000, 999999))  # 6 dígitos

def Login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        usuario = authenticate(request , correo=email , password=password)

        if usuario:
            request.session['user_id'] = usuario.id
            
            login(request , usuario , backend='usuarios.backends.EmailBackend')

            email_verificado = request.user.email_verificado

            if(email_verificado):
                # Ir directamente al dashboard sin requerir PIN
                return redirect('core:dashboard')
            else:
                return redirect('usuarios:pagina_verificar_correo')
        else:
            return render(request, 'usuarios/login.html' , {
                "message_error": "Credenciales no validas.",
            })

    return render(request, 'usuarios/login.html')


def Register(request):
    monedas = Moneda.objects.all()

    if request.method == "POST":
        documento_identidad = request.POST.get('documento_identidad')
        nombres = request.POST.get('nombres')
        apellido_paterno = request.POST.get('apellido_paterno')
        apellido_materno = request.POST.get('apellido_materno')
        correo = request.POST.get('correo')
        contrasena = request.POST.get('contrasena')
        telefono = request.POST.get('telefono')
        pin_acceso_rapido = request.POST.get("pin_acceso_rapido")
        imagen_perfil = request.FILES.get('imagen_perfil')

        id_moneda_seleccionada = request.POST.get('id_moneda')
        print(id_moneda_seleccionada)
        try:
            moneda_obj = Moneda.objects.get(id=id_moneda_seleccionada)
        except Moneda.DoesNotExist:
            error = "La moneda seleccionada no es válida."
            return render(request, "usuarios/register_new_clean.html", {"error": error, 'monedas': monedas})

        nombre_cuenta = request.POST.get('nombre_cuenta')
        saldo_inicial = request.POST.get('saldo_inicial')
        descripcion = request.POST.get('descripcion_cuenta')

        if not descripcion:
            descripcion = ""
        if not nombre_cuenta:
            nombre_cuenta = "Cuenta principal"

        try:
            saldo_inicial_float = float(saldo_inicial)
        except (ValueError, TypeError):
            error = "El saldo inicial debe ser un número válido."
            return render(request, "usuarios/register_new_clean.html", {"error": error, 'monedas': monedas})

        if imagen_perfil:
            import base64
            imagen_b64 = base64.b64encode(imagen_perfil.read()).decode('utf-8')
        else:
            imagen_b64 = None

        if Usuario.objects.filter(correo=correo).exists():
            error = "El correo ya está registrado."
            return render(request, "usuarios/register_new_clean.html", {"error": error, 'monedas': monedas})

        request.session['registro_temp'] = {
            'documento_identidad': documento_identidad,
            'nombres': nombres,
            'apellido_paterno': apellido_paterno,
            'apellido_materno': apellido_materno,
            'correo': correo,
            'contrasena': contrasena,
            'telefono': telefono,
            'id_moneda': id_moneda_seleccionada,
            'nombre_cuenta': nombre_cuenta,
            'saldo_inicial': saldo_inicial,
            'descripcion': descripcion,
            'imagen_perfil': imagen_b64,
            'pin_acceso_rapido': pin_acceso_rapido,
        }

        return redirect('usuarios:pagina_verificar_correo')

    return render(request, 'usuarios/register_new_clean.html', {
        'monedas': monedas,
    })

def Pagina_Verificar_Correo(request):
    print("🔍 DEBUG: Entrando a Pagina_Verificar_Correo")
    data = request.session.get('registro_temp')
    print(f"🔍 DEBUG: Datos de sesión: {data}")
    
    if data and 'correo' in data:
        user_email = data['correo']
        print(f"🔍 DEBUG: Enviando PIN a: {user_email}")

        PIN = Generar_Pin()
        request.session['pin_acceso'] = PIN
        request.session['correo_usuario'] = user_email
        
        print(f"🔍 DEBUG: PIN generado: {PIN}")
        print(f"🔍 DEBUG: EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"🔍 DEBUG: DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

        try:
            result = send_mail(
                subject='Tu código de acceso rápido - FinGest',
                message=f'Tu código de acceso rapido para es: {PIN}',        
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False,
            )
            print(f"🔍 DEBUG: Resultado del envío: {result}")
            print(f"✅ Email enviado exitosamente")
        except Exception as e:
            print(f"❌ ERROR al enviar email: {str(e)}")
            print(f"❌ Tipo de error: {type(e).__name__}")
            import traceback
            traceback.print_exc()

        return render(request , 'usuarios/validar_correo.html')
    else:
        print("🔍 DEBUG: No hay datos de registro en la sesión")
        return redirect('usuarios:register')

def Verificacion_Correo(request):
    print("🔍 DEBUG: Entrando a Verificacion_Correo")
    print(f"🔍 DEBUG: Método: {request.method}")
    
    if(request.method == 'POST'):
        input_pin = ''.join([
            request.POST.get(f'pin{i}', '') for i in range(6)
        ])
        
        print(f"🔍 DEBUG: PIN ingresado: {input_pin}")
        
        session_pin = request.session.get('pin_acceso')
        print(f"🔍 DEBUG: PIN de sesión: {session_pin}")
        
        if(input_pin == session_pin):
            print("🔍 DEBUG: PIN correcto, creando usuario...")
            data = request.session.get('registro_temp')

            request.session['pin_validado'] = True

            del request.session['pin_acceso']
            del request.session['correo_usuario']

            saldo_inicial = float(data['saldo_inicial'])
            id_moneda_seleccionada = int(data['id_moneda'])

            imagen_binario = None
            if 'imagen_perfil' in data:
                if(data['imagen_perfil']):
                    import base64
                    imagen_binario = base64.b64decode(data['imagen_perfil'])

            moneda = Moneda.objects.get(id=id_moneda_seleccionada)
            usuario = Usuario.objects.create_user(
                documento_identidad=data['documento_identidad'],
                nombres=data['nombres'],
                apellido_paterno=data['apellido_paterno'],
                apellido_materno=data['apellido_materno'],
                correo=data['correo'],
                password=data['contrasena'],
                telefono=data['telefono'],
                imagen_perfil=imagen_binario,
                pin_acceso_rapido=data['pin_acceso_rapido'],
                email_verificado=True,
                id_moneda=moneda
            )

            Cuenta.objects.create(
                id_usuario=usuario,
                nombre=data['nombre_cuenta'],
                saldo_cuenta=saldo_inicial,
                descripcion=data['descripcion'],
            )

            del request.session['registro_temp']

            login(request, usuario, backend='usuarios.backends.EmailBackend')

            return redirect('core:dashboard')
        else:
            return render(request , 'usuarios/validar_correo.html' , { 'error_message' : 'PIN incorrecto'})

@login_required
def Acceso_Rapido(request):
    user = request.user
    if(not user.is_authenticated):
        return redirect('usuarios:login')
    print("Ingreso acceso rapido")

    if(request.method == "POST"):
        # Intentar obtener PIN de diferentes formatos posibles
        pin_input = request.POST.get('pin_input', '')  # Formato del template actual
        
        # Si no viene en pin_input, intentar formato individual (pin0, pin1, etc.)
        if not pin_input:
            pin_input = ''.join([
                request.POST.get(f'pin{i}', '') for i in range(6)
            ])
        
        print(f"🔍 DEBUG ACCESO_RAPIDO: Todos los datos POST: {dict(request.POST)}")
        print(f"🔍 DEBUG ACCESO_RAPIDO: PIN obtenido: '{pin_input}'")

        if not pin_input.isdigit() or len(pin_input) != 6:
            error_message = "PIN inválido. Ingrese 6 dígitos numéricos."
            return render(request, 'usuarios/acceso_rapido.html', {'error_message': error_message})

        try:
            usuario = Usuario.objects.get(id=user.id)
        except Usuario.DoesNotExist:
            error_message = "Usuario no encontrado."
            return render(request, 'usuarios/acceso_rapido.html', {'error_message': error_message})

        print(f"🔍 DEBUG ACCESO_RAPIDO: PIN ingresado: '{pin_input}'")
        print(f"🔍 DEBUG ACCESO_RAPIDO: PIN guardado: '{usuario.pin_acceso_rapido}' (tipo: {type(usuario.pin_acceso_rapido)})")

        # Comparar ambos como strings
        if str(usuario.pin_acceso_rapido) == pin_input:
            request.session['pin_acceso_rapido_validado'] = True

            return redirect('core:dashboard') 
        else:
            error_message = "El PIN ingresado es incorrecto."
            return render(request, 'usuarios/acceso_rapido.html', {'error_message': error_message})

    return render(request , 'usuarios/acceso_rapido.html')

def Reestablecer_Contraseña(request):
    pass

# === FUNCIONES PLACEHOLDER PARA URLs FALTANTES ===

def pin_login(request):
    """Login directo usando solo PIN"""
    if request.method == "POST":
        # Intentar obtener PIN de diferentes formatos posibles
        pin_input = request.POST.get('pin_input', '')  # Formato del template actual
        
        # Si no viene en pin_input, intentar formato individual (pin0, pin1, etc.)
        if not pin_input:
            pin_input = ''.join([
                request.POST.get(f'pin{i}', '') for i in range(6)
            ])
        
        print(f"🔍 DEBUG PIN_LOGIN: Todos los datos POST: {dict(request.POST)}")
        print(f"🔍 DEBUG PIN_LOGIN: PIN obtenido: '{pin_input}'")
        
        if not pin_input.isdigit() or len(pin_input) != 6:
            error_message = f"PIN inválido. Recibido: '{pin_input}' (longitud: {len(pin_input)})"
            return render(request, 'usuarios/pin_login.html', {'error_message': error_message})
        
        try:
            # Buscar usuario por PIN
            print(f"🔍 DEBUG PIN_LOGIN: Buscando usuario con PIN como string: '{pin_input}'")
            
            # Buscar por PIN como string (no como int)
            usuario = Usuario.objects.get(pin_acceso_rapido=pin_input)
            print(f"🔍 DEBUG PIN_LOGIN: Usuario encontrado: {usuario.correo}")
            
            # Autenticar y hacer login
            login(request, usuario, backend='usuarios.backends.EmailBackend')
            request.session['pin_acceso_rapido_validado'] = True
            
            return redirect('core:dashboard')
            
        except Usuario.DoesNotExist:
            error_message = "PIN incorrecto. No se encontró ningún usuario con ese PIN."
            return render(request, 'usuarios/pin_login.html', {'error_message': error_message})
        except Exception as e:
            error_message = f"Error al procesar el PIN: {str(e)}"
            return render(request, 'usuarios/pin_login.html', {'error_message': error_message})
    
    return render(request, 'usuarios/pin_login.html')

def onboarding_view(request):
    """Placeholder para onboarding de nuevos usuarios"""
    try:
        return render(request, 'usuarios/onboarding.html', {
            'message': 'Sistema de onboarding no implementado aún'
        })
    except Exception as e:
        from django.http import HttpResponse
        return HttpResponse(f"Vista de onboarding no disponible: {str(e)}", status=503)

def complete_onboarding(request):
    """Placeholder para completar onboarding"""
    from django.http import JsonResponse
    return JsonResponse({
        'success': False,
        'message': 'Sistema de onboarding no implementado aún'
    })

def fix_incomplete_onboarding(request):
    """Placeholder para corregir onboarding incompleto"""
    try:
        return render(request, 'usuarios/fix_onboarding.html', {
            'message': 'Sistema de corrección de onboarding no implementado aún'
        })
    except Exception as e:
        from django.http import HttpResponse
        return HttpResponse(f"Vista de corrección de onboarding no disponible: {str(e)}", status=503)

def password_reset_request(request):
    """Placeholder para solicitud de recuperación de contraseña"""
    try:
        return render(request, 'usuarios/password_reset_modern.html', {
            'message': 'Sistema de recuperación de contraseña no implementado aún'
        })
    except Exception as e:
        from django.http import HttpResponse
        return HttpResponse(f"Vista de recuperación de contraseña no disponible: {str(e)}", status=503)

def recuperar_con_codigo(request):
    """Placeholder para recuperación con código"""
    from django.http import JsonResponse
    return JsonResponse({
        'success': False,
        'message': 'API de recuperación con código no implementada aún'
    })

def test_view(request):
    """Vista de prueba para desarrollo"""
    try:
        return render(request, 'usuarios/test.html', {
            'message': 'Vista de prueba - Sistema funcionando correctamente',
            'user': request.user if request.user.is_authenticated else None
        })
    except Exception as e:
        from django.http import HttpResponse
        return HttpResponse(f"Vista de prueba no disponible: {str(e)}", status=503)