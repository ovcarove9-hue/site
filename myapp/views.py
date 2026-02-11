# myapp/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import json
import decimal
from datetime import datetime, timedelta, date
import calendar
from .models import (
    UserProfile, VolleyballCourt, Game, GameParticipation,
    Friendship, CourtBooking, TimeSlot, Review, CourtPhoto
)
from .forms import (
    ProfileEditForm, AvatarUploadForm, SearchForm, FriendSearchForm,
    GameCreationForm, GameJoinForm, CourtSuggestionForm,
    CourtBookingForm, ReviewForm, QuickBookingForm,
    CustomUserRegistrationForm
)
from django.contrib.auth import login
from django.core import serializers

# API функции перемещены в myapp.api
# см. myapp.api.games_by_date_api

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')  # или 'profile'
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def upload_player_avatar(request):
    """Загрузка аватара игрока"""
    if request.method == 'POST':
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        form = AvatarUploadForm(request.POST, request.FILES, instance=profile)
        
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Аватар успешно обновлён')
        else:
            messages.error(request, 'Ошибка при загрузке аватара')
    
    # Возвращаем обратно на страницу профиля
    return redirect('profile', user_id=request.user.id)
# ============================================================================
# ОСНОВНЫЕ СТРАНИЦЫ
# ============================================================================
# myapp/views.py
import json

def volleyball_map(request):
    """Отображение карты волейбольных площадок"""
    return render(request, 'volleyball_map.html')

def court_page(request):
    """Отображение страницы конкретной площадки"""
    court_id = request.GET.get('id', 1)
    
    # Данные площадок
    courts_data = {
        1: {
            'id': 1,
            'name': 'Парк Горького (центральная площадка)',
            'address': 'Крымский Вал, 9',
            'district': 'ЦАО',
            'court_type': 'outdoor',
            'price_per_hour': 0,
            'is_free': True,
            'is_lighted': True,
            'description': 'Центральная волейбольная площадка в Парке Горького.',
            'rating': 4.8,
            'capacity': 20,
        },
        2: {
            'id': 2,
            'name': 'СК «Лужники» (открытые корты)',
            'address': 'Лужнецкая наб., 24',
            'district': 'ЦАО',
            'court_type': 'outdoor',
            'price_per_hour': 500,
            'is_free': False,
            'is_lighted': True,
            'description': '4 открытых корта с профессиональным покрытием.',
            'rating': 4.7,
            'capacity': 24,
        },
        # Добавьте остальные площадки...
    }
    
    # Получаем данные для текущей площадки
    court_data = courts_data.get(int(court_id), courts_data[1])
    
    context = {
        'court': court_data,
        'court_id': court_id,
    }
    
    return render(request, 'court_page.html', context)

def home(request):
    """Главная страница"""
    # Статистика сообщества
    total_courts = VolleyballCourt.objects.filter(status='approved', is_active=True).count()
    total_games = Game.objects.filter(is_active=True).count()
    total_users = User.objects.filter(is_active=True).count()

    # Дополнительная статистика
    today_games = Game.objects.filter(
        game_date=timezone.now().date(),
        is_active=True
    ).count()
    upcoming_games = Game.objects.filter(
        game_date__gt=timezone.now().date(),
        is_active=True
    ).count()
    indoor_courts = VolleyballCourt.objects.filter(
        status='approved',
        is_active=True,
        court_type='indoor'
    ).count()
    outdoor_courts = VolleyballCourt.objects.filter(
        status='approved',
        is_active=True,
        court_type='outdoor'
    ).count()
    beach_courts = VolleyballCourt.objects.filter(
        status='approved',
        is_active=True,
        court_type='beach'
    ).count()

    # Ближайшие игры (используем timezone.now() для корректной работы с часовыми поясами)
    upcoming_games_queryset = Game.objects.filter(
        game_date__gte=timezone.now().date(),
        is_active=True
    ).select_related('organizer').prefetch_related('participants').order_by('game_date', 'game_time')[:5]

    # Получаем общее количество предстоящих игр (не только ближайших 5)
    upcoming_games_count = Game.objects.filter(
        game_date__gt=timezone.now().date(),
        is_active=True
    ).count()

    # Преобразуем в список, чтобы можно было итерировать дважды
    upcoming_games = list(upcoming_games_queryset)

    # Добавляем информацию о возможности присоединиться для каждого гейма
    if request.user.is_authenticated:
        for game in upcoming_games:
            game.can_join = (
                game.organizer != request.user and
                request.user not in game.participants.all() and
                game.participants.count() < game.max_players
            )
    else:
        # Для анонимных пользователей нельзя присоединиться
        for game in upcoming_games:
            game.can_join = False

    # Последние одобренные площадки
    recent_courts = VolleyballCourt.objects.filter(
        status='approved',
        is_active=True
    ).order_by('-created_at')[:6]

    # Предстоящие бронирования (если пользователь авторизован)
    upcoming_bookings = None
    if request.user.is_authenticated:
        upcoming_bookings = CourtBooking.objects.filter(
            user=request.user,
            booking_date__gte=timezone.now().date(),
            status__in=['pending', 'confirmed']
        ).order_by('booking_date', 'start_time')[:3]


    # Получаем игры пользователя, если авторизован
    today = timezone.now().date()
    user_games = []
    if request.user.is_authenticated:
        user_games_queryset = Game.objects.filter(
            participants=request.user,
            game_date__gte=today,
            is_active=True
        ).select_related('organizer').prefetch_related('participants').order_by('game_date', 'game_time')[:10]
        user_games = list(user_games_queryset)

    # Подготовка данных для календаря на главной странице
    current_date = timezone.now().date()
    current_month = current_date.month
    current_year = current_date.year

    # Получаем все игры для текущего месяца
    games_for_month_queryset = Game.objects.filter(
        game_date__year=current_year,
        game_date__month=current_month,
        is_active=True
    ).select_related('organizer').prefetch_related('participants').order_by('game_date', 'game_time')
    games_for_month = list(games_for_month_queryset)

    # Создаем календарь для текущего месяца
    import calendar
    cal = calendar.Calendar(firstweekday=0)  # Понедельник - первый день недели
    month_days = cal.monthdayscalendar(current_year, current_month)

    # Группируем игры по датам
    games_by_date = {}
    for game in games_for_month:
        date_str = game.game_date.strftime('%Y-%m-%d')
        if date_str not in games_by_date:
            games_by_date[date_str] = []
        games_by_date[date_str].append(game)

    # Формируем данные для календаря
    calendar_data = []
    for week in month_days:
        week_data = []
        for day in week:
            if day == 0:  # День вне текущего месяца
                week_data.append({'day': 0, 'games': []})
            else:
                date_str = f"{current_year}-{current_month:02d}-{day:02d}"
                games = games_by_date.get(date_str, [])
                week_data.append({'day': day, 'games': games})
        calendar_data.append(week_data)

    # Подготовка данных для календаря текущей недели
    # Определяем начало и конец текущей недели
    start_of_week = current_date - timedelta(days=current_date.weekday())  # Понедельник недели
    end_of_week = start_of_week + timedelta(days=6)  # Воскресенье недели

    # Получаем игры для текущей недели
    games_for_week_queryset = Game.objects.filter(
        game_date__gte=start_of_week,
        game_date__lte=end_of_week,
        is_active=True
    ).select_related('organizer').prefetch_related('participants').order_by('game_date', 'game_time')
    games_for_week = list(games_for_week_queryset)

    # Группируем игры по датам для недели
    week_games_by_date = {}
    for game in games_for_week:
        date_str = game.game_date.strftime('%Y-%m-%d')
        if date_str not in week_games_by_date:
            week_games_by_date[date_str] = []
        week_games_by_date[date_str].append({
            'id': game.id,
            'title': game.title,
            'time': game.game_time.strftime('%H:%M'),
            'location': game.location,
            'sport_type': game.get_sport_type_display(),
        })

    # Формируем данные для календаря недели
    week_calendar_data = []
    for i in range(7):  # 7 дней недели
        day_date = start_of_week + timedelta(days=i)
        date_str = day_date.strftime('%Y-%m-%d')
        games = week_games_by_date.get(date_str, [])

        # Определяем название дня недели
        ru_day_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        if day_date == current_date:
            day_name = 'Сегодня'
        else:
            day_name = ru_day_names[day_date.weekday()]

        week_calendar_data.append({
            'day': day_date.day,
            'date': date_str,
            'day_name': day_name,
            'is_today': day_date == current_date,
            'games': games
        })

    calendar_context = {
        'days': calendar_data,
        'week_days': week_calendar_data,
        'today': current_date,
        'month': current_month,
        'year': current_year,
        'month_name': calendar.month_name[current_month],
        'prev_month': (current_month - 1) if current_month > 1 else 12,
        'prev_year': current_year if current_month > 1 else current_year - 1,
        'next_month': (current_month + 1) if current_month < 12 else 1,
        'next_year': current_year if current_month < 12 else current_year + 1,
    }

    # Игры на сегодня
    today_games_queryset = Game.objects.filter(
        game_date=timezone.now().date(),
        is_active=True
    ).select_related('organizer').prefetch_related('participants').order_by('game_time')

    # Получаем количество игр на сегодня (до преобразования в список)
    today_games_count = today_games_queryset.count()

    # Преобразуем в список, чтобы можно было итерировать дважды
    today_games = list(today_games_queryset)

    # Добавляем информацию о возможности присоединиться для каждого гейма
    if request.user.is_authenticated:
        for game in today_games:
            game.can_join = (
                game.organizer != request.user and
                request.user not in game.participants.all() and
                game.participants.count() < game.max_players
            )
    else:
        # Для анонимных пользователей нельзя присоединиться
        for game in today_games:
            game.can_join = False

    context = {
        'page_title': 'Волейбольное сообщество - Главная',
        'total_courts': total_courts,
        'total_games': total_games,
        'total_users': total_users,
        'today_games_count': today_games_count,  # количество игр на сегодня (COUNT)
        'upcoming_games_count': upcoming_games_count,  # количество предстоящих игр (COUNT)
        'indoor_courts': indoor_courts,  # количество зальных площадок
        'outdoor_courts': outdoor_courts,  # количество открытых площадок
        'beach_courts': beach_courts,  # количество пляжных площадок
        'upcoming_games': upcoming_games_queryset,  # передаем объект QuerySet вместо количества
        'today_games': today_games,  # добавляем игры на сегодня (список объектов)
        'recent_courts': recent_courts,
        'upcoming_bookings': upcoming_bookings,
        'today': today,
        'user_games': user_games,
        'calendar': calendar_context,
        'week_calendar': calendar_context['week_days'],  # Добавляем календарь недели в контекст
    }

    return render(request, 'common/home.html', context)

