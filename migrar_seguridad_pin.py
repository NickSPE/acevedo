"""
Script para mejorar la seguridad del PIN de acceso rápido
Este script migra los PINs de texto plano a hash seguro usando PBKDF2
"""

import os
import sys
import django
from django.core.management.utils import get_random_secret_key
from django.contrib.auth.hashers import make_password, check_password
import json
from datetime import datetime

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FinGest.settings')
django.setup()

from usuarios.models import Usuario

def backup_pins_actuales():
    """Crear backup de los PINs actuales antes de la migración"""
    backup_data = []
    usuarios = Usuario.objects.all()
    
    print(f"📋 Creando backup de {usuarios.count()} usuarios...")
    
    for usuario in usuarios:
        backup_data.append({
            'id': usuario.id,
            'correo': usuario.correo,
            'pin_actual': usuario.pin_acceso_rapido,
            'fecha_backup': datetime.now().isoformat()
        })
    
    backup_filename = f'backup_pins_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(backup_filename, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Backup guardado en: {backup_filename}")
    return backup_filename

def hashear_pin(pin_texto_plano):
    """Convertir PIN de texto plano a hash seguro"""
    return make_password(pin_texto_plano)

def verificar_pin(pin_texto_plano, pin_hasheado):
    """Verificar PIN usando hash"""
    return check_password(pin_texto_plano, pin_hasheado)

def migrar_pins_a_hash():
    """Migrar todos los PINs de texto plano a hash"""
    usuarios = Usuario.objects.all()
    migrados = 0
    errores = 0
    
    print(f"🔄 Iniciando migración de PINs para {usuarios.count()} usuarios...")
    
    for usuario in usuarios:
        try:
            pin_actual = usuario.pin_acceso_rapido
            
            # Verificar si ya está hasheado (los hashes de Django empiezan con pbkdf2_sha256$)
            if pin_actual.startswith('pbkdf2_sha256$'):
                print(f"⏭️  Usuario {usuario.correo}: PIN ya está hasheado")
                continue
            
            # Hashear el PIN actual
            pin_hasheado = hashear_pin(pin_actual)
            
            # Actualizar en la base de datos
            usuario.pin_acceso_rapido = pin_hasheado
            usuario.save()
            
            print(f"✅ Usuario {usuario.correo}: PIN migrado exitosamente")
            migrados += 1
            
        except Exception as e:
            print(f"❌ Error migrando PIN para {usuario.correo}: {e}")
            errores += 1
    
    print(f"\n📊 Resumen de migración:")
    print(f"   - PINs migrados: {migrados}")
    print(f"   - Errores: {errores}")
    print(f"   - Total usuarios: {usuarios.count()}")
    
    return migrados, errores

def test_verificacion_pins():
    """Probar que la verificación de PINs funciona correctamente"""
    print("\n🧪 Probando verificación de PINs...")
    
    # Crear un PIN de prueba
    pin_prueba = "123456"
    pin_hasheado = hashear_pin(pin_prueba)
    
    # Verificar que funciona
    if verificar_pin(pin_prueba, pin_hasheado):
        print("✅ Verificación de PIN funcionando correctamente")
    else:
        print("❌ Error en la verificación de PIN")
        return False
    
    # Verificar que un PIN incorrecto falla
    if not verificar_pin("654321", pin_hasheado):
        print("✅ Verificación de PIN incorrecto funcionando correctamente")
    else:
        print("❌ Error: PIN incorrecto fue aceptado")
        return False
    
    return True

def main():
    print("🔐 Script de Migración de Seguridad de PINs")
    print("=" * 50)
    
    # 1. Crear backup
    backup_file = backup_pins_actuales()
    
    # 2. Probar la funcionalidad de hasheo
    if not test_verificacion_pins():
        print("❌ Las pruebas de verificación fallaron. Deteniendo migración.")
        return
    
    # 3. Confirmar migración
    response = input("\n¿Desea continuar con la migración de PINs? (s/N): ").strip().lower()
    if response != 's':
        print("❌ Migración cancelada por el usuario.")
        return
    
    # 4. Migrar PINs
    migrados, errores = migrar_pins_a_hash()
    
    if errores == 0:
        print(f"\n✅ Migración completada exitosamente!")
        print(f"   - {migrados} PINs migrados")
        print(f"   - Backup guardado en: {backup_file}")
        print("\n⚠️  IMPORTANTE: Debes actualizar el código de las vistas para usar check_password()")
    else:
        print(f"\n⚠️  Migración completada con errores:")
        print(f"   - {migrados} PINs migrados")
        print(f"   - {errores} errores")
        print(f"   - Backup guardado en: {backup_file}")

if __name__ == "__main__":
    main()
