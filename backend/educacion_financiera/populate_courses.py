"""
Script para poblar la base de datos con cursos externos de ejemplo
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FinGest.settings')
django.setup()

from educacion_financiera.models import CursoExterno


def populate_courses():
    """Poblar la base de datos con cursos externos de ejemplo"""
    
    cursos_ejemplo = [
        {
            'titulo': 'Finanzas Personales - Curso Completo',
            'descripcion': 'Aprende a manejar tu dinero de manera inteligente. Curso completo de finanzas personales desde cero.',
            'nivel': 'basico',
            'plataforma': 'youtube',
            'url_externa': 'https://www.youtube.com/watch?v=0lMDd6iX85c&list=PLabB0iEnTHCARV9-O2OzkFlsSli_5NsKn',
            'imagen_url': 'https://img.youtube.com/vi/0lMDd6iX85c/maxresdefault.jpg',
            'duracion_estimada': '8 horas',
            'instructor': 'Finanzas y Proyectos',
            'idioma': 'Español',
            'gratis': True,
            'orden': 1,
        },
        {
            'titulo': 'Educación Financiera Básica',
            'descripcion': 'Conceptos fundamentales de educación financiera para principiantes.',
            'nivel': 'basico',
            'plataforma': 'youtube',
            'url_externa': 'https://www.youtube.com/playlist?list=PLqBLmGEGTI4cjsHiQY-e6BuQGPe0Q_UwQ',
            'duracion_estimada': '4 horas',
            'instructor': 'Platzi',
            'idioma': 'Español',
            'gratis': True,
            'orden': 2,
        },
        {
            'titulo': 'Presupuesto Familiar Efectivo',
            'descripcion': 'Aprende a crear y mantener un presupuesto familiar que realmente funcione.',
            'nivel': 'basico',
            'plataforma': 'youtube',
            'url_externa': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'duracion_estimada': '2 horas',
            'instructor': 'Finanzas Prácticas',
            'idioma': 'Español',
            'gratis': True,
            'orden': 3,
        },
        {
            'titulo': 'Inversiones para Principiantes',
            'descripcion': 'Guía completa para comenzar a invertir tu dinero de manera segura y rentable.',
            'nivel': 'intermedio',
            'plataforma': 'udemy',
            'url_externa': 'https://www.udemy.com/course/inversiones-principiantes/',
            'duracion_estimada': '6 horas',
            'instructor': 'Academia de Inversión',
            'idioma': 'Español',
            'gratis': False,
            'orden': 4,
        },
        {
            'titulo': 'Manejo de Deudas y Crédito',
            'descripcion': 'Estrategias efectivas para eliminar deudas y mejorar tu historial crediticio.',
            'nivel': 'intermedio',
            'plataforma': 'youtube',
            'url_externa': 'https://www.youtube.com/playlist?list=PLrAHZDfL-FDSy3rY5e2t6yy6Ss8K4K5wZ',
            'duracion_estimada': '3 horas',
            'instructor': 'Experto en Crédito',
            'idioma': 'Español',
            'gratis': True,
            'orden': 5,
        },
        {
            'titulo': 'Planificación para el Retiro',
            'descripcion': 'Cómo planificar y asegurar tu futuro financiero para el retiro.',
            'nivel': 'avanzado',
            'plataforma': 'coursera',
            'url_externa': 'https://www.coursera.org/learn/retirement-planning',
            'duracion_estimada': '4 semanas',
            'instructor': 'Universidad Financiera',
            'idioma': 'Español',
            'gratis': False,
            'orden': 6,
        },
        {
            'titulo': 'Criptomonedas y Blockchain',
            'descripcion': 'Introducción al mundo de las criptomonedas y la tecnología blockchain.',
            'nivel': 'avanzado',
            'plataforma': 'platzi',
            'url_externa': 'https://platzi.com/cursos/criptomonedas/',
            'duracion_estimada': '5 horas',
            'instructor': 'Platzi',
            'idioma': 'Español',
            'gratis': False,
            'orden': 7,
        },
        {
            'titulo': 'Emprendimiento y Finanzas',
            'descripcion': 'Finanzas esenciales para emprendedores y pequeños negocios.',
            'nivel': 'intermedio',
            'plataforma': 'youtube',
            'url_externa': 'https://www.youtube.com/playlist?list=PLB6uyJ6wKkPzT5pE-7LFpJ9D2LMh2gTAA',
            'duracion_estimada': '4 horas',
            'instructor': 'Emprende Aprendiendo',
            'idioma': 'Español',
            'gratis': True,
            'orden': 8,
        }
    ]
    
    # Limpiar cursos existentes (opcional)
    respuesta = input("¿Desea eliminar los cursos existentes? (s/n): ")
    if respuesta.lower() == 's':
        CursoExterno.objects.all().delete()
        print("Cursos existentes eliminados.")
    
    # Crear cursos de ejemplo
    creados = 0
    for curso_data in cursos_ejemplo:
        curso, created = CursoExterno.objects.get_or_create(
            titulo=curso_data['titulo'],
            defaults=curso_data
        )
        
        if created:
            creados += 1
            print(f"✅ Curso creado: {curso.titulo}")
        else:
            print(f"⚠️  Curso ya existe: {curso.titulo}")
    
    print(f"\n🎉 Proceso completado. {creados} cursos nuevos creados.")
    print(f"📊 Total de cursos en la base de datos: {CursoExterno.objects.count()}")


if __name__ == "__main__":
    print("🚀 Poblando base de datos con cursos externos...")
    populate_courses()