@login_required
def full_map_view(request):
    """Полная карта волейбольных площадок из базы данных"""
    # Получаем все активные площадки
    courts = VolleyballCourt.objects.filter(
        is_active=True
    )

    # Подготавливаем данные для карты
    courts_data = []
    for court in courts:
        court_info = {
            'id': court.id,
            'name': court.name,
            'address': court.address,
            'city': court.city,
            'court_type': court.court_type,
            'court_type_display': court.get_court_type_display(),
            'is_free': court.is_free,
            'price_per_hour': float(court.price_per_hour) if court.price_per_hour else 0,
            'is_lighted': court.is_lighted,
            'has_parking': court.has_parking,
            'has_showers': court.has_showers,
            'has_cafe': court.has_cafe,
            'has_locker_rooms': court.has_locker_rooms,
            'has_equipment_rental': court.has_equipment_rental,
            'description': court.description[:100] if court.description else '',
            'working_days': court.working_days,
            'opening_time': str(court.opening_time) if court.opening_time else '08:00',
            'closing_time': str(court.closing_time) if court.closing_time else '22:00',
            'phone': court.phone or '',
            'website': court.website or '',
            'photo_url': court.photo_url or '',
            'booking_enabled': court.booking_enabled,
            'min_booking_hours': court.min_booking_hours,
            'max_booking_hours': court.max_booking_hours,
            'advance_booking_days': court.advance_booking_days,
            'capacity': court.courts_count,
            'surface': court.get_surface_display(),
        }

        # Добавляем координаты если они есть
        if court.latitude and court.longitude:
            court_info['latitude'] = float(court.latitude)
            court_info['longitude'] = float(court.longitude)
            court_info['has_coordinates'] = True
        else:
            # Если нет координат, используем значения по умолчанию для города
            court_info['latitude'] = 55.7558 if court.city == 'Москва' else 59.9343
            court_info['longitude'] = 37.6173 if court.city == 'Москва' else 30.3351
            court_info['has_coordinates'] = False

        courts_data.append(court_info)

    context = {
        'page_title': 'Карта волейбольных площадок',
        'courts': courts,
        'courts_json': json.dumps(courts_data, ensure_ascii=False),
        'courts_count': courts.count(),
        'free_courts_count': courts.filter(is_free=True).count(),
        'indoor_courts_count': courts.filter(court_type='indoor').count(),
        'outdoor_courts_count': courts.filter(court_type='outdoor').count(),
        'beach_courts_count': courts.filter(court_type='beach').count(),
        'current_filters': {}
    }

    return render(request, 'full_map.html', context)


def map_view(request):
    """Карта ТОЛЬКО ОДОБРЕННЫХ волейбольных площадок с функцией бронирования"""

    # Получаем только одобренные и активные площадки
    courts = VolleyballCourt.objects.filter(
        status='approved',
        is_active=True,
        is_verified=True
    )
    
    # Применяем фильтры из GET-параметров
    court_type = request.GET.get('type', '')
    is_free = request.GET.get('free', '')
    has_lighting = request.GET.get('lighting', '')
    
    if court_type:
        courts = courts.filter(court_type=court_type)
    if is_free == 'true':
        courts = courts.filter(is_free=True)
    if has_lighting == 'true':
        courts = courts.filter(is_lighted=True)
    
    # Подготавливаем данные для карты и бронирования
    courts_data = []
    for court in courts:
        court_info = {
            'id': court.id,
            'name': court.name,
            'address': court.address,
            'city': court.city,
            'court_type': court.court_type,
            'court_type_display': court.get_court_type_display(),
            'is_free': court.is_free,
            'price': float(court.price_per_hour) if court.price_per_hour else 0,
            'is_lighted': court.is_lighted,
            'has_parking': court.has_parking,
            'has_showers': court.has_showers,
            'has_cafe': court.has_cafe,
            'has_locker_rooms': court.has_locker_rooms,
            'has_equipment_rental': court.has_equipment_rental,
            'description': court.description[:100] if court.description else '',
            'working_days': court.working_days,
            'opening_time': str(court.opening_time) if court.opening_time else '08:00',
            'closing_time': str(court.closing_time) if court.closing_time else '22:00',
            'phone': court.phone or '',
            'website': court.website or '',
            'photo_url': court.photo_url or '',
            'booking_enabled': court.booking_enabled,
            'min_booking_hours': court.min_booking_hours,
            'max_booking_hours': court.max_booking_hours,
            'advance_booking_days': court.advance_booking_days,
        }
        
        # Добавляем координаты если они есть
        if court.latitude and court.longitude:
            court_info['latitude'] = float(court.latitude)
            court_info['longitude'] = float(court.longitude)
            court_info['has_coordinates'] = True
        else:
            # Если нет координат, используем значения по умолчанию для города
            court_info['latitude'] = 55.7558 if court.city == 'Москва' else 59.9343
            court_info['longitude'] = 37.6173 if court.city == 'Москва' else 30.3351
            court_info['has_coordinates'] = False
        
        courts_data.append(court_info)
    
    # Статистика для отображения
    context = {
        'page_title': 'Карта волейбольных площадок',
        'courts': courts,
        'courts_json': json.dumps(courts_data, ensure_ascii=False),
        'courts_count': courts.count(),
        'free_courts_count': courts.filter(is_free=True).count(),
        'indoor_courts_count': courts.filter(court_type='indoor').count(),
        'outdoor_courts_count': courts.filter(court_type='outdoor').count(),
        'beach_courts_count': courts.filter(court_type='beach').count(),
        'current_filters': {
            'type': court_type,
            'free': is_free,
            'lighting': has_lighting,
        }
    }
    
    return render(request, 'court/map.html', context)

# ============================================================================
# СИСТЕМА БРОНИРОВАНИЯ ПЛОЩАДОК
# ============================================================================

