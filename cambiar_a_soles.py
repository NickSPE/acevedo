#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.append('c:/Users/ZUZUKA/AppIngRequisitos')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FinGest.settings')
django.setup()

from usuarios.models import Usuario
from cuentas.models import Moneda

def verificar_usuario_actual():
    """Busca el usuario más probable que estés usando"""
    
    print("🔍 BUSCANDO TU USUARIO...")
    
    # Buscar usuarios con nombres comunes
    posibles_usuarios = [
        'evaristoj108@gmail.com',
        'evaristo',
        'nick',
        'usuario',
        'test',
        'admin'
    ]
    
    usuarios = Usuario.objects.all()
    print(f"\n👥 TODOS LOS USUARIOS EN EL SISTEMA:")
    for i, usuario in enumerate(usuarios, 1):
        print(f"  {i}. {usuario.nombres} {usuario.apellido_paterno} ({usuario.correo})")
        if usuario.id_moneda:
            print(f"     Moneda: {usuario.id_moneda.simbolo} ({usuario.id_moneda.codigo})")
        else:
            print(f"     Moneda: NO ASIGNADA")
    
    return usuarios

def cambiar_a_soles(email_usuario):
    """Cambia la moneda del usuario a soles peruanos"""
    try:
        usuario = Usuario.objects.get(correo=email_usuario)
        moneda_soles = Moneda.objects.get(codigo='PEN')
        
        print(f"\n🔄 CAMBIANDO MONEDA...")
        print(f"Usuario: {usuario.nombres} {usuario.apellido_paterno}")
        print(f"Email: {usuario.correo}")
        print(f"Moneda anterior: {usuario.id_moneda.simbolo if usuario.id_moneda else 'NINGUNA'}")
        print(f"Nueva moneda: {moneda_soles.simbolo} ({moneda_soles.codigo})")
        
        usuario.id_moneda = moneda_soles
        usuario.save()
        
        print(f"✅ ¡CAMBIADO EXITOSAMENTE!")
        print(f"Ahora {usuario.nombres} tiene la moneda: {moneda_soles.simbolo} (Soles)")
        
        return True
    except Usuario.DoesNotExist:
        print(f"❌ Usuario con email {email_usuario} no encontrado")
        return False
    except Moneda.DoesNotExist:
        print(f"❌ Moneda PEN (Soles) no encontrada")
        return False

if __name__ == "__main__":
    usuarios = verificar_usuario_actual()
    
    print(f"\n" + "="*60)
    print("🔧 PARA CAMBIAR A SOLES (S/):")
    print("Copia y pega uno de estos comandos según tu usuario:")
    print()
    
    for usuario in usuarios:
        print(f"# Para {usuario.nombres} {usuario.apellido_paterno}:")
        print(f"# cambiar_a_soles('{usuario.correo}')")
        print()
    
    # Si encuentras el email correcto, descomenta esta línea:
    # cambiar_a_soles('evaristoj108@gmail.com')  # CAMBIAR POR TU EMAIL
