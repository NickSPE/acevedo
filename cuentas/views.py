from django.contrib.auth.decorators import login_required
from django.shortcuts import render , redirect
from django.http import HttpResponse
from usuarios.models import Usuario

import base64
from PIL import Image
import io

""" Views App CUENTAS """
@login_required
def profile(request):
    user_id = request.user.id

    if(request.method == "POST"):
        nombres = request.POST.get("nombres")
        apellido_paterno = request.POST.get("apellido_paterno")
        apellido_materno = request.POST.get("apellido_materno")
        email = request.POST.get("email")
        telefono = request.POST.get("telefono")
        imagen_perfil = request.FILES.get("imagen_perfil")

        usuario = Usuario.objects.filter(id=user_id).update(
            nombres = nombres,
            apellido_paterno = apellido_paterno,
            apellido_materno = apellido_materno,
            correo = email,
            telefono = telefono,
            imagen_perfil = imagen_perfil,
        )
        return redirect("cuentas:perfil")

    usuario = Usuario.objects.get(id=user_id)
    formato_imagen = None
    imagen_base64 = None
    if(usuario.imagen_perfil):
        imagen_bytes = usuario.imagen_perfil
        imagen_base64 = base64.b64encode(imagen_bytes).decode('utf-8')

        formato_imagen = Image.open(io.BytesIO(imagen_bytes)).format

    tab = request.GET.get("tab", "general")
    return render(request, "cuentas/profile.html", {
        "tab": tab , 
        "usuario": usuario,
        "imagen_perfil": imagen_base64,
        "formato_imagen": formato_imagen,
    })

@login_required
def settings(request):
    return render(request, "cuentas/settings.html")