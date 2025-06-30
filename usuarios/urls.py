from django.urls import path
from . import views


app_name = 'usuarios'
urlpatterns = [
    path('login/', views.Login, name='login'),
    path('register/', views.Register, name='register'),
    path('pagina_verificar_correo/' , views.Pagina_Verificar_Correo , name='pagina_verificar_correo'),
    path('verificacion_correo/' , views.Verificacion_Correo , name='verificacion_correo'),
]