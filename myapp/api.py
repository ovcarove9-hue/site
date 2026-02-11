"""
API views для приложения myapp
"""
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from .models import Game


def games_by_date_api(request):
    """API для получения игр по дате"""
    date_str = request.GET.get('date')

    if not date_str:
        return JsonResponse({'error': 'Не указана дата'}, status=400)

    try:
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Неверный формат даты'}, status=400)

    # Получаем игры на указанную дату
    games_queryset = Game.objects.filter(
        game_date=query_date,
        is_active=True
    ).select_related('organizer').prefetch_related('participants').order_by('game_time')
    games = list(games_queryset)

    games_data = []
    for game in games:
        can_join = False
        if request.user.is_authenticated:
            can_join = (
                game.organizer != request.user and
                not game.participants.filter(id=request.user.id).exists() and
                game.participants.count() < game.max_players
            )

        games_data.append({
            'id': game.id,
            'title': game.title,
            'description': game.description or '',
            'time': game.game_time.strftime('%H:%M'),
            'location': game.location,
            'participants': game.participants.count(),
            'max_players': game.max_players,
            'organizer': game.organizer.username,
            'can_join': can_join,
        })

    return JsonResponse({
        'date': date_str,
        'games': games_data,
        'count': len(games_data)
    })