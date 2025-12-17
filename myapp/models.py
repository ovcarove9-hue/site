# myapp/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
import json
from datetime import datetime, timedelta
import calendar

@login_required
def suggest_court_view(request):
    """Форма для предложения новой площадки"""
    if request.method == 'POST':
        form = CourtSuggestionForm(request.POST)
        coord_form = CourtCoordinatesForm(request.POST)
        
        if form.is_valid() and coord_form.is_valid():
            try:
                # Создаём площадку
                court = form.save(commit=False)
                court.suggested_by = request.user
                court.status = 'pending'
                
                # Добавляем координаты если есть
                latitude = coord_form.cleaned_data.get('latitude')
                longitude = coord_form.cleaned_data.get('longitude')
                if latitude and longitude:
                    court.latitude = latitude
                    court.longitude = longitude
                
                court.save()
                
                messages.success(request, 
                    '✅ Спасибо! Ваше предложение отправлено на модерацию. '
                    'Площадка появится на карте после проверки администратором.'
                )
                
                # Отправляем уведомление администраторам (в реальном проекте)
                # notify_admins_about_new_court(court)
                
                return redirect('my_suggestions')
                
            except Exception as e:
                messages.error(request, f'Ошибка при сохранении: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        form = CourtSuggestionForm()
        coord_form = CourtCoordinatesForm()
    
    context = {
        'page_title': 'Предложить новую площадку',
        'form': form,
        'coord_form': coord_form,
    }
    return render(request, 'myapp/suggest_court.html', context)

def map_view(request):
    """Карта волейбольных площадок (только одобренные)"""
    # Получаем только одобренные площадки
    courts = VolleyballCourt.objects.filter(status='approved', is_verified=True)
    
    # Подготавливаем данные для карты
    courts_data = []
    for court in courts:
        court_info = {
            'id': court.id,
            'name': court.name,
            'address': court.address,
            'city': court.city,
            'type': court.court_type,
            'type_display': court.get_court_type_display(),
            'is_free': court.is_free,
            'price': float(court.price_per_hour) if court.price_per_hour else 0,
            'price_display': court.price_display,
            'rating': float(court.rating) if court.rating else 0,
            'description': court.description[:100] if court.description else '',
            'amenities': court.amenities_list,
            'working_hours': court.working_hours,
            'phone': court.phone,
            'website': court.website,
            'photo_url': court.photo_url,
        }
        
        # Добавляем координаты если они есть
        if court.latitude and court.longitude:
            court_info['latitude'] = float(court.latitude)
            court_info['longitude'] = float(court.longitude)
            court_info['has_coordinates'] = True
        else:
            court_info['has_coordinates'] = False
        
        courts_data.append(court_info)
    
    # Статистика
    context = {
        'page_title': 'Карта волейбольных площадок',
        'courts': courts,
        'courts_json': json.dumps(courts_data),
        'courts_count': courts.count(),
        'free_courts_count': courts.filter(is_free=True).count(),
        'indoor_courts_count': courts.filter(court_type='indoor').count(),
        'outdoor_courts_count': courts.filter(court_type='outdoor').count(),
        'beach_courts_count': courts.filter(court_type='beach').count(),
    }
    
    return render(request, 'myapp/map.html', context)

@login_required
def my_suggestions_view(request):
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
    }
    return render(request, 'myapp/my_suggestions.html', context)

