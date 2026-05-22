from rest_framework import serializers
from .models import CursoExterno, FavoritoCurso

class CursoExternoSerializer(serializers.ModelSerializer):
    es_favorito = serializers.SerializerMethodField()
    plataforma_icon = serializers.SerializerMethodField()

    class Meta:
        model = CursoExterno
        fields = [
            'id', 'titulo', 'descripcion', 'plataforma', 'url', 'imagen_url',
            'duracion', 'nivel', 'autor', 'es_favorito', 'plataforma_icon'
        ]

    def get_es_favorito(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FavoritoCurso.objects.filter(usuario=request.user, curso=obj).exists()
        return False

    def get_plataforma_icon(self, obj):
        iconos_plataforma = {
            'YouTube': '📺',
            'Coursera': '🎓',
            'Udemy': '💻',
            'Khan Academy': '📚',
            'edX': '🏛️',
            'Platzi': '🚀',
            'Otro': '🌐'
        }
        return iconos_plataforma.get(obj.plataforma, '🌐')

class FavoritoCursoSerializer(serializers.ModelSerializer):
    curso_detalle = CursoExternoSerializer(source='curso', read_only=True)

    class Meta:
        model = FavoritoCurso
        fields = ['id', 'usuario', 'curso', 'curso_detalle']
        read_only_fields = ['usuario']
