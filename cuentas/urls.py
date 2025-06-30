from django.urls import path
from . import views

""" Urls App CUENTAS """
urlpatterns = [
    path("profile/", views.profile, name="profile"),
    path("settings/", views.settings, name="settings"),
    
]