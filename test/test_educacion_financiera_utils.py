"""
Tests unitarios para las utilidades de la aplicación educacion_financiera
Ubicación: test/test_educacion_financiera_utils.py
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from educacion_financiera.models import CursoExterno, FavoritoCurso
from educacion_financiera.utils import marcar_favoritos, paginar_cursos
from cuentas.models import Moneda

Usuario = get_user_model()


class EducacionFinancieraUtilsTestCase(TestCase):
    def setUp(self):
        # Crear moneda de prueba
        self.moneda = Moneda.objects.create(
            codigo='PEN',
            nombre='Soles',
            simbolo='S/.'
        )

        # Crear usuario
        self.usuario = Usuario.objects.create_user(
            correo='test_edu_utils@test.com',
            password='Password123!',
            nombres='Juan',
            apellido_paterno='Perez',
            documento_identidad='12345678',
            telefono=999999999,
            id_moneda=self.moneda
        )

        # Crear cursos de prueba (10 cursos para poder probar paginación)
        self.cursos = []
        for i in range(1, 11):
            curso = CursoExterno.objects.create(
                titulo=f'Curso Finanzas {i}',
                descripcion=f'Descripción del curso {i}',
                nivel='basico' if i % 2 == 0 else 'intermedio',
                plataforma='youtube',
                url_externa='https://www.youtube.com/watch?v=123',
                duracion_estimada='2 horas',
                gratis=True,
                orden=i
            )
            self.cursos.append(curso)

        # Marcar los cursos pares como favoritos
        for i, curso in enumerate(self.cursos):
            if (i + 1) % 2 == 0:
                FavoritoCurso.objects.create(
                    usuario=self.usuario,
                    curso=curso
                )

    def test_marcar_favoritos(self):
        """Valida que se agregue dinámicamente el atributo es_favorito con el booleano correcto"""
        cursos_queryset = CursoExterno.objects.all()
        cursos_marcados = marcar_favoritos(cursos_queryset, self.usuario)
        
        # Deben mantener el mismo tamaño
        self.assertEqual(len(cursos_marcados), 10)
        
        # Verificar que los impares tengan es_favorito = False y pares = True
        for i, curso in enumerate(cursos_marcados):
            es_par = (i + 1) % 2 == 0
            self.assertEqual(curso.es_favorito, es_par)

    def test_paginar_cursos_valid_page(self):
        """Valida paginación correcta con una página válida"""
        cursos_queryset = CursoExterno.objects.all().order_by('orden')
        
        # Paginar página 1, 3 items por página
        paginator, pagina = paginar_cursos(cursos_queryset, page_number=1, items_per_page=3)
        
        self.assertEqual(paginator.num_pages, 4) # 10 items / 3 = 4 páginas
        self.assertEqual(len(pagina.object_list), 3)
        self.assertEqual(pagina.object_list[0].titulo, 'Curso Finanzas 1')
        self.assertEqual(pagina.object_list[2].titulo, 'Curso Finanzas 3')

    def test_paginar_cursos_non_integer_page(self):
        """Valida que si se pasa una página inválida (no entera), devuelva la primera página"""
        cursos_queryset = CursoExterno.objects.all().order_by('orden')
        
        _, pagina = paginar_cursos(cursos_queryset, page_number='invalido', items_per_page=4)
        
        # Debe reaccionar devolviendo la página 1
        self.assertEqual(pagina.number, 1)
        self.assertEqual(len(pagina.object_list), 4)

    def test_paginar_cursos_empty_page(self):
        """Valida que si se pasa una página fuera de rango, devuelva la última página"""
        cursos_queryset = CursoExterno.objects.all().order_by('orden')
        
        # Pasamos página 99, solo hay 3 páginas si dividimos de a 4 items
        _, pagina = paginar_cursos(cursos_queryset, page_number=99, items_per_page=4)
        
        # Debe devolver la última página (página 3, ya que hay 10 items total)
        self.assertEqual(pagina.number, 3)
        self.assertEqual(len(pagina.object_list), 2) # última página tiene 2 items (8 + 2 = 10)
        self.assertEqual(pagina.object_list[0].titulo, 'Curso Finanzas 9')
        self.assertEqual(pagina.object_list[1].titulo, 'Curso Finanzas 10')