@login_required
def book_court(request, court_id):
    """Планирование игры на площадке"""
    court = get_object_or_404(VolleyballCourt, id=court_id, status='approved', is_active=True)
    
    if not court.booking_enabled:
        messages.error(request, 'Планирование игры для этой площадки временно недоступно')
        return redirect('map_view')
    
    if request.method == 'POST':
        form = CourtBookingForm(request.POST, court=court, user=request.user)
        
        if form.is_valid():
            try:
                # Создаем игру
                booking = form.save(commit=False)
                booking.court = court
                booking.user = request.user
                booking.price_per_hour = court.price_per_hour
                booking.total_price = court.price_per_hour * booking.hours
                
                # Расчет времени окончания
                start_datetime = datetime.combine(booking.booking_date, booking.start_time)
                end_datetime = start_datetime + timedelta(hours=booking.hours)
                booking.end_time = end_datetime.time()
                
                # Сохраняем игру
                booking.save()
                
                # Создаем временные слоты для этой игры
                for i in range(booking.hours):
                    slot_time = (start_datetime + timedelta(hours=i)).time()
                    slot_end = (start_datetime + timedelta(hours=i+1)).time()
                    
                    TimeSlot.objects.create(
                        court=court,
                        date=booking.booking_date,
                        start_time=slot_time,
                        end_time=slot_end,
                        is_booked=True,
                        booking=booking,
                        price=court.price_per_hour
                    )
                
                # Добавляем участников если указаны email
                participants_emails = form.cleaned_data.get('participants_emails', '')
                if participants_emails:
                    # Здесь можно добавить логику отправки приглашений
                    pass
                
                messages.success(request, 
                    f'✅ Игра на площадке "{court.name}" успешно запланирована! '
                    f'Номер брони: {booking.booking_number}. '
                    f'Общая стоимость: {booking.total_price} руб.'
                )
                
                return redirect('booking_confirmation', booking_id=booking.id)
                
            except Exception as e:
                messages.error(request, f'Ошибка при создании игры: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        # GET запрос - показываем форму с начальными данными
        initial_data = {
            'contact_name': request.user.get_full_name() or request.user.username,
            'contact_email': request.user.email,
            'participants_count': 6,
            'hours': court.min_booking_hours,
        }
        
        # Получаем телефон из профиля если есть
        try:
            profile = request.user.profile
            if hasattr(profile, 'phone') and profile.phone:
                initial_data['contact_phone'] = profile.phone
        except:
            pass
        
        form = CourtBookingForm(court=court, user=request.user, initial=initial_data)
    
    context = {
        'page_title': f'Планирование игры: {court.name}',
        'court': court,
        'form': form,
        'today': timezone.now().date(),
        'max_date': timezone.now().date() + timedelta(days=court.advance_booking_days),
    }
    
    return render(request, 'book_court.html', context)

@login_required
def booking_confirmation(request, booking_id):
    """Страница подтверждения бронирования"""
    booking = get_object_or_404(CourtBooking, id=booking_id, user=request.user)
    
    context = {
        'page_title': 'Подтверждение бронирования',
        'booking': booking,
        'court': booking.court,
    }
    
    return render(request, 'booking_confirmation.html', context)

@login_required
def my_bookings(request):
    """Мои игры"""
    bookings = CourtBooking.objects.filter(user=request.user).order_by('-booking_date', '-start_time')
    
    # Фильтрация по статусу
    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    # Пагинация
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Статистика
    total_bookings = bookings.count()
    active_bookings = bookings.filter(status__in=['pending', 'confirmed']).count()
    cancelled_bookings = bookings.filter(status='cancelled').count()
    completed_bookings = bookings.filter(status='completed').count()
    
    context = {
        'page_title': 'Мои игры',
        'page_obj': page_obj,
        'total_games': total_bookings,
        'active_games': active_bookings,
        'cancelled_games': cancelled_bookings,
        'completed_games': completed_bookings,
        'status_filter': status_filter,
    }
    
    return render(request, 'my_bookings.html', context)

@login_required
def cancel_booking(request, booking_id):
    """Отмена бронирования"""
    booking = get_object_or_404(CourtBooking, id=booking_id, user=request.user)
    
    if booking.status == 'cancelled':
        messages.warning(request, 'Эта игра уже отменена')
        return redirect('my_bookings')
    
    if not booking.can_be_cancelled:
        messages.error(request, 'Игру нельзя отменить менее чем за 24 часа до начала')
        return redirect('my_bookings')
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        booking.cancel(reason=reason)
        messages.success(request, f'Игра №{booking.booking_number} успешно отменена')
        return redirect('my_bookings')
    
    context = {
        'page_title': 'Отмена игры',
        'booking': booking,
        'court': booking.court,
    }
    
    return render(request, 'cancel_booking.html', context)

@login_required
def booking_detail(request, booking_id):
    """Детальная информация о бронировании"""
    booking = get_object_or_404(CourtBooking, id=booking_id, user=request.user)
    
    # Получаем временные слоты для этого бронирования
    time_slots = TimeSlot.objects.filter(booking=booking).order_by('start_time')
    
    context = {
        'page_title': f'Игра №{booking.booking_number}',
        'booking': booking,
        'court': booking.court,
        'time_slots': time_slots,
        'can_cancel': booking.can_be_cancelled,
    }
    
    return render(request, 'booking_detail.html', context)

# ============================================================================
# API ДЛЯ БРОНИРОВАНИЯ И КАРТЫ
# ============================================================================

@require_GET
def check_availability(request):
    """API для проверки доступности времени для бронирования"""
    court_id = request.GET.get('court_id')
    check_date = request.GET.get('date')
    start_time = request.GET.get('start_time')
    hours = int(request.GET.get('hours', 1))
    
    if not all([court_id, check_date, start_time]):
        return JsonResponse({'error': 'Недостаточно параметров'}, status=400)
    
    try:
        court = VolleyballCourt.objects.get(id=court_id)
        
        # Преобразуем строки в datetime объекты
        booking_date = datetime.strptime(check_date, '%Y-%m-%d').date()
        start_dt = datetime.combine(booking_date, datetime.strptime(start_time, '%H:%M').time())
        end_dt = start_dt + timedelta(hours=hours)
        
        # Проверяем доступность
        is_available = True
        conflict_message = ""
        
        # 1. Проверяем время работы площадки
        if start_dt.time() < court.opening_time:
            is_available = False
            conflict_message = f"Площадка открывается в {court.opening_time.strftime('%H:%M')}"
        
        if end_dt.time() > court.closing_time:
            is_available = False
            conflict_message = f"Площадка закрывается в {court.closing_time.strftime('%H:%M')}"
        
        # 2. Проверяем существующие игры
        if is_available:
            conflicting_bookings = CourtBooking.objects.filter(
                court=court,
                booking_date=booking_date,
                status__in=['pending', 'confirmed']
            ).exclude(
                Q(end_time__lte=start_time) | Q(start_time__gte=end_dt.strftime('%H:%M'))
            )
            
            if conflicting_bookings.exists():
                is_available = False
                conflict_message = "Выбранное время уже занято"
        
        # 3. Проверяем заблокированные временные слоты
        if is_available:
            conflicting_slots = TimeSlot.objects.filter(
                court=court,
                date=booking_date,
                start_time__lt=end_dt.time(),
                end_time__gt=start_dt.time(),
                is_blocked=True
            )
            
            if conflicting_slots.exists():
                is_available = False
                conflict_message = "Выбранное время временно недоступно"
        
        # Рассчитываем стоимость
        total_price = 0
        if not court.is_free:
            total_price = float(court.price_per_hour * hours)
        
        return JsonResponse({
            'available': is_available,
            'message': conflict_message,
            'total_price': total_price,
            'currency': 'RUB',
            'court_name': court.name,
            'opening_time': court.opening_time.strftime('%H:%M'),
            'closing_time': court.closing_time.strftime('%H:%M'),
        })
        
    except VolleyballCourt.DoesNotExist:
        return JsonResponse({'error': 'Площадка не найдена'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_GET
def get_time_slots(request, court_id):
    """API для получения временных слотов площадки"""
    court = get_object_or_404(VolleyballCourt, id=court_id)
    selected_date = request.GET.get('date')
    
    if not selected_date:
        return JsonResponse({'error': 'Не указана дата'}, status=400)
    
    try:
        query_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Неверный формат даты'}, status=400)
    
    # Получаем все слоты на указанную дату
    time_slots = TimeSlot.objects.filter(
        court=court,
        date=query_date
    ).order_by('start_time')
    
    # Формируем список доступных слотов
    available_slots = []
    current_time = court.opening_time
    
    while current_time < court.closing_time:
        slot_end = (datetime.combine(date.today(), current_time) + timedelta(hours=1)).time()
        
        # Проверяем, доступен ли этот слот
        is_booked = False
        is_blocked = False
        
        slot = time_slots.filter(start_time=current_time).first()
        if slot:
            is_booked = slot.is_booked
            is_blocked = slot.is_blocked
        
        available_slots.append({
            'start_time': current_time.strftime('%H:%M'),
            'end_time': slot_end.strftime('%H:%M'),
            'available': not (is_booked or is_blocked),
            'is_booked': is_booked,
            'is_blocked': is_blocked,
            'price': float(slot.price) if slot and slot.price else float(court.price_per_hour),
        })
        
        current_time = slot_end
    
    return JsonResponse({
        'court_id': court.id,
        'court_name': court.name,
        'date': selected_date,
        'opening_time': court.opening_time.strftime('%H:%M'),
        'closing_time': court.closing_time.strftime('%H:%M'),
        'min_booking_hours': court.min_booking_hours,
        'max_booking_hours': court.max_booking_hours,
        'slots': available_slots,
    })

def court_detail_api(request, court_id):
    """API для получения детальной информации о площадке"""
    court = get_object_or_404(VolleyballCourt, id=court_id)
    
    # Получаем отзывы
    reviews = Review.objects.filter(court=court, is_published=True).order_by('-created_at')[:5]
    reviews_data = []
    
    for review in reviews:
        reviews_data.append({
            'user': review.user.username,
            'rating': float(review.average_rating),
            'title': review.title,
            'comment': review.comment,
            'pros': review.pros,
            'cons': review.cons,
            'created_at': review.created_at.strftime('%d.%m.%Y'),
        })
    
    # Средний рейтинг
    avg_rating = Review.objects.filter(court=court, is_published=True).aggregate(
        avg=Avg('rating_overall')
    )['avg'] or 0
    
    data = {
        'id': court.id,
        'name': court.name,
        'address': court.address,
        'city': court.city,
        'court_type': court.court_type,
        'court_type_display': court.get_court_type_display(),
        'price_per_hour': float(court.price_per_hour) if court.price_per_hour else 0,
        'is_free': court.is_free,
        'is_lighted': court.is_lighted,
        'has_parking': court.has_parking,
        'has_showers': court.has_showers,
        'has_cafe': court.has_cafe,
        'has_locker_rooms': court.has_locker_rooms,
        'has_equipment_rental': court.has_equipment_rental,
        'description': court.description,
        'phone': court.phone,
        'website': court.website,
        'photo_url': court.photo_url,
        'opening_time': str(court.opening_time),
        'closing_time': str(court.closing_time),
        'working_days': court.working_days,
        'booking_enabled': court.booking_enabled,
        'min_booking_hours': court.min_booking_hours,
        'max_booking_hours': court.max_booking_hours,
        'advance_booking_days': court.advance_booking_days,
        'rating': float(avg_rating),
        'reviews_count': Review.objects.filter(court=court, is_published=True).count(),
        'reviews': reviews_data,
    }
    
    if court.latitude and court.longitude:
        data['latitude'] = float(court.latitude)
        data['longitude'] = float(court.longitude)
    
    return JsonResponse(data)

# ============================================================================
# СИСТЕМА МОДЕРАЦИИ ПЛОЩАДОК
# ============================================================================

@login_required
def suggest_court(request):
    """Форма для предложения новой площадки (отправляется на модерацию)"""
    
    if request.method == 'POST':
        form = CourtSuggestionForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                # Создаём площадку
                court = form.save(commit=False)
                court.suggested_by = request.user
                court.status = 'pending'
                court.is_active = True
                court.is_verified = False
                
                # Сохраняем координаты если они есть
                latitude = form.cleaned_data.get('latitude')
                longitude = form.cleaned_data.get('longitude')
                if latitude and longitude:
                    court.latitude = latitude
                    court.longitude = longitude
                
                court.save()
                
                # Обрабатываем загруженные фото
                photos = request.FILES.getlist('photos')
                for i, photo in enumerate(photos):
                    is_main = (i == 0)  # Первое фото делаем главным
                    CourtPhoto.objects.create(
                        court=court,
                        photo=photo,
                        is_main=is_main
                    )
                
                messages.success(request, 
                    '✅ Спасибо! Ваше предложение отправлено на модерацию. '
                    'Площадка появится на карте после проверки администратором.'
                )
                
                return redirect('my_suggestions')
                
            except Exception as e:
                messages.error(request, f'Ошибка при сохранении: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        form = CourtSuggestionForm()
    
    context = {
        'page_title': 'Предложить новую площадку',
        'form': form,
    }
    
    return render(request, 'suggest_court.html', context)

@login_required
def my_suggestions(request):
    """Мои предложенные площадки с разными статусами"""
    
    courts = VolleyballCourt.objects.filter(suggested_by=request.user).order_by('-created_at')
    
    # Разделяем по статусам
    pending_courts = courts.filter(status='pending')
    approved_courts = courts.filter(status='approved')
    rejected_courts = courts.filter(status='rejected')
    needs_info_courts = courts.filter(status='needs_info')
    
    context = {
        'page_title': 'Мои предложения площадок',
        'all_courts': courts,
        'pending_courts': pending_courts,
        'approved_courts': approved_courts,
        'rejected_courts': rejected_courts,
        'needs_info_courts': needs_info_courts,
        'total_count': courts.count(),
        'approved_count': approved_courts.count(),
        'pending_count': pending_courts.count(),
        'rejected_count': rejected_courts.count(),
        'needs_info_count': needs_info_courts.count(),
    }
    
    return render(request, 'court/my_suggestions.html', context)

# ============================================================================
# АДМИН-МОДЕРАЦИЯ (только для суперпользователей)
# ============================================================================

@login_required
def moderation_dashboard(request):
    """Дашборд модерации (только для суперпользователей)"""
    
    if not request.user.is_superuser:
        return HttpResponseForbidden("Доступ запрещён")
    
    # Статистика
    total_courts = VolleyballCourt.objects.count()
    pending_courts = VolleyballCourt.objects.filter(status='pending').count()
    approved_courts = VolleyballCourt.objects.filter(status='approved').count()
    rejected_courts = VolleyballCourt.objects.filter(status='rejected').count()
    needs_info_courts = VolleyballCourt.objects.filter(status='needs_info').count()
    
    # Последние предложения на модерации
    recent_pending = VolleyballCourt.objects.filter(
        status='pending'
    ).select_related('suggested_by').order_by('-created_at')[:10]
    
    # Последние бронирования
    recent_bookings = CourtBooking.objects.select_related('court', 'user').order_by('-created_at')[:10]
    
    context = {
        'page_title': 'Панель модерации',
        'total_courts': total_courts,
        'pending_courts': pending_courts,
        'approved_courts': approved_courts,
        'rejected_courts': rejected_courts,
        'needs_info_courts': needs_info_courts,
        'recent_pending': recent_pending,
        'recent_bookings': recent_bookings,
        'is_superuser': request.user.is_superuser,
    }
    
    return render(request, 'court/moderation_dashboard.html', context)

@login_required
def moderate_court(request, court_id, action):
    """Модерация конкретной площадки (одобрить/отклонить/запросить информацию)"""
    
    if not request.user.is_superuser:
        return HttpResponseForbidden("Доступ запрещён")
    
    court = get_object_or_404(VolleyballCourt, id=court_id)
    
    if request.method == 'POST':
        comment = request.POST.get('comment', '').strip()
        
        if action == 'approve':
            court.status = 'approved'
            court.reviewed_by = request.user
            court.reviewed_at = timezone.now()
            court.moderator_comment = comment
            court.is_verified = True
            court.save()
            
            messages.success(request, f'✅ Площадка "{court.name}" одобрена')
            
        elif action == 'reject':
            court.status = 'rejected'
            court.reviewed_by = request.user
            court.reviewed_at = timezone.now()
            court.moderator_comment = comment
            court.save()
            
            messages.error(request, f'❌ Площадка "{court.name}" отклонена')
            
        elif action == 'request_info':
            court.status = 'needs_info'
            court.reviewed_by = request.user
            court.reviewed_at = timezone.now()
            court.moderator_comment = comment
            court.save()
            
            messages.warning(request, f'❓ Запрошена информация по площадке "{court.name}"')
        
        return redirect('moderation_dashboard')
    
    # GET запрос - показываем форму с комментарием
    action_labels = {
        'approve': 'одобрения',
        'reject': 'отклонения',
        'request_info': 'запроса информации'
    }
    
    context = {
        'court': court,
        'action': action,
        'action_label': action_labels.get(action, ''),
        'page_title': f'Модерация: {court.name}'
    }
    
    return render(request, 'moderate_court_form.html', context)

# ============================================================================
# API ДЛЯ КАРТЫ И ДАННЫХ
# ============================================================================

def courts_api(request):
    """API для получения данных о площадках (для карты)"""
    
    status = request.GET.get('status', 'approved')
    court_type = request.GET.get('type', '')
    city = request.GET.get('city', '')
    
    # Базовый queryset
    if status == 'all':
        courts = VolleyballCourt.objects.all()
    else:
        courts = VolleyballCourt.objects.filter(status=status, is_active=True)
    
    # Фильтр по типу
    if court_type:
        courts = courts.filter(court_type=court_type)
    
    # Фильтр по городу
    if city:
        courts = courts.filter(city__icontains=city)
    
    # Подготавливаем данные
    courts_data = []
    for court in courts:
        court_info = {
            'id': court.id,
            'name': court.name,
            'address': court.address,
            'city': court.city,
            'court_type': court.court_type,
            'court_type_display': court.get_court_type_display(),
            'status': court.status,
            'status_display': court.get_status_display(),
            'is_free': court.is_free,
            'price': float(court.price_per_hour) if court.price_per_hour else 0,
            'is_lighted': court.is_lighted,
            'has_parking': court.has_parking,
            'has_showers': court.has_showers,
            'has_cafe': court.has_cafe,
            'description': court.description or '',
            'phone': court.phone or '',
            'website': court.website or '',
            'photo_url': court.photo_url or '',
            'created_at': court.created_at.strftime('%d.%m.%Y'),
            'suggested_by': court.suggested_by.username if court.suggested_by else 'Неизвестно',
            'booking_enabled': court.booking_enabled,
        }
        
        # Координаты
        if court.latitude and court.longitude:
            court_info['latitude'] = float(court.latitude)
            court_info['longitude'] = float(court.longitude)
        else:
            # Значения по умолчанию для города
            if court.city == 'Москва':
                court_info['latitude'] = 55.7558
                court_info['longitude'] = 37.6173
            elif court.city == 'Санкт-Петербург':
                court_info['latitude'] = 59.9343
                court_info['longitude'] = 30.3351
            else:
                court_info['latitude'] = 55.7558
                court_info['longitude'] = 37.6173
        
        courts_data.append(court_info)
    
    return JsonResponse({
        'success': True,
        'courts': courts_data,
        'count': len(courts_data),
        'filters': {
            'status': status,
            'type': court_type,
            'city': city
        }
    })

# ============================================================================
# СИСТЕМА ИГР
# ============================================================================

@login_required
def create_game(request):
    """Создание новой игры с привязкой к площадке"""

    # Проверяем, есть ли параметр court в URL
    court_id = request.GET.get('court')
    initial_court = None

    if court_id:
        try:
            initial_court = VolleyballCourt.objects.get(id=court_id, status='approved', is_active=True)
        except VolleyballCourt.DoesNotExist:
            messages.error(request, 'Выбранная площадка не найдена или не одобрена')
            initial_court = None

    if request.method == 'POST':
        form = GameCreationForm(request.POST, user=request.user)

        if form.is_valid():
            try:
                game = form.save(commit=False)
                game.organizer = request.user
                game.is_active = True

                # Если выбрана площадка, заполняем автоматически location
                court = form.cleaned_data.get('court')
                if court:
                    game.court = court
                    game.location = f"{court.name}, {court.address}"

                    # Проверяем, что площадка одобрена
                    if court.status != 'approved':
                        messages.error(request, 'Выбранная площадка еще не одобрена')
                        return redirect('create_game')

                    # Проверяем доступность времени на площадке
                    game_date = form.cleaned_data.get('game_date')
                    game_time = form.cleaned_data.get('game_time')
                    end_time = form.cleaned_data.get('end_time')

                    # Проверяем время работы
                    if game_time < court.opening_time:
                        messages.error(request, f'Площадка открывается в {court.opening_time.strftime("%H:%M")}')
                        return redirect('create_game')

                    if end_time and end_time > court.closing_time:
                        messages.error(request, f'Площадка закрывается в {court.closing_time.strftime("%H:%M")}')
                        return redirect('create_game')

                game.save()

                # Автоматически добавляем организатора как участника
                game.participants.add(request.user)

                # Также добавляем в GameParticipation для совместимости
                GameParticipation.objects.create(
                    user=request.user,
                    game=game,
                    status='confirmed'
                )

                messages.success(request, f'✅ Игра "{game.title}" создана успешно!')

                # Если игра привязана к площадке, показываем ссылку на нее
                if game.court:
                    messages.info(request, f'🏐 Игра привязана к площадке: <a href="/court/{game.court.id}/">{game.court.name}</a>')

                return redirect('game_detail', game_id=game.id)

            except IntegrityError as e:
                messages.error(request, f'Ошибка целостности данных: {str(e)}')
            except ValidationError as e:
                messages.error(request, f'Ошибка валидации: {str(e)}')
            except Exception as e:
                messages.error(request, f'Ошибка при создании игры: {str(e)}')
        else:
            # Выводим конкретные ошибки формы
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Ошибка в поле "{field}": {error}')
    else:
        # Если есть начальная площадка, передаем ее в форму
        if initial_court:
            form = GameCreationForm(user=request.user, initial={'court': initial_court})
        else:
            form = GameCreationForm(user=request.user)

    # Доступные площадки (только одобренные)
    courts = VolleyballCourt.objects.filter(status='approved', is_active=True)

    # Бронирования пользователя
    user_bookings = CourtBooking.objects.filter(
        user=request.user,
        booking_date__gte=timezone.now().date(),
        status='confirmed'
    ).order_by('booking_date', 'start_time')

    context = {
        'page_title': 'Создание игры',
        'form': form,
        'courts': courts,
        'user_bookings': user_bookings,
    }

    return render(request, 'game/create_game.html', context)

@login_required
def game_detail(request, game_id):
    """Детальная информация об игре"""
    
    game = get_object_or_404(Game, id=game_id, is_active=True)
    
    # Проверяем, может ли пользователь видеть эту игру
    if game.is_private and game.organizer != request.user:
        if request.user.is_anonymous or request.user not in game.participants.all():
            messages.error(request, 'Это приватная игра')
            return redirect('home')
    
    # Участники игры (используем прямую связь из модели Game)
    participants = game.participants.all()

    # Проверяем, участвует ли текущий пользователь (включая организатора)
    is_participant = request.user.is_authenticated and (request.user in participants or request.user == game.organizer)
    can_join = request.user.is_authenticated and request.user != game.organizer and not is_participant and game.participants.count() < game.max_players

    context = {
        'page_title': game.title,
        'game': game,
        'participants': participants,
        'is_participant': is_participant,
        'can_join': can_join,
        'spots_left': game.spots_left(),
        'total_participants_count': game.participants.count(),  # Общее количество участников
    }

    return render(request, 'game/game_detail.html', context)

@login_required
def leave_game(request, game_id):
    """Покинуть игру"""

    game = get_object_or_404(Game, id=game_id, is_active=True)

    # Проверяем, может ли пользователь покинуть игру
    if request.user == game.organizer:
        messages.warning(request, 'Организатор не может покинуть свою игру')
        return redirect('game_detail', game_id=game_id)

    # Проверяем, участвует ли пользователь в игре
    if request.user not in game.participants.all():
        messages.warning(request, 'Вы не участвуете в этой игре')
        return redirect('game_detail', game_id=game_id)

    if request.method == 'POST':
        # Удаляем пользователя из участников
        game.participants.remove(request.user)

        # Удаляем запись из GameParticipation
        GameParticipation.objects.filter(game=game, user=request.user).delete()

        messages.success(request, '❌ Вы покинули игру')
        return redirect('game_detail', game_id=game_id)

    # Если GET запрос, перенаправляем на страницу игры
    return redirect('game_detail', game_id=game_id)

@login_required
def join_game(request, game_id):
    """Вступить в игру"""
    
    game = get_object_or_404(Game, id=game_id, is_active=True)
    
    # Проверяем, может ли пользователь присоединиться
    if request.user == game.organizer:
        messages.warning(request, 'Вы являетесь организатором этой игры')
        return redirect('game_detail', game_id=game_id)

    # Проверяем, можно ли присоединиться
    if game.participants.count() >= game.max_players:
        messages.error(request, 'В игре нет свободных мест')
        return redirect('game_detail', game_id=game_id)

    # Проверяем, не участвует ли уже пользователь
    if GameParticipation.objects.filter(game=game, user=request.user).exists():
        messages.warning(request, 'Вы уже участвуете в этой игре')
        return redirect('game_detail', game_id=game_id)
    
    if request.method == 'POST':
        form = GameJoinForm(request.POST)
        
        if form.is_valid():
            participation = form.save(commit=False)
            participation.user = request.user
            participation.game = game
            participation.status = 'pending' if game.is_private else 'confirmed'
            participation.save()

            # Также добавляем пользователя в participants ManyToManyField
            game.participants.add(request.user)

            if game.is_private:
                messages.success(request, '✅ Заявка на участие отправлена организатору')
            else:
                messages.success(request, '✅ Вы успешно присоединились к игре!')
            
            return redirect('game_detail', game_id=game_id)
    else:
        form = GameJoinForm()
    
    context = {
        'page_title': f'Вступление в игру: {game.title}',
        'game': game,
        'form': form,
    }
    
    return render(request, 'game/join_game.html', context)

@login_required
def my_games(request):
    """Мои игры (организованные и участвую)"""
    
    # Игры, которые я организовал
    organized_games = Game.objects.filter(
        organizer=request.user,
        is_active=True
    ).order_by('game_date', 'game_time')
    
    # Игры, в которых я участвую
    participations = GameParticipation.objects.filter(
        user=request.user
    ).select_related('game')
    
    participating_games = [p.game for p in participations if p.game.is_active]
    
    # Предстоящие игры (используем timezone.now())
    upcoming_games = Game.objects.filter(
        game_date__gte=timezone.now().date(),
        is_active=True
    ).exclude(organizer=request.user).order_by('game_date', 'game_time')[:10]
    
    context = {
        'page_title': 'Мои игры',
        'organized_games': organized_games,
        'participating_games': participating_games,
        'upcoming_games': upcoming_games,
    }
    
    return render(request, 'my_games.html', context)

# ============================================================================
# ПОИСК И ПРОФИЛИ
# ============================================================================

def search_players(request):
    """Поиск игроков"""
    
    form = SearchForm(request.GET or None)
    results = []
    
    if form.is_valid():
        query = form.cleaned_data.get('query', '')
        city = form.cleaned_data.get('city', '')
        position = form.cleaned_data.get('position', '')
        skill_level = form.cleaned_data.get('skill_level', '')
        min_age = form.cleaned_data.get('min_age')
        max_age = form.cleaned_data.get('max_age')
        
        # Базовый запрос
        profiles = UserProfile.objects.select_related('user').filter(
            user__is_active=True
        )
        
        # Применяем фильтры
        if query:
            profiles = profiles.filter(
                Q(user__username__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(bio__icontains=query) |
                Q(city__icontains=query)
            )
        
        if city:
            profiles = profiles.filter(city__icontains=city)
        
        if position:
            profiles = profiles.filter(position=position)
        
        if skill_level:
            profiles = profiles.filter(skill_level=skill_level)
        
        if min_age:
            profiles = profiles.filter(age__gte=min_age)
        
        if max_age:
            profiles = profiles.filter(age__lte=max_age)
        
        results = profiles.order_by('user__username')
    
    # Пагинация
    paginator = Paginator(results, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем ID д��узей текуще��о пользов��теля
    friends_list = []
    sent_requests = []
    received_requests = []

    if request.user.is_authenticated:
        # Список друзей (принятые запросы)
        friends = Friendship.objects.filter(
            (Q(from_user=request.user) | Q(to_user=request.user)),
            status='accepted'
        )

        friends_list = []
        for friendship in friends:
            friend_id = friendship.to_user.id if friendship.from_user == request.user else friendship.from_user.id
            friends_list.append(friend_id)

        # Исходящие запросы
        sent_requests = list(Friendship.objects.filter(
            from_user=request.user,
            status='pending'
        ).values_list('to_user_id', flat=True))

        # Входящие запросы
        received_requests = list(Friendship.objects.filter(
            to_user=request.user,
            status='pending'
        ).values_list('from_user_id', flat=True))

    context = {
        'page_title': 'Поиск игроков',
        'form': form,
        'page_obj': page_obj,
        'results_count': len(results),
        'friends_list': friends_list,
        'sent_requests': sent_requests,
        'received_requests': received_requests,
    }

    return render(request, 'user/search.html', context)

@login_required
def profile(request, user_id):
    """Просмотр профиля пользователя"""

    user = get_object_or_404(User, id=user_id, is_active=True)
    profile = get_object_or_404(UserProfile, user=user)

    # Проверяем дружбу
    is_friend = False
    friendship_status = None

    if request.user.is_authenticated and request.user != user:
        friendship = Friendship.objects.filter(
            (Q(from_user=request.user) & Q(to_user=user)) |
            (Q(from_user=user) & Q(to_user=request.user))
        ).first()

        if friendship:
            is_friend = friendship.status == 'accepted'
            friendship_status = friendship.status

    # Игры пользователя
    organized_games = Game.objects.filter(
        organizer=user,
        is_active=True
    ).order_by('-game_date')[:3]

    # Бронирования пользователя
    recent_bookings = CourtBooking.objects.filter(
        user=user,
        booking_date__gte=timezone.now().date()
    ).order_by('booking_date', 'start_time')[:3]

    # Получаем друзей пользователя
    friends = User.objects.filter(
        Q(friendships_sent__to_user=user, friendships_sent__status='accepted') |
        Q(friendships_received__from_user=user, friendships_received__status='accepted')
    ).distinct().order_by('username')[:9]  # Ограничиваем первые 9 друзей для отображения

    # Получаем общее количество друзей
    friends_count = User.objects.filter(
        Q(friendships_sent__to_user=user, friendships_sent__status='accepted') |
        Q(friendships_received__from_user=user, friendships_received__status='accepted')
    ).distinct().count()

    context = {
        'page_title': f'Профиль: {user.username}',
        'profile_user': user,
        'profile': profile,
        'is_friend': is_friend,
        'friendship_status': friendship_status,
        'organized_games': organized_games,
        'recent_bookings': recent_bookings,
        'is_own_profile': request.user == user,
        'friends': friends,
        'friends_count': friends_count,
        'all_friends': friends,  # для модального окна
    }

    return render(request, 'user/profile.html', context)

@login_required
def friends_list(request, user_id=None):
    """Страница со всеми друзьями пользователя"""
    if user_id:
        user = get_object_or_404(User, id=user_id, is_active=True)
    else:
        user = request.user
    
    profile = get_object_or_404(UserProfile, user=user)
    
    # Получаем всех друзей
    friends = User.objects.filter(
        Q(friendships_sent__to_user=user, friendships_sent__status='accepted') |
        Q(friendships_received__from_user=user, friendships_received__status='accepted')
    ).distinct().order_by('username')
    
    # Получаем заявки в друзья (для текущего пользователя)
    friend_requests = None
    if request.user == user:
        friend_requests = Friendship.objects.filter(
            to_user=request.user,
            status='pending'
        ).select_related('from_user')
    
    # Добавляем пагинацию для друзей
    from django.core.paginator import Paginator
    paginator = Paginator(friends, 12)  # 12 друзей на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Дополнительная статистика
    friends_with_games_count = friends.filter(games_joined__isnull=False).distinct().count()
    friends_in_city_count = friends.filter(profile__city=user.profile.city).count() if hasattr(user, 'profile') and user.profile.city else 0
    # Для простоты считаем, что все друзья онлайн (в реальном приложении это было бы по сессиям)
    friends_online_count = friends.count()  # условно

    context = {
        'page_title': f'Друзья {user.username}',
        'profile_user': user,
        'profile': profile,
        'friends': page_obj,  # передаем постранично
        'friends_count': friends.count(),
        'friend_requests': friend_requests,
        'is_own_profile': request.user == user,
        'page_obj': page_obj,
        'friends_with_games_count': friends_with_games_count,
        'friends_in_city_count': friends_in_city_count,
        'friends_online_count': friends_online_count,
    }

    return render(request, 'user/friends_list.html', context)

@login_required
def friend_requests(request):
    """Управление заявками в друзья"""

    # Получаем входящие заявки
    incoming_requests = Friendship.objects.filter(
        to_user=request.user,
        status='pending'
    ).select_related('from_user', 'from_user__profile')

    # Получаем исходящие заявки
    outgoing_requests = Friendship.objects.filter(
        from_user=request.user,
        status='pending'
    ).select_related('to_user', 'to_user__profile')

    # Получаем список друзей
    friends = User.objects.filter(
        Q(friendships_sent__to_user=request.user, friendships_sent__status='accepted') |
        Q(friendships_received__from_user=request.user, friendships_received__status='accepted')
    ).distinct().order_by('username')

    context = {
        'page_title': 'Заявки в друзья',
        'incoming_requests': incoming_requests,
        'outgoing_requests': outgoing_requests,
        'friends': friends,
        'friends_count': friends.count(),
    }

    return render(request, 'user/friend_requests.html', context)

@login_required
def edit_profile(request):
    """Редактирование профиля"""
    
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Профиль успешно обновлён')
            return redirect('profile', user_id=request.user.id)
        else:
            messages.error(request, '❌ Пожалуйста, исправьте ошибки в форме')
    else:
        form = ProfileEditForm(instance=profile)
    
    context = {
        'page_title': 'Редактирование проф��ля',
        'form': form,
        'profile': profile,
        'user': request.user,
    }
    
    return render(request, 'user/edit_profile.html', context)

@login_required
def upload_avatar(request):
    """Загрузка аватара"""
    
    if request.method == 'POST':
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        form = AvatarUploadForm(request.POST, request.FILES, instance=profile)
        
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Аватар успешно обновлён')
        else:
            messages.error(request, 'Ошибка при загрузке аватара')
    
    return redirect('edit_profile')

# ============================================================================
# СИСТЕМА ДРУЗЕЙ
# ============================================================================

@login_required
def add_friend(request, user_id):
    """Добавить в друзья"""

    if request.method == 'POST':
        friend_user = get_object_or_404(User, id=user_id, is_active=True)

        if request.user == friend_user:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Нельзя добавить себя в друзья'})
            messages.error(request, 'Нельзя добавить себя в друзья')
            return redirect('profile', user_id=user_id)

        # Проверяем, существует ли уже заявка
        existing = Friendship.objects.filter(
            from_user=request.user,
            to_user=friend_user
        ).first()

        if existing:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Заявка уже отправлена'})
            messages.warning(request, 'Заявка уже отправлена')
        else:
            Friendship.objects.create(
                from_user=request.user,
                to_user=friend_user,
                status='pending'
            )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': f'Заявка в друзья отправлена пользователю {friend_user.username}'})
            messages.success(request, f'✅ Заявка в друзья отправлена пользователю {friend_user.username}')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Заявка в друзья отправлена'})

    # Если не POST запрос, перенаправляем на профиль
    return redirect('profile', user_id=user_id)

@login_required
def accept_friend(request, friendship_id):
    """Принять заявку в друзья"""

    if request.method == 'POST':
        friendship = get_object_or_404(Friendship, id=friendship_id, to_user=request.user)

        if friendship.status == 'pending':
            friendship.status = 'accepted'
            friendship.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': f'Вы приняли заявку в друзья от {friendship.from_user.username}'})
            messages.success(request, f'✅ Вы приняли заявку в друзья от {friendship.from_user.username}')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Заявка уже обработана'})

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Заявка в друзья принята'})

    return redirect('profile', user_id=request.user.id)

@login_required
def reject_friend(request, friendship_id):
    """Отклонить заявку в друзья"""

    if request.method == 'POST':
        friendship = get_object_or_404(Friendship, id=friendship_id, to_user=request.user)

        if friendship.status == 'pending':
            friendship.status = 'rejected'
            friendship.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': f'Заявка в друзья от {friendship.from_user.username} отклонена'})
            messages.info(request, f'Заявка в друзья от {friendship.from_user.username} отклонена')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Заявка уже обработана'})

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Заявка в друзья отклонена'})

    return redirect('profile', user_id=request.user.id)

@login_required
def remove_friend(request, user_id):
    """Удалить из друзей"""

    if request.method == 'POST':
        friend_user = get_object_or_404(User, id=user_id)

        # Удаляем обе связи
        deleted_count, _ = Friendship.objects.filter(
            Q(from_user=request.user, to_user=friend_user) |
            Q(from_user=friend_user, to_user=request.user)
        ).delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if deleted_count > 0:
                return JsonResponse({'success': True, 'message': f'Пользователь {friend_user.username} удален из друзей'})
            else:
                return JsonResponse({'success': False, 'error': 'Дружба не найдена'})

        messages.info(request, f'Пользователь {friend_user.username} удалён из друзей')
        return redirect('profile', user_id=request.user.id)

    # Если не POST запрос, перенаправляем на профиль
    return redirect('profile', user_id=request.user.id)

# ============================================================================
# ОТЗЫВЫ И РЕЙТИНГИ
# ============================================================================

@login_required
def add_review(request, court_id):
    """Добавить отзыв о площадке"""
    
    court = get_object_or_404(VolleyballCourt, id=court_id, status='approved')
    
    # Проверяем, есть ли уже отзыв от этого пользователя
    existing_review = Review.objects.filter(court=court, user=request.user).first()
    
    # Пров��ряем, было ли бронирование у этого пользователя
    has_booking = CourtBooking.objects.filter(
        court=court,
        user=request.user,
        status__in=['confirmed', 'completed']
    ).exists()
    
    if not has_booking:
        messages.warning(request, 'Вы можете остави��ь отзыв только по��ле бронирования площадки')
        return redirect('court_detail', court_id=court_id)
    
    if request.method == 'POST':
        if existing_review:
            form = ReviewForm(request.POST, instance=existing_review)
        else:
            form = ReviewForm(request.POST)
        
        if form.is_valid():
            review = form.save(commit=False)
            review.court = court
            review.user = request.user
            review.is_published = True
            review.save()
            
            # Обновляем рейтинг площадки
            update_court_rating(court)
            
            messages.success(request, '✅ Спасибо за ваш отзыв!')
            return redirect('court_detail', court_id=court_id)
    else:
        if existing_review:
            form = ReviewForm(instance=existing_review)
        else:
            form = ReviewForm()
    
    context = {
        'page_title': f'Отзыв о площадке: {court.name}',
        'court': court,
        'form': form,
        'existing_review': existing_review,
    }
    
    return render(request, 'add_review.html', context)

def update_court_rating(court):
    """Обновление рейтинга площадки на основе отзывов"""
    reviews = Review.objects.filter(court=court, is_published=True)
    
    if reviews.exists():
        avg_rating = reviews.aggregate(
            avg=Avg('rating_overall')
        )['avg'] or 0
        
        court.rating = avg_rating
        court.save()

# ============================================================================
# ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def court_detail(request, court_id):
    """Детальн��я страница площадки"""
    
    court = get_object_or_404(VolleyballCourt, id=court_id, status='approved')
    
    # Получаем отзывы
    reviews = Review.objects.filter(court=court, is_published=True).order_by('-created_at')
    
    # Получаем фотографии
    photos = CourtPhoto.objects.filter(court=court).order_by('-is_main')
    
    # Проверяем, может ли пользователь оставить отзыв
    can_review = False
    if request.user.is_authenticated:
        has_booking = CourtBooking.objects.filter(
            court=court,
            user=request.user,
            status__in=['confirmed', 'completed']
        ).exists()
        has_review = Review.objects.filter(court=court, user=request.user).exists()
        can_review = has_booking and not has_review
    
    context = {
        'page_title': court.name,
        'court': court,
        'reviews': reviews,
        'photos': photos,
        'can_review': can_review,
        'reviews_count': reviews.count(),
        'avg_rating': court.rating,
    }
    
    return render(request, 'court/court_detail.html', context)

@login_required
def dashboard(request):
    """Личный кабинет пользователя"""
    
    # Статистика
    organized_games_count = Game.objects.filter(organizer=request.user, is_active=True).count()
    participating_games_count = GameParticipation.objects.filter(user=request.user).count()
    bookings_count = CourtBooking.objects.filter(user=request.user).count()
    suggestions_count = VolleyballCourt.objects.filter(suggested_by=request.user).count()
    
    # Последние активности
    recent_games = Game.objects.filter(
        organizer=request.user,
        is_active=True
    ).order_by('-created_at')[:5]
    
    recent_bookings = CourtBooking.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    upcoming_bookings = CourtBooking.objects.filter(
        user=request.user,
        booking_date__gte=timezone.now().date(),
        status__in=['pending', 'confirmed']
    ).order_by('booking_date', 'start_time')[:5]
    
    context = {
        'page_title': 'Личный кабинет',
        'organized_games_count': organized_games_count,
        'participating_games_count': participating_games_count,
        'bookings_count': bookings_count,
        'suggestions_count': suggestions_count,
        'recent_games': recent_games,
        'recent_bookings': recent_bookings,
        'upcoming_bookings': upcoming_bookings,
    }
    
    return render(request, 'dashboard.html', context)

# ============================================================================
# АВТОРИЗАЦИЯ И РЕГИСТРАЦИЯ
# ============================================================================

from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


def login_view(request):
    """Вход в систему"""
    
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Перенаправляем на следующую страницу или домой
            next_page = request.GET.get('next', 'home')
            return redirect(next_page)
    else:
        form = AuthenticationForm()
    
    context = {
        'page_title': 'Вход в систему',
        'form': form,
    }
    
    return render(request, 'user/login.html', context)

@login_required
def logout_view(request):
    """Выход из системы"""
    
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы')
    return redirect('home')

# ============================================================================
# ТЕСТОВАЯ СТРАНИЦА
# ============================================================================

def test_change(request):
    """Тестовая страница для проверки изменений"""
    
    context = {
        'page_title': 'Тестовая страница',
        'message': 'Система работает корректно!',
        'timestamp': timezone.now(),
        'bookings_count': CourtBooking.objects.count(),
        'time_slots_count': TimeSlot.objects.count(),
        'reviews_count': Review.objects.count(),
    }
    
    return render(request, 'test_change.html', context)

# ============================================================================
# ОБРАБОТЧИК ОШИБОК
# ============================================================================



def event_calendar(request):
    """Страница календаря событий"""
    from datetime import date

    # Получаем параметр фильтра из URL
    filter_param = request.GET.get('filter', 'all')

    # Фильтруем игры в зависимости от параметра
    if filter_param == 'today':
        # Только игры на сегодня
        games = Game.objects.filter(
            is_active=True,
            game_date=date.today()
        ).select_related('organizer', 'court').order_by('game_date', 'game_time')
    elif filter_param == 'upcoming':
        # Только предстоящие игры (включая сегодня)
        games = Game.objects.filter(
            is_active=True,
            game_date__gte=date.today()
        ).select_related('organizer', 'court').order_by('game_date', 'game_time')
    else:  # filter == 'all' или по умолчанию
        # Все активные игры
        games = Game.objects.filter(is_active=True).select_related('organizer', 'court').order_by('game_date', 'game_time')

    # Подготовим данные для календаря
    games_by_date = {}
    for game in games:
        date_key = game.game_date.strftime('%Y-%m-%d')
        if date_key not in games_by_date:
            games_by_date[date_key] = []
        games_by_date[date_key].append({
            'id': game.id,
            'title': game.title,
            'description': game.description,
            'time': game.game_time.strftime('%H:%M'),
            'location': game.location,
            'organizer': game.organizer.username,
            'sport_type': game.get_sport_type_display(),
            'skill_level': game.get_skill_level_display(),
            'max_players': game.max_players,
            'current_players': game.participants.count(),
        })

    context = {
        'page_title': 'Календарь событий',
        'games_by_date': games_by_date,
        'all_games': games,
        'filter_param': filter_param,  # Передаем параметр фильтра в шаблон
    }
    return render(request, 'common/event_calendar.html', context)

# ============================================================================
# ФУНКЦИИ ДЛЯ ПРОФИЛЯ И ДРУЗЕЙ (добавьте эти функции в views.py)
# ============================================================================

def user_profile_view(request, user_id):
    """Просмотр профиля пользователя"""
    profile_user = get_object_or_404(User, id=user_id, is_active=True)
    
    # Определяем статус дружбы
    friendship_status = 'none'
    friendship = None
    
    if request.user.is_authenticated:
        # Проверяем, есть ли заявка в друзья
        friendship = Friendship.objects.filter(
            (Q(from_user=request.user) & Q(to_user=profile_user)) |
            (Q(from_user=profile_user) & Q(to_user=request.user))
        ).first()
        
        if friendship:
            friendship_status = friendship.status
    
    context = {
        'page_title': f'Профиль пользователя {profile_user.username}',
        'profile_user': profile_user,
        'friendship_status': friendship_status,
        'friendship': friendship,
    }
    
    return render(request, 'profile_detail.html', context)

@login_required
def send_friend_request(request, user_id):
    """Отправка заявки в друзья"""
    to_user = get_object_or_404(User, id=user_id)
    
    # Нельзя отправлять заявку самому себе
    if request.user == to_user:
        return redirect('user_profile', user_id=user_id)
    
    # Проверяем, не отправили ли уже заявку
    existing_request = Friendship.objects.filter(
        from_user=request.user,
        to_user=to_user
    ).first()
    
    if not existing_request:
        # Проверяем, нет ли уже обратной заявки
        reverse_request = Friendship.objects.filter(
            from_user=to_user,
            to_user=request.user
        ).first()
        
        if reverse_request:
            # Если есть обратная заявка, принимаем ее
            reverse_request.status = 'accepted'
            reverse_request.save()
        else:
            # Создаем новую заявку
            Friendship.objects.create(
                from_user=request.user,
                to_user=to_user,
                status='pending'
            )
    
    return redirect('user_profile', user_id=user_id)

@login_required
def cancel_friend_request(request, request_id):
    """Отмена отправленной заявки"""
    friendship = get_object_or_404(Friendship, id=request_id, from_user=request.user)
    user_id = friendship.to_user.id
    friendship.delete()
    return redirect('user_profile', user_id=user_id)

@login_required
def accept_friend_request(request, request_id):
    """Принятие заявки в друзья"""
    friendship = get_object_or_404(Friendship, id=request_id, to_user=request.user)
    friendship.status = 'accepted'
    friendship.save()
    return redirect('user_profile', user_id=friendship.from_user.id)

@login_required
def reject_friend_request(request, request_id):
    """Отклонение заявки в друзья"""
    friendship = get_object_or_404(Friendship, id=request_id, to_user=request.user)
    user_id = friendship.from_user.id
    friendship.delete()
    return redirect('user_profile', user_id=user_id)

@login_required
def remove_friend(request, friendship_id):
    """Удаление из друзей"""
    friendship = get_object_or_404(Friendship, id=friendship_id)
    
    # Проверяем, что пользователь является участником дружбы
    if friendship.from_user == request.user or friendship.to_user == request.user:
        user_id = friendship.to_user.id if friendship.from_user == request.user else friendship.from_user.id
        friendship.delete()
        return redirect('user_profile', user_id=user_id)

    return redirect('friends')


@login_required
def create_court(request):
    """Форма для создания новой площадки (отправляется на модерацию)"""

    if request.method == 'POST':
        form = CourtSuggestionForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                # Создаём площадку
                court = form.save(commit=False)
                court.suggested_by = request.user
                court.status = 'pending'
                court.is_active = True
                court.is_verified = False

                # Сохраняем координаты если они есть
                latitude = form.cleaned_data.get('latitude')
                longitude = form.cleaned_data.get('longitude')
                if latitude and longitude:
                    court.latitude = latitude
                    court.longitude = longitude

                court.save()

                # Обрабатываем загруженные фото
                photos = request.FILES.getlist('photos')
                for i, photo in enumerate(photos):
                    is_main = (i == 0)  # Первое фото делаем главным
                    CourtPhoto.objects.create(
                        court=court,
                        photo=photo,
                        is_main=is_main
                    )

                messages.success(request,
                    '✅ Спасибо! Ваша площадка отправлена на модерацию. '
                    'Площадка появится на карте после проверки администратором.'
                )

                return redirect('my_suggestions')

            except Exception as e:
                messages.error(request, f'Ошибка при сохранении: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        form = CourtSuggestionForm()

    context = {
        'page_title': 'Создать новую площадку',
        'form': form,
    }

    return render(request, 'court/create_court.html', context)




def search_courts_view(request):
    """Отображение страницы поиска волейбольных площадок"""
    return render(request, 'court/map.html')


def search_courts_api(request):
    """API для поиска волейбольных площадок"""
    query = request.GET.get('query', '')
    court_type = request.GET.get('court_type', '')
    surface = request.GET.get('surface', '')
    city = request.GET.get('city', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    free_only = request.GET.get('free_only', '') == 'true'
    with_lighting = request.GET.get('with_lighting', '') == 'true'
    with_parking = request.GET.get('with_parking', '') == 'true'
    with_showers = request.GET.get('with_showers', '') == 'true'
    with_locker_rooms = request.GET.get('with_locker_rooms', '') == 'true'
    with_equipment = request.GET.get('with_equipment', '') == 'true'

    # Начинаем с базового QuerySet
    courts = VolleyballCourt.objects.filter(
        is_active=True,
        status='approved'
    )

    # Применяем фильтры
    if query:
        courts = courts.filter(
            Q(name__icontains=query) | Q(address__icontains=query)
        )

    if court_type:
        courts = courts.filter(court_type=court_type)

    if surface:
        courts = courts.filter(surface=surface)

    if city:
        courts = courts.filter(city__icontains=city)

    if price_min:
        try:
            price_min_val = int(price_min)
            courts = courts.filter(price_per_hour__gte=price_min_val)
        except ValueError:
            pass

    if price_max:
        try:
            price_max_val = int(price_max)
            courts = courts.filter(price_per_hour__lte=price_max_val)
        except ValueError:
            pass

    if free_only:
        courts = courts.filter(is_free=True)

    if with_lighting:
        courts = courts.filter(is_lighted=True)

    if with_parking:
        courts = courts.filter(has_parking=True)

    if with_showers:
        courts = courts.filter(has_showers=True)

    if with_locker_rooms:
        courts = courts.filter(has_locker_rooms=True)

    if with_equipment:
        courts = courts.filter(has_equipment_rental=True)

    # Получаем значения
    courts = courts.values(
        'id', 'name', 'address', 'latitude', 'longitude',
        'court_type', 'surface', 'is_free', 'is_lighted',
        'has_parking', 'has_showers', 'has_locker_rooms',
        'has_equipment_rental', 'has_cafe', 'description',
        'status', 'price_per_hour', 'opening_time', 'closing_time',
        'city', 'rating'
    )

    # Преобразуем Decimal значения в float для JSON сериализации
    courts_list = []
    for court in courts:
        court_dict = {}
        for key, value in court.items():
            if isinstance(value, decimal.Decimal):
                court_dict[key] = float(value)
            else:
                court_dict[key] = value
        courts_list.append(court_dict)

    return JsonResponse(courts_list, safe=False)
# Импорты для SEO функций
from .seo_views import robots_txt, sitemap_xml
