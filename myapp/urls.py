# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('create-court/', views.create_court_view, name='create_court'),
    path('', views.home_view, name='home'),
    path('create-game/', views.create_game_view, name='create_game'),
    
    # Площадки
    path('create-court/', views.create_court_view, name='create_court'),
    path('map/', views.map_view, name='map'),
    path('map/my-suggestions/', views.my_suggestions_view, name='my_suggestions'),
    
    # API
    path('api/games/', views.games_api_view, name='games_api'),
    path('api/courts/', views.courts_api_view, name='courts_api'),
    
    # Игры
    path('game/<int:game_id>/join/', views.join_game_view, name='join_game'),
    path('game/<int:game_id>/leave/', views.leave_game_view, name='leave_game'),
    
    # Поиск
    path('search/', views.search_players_view, name='search'),
]