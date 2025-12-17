# myapp/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Game, Location, UserProfile, VolleyballCourt, Friendship
import json
from datetime import datetime, timedelta
import calendar

@login_required
def create_court_view(request):
    """Создание новой волейбольной площадки"""
    if request.method == 'POST':
        try:
            # Получаем данные из формы
            name = request.POST.get('name', '').strip()
            address = request.POST.get('address', '').strip()
            city = request.POST.get('city', '').strip()
            court_type = request.POST.get('court_type', 'outdoor')
            description = request.POST.get('description', '').strip()
            is_free = request.POST.get('is_free') == 'on'
            
            # Цена
            price_str = request.POST.get('price', '0')
            try:
                price_per_hour = float(price_str)
            except:
                price_per_hour = 0
            
            # Проверка обязательных полей
            if not name or not address or not city:
                messages.error(request, 'Заполните название, адрес и город')
                return render(request, 'myapp/create_court.html')
            
            # Создаём площадку
            court = VolleyballCourt.objects.create(
                name=name,
                address=address,
                city=city,
                court_type=court_type,
                description=description,
                is_free=is_free,
                price_per_hour=price_per_hour,
                suggested_by=request.user,
                status='pending'
            )
            
            messages.success(request, 
                '✅ Площадка отправлена на модерацию! '
                'Она появится на карте после проверки администратором.'
            )
            return redirect('map')
            
        except Exception as e:
            messages.error(request, f'Ошибка: {str(e)}')
    
    # GET запрос - показываем форму
    return render(request, 'myapp/create_court.html')

def courts_api_view(request):
    """API для получения площадок"""
    # Получаем только одобренные площадки
    courts = VolleyballCourt.objects.filter(status='approved')
    
    courts_data = []
    for court in courts:
        court_info = {
            'id': court.id,
            'name': court.name,
            'address': court.address,
            'city': court.city,
            'type': court.court_type,
            'is_free': court.is_free,
            'price': float(court.price_per_hour) if court.price_per_hour else 0,
            'rating': float(court.rating) if court.rating else 0,
        }
        
        if court.latitude and court.longitude:
            court_info['latitude'] = float(court.latitude)
            court_info['longitude'] = float(court.longitude)
        
        courts_data.append(court_info)
    
    return JsonResponse({
        'success': True,
        'courts': courts_data,
        'count': courts.count(),
    })

@login_required
def suggest_court_view(request):
    """Предложить новую площадку"""
    if request.method == 'POST':
        try:
            # Получаем данные из формы
            name = request.POST.get('name')
            address = request.POST.get('address')
            city = request.POST.get('city')
            court_type = request.POST.get('court_type', 'outdoor')
            description = request.POST.get('description', '')
            is_free = request.POST.get('is_free') == 'on'
            
            # Создаём площадку
            court = VolleyballCourt.objects.create(
                name=name,
                address=address,
                city=city,
                court_type=court_type,
                description=description,
                is_free=is_free,
                suggested_by=request.user,
                status='pending'
            )
            
            messages.success(request, 'Спасибо! Ваше предложение отправлено на модерацию.')
            return redirect('map')
            
        except Exception as e:
            messages.error(request, f'Ошибка: {str(e)}')
    
    # Для GET запроса показываем форму
    context = {
        'page_title': 'Предложить новую площадку',
    }
    return render(request, 'myapp/suggest_court.html', context)

def home_view(request):
    """Главная страница с календарём игр"""
    today = datetime.now().date()
    
    # Получаем текущий месяц и год
    try:
        month = int(request.GET.get('month', today.month))
        year = int(request.GET.get('year', today.year))
    except (ValueError, TypeError):
        month = today.month
        year = today.year
    
    # Создаём календарь
    cal = calendar.Calendar()
    weeks = cal.monthdatescalendar(year, month)
    
    # Получаем игры на выбранный месяц
    games = Game.objects.filter(
        date__year=year,
        date__month=month,
        status='active'
    ).order_by('date', 'start_time')
    
    # Группируем игры по дням
    games_by_day = {}
    for game in games:
        day_key = game.date.day
        if day_key not in games_by_day:
            games_by_day[day_key] = []
        games_by_day[day_key].append(game)
    
    # Получаем локации для боковой панели
    locations = Location.objects.filter(is_active=True)[:5]
    
    # Название месяца на русском
    month_names = [
        'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
        'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
    ]
    
    # Статистика
    upcoming_games = Game.objects.filter(
        date__gte=today,
        status='active'
    ).count()
    
    # Игры пользователя
    user_games = []
    if request.user.is_authenticated:
        user_games = Game.objects.filter(
            Q(created_by=request.user) | 
            Q(participants=request.user),
            date__gte=today
        ).distinct()[:5]
    
    context = {
        'page_title': 'Волейбольный клуб - Календарь игр',
        'weeks': weeks,
        'games_by_day': games_by_day,
        'current_month': month,
        'current_year': year,
        'month_name': month_names[month-1],
        'today': today,
        'locations': locations,
        'upcoming_games': upcoming_games,
        'user_games': user_games,
        'user': request.user,
    }
    return render(request, 'myapp/home.html', context)

