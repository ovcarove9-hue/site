# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ============================================================================
    # ОСНОВНЫЕ СТРАНИЦЫ
    # ============================================================================
    path('', views.home, name='base'),
    path('map/', views.map_view, name='map'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('court/', views.court_page, name='court_page'),  # Для /court/?id=1
    path('court/<int:court_id>/', views.court_page, name='court_detail'),
    
    # ============================================================================
    # СИСТЕМА БРОНИРОВАНИЯ ПЛОЩАДОК
    # ============================================================================
    path('book/court/<int:court_id>/', views.book_court, name='book_court'),
    path('booking/confirmation/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),
    path('booking/detail/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('booking/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    
    # ============================================================================
    # ПЛОЩАДКИ И МОДЕРАЦИЯ
    # ============================================================================
    path('court/<int:court_id>/', views.court_detail, name='court_detail'),
    path('court/<int:court_id>/review/', views.add_review, name='add_review'),
    
    path('suggest-court/', views.suggest_court, name='suggest_court'),
    path('my-suggestions/', views.my_suggestions, name='my_suggestions'),
    
    path('moderation/', views.moderation_dashboard, name='moderation_dashboard'),
    path('moderate/<int:court_id>/<str:action>/', views.moderate_court, name='moderate_court'),
    
    # ============================================================================
    # API ДЛЯ КАРТЫ И БРОНИРОВАНИЯ
    # ============================================================================
    path('api/courts/', views.courts_api, name='courts_api'),
    path('api/courts/<int:court_id>/', views.court_detail_api, name='court_detail_api'),
    path('api/check-availability/', views.check_availability, name='check_availability'),
    path('api/time-slots/<int:court_id>/', views.get_time_slots, name='get_time_slots'),
    
    # ============================================================================
    # СИСТЕМА ИГР
    # ============================================================================
    path('create_game/', views.create_game, name='create_game'),  # ИЗМЕНИЛИ ЗДЕСЬ
    path('game/<int:game_id>/', views.game_detail, name='game_detail'),
    path('game/<int:game_id>/join/', views.join_game, name='join_game'),
    path('my-games/', views.my_games, name='my_games'),
    
    # ============================================================================
    # ПОИСК И ПРОФИЛИ
    # ============================================================================
    path('search/', views.search_players, name='search'),
    path('profile/<int:user_id>/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('upload-avatar/', views.upload_avatar, name='upload_avatar'),
    
    # ============================================================================
    # СИСТЕМА ДРУЗЕЙ
    # ============================================================================
    path('add-friend/<int:user_id>/', views.add_friend, name='add_friend'),
    path('accept-friend/<int:friendship_id>/', views.accept_friend, name='accept_friend'),
    path('reject-friend/<int:friendship_id>/', views.reject_friend, name='reject_friend'),
    path('remove-friend/<int:user_id>/', views.remove_friend, name='remove_friend'),
    
    # ============================================================================
    # АВТОРИЗАЦИЯ
    # ============================================================================
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # ============================================================================
    # ТЕСТ И ОБРАБОТЧИКИ ОШИБОК
    # ============================================================================
    path('test-change/', views.test_change, name='test_change'),
    
    # Обработчики ошибок
    path('404/', views.handler404, name='handler404'),
    path('500/', views.handler500, name='handler500'),
    path('403/', views.handler403, name='handler403'),
    path('400/', views.handler400, name='handler400'),
]