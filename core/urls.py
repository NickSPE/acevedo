from django.urls import path
from . import views
app_name = 'core'

""" Urls App CORE """
urlpatterns = [
    path("" , views.Inicio , name="index"),
    path("dashboard/" , views.dashboard , name="dashboard"),
    path('logout/', views.logout_view, name='logout'),
    path('temporary_logout/' , views.temporary_logout , name='temporary_logout'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('terms/', views.terms_of_service, name='terms'),
    path('help/', views.help_center, name='help'),
    path('contact/', views.contact_view, name='contact'),
]