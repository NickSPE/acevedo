from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class CursoExterno(models.Model):
    """Modelo para cursos externos (YouTube, Udemy, etc.)"""
    NIVEL_CHOICES = [
        ('basico', 'Básico'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
    ]
    
    PLATAFORMA_CHOICES = [
        ('youtube', 'YouTube'),
        ('udemy', 'Udemy'),
        ('coursera', 'Coursera'),
        ('khan_academy', 'Khan Academy'),
        ('edx', 'edX'),
        ('platzi', 'Platzi'),
        ('otro', 'Otro'),
    ]
    
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='basico')
    plataforma = models.CharField(max_length=20, choices=PLATAFORMA_CHOICES, default='youtube')
    url_externa = models.URLField(help_text="Link al curso externo")
    imagen_url = models.URLField(blank=True, null=True, help_text="URL de imagen/thumbnail")
    duracion_estimada = models.CharField(max_length=50, help_text="ej: '2 horas', '10 videos'")
    instructor = models.CharField(max_length=100, blank=True)
    idioma = models.CharField(max_length=20, default='Español')
    gratis = models.BooleanField(default=True, help_text="¿Es gratuito?")
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['orden', 'titulo']
        verbose_name = 'Curso Externo'
        verbose_name_plural = 'Cursos Externos'
    
    def __str__(self):
        return f"{self.titulo} ({self.get_plataforma_display()})"
    
    @property
    def plataforma_icon(self):
        """Retorna el ícono correspondiente a la plataforma"""
        icons = {
            'youtube': '📺',
            'udemy': '💻',
            'coursera': '🎓',
            'khan_academy': '📚',
            'edx': '🏛️',
            'platzi': '�',
            'otro': '🌐'
        }
        return icons.get(self.plataforma, '🌐')
    
    @property
    def nivel_color(self):
        """Retorna el color correspondiente al nivel"""
        colors = {
            'basico': 'green',
            'intermedio': 'yellow', 
            'avanzado': 'red'
        }
        return colors.get(self.nivel, 'gray')


class FavoritoCurso(models.Model):
    """Modelo para cursos marcados como favoritos por el usuario"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    curso = models.ForeignKey(CursoExterno, on_delete=models.CASCADE)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['usuario', 'curso']
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'
    
    def __str__(self):
        return f"{self.usuario.username} - {self.curso.titulo}"
