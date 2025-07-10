from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate , login
from django.core.mail import send_mail
from django.conf import settings

from django.shortcuts import redirect

from cuentas.models import Moneda, Cuenta
from .models import Usuario
import random
import json

def check_onboarding_required(user):
    """Verificar si el usuario necesita completar onboarding"""
    if user.is_authenticated and not user.onboarding_completed:
        return True
    return False

def Generar_Pin():
    return str(random.randint(100000, 999999))  # 6 dígitos

def Login(request):
    # print(f"🔍 DEBUG LOGIN: Método {request.method}, URL: {request.path}") - DESACTIVADO
    
    if request.method == "POST":
        # print(f"🔍 DEBUG LOGIN: Datos POST recibidos: {list(request.POST.keys())}") - DESACTIVADO
        
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        # print(f"🔍 DEBUG LOGIN: Email: {email}, Password: {'*' * len(password) if password else 'None'}") - DESACTIVADO

        usuario = authenticate(request , correo=email , password=password)
        
        # print(f"🔍 DEBUG LOGIN: Resultado authenticate: {usuario}") - DESACTIVADO

        if usuario:
            request.session['user_id'] = usuario.id
            
            login(request , usuario , backend='usuarios.backends.EmailBackend')

            email_verificado = request.user.email_verificado
            
            print(f"🔍 DEBUG LOGIN: Email verificado: {email_verificado}")

            if(email_verificado):
                # Verificar si necesita onboarding
                if check_onboarding_required(request.user):
                    print("🔍 DEBUG LOGIN: Redirigiendo a onboarding")
                    return redirect('usuarios:onboarding')
                # Ir directamente al dashboard sin requerir PIN
                print("🔍 DEBUG LOGIN: Redirigiendo a dashboard")
                return redirect('core:dashboard')
            else:
                print("🔍 DEBUG LOGIN: Email no verificado, redirigiendo a verificación")
                return redirect('usuarios:pagina_verificar_correo')
        else:
            print("🔍 DEBUG LOGIN: Credenciales inválidas")
            return render(request, 'usuarios/login.html' , {
                "message_error": "Credenciales no validas.",
            })

    print("🔍 DEBUG LOGIN: Mostrando formulario de login")
    return render(request, 'usuarios/login.html')


