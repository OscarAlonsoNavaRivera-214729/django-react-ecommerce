from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='user-register'),
    path('login/', views.login, name='user-login'),
    path('logout/', views.logout, name='user-logout'),
    path('profile/', views.profile, name='user-profile'),
    path('profile/update/', views.update_profile, name='user-profile-update'),
]
