
"""
URL configuration for FinGest project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path , include

urlpatterns = [
    path("administracion/" , include('administracion.urls')),
    path("alertas_notificaciones/" , include('alertas_notificaciones.urls')),
    path("analisis_reportes/" , include('analisis_reportes.urls')),
    path("" , include('core.urls')),
    path("cuentas/" , include('cuentas.urls')),
    path("educacion_financiera/" , include('educacion_financiera.urls')),
    path("gestion_financiera_basica/" , include('gestion_financiera_basica.urls')),
    path("usuarios/" , include('usuarios.urls')),
]