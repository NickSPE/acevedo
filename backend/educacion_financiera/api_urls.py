from django.urls import path
from .api_views import (
    CalculatorsAPIView,
    CoursesListAPIView,
    ToggleFavoritoCursoAPIView,
    FinancialTipsAPIView,
    AIChatAPIView,
)

urlpatterns = [
    # Calculadoras
    path('calculadora/', CalculatorsAPIView.as_view(), name='api_educacion_calculadora'),
    
    # Cursos
    path('cursos/', CoursesListAPIView.as_view(), name='api_educacion_cursos'),
    path('cursos/<int:curso_id>/favorito/', ToggleFavoritoCursoAPIView.as_view(), name='api_educacion_curso_favorito'),
    
    # Consejos
    path('tips/', FinancialTipsAPIView.as_view(), name='api_educacion_tips'),
    
    # Chat de IA
    path('chat-ia/', AIChatAPIView.as_view(), name='api_educacion_chat_ia'),
]
