"""Funciones utilitarias para la app educacion_financiera"""

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import FavoritoCurso


def marcar_favoritos(cursos, usuario):
    """
    Marca los cursos favoritos del usuario.
    
    Args:
        cursos: QuerySet de CursoExterno
        usuario: Usuario actual
    
    Returns:
        QuerySet con atributo 'es_favorito' agregado a cada curso
    """
    favoritos_ids = FavoritoCurso.objects.filter(usuario=usuario).values_list('curso_id', flat=True)
    for curso in cursos:
        curso.es_favorito = curso.id in favoritos_ids
    return cursos


def paginar_cursos(cursos, page_number, items_per_page=6):
    """
    Pagina los cursos y maneja excepciones.
    
    Args:
        cursos: QuerySet de CursoExterno
        page_number: Número de página (puede venir de GET)
        items_per_page: Cantidad de items por página (default: 6)
    
    Returns:
        Tupla (paginator, cursos_pagina)
    """
    paginator = Paginator(cursos, items_per_page)
    
    try:
        cursos_pagina = paginator.page(page_number)
    except PageNotAnInteger:
        # Si page no es un entero, mostrar la primera página
        cursos_pagina = paginator.page(1)
    except EmptyPage:
        # Si page está fuera de rango, mostrar la última página
        cursos_pagina = paginator.page(paginator.num_pages)
    
    return paginator, cursos_pagina
