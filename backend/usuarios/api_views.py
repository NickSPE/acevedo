import secrets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import datetime

from .models import Usuario
from cuentas.models import Moneda, Cuenta
from .api_serializers import UsuarioSerializer, RegistroUsuarioSerializer

class SendVerificationCodeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        correo = request.data.get('correo')
        nombres = request.data.get('nombres')

        if not correo or not nombres:
            return Response({
                'success': False,
                'error': 'Correo y nombres son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)

        if Usuario.objects.filter(correo=correo).exists():
            return Response({
                'success': False,
                'error': 'El correo ya está registrado'
            }, status=status.HTTP_400_BAD_REQUEST)

        PIN = str(secrets.randbelow(900000) + 100000)
        request.session['pin_verification'] = PIN
        request.session['email_for_verification'] = correo

        try:
            send_mail(
                subject='Código de verificación - FinGest',
                message=f'Hola {nombres},\n\nTu código de verificación para registrarte en FinGest es: {PIN}\n\nEste código expira en 10 minutos.\n\n¡Gracias por unirte a FinGest!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[correo],
                fail_silently=False,
            )
            return Response({
                'success': True,
                'message': 'Código enviado exitosamente'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error al enviar el código: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RegistroUsuarioView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegistroUsuarioSerializer(data=request.data)
        if serializer.is_valid():
            # Validar PIN si se tiene en la sesión
            verification_code = request.data.get('codigo_verificacion')
            session_pin = request.session.get('pin_verification')
            session_email = request.session.get('email_for_verification')
            correo = request.data.get('correo')

            # Si es a través de API y no hay sesión (ej. Front desacoplado),
            # podemos permitir omitir la verificación de sesión en fase REST si se provee el código
            # o si el front-end maneja su propia lógica. Por compatibilidad estricta:
            if session_pin and session_email:
                if session_email != correo:
                    return Response({'error': 'El correo no coincide con la sesión de verificación.'}, status=status.HTTP_400_BAD_REQUEST)
                if verification_code != session_pin:
                    return Response({'error': 'Código de verificación incorrecto.'}, status=status.HTTP_400_BAD_REQUEST)

            usuario = serializer.save()
            
            # Limpiar sesión
            if 'pin_verification' in request.session:
                del request.session['pin_verification']
            if 'email_for_verification' in request.session:
                del request.session['email_for_verification']

            return Response({
                'success': True,
                'message': f'¡Registro exitoso! Ahora inicia sesión con tu nueva cuenta.',
                'usuario': UsuarioSerializer(usuario).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UsuarioSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CompleteOnboardingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        usuario = request.user
        data = request.data

        if data.get('skipped'):
            usuario.onboarding_completed = True
            usuario.save()
            return Response({'success': True, 'message': 'Onboarding saltado'})

        pin_acceso_rapido = data.get('pin_acceso_rapido', '').strip()
        if pin_acceso_rapido and len(pin_acceso_rapido) == 6 and pin_acceso_rapido.isdigit():
            usuario.pin_acceso_rapido = pin_acceso_rapido

        telefono = data.get('telefono', '').strip()
        if telefono:
            try:
                usuario.telefono = int(telefono)
            except ValueError:
                return Response({'error': 'Teléfono inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        saldo_inicial = data.get('saldo_inicial', '').strip()
        nombre_cuenta = data.get('nombre_cuenta', '').strip()

        if saldo_inicial or nombre_cuenta:
            cuenta = Cuenta.objects.filter(id_usuario=usuario).first()
            if cuenta:
                if saldo_inicial:
                    try:
                        cuenta.saldo_cuenta = float(saldo_inicial)
                    except ValueError:
                        return Response({'error': 'Saldo inválido.'}, status=status.HTTP_400_BAD_REQUEST)
                if nombre_cuenta:
                    cuenta.nombre = nombre_cuenta
                cuenta.save()

        usuario.onboarding_completed = True
        usuario.save()
        return Response({'success': True, 'message': 'Onboarding completado exitosamente'})

class ValidateAccesoRapidoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        pin_input = request.data.get('pin_input', '')
        usuario = request.user

        if not pin_input.isdigit() or len(pin_input) != 6:
            return Response({'success': False, 'error': 'PIN inválido. Ingrese 6 dígitos numéricos.'}, status=status.HTTP_400_BAD_REQUEST)

        if str(usuario.pin_acceso_rapido) == pin_input:
            request.session['pin_acceso_rapido_validado'] = True
            return Response({'success': True, 'message': 'PIN validado exitosamente.'})
        return Response({'success': False, 'error': 'El PIN ingresado es incorrecto.'}, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        action = request.data.get('action', '')

        if action == 'send_code':
            try:
                usuario = Usuario.objects.get(correo=email)
                codigo_recuperacion = str(secrets.randbelow(900000) + 100000)
                usuario.codigo_recuperacion = codigo_recuperacion
                usuario.codigo_expiracion = timezone.now() + datetime.timedelta(minutes=15)
                usuario.save()

                send_mail(
                    subject='Código de recuperación - FinGest',
                    message=f'Hola {usuario.nombres},\n\nTu código de recuperación de contraseña para FinGest es: {codigo_recuperacion}\n\nEste código expira en 15 minutos.\n\nSi no solicitaste este cambio, ignora este mensaje.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                return Response({'success': True, 'message': 'Código de recuperación enviado a tu email'})
            except Usuario.DoesNotExist:
                return Response({'success': True, 'message': 'Si tu email está registrado, recibirás un código de recuperación'})
            except Exception as e:
                return Response({'success': False, 'message': f'Error al enviar el código: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif action == 'verify_code':
            codigo = request.data.get('codigo', '').strip()
            try:
                usuario = Usuario.objects.get(correo=email)
                if (usuario.codigo_recuperacion == codigo and 
                    usuario.codigo_expiracion and 
                    usuario.codigo_expiracion > timezone.now()):
                    return Response({'success': True, 'message': 'Código verificado correctamente'})
                return Response({'success': False, 'message': 'Código inválido o expirado'}, status=status.HTTP_400_BAD_REQUEST)
            except Usuario.DoesNotExist:
                return Response({'success': False, 'message': 'Error en la verificación'}, status=status.HTTP_400_BAD_REQUEST)

        elif action == 'reset_password':
            codigo = request.data.get('codigo', '').strip()
            nueva_password = request.data.get('nueva_password')
            try:
                usuario = Usuario.objects.get(correo=email)
                if (usuario.codigo_recuperacion == codigo and 
                    usuario.codigo_expiracion and 
                    usuario.codigo_expiracion > timezone.now()):
                    
                    if nueva_password:
                        usuario.set_password(nueva_password)
                    usuario.codigo_recuperacion = None
                    usuario.codigo_expiracion = None
                    usuario.save()
                    return Response({'success': True, 'message': 'Contraseña actualizada exitosamente'})
                return Response({'success': False, 'message': 'Código inválido o expirado'}, status=status.HTTP_400_BAD_REQUEST)
            except Usuario.DoesNotExist:
                return Response({'success': False, 'message': 'Error en el proceso'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Acción no permitida'}, status=status.HTTP_400_BAD_REQUEST)

from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

class CustomLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('correo', '').strip().lower()
        password = request.data.get('password', '')

        if not email or not password:
            return Response({'error': 'Correo y contraseña son requeridos.'}, status=status.HTTP_400_BAD_REQUEST)

        # Buscar usuario por correo
        try:
            user = Usuario.objects.get(correo=email)
        except Usuario.DoesNotExist:
            return Response({'error': 'Credenciales incorrectas.'}, status=status.HTTP_401_UNAUTHORIZED)

        # Autenticar
        if user.check_password(password):
            if not user.is_active:
                return Response({'error': 'Esta cuenta ha sido desactivada.'}, status=status.HTTP_403_FORBIDDEN)
            
            # Generar tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            
            response = Response({
                'success': True,
                'access_token': access_token,
                'usuario': UsuarioSerializer(user).data
            }, status=status.HTTP_200_OK)

            # Asignar cookie segura HttpOnly
            response.set_cookie(
                key='refresh_token',
                value=str(refresh),
                httponly=True,
                secure=False,  # En localhost usar False, True en prod con HTTPS
                samesite='Lax',
                max_age=7 * 24 * 60 * 60  # 7 días
            )
            return response
        else:
            return Response({'error': 'Credenciales incorrectas.'}, status=status.HTTP_401_UNAUTHORIZED)

class CustomTokenRefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'error': 'Refresh token no encontrado.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            
            response = Response({
                'success': True,
                'access_token': access_token
            }, status=status.HTTP_200_OK)

            # Rotar el token si SIMPLE_JWT['ROTATE_REFRESH_TOKENS'] está activo
            # Para mayor seguridad, refrescamos la cookie
            response.set_cookie(
                key='refresh_token',
                value=str(refresh),
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=7 * 24 * 60 * 60
            )
            return response
        except TokenError as e:
            return Response({'error': 'Token inválido o expirado.', 'detail': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class CustomLogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        response = Response({
            'success': True,
            'message': 'Sesión cerrada exitosamente.'
        }, status=status.HTTP_200_OK)
        
        # Eliminar cookie de refresh token
        response.delete_cookie('refresh_token')
        return response

class PINLoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        pin_input = request.data.get('pin_input', '').strip()
        if not pin_input or not pin_input.isdigit() or len(pin_input) != 6:
            return Response({'error': 'PIN inválido. Debe tener exactamente 6 dígitos numéricos.'}, status=status.HTTP_400_BAD_REQUEST)
        
        usuario = Usuario.objects.filter(pin_acceso_rapido=pin_input).first()
        if not usuario:
            return Response({'error': 'PIN incorrecto o usuario no registrado.'}, status=status.HTTP_401_UNAUTHORIZED)
            
        if not usuario.is_active:
            return Response({'error': 'Esta cuenta ha sido desactivada.'}, status=status.HTTP_403_FORBIDDEN)
            
        refresh = RefreshToken.for_user(usuario)
        access_token = str(refresh.access_token)
        
        response = Response({
            'success': True,
            'access_token': access_token,
            'usuario': UsuarioSerializer(usuario).data
        }, status=status.HTTP_200_OK)

        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=7 * 24 * 60 * 60
        )
        return response


