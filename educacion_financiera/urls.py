from django.urls import path
from . import views

""" Urls App EDUCACION_FINANCIERA """
app_name = 'educacion_financiera'

urlpatterns = [
    path("calculators/", views.calculators, name="calculators"),
    path("courses/", views.courses, name="courses"),
    path("courses/<int:curso_id>/favorito/", views.toggle_favorito, name="toggle_favorito"),
    path("tips/", views.tips, name="tips"),
    path("ai-chat/", views.ai_chat, name="ai_chat"),
]