def courts_api_view(request):
    """API для получения площадок (для карты)"""
    status = request.GET.get('status', 'approved')
    
    try:
        if status == 'all':
            courts = VolleyballCourt.objects.all()
        else:
            courts = VolleyballCourt.objects.filter(status=status)
        
        courts_data = []
        for court in courts:
            court_info = {
                'id': court.id,
                'name': court.name,
                'address': court.address,
                'city': court.city,
                'type': court.court_type,
                'status': court.status,
                'status_display': court.get_status_display(),
                'is_free': court.is_free,
                'price': float(court.price_per_hour) if court.price_per_hour else 0,
                'rating': float(court.rating) if court.rating else 0,
                'created_at': court.created_at.strftime('%d.%m.%Y'),
                'suggested_by': court.suggested_by.username if court.suggested_by else 'Неизвестно',
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
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

class VolleyballCourt(models.Model):
    """Модель волейбольной площадки с модерацией"""
    
    COURT_TYPE_CHOICES = [
        ('indoor', '🏠 Крытая'),
        ('outdoor', '☀️ Открытая'),
        ('beach', '🏖️ Пляжная'),
    ]
    
    SURFACE_CHOICES = [
        ('wood', 'Дерево'),
        ('parquet', 'Паркет'),
        ('synthetic', 'Синтетика'),
        ('asphalt', 'Асфальт'),
        ('sand', 'Песок'),
        ('grass', 'Трава'),
    ]
    
    # Статусы для модерации
    STATUS_CHOICES = [
        ('pending', '⏳ На рассмотрении'),
        ('approved', '✅ Одобрена'),
        ('rejected', '❌ Отклонена'),
        ('needs_info', '❓ Требует уточнений'),
    ]
    
    # Основная информация
    name = models.CharField('Название площадки', max_length=200)
    description = models.TextField('Описание', blank=True)
    address = models.CharField('Адрес', max_length=300)
    city = models.CharField('Город', max_length=100)
    
    # Координаты (обязательные для карты)
    latitude = models.DecimalField('Широта', max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField('Долгота', max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Характеристики
    court_type = models.CharField('Тип площадки', max_length=20, choices=COURT_TYPE_CHOICES, default='outdoor')
    surface = models.CharField('Покрытие', max_length=20, choices=SURFACE_CHOICES, default='asphalt')
    courts_count = models.PositiveIntegerField('Количество площадок', default=1)
    
    # Размеры
    length = models.DecimalField('Длина (м)', max_digits=4, decimal_places=1, default=18.0, null=True, blank=True)
    width = models.DecimalField('Ширина (м)', max_digits=4, decimal_places=1, default=9.0, null=True, blank=True)
    
    # Удобства
    is_free = models.BooleanField('Бесплатная', default=False)
    is_lighted = models.BooleanField('Есть освещение', default=False)
    has_showers = models.BooleanField('Есть душ', default=False)
    has_locker_rooms = models.BooleanField('Есть раздевалки', default=False)
    has_equipment_rental = models.BooleanField('Аренда инвентаря', default=False)
    has_bleachers = models.BooleanField('Есть трибуны', default=False)
    has_parking = models.BooleanField('Есть парковка', default=False)
    has_cafe = models.BooleanField('Есть кафе/буфет', default=False)
    
    # Стоимость
    price_per_hour = models.DecimalField('Цена за час (руб)', max_digits=8, decimal_places=2, default=0)
    price_details = models.TextField('Детали оплаты', blank=True, help_text="Например: студентам скидка 50%")
    
    # Контактная информация
    phone = models.CharField('Телефон', max_length=20, blank=True)
    website = models.URLField('Сайт', blank=True)
    email = models.EmailField('Email', blank=True)
    
    # Время работы
    opening_time = models.TimeField('Время открытия', default='08:00')
    closing_time = models.TimeField('Время закрытия', default='22:00')
    working_days = models.CharField('Дни работы', max_length=100, default='Пн-Вс', 
                                    help_text="Например: Пн-Пт 8:00-22:00, Сб-Вс 9:00-20:00")
    
    # Статус модерации
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    is_verified = models.BooleanField('Проверена администрацией', default=False)
    rejection_reason = models.TextField('Причина отклонения', blank=True, 
                                       help_text="Заполняется при отклонении заявки")
    
    # Рейтинг
    rating = models.DecimalField('Рейтинг', max_digits=3, decimal_places=1, default=0)
    total_reviews = models.PositiveIntegerField('Количество отзывов', default=0)
    
    # Кто предложил
    suggested_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name='Предложил',
        related_name='suggested_courts'
    )
    
    # Кто проверил (модератор)
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Проверил',
        related_name='verified_courts'
    )
    
    # Даты
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    verified_at = models.DateTimeField('Дата проверки', null=True, blank=True)
    
    # Теги для поиска
    tags = models.CharField('Теги', max_length=300, blank=True, 
                           help_text="Через запятую: волейбол, спорт, площадка, турниры")
    
    # Фотографии (в реальном проекте сделайте отдельную модель для фото)
    photo_url = models.URLField('Ссылка на фото', blank=True, 
                               help_text="Ссылка на фото площадки (можно загрузить на imgur.com)")
    
    class Meta:
        verbose_name = 'Волейбольная площадка'
        verbose_name_plural = 'Волейбольные площадки'
        ordering = ['-created_at', 'status']
        indexes = [
            models.Index(fields=['status', 'city']),
            models.Index(fields=['is_free', 'is_lighted']),
            models.Index(fields=['rating']),
        ]
    
    def __str__(self):
        status_icon = {
            'pending': '⏳',
            'approved': '✅',
            'rejected': '❌',
            'needs_info': '❓',
        }.get(self.status, '')
        return f"{status_icon} {self.name} ({self.city}) - {self.get_status_display()}"
    
    @property
    def is_visible_on_map(self):
        """Видна ли площадка на карте"""
        return self.status == 'approved' and self.is_verified
    
    @property
    def working_hours(self):
        """Форматированное время работы"""
        return f"{self.opening_time.strftime('%H:%M')} - {self.closing_time.strftime('%H:%M')}"
    
    @property
    def price_display(self):
        """Отображение цены"""
        if self.is_free:
            return "Бесплатно"
        elif self.price_per_hour > 0:
            return f"{self.price_per_hour} руб/час"
        return "Цена не указана"
    
    @property
    def amenities_list(self):
        """Список удобств"""
        amenities = []
        if self.is_lighted:
            amenities.append("Освещение")
        if self.has_showers:
            amenities.append("Душ")
        if self.has_locker_rooms:
            amenities.append("Раздевалки")
        if self.has_equipment_rental:
            amenities.append("Аренда инвентаря")
        if self.has_parking:
            amenities.append("Парковка")
        if self.has_cafe:
            amenities.append("Кафе")
        return amenities
    
    def approve(self, moderator):
        """Одобрить площадку"""
        self.status = 'approved'
        self.is_verified = True
        self.verified_by = moderator
        self.verified_at = timezone.now()
        self.save()
    
    def reject(self, moderator, reason):
        """Отклонить площадку"""
        self.status = 'rejected'
        self.rejection_reason = reason
        self.verified_by = moderator
        self.verified_at = timezone.now()
        self.save()
    
    def request_info(self, moderator):
        """Запросить дополнительную информацию"""
        self.status = 'needs_info'
        self.verified_by = moderator
        self.verified_at = timezone.now()
        self.save()

class Location(models.Model):
    """Модель для локаций/спорткомплексов"""
    
    TYPE_CHOICES = [
        ('sport_complex', 'Спорткомплекс'),
        ('stadium', 'Стадион'),
        ('park', 'Парк'),
        ('beach', 'Пляж'),
        ('school', 'Школа/ВУЗ'),
        ('other', 'Другое'),
    ]
    
    name = models.CharField('Название', max_length=200)
    location_type = models.CharField('Тип', max_length=20, choices=TYPE_CHOICES, default='sport_complex')
    description = models.TextField('Описание', blank=True)
    address = models.CharField('Адрес', max_length=300)
    city = models.CharField('Город', max_length=100)
    
    # Контактная информация
    phone = models.CharField('Телефон', max_length=20, blank=True)
    website = models.URLField('Сайт', blank=True)
    email = models.EmailField('Email', blank=True)
    
    # Координаты
    latitude = models.DecimalField('Широта', max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField('Долгота', max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Удобства
    has_parking = models.BooleanField('Есть парковка', default=False)
    has_locker_rooms = models.BooleanField('Есть раздевалки', default=False)
    has_showers = models.BooleanField('Есть душ', default=False)
    has_cafe = models.BooleanField('Есть кафе', default=False)
    is_lighted = models.BooleanField('Есть освещение', default=False)
    
    # Время работы
    opening_time = models.TimeField('Время открытия', default='08:00')
    closing_time = models.TimeField('Время закрытия', default='22:00')
    
    # Статус
    is_active = models.BooleanField('Активен', default=True)
    rating = models.DecimalField('Рейтинг', max_digits=3, decimal_places=1, default=0)
    
    # Кто добавил
    added_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Добавил',
        related_name='added_locations'
    )
    
    # Даты
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Локация'
        verbose_name_plural = 'Локации'
        ordering = ['city', 'name']
    
    def __str__(self):
        return f"{self.name}, {self.city}"

class Game(models.Model):
    """Модель волейбольной игры/события"""
    
    TYPE_CHOICES = [
        ('training', 'Тренировка'),
        ('game', 'Свободная игра'),
        ('tournament', 'Турнир'),
        ('match', 'Товарищеский матч'),
        ('sparring', 'Спарринг'),
    ]
    
    LEVEL_CHOICES = [
        ('any', 'Любой'),
        ('beginner', 'Начинающий'),
        ('intermediate', 'Любитель'),
        ('advanced', 'Продвинутый'),
        ('professional', 'Профессионал'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('full', 'Заполнена'),
        ('cancelled', 'Отменена'),
        ('completed', 'Завершена'),
    ]
    
    # Основная информация
    title = models.CharField('Название игры', max_length=200)
    game_type = models.CharField('Тип', max_length=20, choices=TYPE_CHOICES, default='game')
    description = models.TextField('Описание', blank=True)
    
    # Время и дата
    date = models.DateField('Дата игры')
    start_time = models.TimeField('Время начала')
    end_time = models.TimeField('Время окончания')
    duration = models.DecimalField('Продолжительность (часы)', max_digits=3, decimal_places=1, default=2.0)
    
    # Место проведения
    court = models.ForeignKey(
        VolleyballCourt, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Площадка',
        related_name='games'
    )
    location_text = models.CharField('Место проведения', max_length=300, blank=True)
    
    # Участники
    max_players = models.PositiveIntegerField('Максимум игроков', default=12)
    min_skill_level = models.CharField('Минимальный уровень', max_length=20, choices=LEVEL_CHOICES, default='any')
    game_format = models.CharField('Формат', max_length=20, default='6v6')
    
    # Организатор и участники
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='Организатор',
        related_name='organized_games'
    )
    participants = models.ManyToManyField(
        User,
        verbose_name='Участники',
        related_name='participating_games',
        blank=True
    )
    
    # Стоимость
    price_type = models.CharField('Тип оплаты', max_length=20, default='free',
                                  choices=[('free', 'Бесплатно'), ('split', 'Сбор'), ('fixed', 'Фиксированная')])
    price_per_player = models.DecimalField('Стоимость с игрока', max_digits=8, decimal_places=2, default=0)
    
    # Статус и системные поля
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='active')
    is_public = models.BooleanField('Публичная игра', default=True)
    requirements = models.TextField('Требования к игрокам', blank=True)
    
    # Даты
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.title} ({self.get_game_type_display()}) - {self.date}"
    
    @property
    def datetime_start(self):
        """Возвращает полную дату-время начала"""
        return datetime.datetime.combine(self.date, self.start_time)
    
    @property
    def datetime_end(self):
        """Возвращает полную дату-время окончания"""
        return datetime.datetime.combine(self.date, self.end_time)
    
    @property
    def spots_left(self):
        """Оставшееся количество мест"""
        return self.max_players - self.participants.count()
    
    @property
    def is_full(self):
        """Игра заполнена?"""
        return self.spots_left <= 0
    
    @property
    def can_join(self):
        """Можно ли присоединиться к игре"""
        return (self.status == 'active' and 
                not self.is_full and
                self.datetime_start > timezone.now())
    
    @property
    def location_display(self):
        """Место проведения (из площадки или текста)"""
        if self.court:
            return self.court.name
        return self.location_text