def Register(request):
    monedas = Moneda.objects.all()

    if request.method == "POST":
        print(f"🔍 DEBUG: POST recibido. Action: {request.POST.get('action')}")
        print(f"🔍 DEBUG: Datos POST: {list(request.POST.keys())}")
        
        # Manejar petición AJAX para enviar código de verificación
        if request.POST.get('action') == 'send_verification':
            print("🔍 DEBUG: Petición AJAX para enviar código")
            
            correo = request.POST.get('correo')
            nombres = request.POST.get('nombres')
            
            if not correo or not nombres:
                return JsonResponse({
                    'success': False,
                    'error': 'Correo y nombres son requeridos'
                })
            
            # Verificar que el correo no esté ya registrado
            if Usuario.objects.filter(correo=correo).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'El correo ya está registrado'
                })
            
            # Generar y enviar PIN
            PIN = Generar_Pin()
            request.session['pin_verification'] = PIN
            request.session['email_for_verification'] = correo
            
            print(f"🔍 DEBUG: PIN generado para verificación: {PIN}")
            print(f"🔍 DEBUG: Enviando PIN a: {correo}")
            
            try:
                result = send_mail(
                    subject='Código de verificación - FinGest',
                    message=f'Hola {nombres},\n\nTu código de verificación para registrarte en FinGest es: {PIN}\n\nEste código expira en 10 minutos.\n\n¡Gracias por unirte a FinGest!',        
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[correo],
                    fail_silently=False,
                )
                print(f"🔍 DEBUG: Resultado del envío de verificación: {result}")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Código enviado exitosamente'
                })
                
            except Exception as e:
                print(f"❌ ERROR al enviar email de verificación: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'error': f'Error al enviar el código: {str(e)}'
                })
        
        # Manejar registro normal (cuando se envía el formulario completo)
        print("🔍 DEBUG: Procesando registro normal")
        
        documento_identidad = request.POST.get('documento_identidad')
        nombres = request.POST.get('nombres')
        apellido_paterno = request.POST.get('apellido_paterno')
        apellido_materno = request.POST.get('apellido_materno')
        correo = request.POST.get('correo')
        contrasena = request.POST.get('contrasena')
        telefono = request.POST.get('telefono')
        pin_acceso_rapido = request.POST.get("pin_acceso_rapido")
        imagen_perfil = request.FILES.get('imagen_perfil')
        verification_code = request.POST.get('codigo_verificacion')

        print(f"🔍 DEBUG: Datos recibidos - correo: {correo}, código: {verification_code}")
        
        # Verificar código de verificación
        session_pin = request.session.get('pin_verification')
        session_email = request.session.get('email_for_verification')
        
        print(f"🔍 DEBUG: Sesión - PIN: {session_pin}, Email: {session_email}")
        
        if not session_pin or not session_email or session_email != correo:
            print("🔍 DEBUG: Error - No hay PIN en sesión o email no coincide")
            return render(request, "usuarios/register_simple.html", {
                "error": "Por favor solicita un código de verificación primero.", 
                'monedas': monedas
            })
        
        if verification_code != session_pin:
            print(f"🔍 DEBUG: Error - Código incorrecto. Recibido: '{verification_code}', Esperado: '{session_pin}'")
            return render(request, "usuarios/register_simple.html", {
                "error": "Código de verificación incorrecto.", 
                'monedas': monedas
            })
        
        print("🔍 DEBUG: Código de verificación correcto, continuando con registro...")

        id_moneda_seleccionada = request.POST.get('id_moneda')
        print(f"🔍 DEBUG: Moneda seleccionada: {id_moneda_seleccionada}")
        
        try:
            moneda_obj = Moneda.objects.get(id=id_moneda_seleccionada)
        except Moneda.DoesNotExist:
            error = "La moneda seleccionada no es válida."
            return render(request, "usuarios/register_simple.html", {"error": error, 'monedas': monedas})

        nombre_cuenta = request.POST.get('nombre_cuenta')
        saldo_inicial = request.POST.get('saldo_inicial')
        descripcion = request.POST.get('descripcion_cuenta')

        if not descripcion:
            descripcion = ""
        if not nombre_cuenta:
            nombre_cuenta = "Cuenta principal"

        try:
            saldo_inicial_float = float(saldo_inicial) if saldo_inicial else 0.0
        except (ValueError, TypeError):
            error = "El saldo inicial debe ser un número válido."
            return render(request, "usuarios/register_simple.html", {"error": error, 'monedas': monedas})

        if imagen_perfil:
            import base64
            imagen_b64 = base64.b64encode(imagen_perfil.read()).decode('utf-8')
        else:
            imagen_b64 = None

        if Usuario.objects.filter(correo=correo).exists():
            error = "El correo ya está registrado."
            return render(request, "usuarios/register_simple.html", {"error": error, 'monedas': monedas})

        print("🔍 DEBUG: Creando usuario...")
        
        try:
            # Crear el usuario con valores por defecto para campos requeridos
            nuevo_usuario = Usuario.objects.create_user(
                documento_identidad=documento_identidad or '00000000',  # Valor por defecto si está vacío
                nombres=nombres,
                apellido_paterno=apellido_paterno,
                apellido_materno=apellido_materno,
                correo=correo,
                password=contrasena,
                telefono=int(telefono) if telefono else 0,  # Convertir a int o usar 0
                pin_acceso_rapido=pin_acceso_rapido or '000000',  # PIN por defecto
                imagen_perfil=imagen_b64,
                email_verificado=True,  # Ya verificamos el correo con el código
                id_moneda=moneda_obj
            )
            
            print(f"🔍 DEBUG: Usuario creado: {nuevo_usuario.correo}")
            
            # Crear la cuenta principal
            nueva_cuenta = Cuenta.objects.create(
                id_usuario=nuevo_usuario,
                nombre=nombre_cuenta,
                saldo_cuenta=saldo_inicial_float,
                descripcion=descripcion
            )
            
            print(f"🔍 DEBUG: Cuenta creada: {nueva_cuenta.nombre}")
            
            # Limpiar sesión de verificación
            if 'pin_verification' in request.session:
                del request.session['pin_verification']
            if 'email_for_verification' in request.session:
                del request.session['email_for_verification']
            
            # NO autenticar automáticamente - redirigir al login
            print("🔍 DEBUG: Usuario creado exitosamente, redirigiendo al login")
            return render(request, "usuarios/login.html", {
                "message_success": f"¡Registro exitoso, {nuevo_usuario.nombres}! Ahora inicia sesión con tu nueva cuenta."
            })
                
        except Exception as e:
            print(f"❌ ERROR al crear usuario: {str(e)}")
            import traceback
            traceback.print_exc()
            return render(request, "usuarios/register_simple.html", {
                "error": f"Error al crear la cuenta: {str(e)}", 
                'monedas': monedas
            })

    return render(request, 'usuarios/register_simple.html', {
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
        pin_input = request.POST.get('pin_input', '').strip()
        
        # Si no viene en pin_input, intentar formato individual (pin0, pin1, etc.)
        if not pin_input:
            pin_input = ''.join([
                request.POST.get(f'pin{i}', '') for i in range(6)
            ])
        
        print(f"🔍 DEBUG PIN_LOGIN: Método: {request.method}")
        print(f"🔍 DEBUG PIN_LOGIN: Todos los datos POST: {dict(request.POST)}")
        print(f"🔍 DEBUG PIN_LOGIN: PIN obtenido: '{pin_input}' (longitud: {len(pin_input)})")
        
        if not pin_input:
            error_message = "No se recibió ningún PIN."
            return render(request, 'usuarios/pin_login.html', {'error_message': error_message})
        
        if not pin_input.isdigit():
            error_message = f"PIN inválido. Solo se permiten números. Recibido: '{pin_input}'"
            return render(request, 'usuarios/pin_login.html', {'error_message': error_message})
            
        if len(pin_input) != 6:
            error_message = f"PIN inválido. Debe tener exactamente 6 dígitos. Recibido: '{pin_input}' (longitud: {len(pin_input)})"
            return render(request, 'usuarios/pin_login.html', {'error_message': error_message})
        
        try:
            # Buscar usuario por PIN
            print(f"🔍 DEBUG PIN_LOGIN: Buscando usuario con PIN: '{pin_input}'")
            
            # Buscar exactamente por el PIN como string
            usuario = Usuario.objects.filter(pin_acceso_rapido=pin_input).first()
            
            if usuario:
                print(f"✅ DEBUG PIN_LOGIN: Usuario encontrado: {usuario.correo} (ID: {usuario.id})")
                
                # Verificar si el usuario está activo
                if not usuario.is_active:
                    error_message = "Esta cuenta está desactivada."
                    return render(request, 'usuarios/pin_login.html', {'error_message': error_message})
                
                # Autenticar y hacer login
                login(request, usuario, backend='usuarios.backends.EmailBackend')
                request.session['pin_acceso_rapido_validado'] = True
                
                print(f"✅ DEBUG PIN_LOGIN: Login exitoso para {usuario.correo}")
                
                # Verificar si necesita onboarding
                if not usuario.onboarding_completed:
                    print("🔍 DEBUG PIN_LOGIN: Redirigiendo a onboarding")
                    return redirect('usuarios:onboarding')
                
                print("🔍 DEBUG PIN_LOGIN: Redirigiendo a dashboard")
                return redirect('core:dashboard')
            else:
                print(f"❌ DEBUG PIN_LOGIN: No se encontró usuario con PIN '{pin_input}'")
                
                # Debug: Mostrar todos los PINs existentes
                all_pins = Usuario.objects.values_list('pin_acceso_rapido', 'correo')
                print(f"🔍 DEBUG PIN_LOGIN: PINs existentes en BD:")
                for pin, email in all_pins:
                    print(f"   PIN: '{pin}' -> {email}")
                
                error_message = "PIN incorrecto. No se encontró ningún usuario con ese PIN."
                return render(request, 'usuarios/pin_login.html', {'error_message': error_message})
            
        except Exception as e:
            print(f"❌ DEBUG PIN_LOGIN: Error inesperado: {str(e)}")
            import traceback
            traceback.print_exc()
            error_message = f"Error al procesar el PIN: {str(e)}"
            return render(request, 'usuarios/pin_login.html', {'error_message': error_message})
    
    return render(request, 'usuarios/pin_login.html')

def onboarding_view(request):
    """Vista de onboarding para nuevos usuarios"""
    if not request.user.is_authenticated:
        return redirect('usuarios:login')
    
    # Si el onboarding ya está completo, redirigir al dashboard
    if request.user.onboarding_completed:
        return redirect('core:dashboard')
    
    try:
        return render(request, 'usuarios/onboarding.html', {
            'user': request.user
        })
    except Exception as e:
        from django.http import HttpResponse
        return HttpResponse(f"Vista de onboarding no disponible: {str(e)}", status=503)

def complete_onboarding(request):
    """Completar onboarding y actualizar datos del usuario"""
    from django.http import JsonResponse
    import json
    
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Usuario no autenticado'
        })
    
    if request.method == 'POST':
        try:
            # Obtener datos del request
            if request.content_type == 'application/json':
                data = json.loads(request.body.decode('utf-8'))
            else:
                data = request.POST
            
            print(f"🔍 DEBUG ONBOARDING: Datos recibidos: {data}")
            
            usuario = request.user
            
            # Si fue saltado, solo marcar como completado
            if data.get('skipped'):
                usuario.onboarding_completed = True
                usuario.save()
                print("🔍 DEBUG ONBOARDING: Onboarding saltado")
                return JsonResponse({
                    'success': True,
                    'message': 'Onboarding completado (saltado)'
                })
            
            # Actualizar PIN si se proporcionó
            pin_acceso_rapido = data.get('pin_acceso_rapido', '').strip()
            if pin_acceso_rapido and len(pin_acceso_rapido) == 6 and pin_acceso_rapido.isdigit():
                usuario.pin_acceso_rapido = pin_acceso_rapido
                print(f"🔍 DEBUG ONBOARDING: PIN actualizado: {pin_acceso_rapido}")
            
            # Actualizar teléfono si se proporcionó
            telefono = data.get('telefono', '').strip()
            codigo_pais = data.get('codigo_pais', '+51')
            if telefono:
                # Convertir a int para almacenar (sin código de país)
                try:
                    telefono_int = int(telefono)
                    usuario.telefono = telefono_int
                    print(f"🔍 DEBUG ONBOARDING: Teléfono actualizado: {codigo_pais}{telefono}")
                except ValueError:
                    print(f"⚠️ DEBUG ONBOARDING: Teléfono inválido: {telefono}")
            
            # Actualizar saldo de la cuenta principal si se proporcionó
            saldo_inicial = data.get('saldo_inicial', '').strip()
            nombre_cuenta = data.get('nombre_cuenta', '').strip()
            
            if saldo_inicial or nombre_cuenta:
                try:
                    # Buscar la cuenta principal del usuario
                    cuenta = Cuenta.objects.filter(id_usuario=usuario).first()
                    if cuenta:
                        if saldo_inicial:
                            try:
                                nuevo_saldo = float(saldo_inicial)
                                cuenta.saldo_cuenta = nuevo_saldo
                                print(f"🔍 DEBUG ONBOARDING: Saldo actualizado: {nuevo_saldo}")
                            except ValueError:
                                print(f"⚠️ DEBUG ONBOARDING: Saldo inválido: {saldo_inicial}")
                        
                        if nombre_cuenta:
                            cuenta.nombre = nombre_cuenta
                            print(f"🔍 DEBUG ONBOARDING: Nombre de cuenta actualizado: {nombre_cuenta}")
                        
                        cuenta.save()
                    else:
                        print("⚠️ DEBUG ONBOARDING: No se encontró cuenta principal")
                except Exception as e:
                    print(f"❌ DEBUG ONBOARDING: Error actualizando cuenta: {str(e)}")
            
            # Marcar onboarding como completado
            usuario.onboarding_completed = True
            usuario.save()
            
            print("✅ DEBUG ONBOARDING: Onboarding completado exitosamente")
            
            return JsonResponse({
                'success': True,
                'message': 'Onboarding completado exitosamente'
            })
            
        except Exception as e:
            print(f"❌ ERROR ONBOARDING: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': f'Error al completar onboarding: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
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
    """Solicitud de recuperación de contraseña - Paso 1: Enviar código"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        action = request.POST.get('action', '')
        
        print(f"🔍 DEBUG PASSWORD_RESET: Email: {email}, Action: {action}")
        
        if action == 'send_code':
            # Verificar si el usuario existe
            try:
                usuario = Usuario.objects.get(correo=email)
                print(f"🔍 DEBUG PASSWORD_RESET: Usuario encontrado: {usuario.nombres}")
                
                # Generar código de 6 dígitos
                codigo_recuperacion = str(random.randint(100000, 999999))
                print(f"🔍 DEBUG PASSWORD_RESET: Código generado: {codigo_recuperacion}")
                
                # Guardar código y expiración
                from django.utils import timezone
                import datetime
                
                usuario.codigo_recuperacion = codigo_recuperacion
                usuario.codigo_expiracion = timezone.now() + datetime.timedelta(minutes=15)
                usuario.save()
                
                # Enviar email
                try:
                    result = send_mail(
                        subject='Código de recuperación - FinGest',
                        message=f'Hola {usuario.nombres},\n\nTu código de recuperación de contraseña para FinGest es: {codigo_recuperacion}\n\nEste código expira en 15 minutos.\n\nSi no solicitaste este cambio, ignora este mensaje.',        
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        fail_silently=False,
                    )
                    print(f"🔍 DEBUG PASSWORD_RESET: Resultado del envío: {result}")
                    
                    if result == 1:
                        print(f"✅ DEBUG PASSWORD_RESET: Código enviado exitosamente")
                        return JsonResponse({
                            'success': True,
                            'message': 'Código de recuperación enviado a tu email'
                        })
                    else:
                        print(f"❌ DEBUG PASSWORD_RESET: Error al enviar email, resultado: {result}")
                        return JsonResponse({
                            'success': False,
                            'message': 'Error al enviar el código. Inténtalo de nuevo.'
                        })
                except Exception as e:
                    print(f"❌ DEBUG PASSWORD_RESET: Error en envío: {str(e)}")
                    return JsonResponse({
                        'success': False,
                        'message': f'Error de conexión: {str(e)}'
                    })
                    
            except Usuario.DoesNotExist:
                print(f"❌ DEBUG PASSWORD_RESET: Usuario no encontrado para email: {email}")
                # Por seguridad, no revelamos si el email existe o no
                return JsonResponse({
                    'success': True,
                    'message': 'Si tu email está registrado, recibirás un código de recuperación'
                })
                
        elif action == 'verify_code':
            codigo = request.POST.get('codigo', '').strip()
            
            try:
                usuario = Usuario.objects.get(correo=email)
                
                # Verificar código y expiración
                from django.utils import timezone
                
                if (usuario.codigo_recuperacion == codigo and 
                    usuario.codigo_expiracion and 
                    usuario.codigo_expiracion > timezone.now()):
                    
                    print(f"✅ DEBUG PASSWORD_RESET: Código verificado correctamente")
                    return JsonResponse({
                        'success': True,
                        'message': 'Código verificado correctamente'
                    })
                else:
                    print(f"❌ DEBUG PASSWORD_RESET: Código inválido o expirado")
                    return JsonResponse({
                        'success': False,
                        'message': 'Código inválido o expirado'
                    })
                    
            except Usuario.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Error en la verificación'
                })
                
        elif action == 'reset_password':
            codigo = request.POST.get('codigo', '').strip()
            nueva_password = request.POST.get('nueva_password', '')
            
            try:
                usuario = Usuario.objects.get(correo=email)
                
                # Verificar código una vez más
                from django.utils import timezone
                
                if (usuario.codigo_recuperacion == codigo and 
                    usuario.codigo_expiracion and 
                    usuario.codigo_expiracion > timezone.now()):
                    
                    # Cambiar contraseña
                    usuario.set_password(nueva_password)
                    usuario.codigo_recuperacion = None
                    usuario.codigo_expiracion = None
                    usuario.save()
                    
                    print(f"✅ DEBUG PASSWORD_RESET: Contraseña cambiada exitosamente")
                    return JsonResponse({
                        'success': True,
                        'message': 'Contraseña actualizada exitosamente'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'Código inválido o expirado'
                    })
                    
            except Usuario.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Error en el proceso'
                })
    
    # GET request - mostrar formulario
    return render(request, 'usuarios/password_reset_modern.html')

def recuperar_con_codigo(request):
    """API para recuperación con código - Alias para password_reset_request"""
    return password_reset_request(request)

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
