from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('api/wordlist', views.wordlist_view, name='wordlist'),
    path('api/mapping', views.mapping_view, name='mapping'),
    path('api/state', views.state_view, name='state'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]
