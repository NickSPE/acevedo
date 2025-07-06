from django.urls import path
from . import views


app_name = 'usuarios'
urlpatterns = [
    path('login/', views.Login, name='login'),
    path('login/pin/', views.pin_login, name='pin_login'),
    path('register/', views.Register, name='register'),
    path('register/new/', views.Register, name='register_new'),  # Nueva ruta para el registro simplificado
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('complete-onboarding/', views.complete_onboarding, name='complete_onboarding'),
    path('fix-onboarding/', views.fix_incomplete_onboarding, name='fix_onboarding'),
    path('acceso_rapido/' , views.Acceso_Rapido , name='acceso_rapido'),
    
    # Verificación de correo
    path('verificar-correo/', views.Pagina_Verificar_Correo, name='pagina_verificar_correo'),
    path('verificacion-correo/', views.Verificacion_Correo, name='verificacion_correo'),
    
    # Recuperación de contraseña
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('api/recuperar-con-codigo/', views.recuperar_con_codigo, name='recuperar_con_codigo'),
    
    # URL de prueba
    path('test/', views.test_view, name='test'),
]