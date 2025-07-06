"""
Script para monitorear y debuggear notificaciones duplicadas en tiempo real
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
sys.path.append('c:\\Users\\ZUZUKA\\AppIngRequisitos')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FinGest.settings')
django.setup()

from alertas_notificaciones.models import Notificacion, TipoNotificacion
from gestion_financiera_basica.models import Movimiento
from usuarios.models import Usuario
from django.utils import timezone

def limpiar_duplicados_recientes():
    """Limpia notificaciones duplicadas de las últimas 2 horas"""
    hace_2h = timezone.now() - timedelta(hours=2)
    
    # Encontrar grupos de notificaciones potencialmente duplicadas
    notificaciones = Notificacion.objects.filter(
        fecha_creacion__gte=hace_2h
    ).order_by('usuario', 'tipo_notificacion', 'fecha_creacion')
    
    duplicados_encontrados = []
    grupos = {}
    
    for notif in notificaciones:
        # Crear clave de agrupación
        key = f"{notif.usuario.id}_{notif.tipo_notificacion.nombre}"
        
        # Agregar información específica si está disponible
        if notif.datos_adicionales:
            if 'movimiento_id' in notif.datos_adicionales:
                key += f"_mov_{notif.datos_adicionales['movimiento_id']}"
            elif 'meta_id' in notif.datos_adicionales:
                key += f"_meta_{notif.datos_adicionales['meta_id']}"
        
        if key not in grupos:
            grupos[key] = []
        grupos[key].append(notif)
    
    # Identificar duplicados reales
    for key, notifs in grupos.items():
        if len(notifs) > 1:
            # Verificar si son duplicados reales (mismo contenido en poco tiempo)
            for i in range(len(notifs)):
                for j in range(i + 1, len(notifs)):
                    notif1, notif2 = notifs[i], notifs[j]
                    
                    # Verificar si son duplicados temporales (menos de 5 minutos de diferencia)
                    diff = abs((notif1.fecha_creacion - notif2.fecha_creacion).total_seconds())
                    
                    if diff < 300:  # 5 minutos
                        duplicados_encontrados.append({
                            'notif1': notif1,
                            'notif2': notif2,
                            'diferencia_segundos': diff,
                            'key': key
                        })
    
    return duplicados_encontrados

def mostrar_estadisticas():
    """Muestra estadísticas actuales del sistema"""
    print("=" * 60)
    print(f"MONITOREO DE NOTIFICACIONES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Estadísticas generales
    total = Notificacion.objects.count()
    hoy = Notificacion.objects.filter(fecha_creacion__date=timezone.now().date()).count()
    ultima_hora = Notificacion.objects.filter(
        fecha_creacion__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    print(f"📊 ESTADÍSTICAS GENERALES:")
    print(f"   Total notificaciones: {total}")
    print(f"   Creadas hoy: {hoy}")
    print(f"   Última hora: {ultima_hora}")
    
    # Duplicados
    duplicados = limpiar_duplicados_recientes()
    print(f"\n🔍 ANÁLISIS DE DUPLICADOS:")
    print(f"   Duplicados encontrados: {len(duplicados)}")
    
    if duplicados:
        print("\n⚠️  DUPLICADOS DETECTADOS:")
        for dup in duplicados:
            print(f"   - ID {dup['notif1'].id} y {dup['notif2'].id}")
            print(f"     Usuario: {dup['notif1'].usuario.nombres}")
            print(f"     Tipo: {dup['notif1'].tipo_notificacion.nombre}")
            print(f"     Diferencia: {dup['diferencia_segundos']:.1f} segundos")
            print(f"     Key: {dup['key']}")
            print()
    
    # Últimas 5 notificaciones
    ultimas = Notificacion.objects.order_by('-fecha_creacion')[:5]
    print(f"\n📋 ÚLTIMAS 5 NOTIFICACIONES:")
    for notif in ultimas:
        print(f"   {notif.fecha_creacion.strftime('%H:%M:%S')} - "
              f"{notif.usuario.nombres} - {notif.tipo_notificacion.nombre} - "
              f"ID:{notif.id} - {notif.estado}")
    
    print("=" * 60)

def eliminar_duplicados_reales():
    """Elimina notificaciones duplicadas manteniendo la más reciente"""
    duplicados = limpiar_duplicados_recientes()
    eliminados = 0
    
    for dup in duplicados:
        # Mantener la más reciente, eliminar la más antigua
        if dup['notif1'].fecha_creacion > dup['notif2'].fecha_creacion:
            dup['notif2'].delete()
            print(f"🗑️  Eliminado duplicado ID {dup['notif2'].id}")
        else:
            dup['notif1'].delete()
            print(f"🗑️  Eliminado duplicado ID {dup['notif1'].id}")
        eliminados += 1
    
    return eliminados

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor de notificaciones')
    parser.add_argument('--limpiar', action='store_true', help='Eliminar duplicados')
    parser.add_argument('--continuo', action='store_true', help='Monitoreo continuo')
    
    args = parser.parse_args()
    
    if args.limpiar:
        print("🧹 Limpiando duplicados...")
        eliminados = eliminar_duplicados_reales()
        print(f"✅ Se eliminaron {eliminados} notificaciones duplicadas")
    
    mostrar_estadisticas()
    
    if args.continuo:
        print("\n🔄 Modo monitoreo continuo activado (Ctrl+C para salir)")
        try:
            import time
            while True:
                time.sleep(30)  # Cada 30 segundos
                os.system('cls' if os.name == 'nt' else 'clear')
                mostrar_estadisticas()
        except KeyboardInterrupt:
            print("\n👋 Monitoreo detenido")
