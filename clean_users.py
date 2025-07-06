#!/usr/bin/env python
"""
Script para limpiar usuarios registrados
"""
import os
import sys
import django
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FinGest.settings')
django.setup()

from usuarios.models import Usuario
from cuentas.models import Cuenta

def clean_all_users():
    """Limpiar todos los usuarios registrados"""
    print("🔍 LIMPIANDO TODOS LOS USUARIOS REGISTRADOS")
    print("="*50)
    
    try:
        # Contar usuarios antes de limpiar
        total_usuarios = Usuario.objects.count()
        total_cuentas = Cuenta.objects.count()
        
        print(f"📊 Usuarios encontrados: {total_usuarios}")
        print(f"📊 Cuentas encontradas: {total_cuentas}")
        
        if total_usuarios == 0:
            print("✅ No hay usuarios para limpiar")
            return
        
        # Mostrar lista de usuarios
        print("\n📋 Lista de usuarios a eliminar:")
        usuarios = Usuario.objects.all()
        for i, usuario in enumerate(usuarios, 1):
            print(f"  {i}. {usuario.nombres} {usuario.apellido_paterno} ({usuario.correo})")
            print(f"     - Email verificado: {usuario.email_verificado}")
            print(f"     - Onboarding completo: {usuario.onboarding_completed}")
            print(f"     - PIN: {usuario.pin_acceso_rapido}")
        
        # Confirmar eliminación
        respuesta = input(f"\n⚠️  ¿Estás seguro de eliminar {total_usuarios} usuario(s)? (s/N): ").strip().lower()
        
        if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
            print("\n🗑️  Eliminando usuarios...")
            
            # Eliminar usuarios (las cuentas se eliminan automáticamente por CASCADE)
            usuarios_eliminados = Usuario.objects.all().delete()
            
            print(f"✅ {usuarios_eliminados[0]} usuario(s) eliminado(s)")
            print(f"✅ {usuarios_eliminados[1].get('cuentas.Cuenta', 0)} cuenta(s) eliminada(s)")
            print(f"✅ Base de datos limpia")
            
            # Verificar que está vacía
            remaining_users = Usuario.objects.count()
            remaining_accounts = Cuenta.objects.count()
            
            print(f"\n📊 Usuarios restantes: {remaining_users}")
            print(f"📊 Cuentas restantes: {remaining_accounts}")
            
            if remaining_users == 0 and remaining_accounts == 0:
                print("🎉 Limpieza completada exitosamente")
            else:
                print("⚠️  Algunos registros no se eliminaron completamente")
                
        else:
            print("❌ Operación cancelada")
            
    except Exception as e:
        print(f"❌ Error durante la limpieza: {str(e)}")
        import traceback
        traceback.print_exc()

def clean_test_users_only():
    """Limpiar solo usuarios de prueba"""
    print("🔍 LIMPIANDO SOLO USUARIOS DE PRUEBA")
    print("="*50)
    
    try:
        # Definir emails de prueba
        test_emails = [
            'test@fingest.com',
            'onboarding@test.com',
            'newflow@test.com',
            'incomplete@test.com',
            'returning@test.com',
            'evaristojara1981@gmail.com'  # Email real usado en pruebas
        ]
        
        usuarios_prueba = Usuario.objects.filter(correo__in=test_emails)
        count = usuarios_prueba.count()
        
        if count == 0:
            print("✅ No hay usuarios de prueba para eliminar")
            return
        
        print(f"📊 Usuarios de prueba encontrados: {count}")
        
        for usuario in usuarios_prueba:
            print(f"  - {usuario.nombres} {usuario.apellido_paterno} ({usuario.correo})")
        
        respuesta = input(f"\n⚠️  ¿Eliminar {count} usuario(s) de prueba? (s/N): ").strip().lower()
        
        if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
            eliminados = usuarios_prueba.delete()
            print(f"✅ {eliminados[0]} usuario(s) de prueba eliminado(s)")
            print("🎉 Usuarios de prueba limpiados")
        else:
            print("❌ Operación cancelada")
            
    except Exception as e:
        print(f"❌ Error eliminando usuarios de prueba: {str(e)}")

def show_user_stats():
    """Mostrar estadísticas de usuarios"""
    print("📊 ESTADÍSTICAS DE USUARIOS")
    print("="*30)
    
    total_usuarios = Usuario.objects.count()
    usuarios_verificados = Usuario.objects.filter(email_verificado=True).count()
    usuarios_onboarding_completo = Usuario.objects.filter(onboarding_completed=True).count()
    total_cuentas = Cuenta.objects.count()
    
    print(f"👥 Total de usuarios: {total_usuarios}")
    print(f"✅ Usuarios verificados: {usuarios_verificados}")
    print(f"🎯 Onboarding completo: {usuarios_onboarding_completo}")
    print(f"🏦 Total de cuentas: {total_cuentas}")
    
    if total_usuarios > 0:
        print(f"\n📈 Porcentajes:")
        print(f"   - Verificados: {(usuarios_verificados/total_usuarios)*100:.1f}%")
        print(f"   - Onboarding completo: {(usuarios_onboarding_completo/total_usuarios)*100:.1f}%")

if __name__ == "__main__":
    # Mostrar estadísticas primero
    show_user_stats()
    
    if Usuario.objects.count() > 0:
        print("\n" + "="*50)
        print("OPCIONES DE LIMPIEZA:")
        print("1. Limpiar TODOS los usuarios")
        print("2. Limpiar solo usuarios de prueba")
        print("3. Solo mostrar estadísticas")
        print("4. Salir")
        
        opcion = input("\nSelecciona una opción (1-4): ").strip()
        
        if opcion == "1":
            clean_all_users()
        elif opcion == "2":
            clean_test_users_only()
        elif opcion == "3":
            print("✅ Solo mostrando estadísticas")
        elif opcion == "4":
            print("👋 Saliendo...")
        else:
            print("❌ Opción inválida")
    else:
        print("\n✅ No hay usuarios registrados para limpiar")
