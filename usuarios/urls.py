from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # Autenticación básica
    path('login/', views.Login, name='login'),
    path('register/', views.Register, name='register'),
    path('register/new/', views.Register, name='register_new'),  # Alias para el registro simplificado
    path('register/simple/', views.Register, name='register_simple'),  # URL para el registro simplificado
    
    # Login alternativo
    path('login/pin/', views.pin_login, name='pin_login'),
    path('acceso-rapido/', views.Acceso_Rapido, name='acceso_rapido'),
    
    # Verificación de correo electrónico
    path('verificar-correo/', views.Pagina_Verificar_Correo, name='pagina_verificar_correo'),
    path('verificacion-correo/', views.Verificacion_Correo, name='verificacion_correo'),
    
    # Recuperación de contraseña
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/modern/', views.password_reset_request, name='password_reset_modern'),
    path('api/recuperar-con-codigo/', views.recuperar_con_codigo, name='recuperar_con_codigo'),
    path('reestablecer-contrasena/', views.Reestablecer_Contraseña, name='reestablecer_contrasena'),
    
    # Onboarding
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('complete-onboarding/', views.complete_onboarding, name='complete_onboarding'),
    path('fix-onboarding/', views.fix_incomplete_onboarding, name='fix_onboarding'),
    
    # Utilidades y pruebas
    path('test/', views.test_view, name='test'),
    
    # Perfil y configuración de usuario (futuras)
    # path('profile/', views.profile_view, name='profile'),
    # path('settings/', views.settings_view, name='settings'),
    # path('logout/', views.logout_view, name='logout'),
    
    # APIs internas para AJAX
    # path('api/check-email/', views.check_email_availability, name='check_email'),
    # path('api/resend-verification/', views.resend_verification_email, name='resend_verification'),
    # path('api/validate-pin/', views.validate_pin_format, name='validate_pin'),
]
