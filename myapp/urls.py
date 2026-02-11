"""
URL-маршруты приложения myapp

Структура:
- Основные страницы
- Площадки и модерация
- Система игр
- Система бронирования
- Поиск и профили
- Авторизация
- API эндпоинты
- Служебные маршруты
"""

from django.urls import path
from . import views
from . import api

urlpatterns = [
    # ============================================================================
    # ОСНОВНЫЕ СТРАНИЦЫ
    # ============================================================================
    path('', views.home, name='home'),  # Главная страница
    path('map/', views.map_view, name='map'),  # Карта площадок
    path('full-map/', views.full_map_view, name='full_map'),  # Полная карта
    path('search-courts/', views.search_courts_view, name='search_courts'),  # Поиск площадок
    path('dashboard/', views.dashboard, name='dashboard'),  # Личный кабинет
    path('court/', views.court_page, name='court_page'),  # Страница площадки (временно)
    path('court/<int:court_id>/', views.court_detail, name='court_detail'),  # Детали площадки
    path('friends/', views.friends_list, name='friends'),  # Друзья (без ID)
    path('avatar/upload/', views.upload_player_avatar, name='upload_player_avatar'),  # Загрузка аватара
    
    # ============================================================================
    # ПЛОЩАДКИ И МОДЕРАЦИЯ
    # ============================================================================
    path('suggest-court/', views.suggest_court, name='suggest_court'),  # Предложить площадку
    path('create-court/', views.create_court, name='create_court'),  # Создать площадку
    path('my-suggestions/', views.my_suggestions, name='my_suggestions'),  # Мои предложения
    path('moderation/', views.moderation_dashboard, name='moderation_dashboard'),  # Модерация
    path('moderate/<int:court_id>/<str:action>/', views.moderate_court, name='moderate_court'),  # Модерация площадки
    
    # ============================================================================
    # СИСТЕМА ИГР
    # ============================================================================
    path('create_game/', views.create_game, name='create_game'),  # Создать игру
    path('game/<int:game_id>/', views.game_detail, name='game_detail'),  # Детали игры
    path('game/<int:game_id>/join/', views.join_game, name='join_game'),  # Присоединиться к игре
    path('game/<int:game_id>/leave/', views.leave_game, name='leave_game'),  # Покинуть игру
    path('my-games/', views.my_games, name='my_games'),  # Мои игры
    
    # ============================================================================
    # СИСТЕМА БРОНИРОВАНИЯ ПЛОЩАДОК
    # ============================================================================
    path('book/court/<int:court_id>/', views.book_court, name='book_court'),  # Забронировать площадку
    path('booking/confirmation/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),  # Подтверждение брони
    path('booking/detail/<int:booking_id>/', views.booking_detail, name='booking_detail'),  # Детали брони
    path('my-bookings/', views.my_bookings, name='my_bookings'),  # Мои бронирования
    path('booking/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),  # Отменить бронирование
    
    # ============================================================================
    # ПОИСК И ПРОФИЛИ
    # ============================================================================
    path('search/', views.search_players, name='search'),  # Поиск игроков
    path('profile/<int:user_id>/', views.profile, name='profile'),  # Профиль пользователя
    path('edit-profile/', views.edit_profile, name='edit_profile'),  # Редактировать профиль
    path('upload-avatar/', views.upload_avatar, name='upload_avatar'),  # Загрузить аватар
    path('friends/<int:user_id>/', views.friends_list, name='friends_list'),  # Список друзей
    path('friends/', views.friends_list, name='my_friends'),  # Список друзей (без ID)
    path('friend-requests/', views.friend_requests, name='friend_requests'),  # Заявки в друзья
    path('add-friend/<int:user_id>/', views.add_friend, name='add_friend'),  # Добавить в друзья
    path('accept-friend/<int:friendship_id>/', views.accept_friend, name='accept_friend'),  # Принять заявку
    path('reject-friend/<int:friendship_id>/', views.reject_friend, name='reject_friend'),  # Отклонить заявку
    path('remove-friend/<int:user_id>/', views.remove_friend, name='remove_friend'),  # Удалить из друзей
    
    # ============================================================================
    # АВТОРИЗАЦИЯ
    # ============================================================================
    path('register/', views.register, name='register'),  # Регистрация
    path('login/', views.login_view, name='login'),  # Вход
    path('logout/', views.logout_view, name='logout'),  # Выход
    
    # ============================================================================
    # API ЭНДПОИНТЫ
    # ============================================================================
    # API для карты и бронирования
    path('api/courts/', views.courts_api, name='courts_api'),  # API площадок
    path('api/courts/<int:court_id>/', views.court_detail_api, name='court_detail_api'),  # API деталей площадки
    path('api/check-availability/', views.check_availability, name='check_availability'),  # Проверка доступности
    path('api/time-slots/<int:court_id>/', views.get_time_slots, name='get_time_slots'),  # Временные слоты
    path('api/search-courts/', views.search_courts_api, name='search_courts_api'),  # Поиск площадок API
    # API для игр
    path('api/games-by-date/', api.games_by_date_api, name='games_by_date_api'),  # Игры по дате
    
    # ============================================================================
    # СЛУЖЕБНЫЕ МАРШРУТЫ
    # ============================================================================
    # Календарь событий
    path('events-calendar/', views.event_calendar, name='event_calendar'),  # Календарь событий
    
    # SEO файлы
    path('robots.txt', views.robots_txt, name='robots_txt'),  # robots.txt
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),  # sitemap.xml
    
    # Тестовые и отладочные маршруты
    path('test-change/', views.test_change, name='test_change'),  # Тестовое изменение
    
    # Обработчики ошибок (для тестирования)
    path('404/', views.handler404, name='handler404'),  # 404 ошибка
    path('500/', views.handler500, name='handler500'),  # 500 ошибка
    path('403/', views.handler403, name='handler403'),  # 403 ошибка
    path('400/', views.handler400, name='handler400'),  # 400 ошибка
]