from django.contrib import admin
from .models import CursoExterno, FavoritoCurso

@admin.register(CursoExterno)
class CursoExternoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'plataforma', 'nivel', 'instructor', 'gratis', 'orden', 'activo')
    list_filter = ('plataforma', 'nivel', 'gratis', 'activo', 'idioma')
    search_fields = ('titulo', 'descripcion', 'instructor')
    list_editable = ('orden', 'activo')
    
    fieldsets = (
        (None, {
            'fields': ('titulo', 'descripcion', 'url_externa')
        }),
        ('Información del Curso', {
            'fields': ('plataforma', 'nivel', 'instructor', 'idioma', 'duracion_estimada')
        }),
        ('Configuración', {
            'fields': ('imagen_url', 'gratis', 'orden', 'activo')
        }),
    )

@admin.register(FavoritoCurso)
class FavoritoCursoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'curso', 'fecha_agregado')
    list_filter = ('curso__plataforma', 'fecha_agregado')
    search_fields = ('usuario__username', 'curso__titulo')
    raw_id_fields = ('usuario', 'curso')