@login_required
def create_game_view(request):
    """Создание новой игры"""
    if request.method == 'POST':
        # Получаем данные из формы
        title = request.POST.get('title')
        game_type = request.POST.get('game_type')
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        location = request.POST.get('location')
        max_players = request.POST.get('max_players', 12)
        description = request.POST.get('description', '')
        
        # Проверяем обязательные поля
        if not all([title, game_type, date, start_time, end_time, location]):
            messages.error(request, 'Пожалуйста, заполните все обязательные поля')
            return render(request, 'myapp/create_game.html')
        
        try:
            # Создаём игру
            game = Game.objects.create(
                title=title,
                game_type=game_type,
                date=date,
                start_time=start_time,
                end_time=end_time,
                location_text=location,
                max_players=int(max_players),
                description=description,
                created_by=request.user
            )
            messages.success(request, f'Игра "{title}" успешно создана!')
            return redirect('home')
            
        except Exception as e:
            messages.error(request, f'Ошибка при создании игры: {str(e)}')
            return render(request, 'myapp/create_game.html')
    
    # Для GET запроса
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    context = {
        'tomorrow': tomorrow,
        'courts': VolleyballCourt.objects.filter(status='approved')[:10],
    }
    return render(request, 'myapp/create_game.html', context)

@login_required
def join_game_view(request, game_id):
    """Присоединиться к игре"""
    game = get_object_or_404(Game, id=game_id)
    
    if not game.can_join:
        messages.error(request, 'Нельзя присоединиться к этой игре')
        return redirect('home')
    
    if request.user in game.participants.all():
        messages.warning(request, 'Вы уже участвуете в этой игре')
    else:
        if game.spots_left > 0:
            game.participants.add(request.user)
            messages.success(request, f'Вы присоединились к игре "{game.title}"')
        else:
            messages.error(request, 'В игре не осталось свободных мест')
    
    return redirect('home')

@login_required
def leave_game_view(request, game_id):
    """Покинуть игру"""
    game = get_object_or_404(Game, id=game_id)
    
    if request.user in game.participants.all():
        game.participants.remove(request.user)
        messages.success(request, f'Вы вышли из игры "{game.title}"')
    else:
        messages.warning(request, 'Вы не участвуете в этой игре')
    
    return redirect('home')

def games_api_view(request):
    """API для получения игр в формате JSON"""
    year = request.GET.get('year', datetime.now().year)
    month = request.GET.get('month', datetime.now().month)
    
    try:
        games = Game.objects.filter(
            date__year=year,
            date__month=month,
            status='active'
        )
        
        games_data = []
        for game in games:
            games_data.append({
                'id': game.id,
                'title': game.title,
                'type': game.get_game_type_display(),
                'date': game.date.strftime('%Y-%m-%d'),
                'day': game.date.day,
                'start_time': game.start_time.strftime('%H:%M'),
                'end_time': game.end_time.strftime('%H:%M'),
                'location': game.location_display,
                'created_by': game.created_by.username,
                'max_players': game.max_players,
                'current_players': game.participants.count(),
                'spots_left': game.spots_left,
            })
        
        return JsonResponse({
            'success': True,
            'games': games_data,
            'month': int(month),
            'year': int(year),
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def search_players_view(request):
    """Поиск игроков"""
    players = UserProfile.objects.all()
    
    # Фильтрация
    query = request.GET.get('q', '')
    city = request.GET.get('city', '')
    position = request.GET.get('position', '')
    
    if query:
        players = players.filter(
            Q(user__username__icontains=query) |
            Q(bio__icontains=query) |
            Q(city__icontains=query)
        )
    
    if city:
        players = players.filter(city__icontains=city)
    
    if position:
        players = players.filter(position=position)
    
    context = {
        'players': players,
        'query': query,
        'city': city,
        'position': position,
        'positions': UserProfile.POSITION_CHOICES,
    }
    return render(request, 'myapp/search.html', context)

def my_suggestions_view(request):
    """Мои предложенные площадки"""
    if not request.user.is_authenticated:
        return redirect('home')
    
    courts = VolleyballCourt.objects.filter(suggested_by=request.user)
    
    context = {
        'courts': courts,
        'approved_count': courts.filter(status='approved').count(),
        'pending_count': courts.filter(status='pending').count(),
    }
    return render(request, 'myapp/my-suggestions.html', context)

# myapp/views.py (добавьте эту функцию)
def map_view(request):
    """Страница карты волейбольных площадок"""
    # Получаем все одобренные площадки
    courts = VolleyballCourt.objects.filter(status='approved')
    
    # Подготавливаем данные для JavaScript
    courts_data = []
    for court in courts:
        court_info = {
            'id': court.id,
            'name': court.name,
            'address': court.address or f"{court.city}",
            'city': court.city,
            'type': court.get_court_type_display(),
            'type_code': court.court_type,
            'is_free': court.is_free,
            'price': float(court.price_per_hour) if court.price_per_hour else 0,
            'rating': float(court.rating) if court.rating else 0,
            'description': court.description[:100] if court.description else '',
        }
        
        # Добавляем координаты, если они есть
        if court.latitude and court.longitude:
            court_info['latitude'] = float(court.latitude)
            court_info['longitude'] = float(court.longitude)
        
        courts_data.append(court_info)
    
    # Статистика
    free_courts = courts.filter(is_free=True)
    indoor_courts = courts.filter(court_type='indoor')
    outdoor_courts = courts.filter(court_type='outdoor')
    beach_courts = courts.filter(court_type='beach')
    
    context = {
        'page_title': 'Карта волейбольных площадок',
        'courts': courts,
        'courts_json': json.dumps(courts_data),  # Для JavaScript
        'courts_count': courts.count(),
        'free_courts_count': free_courts.count(),
        'indoor_courts_count': indoor_courts.count(),
        'outdoor_courts_count': outdoor_courts.count(),
        'beach_courts_count': beach_courts.count(),
    }
    
    return render(request, 'myapp/map.html', context)