class UserProfile(models.Model):
    """Расширенный профиль пользователя для волейбола"""
    POSITION_CHOICES = [
        ('setter', 'Связующий'),
        ('outside', 'Доигровщик'),
        ('opposite', 'Диагональный'),
        ('middle', 'Центральный блокирующий'),
        ('libero', 'Либеро'),
    ]

    SKILL_LEVEL_CHOICES = [
        ('beginner', 'Начинающий'),
        ('intermediate', 'Любитель'),
        ('advanced', 'Продвинутый'),
        ('professional', 'Профессионал'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField('О себе', blank=True)
    city = models.CharField('Город', max_length=100, blank=True)
    age = models.PositiveIntegerField('Возраст', null=True, blank=True)

    # Волейбольная специализация
    position = models.CharField(
        'Основная позиция', 
        max_length=20, 
        choices=POSITION_CHOICES, 
        blank=True
    )
    positions = models.CharField(
        'Все позиции', 
        max_length=100, 
        blank=True,
        help_text="Укажите через запятую (например: доигровщик, либеро)"
    )
    skill_level = models.CharField(
        'Уровень игры', 
        max_length=20, 
        choices=SKILL_LEVEL_CHOICES, 
        default='intermediate'
    )
    playing_years = models.PositiveIntegerField('Стаж игры (лет)', default=0)
    height = models.PositiveIntegerField('Рост (см)', null=True, blank=True)
    jump_reach = models.PositiveIntegerField('Высота прыжка (см)', null=True, blank=True)

    # Предпочтения
    play_style = models.CharField(
        'Стиль игры', 
        max_length=50, 
        blank=True,
        help_text="Например: атакующий, тактический, защитный"
    )
    preferred_venue = models.CharField(
        'Предпочитаемая площадка', 
        max_length=200, 
        blank=True
    )
    play_days = models.CharField(
        'Дни для игр', 
        max_length=100, 
        blank=True,
        help_text="Например: вечера будних, выходные"
    )

    # Социальные сети
    telegram = models.CharField('Telegram', max_length=100, blank=True)
    vk = models.CharField('ВКонтакте', max_length=100, blank=True)
    whatsapp = models.CharField('WhatsApp', max_length=100, blank=True)

    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True)
    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True)

    class Meta:
        verbose_name = 'Профиль волейболиста'
        verbose_name_plural = 'Профили волейболистов'

    def __str__(self):
        return f"{self.user.username} - {self.get_position_display() if self.position else 'Не указана'} ({self.city})"

class Friendship(models.Model):
    """Система друзей/партнёров по волейболу"""
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships_received')
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Ожидает подтверждения'),
            ('accepted', 'Принято'),
            ('rejected', 'Отклонено'),
        ],
        default='pending'
    )
    court_partner = models.BooleanField('Партнёр по площадке', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')
        verbose_name = 'Волейбольное знакомство'
        verbose_name_plural = 'Волейбольные знакомства'

    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.get_status_display()})"