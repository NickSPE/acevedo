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
    
    lista_de_usuarios_local = Usuario.objects.all()
    print("\n👥 TODOS LOS USUARIOS EN EL SISTEMA:")
    for i, usuario_local in enumerate(lista_de_usuarios_local, 1):
        print(f"  {i}. {usuario_local.nombres} {usuario_local.apellido_paterno} ({usuario_local.correo})")
        if usuario_local.id_moneda:
            print(f"     Moneda: {usuario_local.id_moneda.simbolo} ({usuario_local.id_moneda.codigo})")
        else:
            print("     Moneda: NO ASIGNADA")
    
    return lista_de_usuarios_local

def cambiar_a_soles(email_usuario):
    """Cambia la moneda del usuario a soles peruanos"""
    try:
        usuario_instance = Usuario.objects.get(correo=email_usuario)
        moneda_soles = Moneda.objects.get(codigo='PEN')
        
        print("\n🔄 CAMBIANDO MONEDA...")
        print(f"Usuario: {usuario_instance.nombres} {usuario_instance.apellido_paterno}")
        print(f"Email: {usuario_instance.correo}")
        print(f"Moneda anterior: {usuario_instance.id_moneda.simbolo if usuario_instance.id_moneda else 'NINGUNA'}")
        print(f"Nueva moneda: {moneda_soles.simbolo} ({moneda_soles.codigo})")
        
        usuario_instance.id_moneda = moneda_soles
        usuario_instance.save()
        
        print("✅ ¡CAMBIADO EXITOSAMENTE!")
        print(f"Ahora {usuario_instance.nombres} tiene la moneda: {moneda_soles.simbolo} (Soles)")
        
        return True
    except Usuario.DoesNotExist:
        print(f"❌ Usuario con email {email_usuario} no encontrado")
        return False
    except Moneda.DoesNotExist:
        print("❌ Moneda PEN (Soles) no encontrada")
        return False

if __name__ == "__main__":
    usuarios = verificar_usuario_actual()
    
    print("\n" + "="*60)
    print("🔧 PARA CAMBIAR A SOLES (S/):")
    print("Copia y pega uno de estos comandos según tu usuario:")
    print()
    
    for usuario in usuarios:
        print(f"# Para {usuario.nombres} {usuario.apellido_paterno}:")
        print(f"# cambiar_a_soles('{usuario.correo}')")
        print()
    
    # Si encuentras el email correcto, descomenta esta línea:
    # cambiar_a_soles('evaristoj108@gmail.com')  # CAMBIAR POR TU EMAIL
