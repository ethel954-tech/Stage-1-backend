from django.urls import path
from . import views

urlpatterns = [
    path('github/', views.github_login),
    path('github/callback/', views.github_callback),
    path('cli/exchange/', views.cli_exchange),
    path('refresh/', views.refresh_token),
    path('logout/', views.logout),
    path('me/', views.me),
    path('csrf/', views.csrf_token),
]