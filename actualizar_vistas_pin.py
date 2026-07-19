"""
Script para actualizar automáticamente las vistas que manejan PINs
Reemplaza las comparaciones de texto plano por verificación segura con hash
"""

import re
import os
from datetime import datetime

def create_backup(file_path):
    """Crear backup de un archivo antes de modificarlo"""
    allowed_files = {"view1.sql", "view2.sql", "views_pin.sql"}
    base_name = os.path.basename(file_path)
    if base_name not in allowed_files:
        raise ValueError(f"File '{base_name}' is not permitted for backup")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"{base_name}.backup_{timestamp}"
    backup_path = os.path.join(os.path.dirname(file_path), backup_filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return backup_path

def update_usuarios_views():
    """Actualizar usuarios/views.py para usar verificación segura de PIN"""
    file_path = r"c:\Users\ZUZUKA\AppIngRequisitos\usuarios\views.py"
    
    # Crear backup
    backup_path = create_backup(file_path)
    print(f"📋 Backup creado: {backup_path}")
    
    # Leer archivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Agregar import necesario al inicio del archivo
    if 'from django.contrib.auth.hashers import make_password, check_password' not in content:
        # Buscar las otras importaciones de Django
        import_pattern = r'(from django\.contrib\.auth import[^\n]*\n)'
        replacement = r'\1from django.contrib.auth.hashers import make_password, check_password\n'
        content = re.sub(import_pattern, replacement, content)
    
    # Actualizar verificación de PIN en acceso_rapido
    replacement1 = 'if check_password(pin_input, usuario.pin_acceso_rapido):'
    content = content.replace('if str(usuario.pin_acceso_rapido) == pin_input:', replacement1)
    
    # Actualizar búsqueda de usuario por PIN en pin_login
    replacement2 = '''# Buscar usuario que tenga este PIN (necesario iterar porque está hasheado)
            usuario = None
            for u in Usuario.objects.all():
                if check_password(pin_input, u.pin_acceso_rapido):
                    usuario = u
                    break'''
    content = content.replace('usuario = Usuario.objects.filter(pin_acceso_rapido=pin_input).first()', replacement2)
    
    # Actualizar creación de usuario para hashear el PIN
    replacement3 = 'pin_acceso_rapido=make_password(pin_acceso_rapido or \'000000\'),'
    content = content.replace("pin_acceso_rapido=pin_acceso_rapido or '000000',", replacement3)
    
    # Buscar otra instancia similar
    replacement4 = 'pin_acceso_rapido=make_password(data[\'pin_acceso_rapido\']),'
    content = content.replace("pin_acceso_rapido=data['pin_acceso_rapido'],", replacement4)
    
    # Escribir archivo actualizado
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ usuarios/views.py actualizado")

def update_cuentas_views():
    """Actualizar cuentas/views.py para usar verificación segura de PIN"""
    file_path = r"c:\Users\ZUZUKA\AppIngRequisitos\cuentas\views.py"
    
    # Crear backup
    backup_path = create_backup(file_path)
    print(f"📋 Backup creado: {backup_path}")
    
    # Leer archivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Agregar import necesario
    if 'from django.contrib.auth.hashers import make_password, check_password' not in content:
        import_pattern = r'(from django\.contrib\.auth import[^\n]*\n)'
        replacement = r'\1from django.contrib.auth.hashers import make_password, check_password\n'
        content = re.sub(import_pattern, replacement, content)
    
    # Actualizar verificación del PIN actual
    replacement1 = 'if not check_password(current_pin, usuario.pin_acceso_rapido):'
    content = content.replace('if str(usuario.pin_acceso_rapido) != current_pin:', replacement1)
    
    # Actualizar verificación de unicidad de PIN (esta es más compleja)
    replacement2 = '''# Verificar que el nuevo PIN no esté siendo usado por otro usuario
            pin_duplicado = False
            for u in Usuario.objects.exclude(id=usuario.id):
                if check_password(new_pin, u.pin_acceso_rapido):
                    pin_duplicado = True
                    break
            
            if pin_duplicado:'''
    content = content.replace('if Usuario.objects.filter(pin_acceso_rapido=new_pin).exclude(id=usuario.id).exists():', replacement2)
    
    # Actualizar asignación del nuevo PIN
    replacement3 = 'usuario.pin_acceso_rapido = make_password(new_pin)'
    content = content.replace('usuario.pin_acceso_rapido = new_pin', replacement3)
    
    # Escribir archivo actualizado
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ cuentas/views.py actualizado")

def update_model_comments():
    """Actualizar comentarios en el modelo para reflejar el cambio de seguridad"""
    file_path = r"c:\Users\ZUZUKA\AppIngRequisitos\usuarios\models.py"
    
    # Crear backup
    backup_path = create_backup(file_path)
    print(f"📋 Backup creado: {backup_path}")
    
    # Leer archivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Actualizar comentario del campo PIN
    replacement = 'pin_acceso_rapido = models.CharField(max_length=128, default=\'000000\')  # PIN hasheado con PBKDF2'
    content = content.replace("pin_acceso_rapido = models.CharField(max_length=6, default='000000')  # PIN de 6 dígitos exactos", replacement)
    
    # Escribir archivo actualizado
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ usuarios/models.py actualizado")

def create_migration_command():
    """Crear comando para generar migración de Django"""
    migration_content = '''"""
Comando para generar la migración de Django después de actualizar el modelo
Ejecutar en el terminal dentro del proyecto:
"""

# 1. Generar migración
python manage.py makemigrations usuarios --name "update_pin_field_length"

# 2. Aplicar migración
python manage.py migrate

# 3. Ejecutar script de migración de seguridad
python migrar_seguridad_pin.py
'''
    
    with open('comandos_migracion.txt', 'w', encoding='utf-8') as f:
        f.write(migration_content)
    
    print("✅ Comandos de migración guardados en: comandos_migracion.txt")

def main():
    print("🔧 Script de Actualización de Seguridad de PINs")
    print("=" * 50)
    
    try:
        # Actualizar archivos
        update_model_comments()
        update_usuarios_views()
        update_cuentas_views()
        create_migration_command()
        
        print("\n✅ Actualización completada exitosamente!")
        print("\nPróximos pasos:")
        print("1. Revisar los archivos actualizados")
        print("2. Ejecutar: python manage.py makemigrations usuarios")
        print("3. Ejecutar: python manage.py migrate")
        print("4. Ejecutar: python migrar_seguridad_pin.py")
        print("\n⚠️  IMPORTANTE: Probar en entorno de desarrollo antes de producción")
        
    except Exception as e:
        print(f"❌ Error durante la actualización: {e}")

if __name__ == "__main__":
    main()
