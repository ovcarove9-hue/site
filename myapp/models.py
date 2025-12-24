# myapp/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class VolleyballCourt(models.Model):
    SURFACE_TYPES = [
        ('sand', 'Песок'),
        ('parquet', 'Паркет'),
        ('synthetic', 'Синтетика'),
        ('asphalt', 'Асфальт'),
        ('grass', 'Газон'),
    ]
    
    COURT_TYPES = [
        ('indoor', 'Закрытый зал'),
        ('outdoor', 'Открытая площадка'),
        ('beach', 'Пляж'),
    ]
    
    MODERATION_STATUS = [
        ('pending', '⏳ На модерации'),
        ('approved', '✅ Одобрено'),
        ('rejected', '❌ Отклонено'),
        ('needs_info', '❓ Требует уточнений'),
    ]
    
    # Основная информация
    name = models.CharField(max_length=200, verbose_name="Название")
    city = models.CharField(max_length=100, verbose_name="Город", default="Москва")
    address = models.CharField(max_length=300, verbose_name="Адрес")
    description = models.TextField(blank=True, verbose_name="Описание")
    
    # Контакты
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    email = models.EmailField(blank=True, verbose_name="Email")
    website = models.URLField(blank=True, verbose_name="Сайт")
    
    # Характеристики
    court_type = models.CharField(
        max_length=20, 
        choices=COURT_TYPES, 
        default='outdoor', 
        verbose_name="Тип площадки"
    )
    surface = models.CharField(
        max_length=20, 
        choices=SURFACE_TYPES, 
        default='synthetic', 
        verbose_name="Покрытие"
    )
    courts_count = models.PositiveIntegerField(default=1, verbose_name="Количество площадок")
    
    # Модерация
    status = models.CharField(
        max_length=20,
        choices=MODERATION_STATUS,
        default='pending',
        verbose_name='Статус модерации'
    )
    
    suggested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Предложил',
        related_name='suggested_courts'
    )
    
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Проверил',
        related_name='reviewed_courts'
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата проверки'
    )
    
    moderator_comment = models.TextField(
        blank=True,
        verbose_name='Комментарий модератора'
    )
    
    # Время работы
    opening_time = models.TimeField(default='08:00:00', verbose_name="Время открытия")
    closing_time = models.TimeField(default='22:00:00', verbose_name="Время закрытия")
    working_days = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Дни работы",
        default="Пн-Вс"
    )
    
    # Удобства
    is_lighted = models.BooleanField(default=False, verbose_name="Есть освещение")
    has_parking = models.BooleanField(default=False, verbose_name="Есть парковка")
    has_showers = models.BooleanField(default=False, verbose_name="Есть душ")
    has_locker_rooms = models.BooleanField(default=False, verbose_name="Есть раздевалки")
    has_equipment_rental = models.BooleanField(default=False, verbose_name="Прокат инвентаря")
    has_cafe = models.BooleanField(default=False, verbose_name="Есть кафе")
    
    # Цены
    is_free = models.BooleanField(default=False, verbose_name="Бесплатно")
    price_per_hour = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0, 
        verbose_name="Цена за час (руб.)"
    )
    price_details = models.TextField(blank=True, verbose_name="Подробнее о ценах")
    
    # Теги
    tags = models.CharField(max_length=200, blank=True, verbose_name="Теги")
    
    # Фото
    photo_url = models.URLField(blank=True, verbose_name="Ссылка на фото")
    
    # Координаты
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Широта")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Долгота")
    
    is_verified = models.BooleanField(default=False, verbose_name="Проверено")
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0, verbose_name="Рейтинг")
    
    # Поля для бронирования
    booking_enabled = models.BooleanField(default=True, verbose_name="Бронирование доступно")
    min_booking_hours = models.PositiveIntegerField(default=1, verbose_name="Минимальное время брони (часы)")
    max_booking_hours = models.PositiveIntegerField(default=3, verbose_name="Максимальное время брони (часы)")
    advance_booking_days = models.PositiveIntegerField(default=14, verbose_name="Макс. дней для бронирования вперед")
    
    # Технические поля
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    
    class Meta:
        ordering = ['city', 'name']
        verbose_name = "Волейбольная площадка"
        verbose_name_plural = "Волейбольные площадки"
    
    def __str__(self):
        return f"{self.name} ({self.city})"
    
    @property
    def amenities_list(self):
        """Список удобств"""
        amenities = []
        if self.is_lighted: amenities.append("Освещение")
        if self.has_parking: amenities.append("Парковка")
        if self.has_showers: amenities.append("Душ")
        if self.has_locker_rooms: amenities.append("Раздевалки")
        if self.has_equipment_rental: amenities.append("Прокат инвентаря")
        if self.has_cafe: amenities.append("Кафе")
        return amenities
    
    @property
    def working_hours(self):
        """Время работы в читаемом формате"""
        return f"{self.opening_time.strftime('%H:%M')} - {self.closing_time.strftime('%H:%M')}"
    
    @property
    def price_display(self):
        """Отображение цены"""
        if self.is_free:
            return "Бесплатно"
        elif self.price_per_hour > 0:
            return f"{self.price_per_hour} руб./час"
        else:
            return "Цена не указана"
    
    def can_be_viewed_by(self, user):
        """Кто может видеть эту площадку"""
        if self.status == 'approved' and self.is_active:
            return True
        if user.is_superuser:
            return True
        if self.suggested_by == user:
            return True
        return False
    
    def approve(self, user, comment=''):
        """Одобрить площадку"""
        self.status = 'approved'
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.moderator_comment = comment
        self.is_verified = True
        self.save()
        
    def reject(self, user, comment=''):
        """Отклонить площадку"""
        self.status = 'rejected'
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.moderator_comment = comment
        self.save()
        
    def request_info(self, user, comment=''):
        """Запросить дополнительную информацию"""
        self.status = 'needs_info'
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.moderator_comment = comment
        self.save()

class CourtPhoto(models.Model):
    """Фотографии площадок"""
    court = models.ForeignKey(VolleyballCourt, on_delete=models.CASCADE, 
                             related_name='photos')
    photo = models.ImageField('Фото', upload_to='court_photos/')
    uploaded_at = models.DateTimeField('Дата загрузки', auto_now_add=True)
    is_main = models.BooleanField('Главное фото', default=False)
    
    class Meta:
        verbose_name = 'Фото площадки'
        verbose_name_plural = 'Фото площадок'
    
    def __str__(self):
        return f"Фото для {self.court.name}"

class Game(models.Model):
    GAME_TYPES = [
        ('beach', 'Пляжный волейбол (2x2)'),
        ('indoor', 'Зал (классика 6x6)'),
        ('mini', 'Мини-волейбол (4x4)'),
        ('mixed', 'Микст (смешанные команды)'),
        ('training', 'Тренировка/разминка'),
        ('tournament', 'Турнирная игра'),
    ]
    
    SKILL_LEVELS = [
        ('any', 'Любой уровень'),
        ('beginner', 'Начинающий'),
        ('intermediate', 'Средний'),
        ('advanced', 'Продвинутый'),
        ('pro', 'Профессиональный'),
    ]
    
    MEETING_TYPES = [
        ('training', 'Тренировка'),
        ('friendly', 'Товарищеская игра'),
        ('tournament', 'Турнир'),
        ('other', 'Другое')
    ]
    
    # Основные поля
    title = models.CharField(max_length=200, verbose_name="Название игры")
    organizer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Организатор"
    )
    
    # Тип игры
    sport_type = models.CharField(
        max_length=50, 
        choices=GAME_TYPES, 
        verbose_name="Тип игры",
        default="indoor"
    )
    
    # Тип встречи
    meeting_type = models.CharField(
        max_length=50, 
        choices=MEETING_TYPES,
        default='friendly',
        verbose_name="Тип встречи"
    )
    
    # Дата и время
    game_date = models.DateField(verbose_name="Дата игры")
    game_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания", null=True, blank=True)
    
    # Местоположение
    location = models.CharField(
        max_length=300, 
        verbose_name="Место проведения",
        default="Не указано"
    )
    custom_location = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Другое место"
    )
    
    # Площадка
    court = models.ForeignKey(
        VolleyballCourt,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Выбранная площадка"
    )
    
    # Описание
    description = models.TextField(blank=True, verbose_name="Описание")
    
    # Участники
    min_players = models.PositiveIntegerField(
        default=4,
        verbose_name="Минимальное количество игроков"
    )
    
    max_players = models.PositiveIntegerField(
        default=12,
        verbose_name="Максимальное количество игроков"
    )
    
    # Уровень и статус
    skill_level = models.CharField(
        max_length=50, 
        choices=SKILL_LEVELS, 
        default='intermediate', 
        verbose_name="Уровень"
    )
    
    price = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        default=0,
        verbose_name="Стоимость участия (руб.)",
        null=True,
        blank=True
    )
    
    is_private = models.BooleanField(
        default=False,
        verbose_name="Приватная игра"
    )
    
    # Контактная информация
    contact_name = models.CharField(
        max_length=100, 
        verbose_name="Контактное лицо",
        blank=True,
        default="Не указано"
    )
    
    contact_phone = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name="Телефон"
    )
    
    # Технические поля
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    
    # Участники
    participants = models.ManyToManyField(
        User,
        related_name='games_joined',
        blank=True,
        verbose_name="Участники"
    )
    
    class Meta:
        ordering = ['game_date', 'game_time']
    
    def __str__(self):
        return f"{self.title} ({self.game_date})"
    
    def current_players_count(self):
        """Количество участников, записавшихся на игру"""
        return self.participants.count()
    
    def is_full(self):
        """Проверка, заполнена ли игра"""
        return self.participants.count() >= self.max_players
    
    def spots_left(self):
        """Сколько мест осталось"""
        return max(0, self.max_players - self.participants.count())

class CourtBooking(models.Model):
    """Бронирование площадок"""
    STATUS_CHOICES = [
        ('pending', '⏳ Ожидает подтверждения'),
        ('confirmed', '✅ Подтверждено'),
        ('cancelled', '❌ Отменено'),
        ('completed', '🏐 Завершено'),
        ('rejected', '🚫 Отклонено'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачено'),
        ('partial', 'Частично оплачено'),
        ('refunded', 'Возвращено'),
        ('cancelled', 'Отмена оплаты'),
    ]
    
    booking_number = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Номер брони")
    court = models.ForeignKey(
        VolleyballCourt, 
        on_delete=models.PROTECT, 
        related_name='bookings',
        verbose_name="Площадка"
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='court_bookings',
        verbose_name="Пользователь"
    )
    
    # Время бронирования
    booking_date = models.DateField(verbose_name="Дата бронирования")
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")
    hours = models.PositiveIntegerField(verbose_name="Количество часов", default=1)
    
    # Участники
    participants_count = models.PositiveIntegerField(
        default=6,
        verbose_name="Количество участников",
        validators=[MinValueValidator(2), MaxValueValidator(24)]
    )
    participants = models.ManyToManyField(
        User,
        related_name='booked_games',
        blank=True,
        verbose_name="Участники игры"
    )
    
    # Цена
    price_per_hour = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Цена за час"
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Общая стоимость"
    )
    deposit_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name="Сумма депозита"
    )
    
    # Статусы
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус бронирования"
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name="Статус оплаты"
    )
    
    # Информация
    contact_name = models.CharField(max_length=100, verbose_name="Контактное лицо")
    contact_phone = models.CharField(max_length=20, verbose_name="Контактный телефон")
    contact_email = models.EmailField(blank=True, verbose_name="Email для связи")
    
    # Примечания
    special_requests = models.TextField(blank=True, verbose_name="Особые пожелания")
    admin_notes = models.TextField(blank=True, verbose_name="Заметки администратора")
    
    # Даты
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата подтверждения")
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата отмены")
    
    # Системные поля
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP адрес")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    
    class Meta:
        verbose_name = "Бронирование площадки"
        verbose_name_plural = "Бронирования площадок"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking_date', 'start_time']),
            models.Index(fields=['status']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.booking_number} - {self.court.name} ({self.booking_date})"
    
    def save(self, *args, **kwargs):
        if not self.booking_number:
            # Генерация уникального номера брони: BOOK-YYYYMMDD-XXXX
            date_part = timezone.now().strftime('%Y%m%d')
            unique_part = uuid.uuid4().hex[:4].upper()
            self.booking_number = f"BOOK-{date_part}-{unique_part}"
        
        if not self.total_price:
            self.total_price = self.price_per_hour * self.hours
        
        if not self.deposit_amount and not self.court.is_free:
            self.deposit_amount = self.total_price * 0.3  # 30% депозит
        
        super().save(*args, **kwargs)
    
    @property
    def is_upcoming(self):
        """Проверка, предстоящая ли это бронь"""
        from datetime import datetime
        booking_datetime = datetime.combine(self.booking_date, self.start_time)
        return booking_datetime > timezone.now()
    
    @property
    def can_be_cancelled(self):
        """Можно ли отменить бронь"""
        from datetime import datetime, timedelta
        booking_datetime = datetime.combine(self.booking_date, self.start_time)
        return self.status == 'confirmed' and (booking_datetime - timedelta(hours=24)) > timezone.now()
    
    def confirm(self, admin_user=None):
        """Подтвердить бронирование"""
        self.status = 'confirmed'
        self.confirmed_at = timezone.now()
        if admin_user:
            self.admin_notes += f"\nПодтверждено администратором {admin_user.username} в {timezone.now()}"
        self.save()
    
    def cancel(self, reason=''):
        """Отменить бронирование"""
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        if reason:
            self.admin_notes += f"\nОтмена: {reason}"
        self.save()

class TimeSlot(models.Model):
    """Временные слоты для бронирования"""
    court = models.ForeignKey(
        VolleyballCourt,
        on_delete=models.CASCADE,
        related_name='time_slots',
        verbose_name="Площадка"
    )
    date = models.DateField(verbose_name="Дата")
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")
    
    # Статус
    is_available = models.BooleanField(default=True, verbose_name="Доступен")
    is_booked = models.BooleanField(default=False, verbose_name="Забронирован")
    is_blocked = models.BooleanField(default=False, verbose_name="Заблокирован")
    
    # Связанное бронирование
    booking = models.ForeignKey(
        CourtBooking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='time_slots',
        verbose_name="Бронирование"
    )
    
    # Цена
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Цена слота"
    )
    
    class Meta:
        verbose_name = "Временной слот"
        verbose_name_plural = "Временные слоты"
        unique_together = ['court', 'date', 'start_time']
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.court.name} - {self.date} {self.start_time}"
    
    @property
    def datetime_start(self):
        from django.utils import timezone
        from datetime import datetime
        return timezone.make_aware(datetime.combine(self.date, self.start_time))
    
    @property
    def datetime_end(self):
        from django.utils import timezone
        from datetime import datetime
        return timezone.make_aware(datetime.combine(self.date, self.end_time))
    
    def is_past(self):
        """Прошедший ли слот"""
        return self.datetime_end < timezone.now()
    
    def is_ongoing(self):
        """Текущий ли слот"""
        return self.datetime_start <= timezone.now() <= self.datetime_end

class UserProfile(models.Model):
    """Расширенный профиль пользователя"""
    POSITION_CHOICES = [
        ('setter', 'Связующий'),
        ('outside', 'Доигровщик'),
        ('opposite', 'Диагональный'),
        ('middle', 'Центральный блокирующий'),
        ('libero', 'Либеро'),
        ('all', 'Универсал'),
    ]

    SKILL_LEVEL_CHOICES = [
        ('beginner', 'Начинающий'),
        ('intermediate', 'Любитель'),
        ('advanced', 'Продвинутый'),
        ('professional', 'Профессионал'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField('О себе', blank=True)
    city = models.CharField('Город', max_length=100, blank=True, default="Москва")
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
        help_text="Укажите через запятую"
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
        blank=True
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
        default="вечера будних, выходные"
    )

    # Социальные сети
    telegram = models.CharField('Telegram', max_length=100, blank=True)
    vk = models.CharField('ВКонтакте', max_length=100, blank=True)
    whatsapp = models.CharField('WhatsApp', max_length=100, blank=True)
    
    # Настройки уведомлений
    notify_bookings = models.BooleanField('Уведомлять о бронированиях', default=True)
    notify_messages = models.BooleanField('Уведомлять о сообщениях', default=True)
    notify_news = models.BooleanField('Уведомлять о новостях', default=False)

    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True)
    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Профиль волейболиста'
        verbose_name_plural = 'Профили волейболистов'

    def __str__(self):
        return f"{self.user.username} - {self.city}"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

class Payment(models.Model):
    """Платежи за бронирования"""
    PAYMENT_METHODS = [
        ('card', 'Банковская карта'),
        ('sbp', 'СБП (СБП)'),
        ('cash', 'Наличные'),
        ('transfer', 'Банковский перевод'),
        ('other', 'Другое'),
    ]
    
    PAYMENT_STATUSES = [
        ('pending', 'Ожидает оплаты'),
        ('processing', 'В обработке'),
        ('completed', 'Завершено'),
        ('failed', 'Не удалось'),
        ('refunded', 'Возвращено'),
        ('cancelled', 'Отменено'),
    ]
    
    booking = models.ForeignKey(
        CourtBooking,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name="Бронирование"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name="Пользователь"
    )
    
    # Информация о платеже
    payment_number = models.CharField(max_length=50, unique=True, verbose_name="Номер платежа")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    currency = models.CharField(max_length=3, default='RUB', verbose_name="Валюта")
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        verbose_name="Способ оплаты"
    )
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUSES,
        default='pending',
        verbose_name="Статус платежа"
    )
    
    # Информация банка/платежной системы
    transaction_id = models.CharField(max_length=100, blank=True, verbose_name="ID транзакции")
    bank_response = models.TextField(blank=True, verbose_name="Ответ банка")
    
    # Даты
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата обработки")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата завершения")
    
    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.payment_number} - {self.amount} {self.currency}"

class Notification(models.Model):
    """Уведомления для пользователей"""
    TYPE_CHOICES = [
        ('booking_confirmed', 'Бронирование подтверждено'),
        ('booking_cancelled', 'Бронирование отменено'),
        ('booking_reminder', 'Напоминание о игре'),
        ('payment_success', 'Оплата прошла успешно'),
        ('payment_failed', 'Ошибка оплаты'),
        ('new_message', 'Новое сообщение'),
        ('friend_request', 'Запрос в друзья'),
        ('game_invite', 'Приглашение на игру'),
        ('system', 'Системное уведомление'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Пользователь"
    )
    notification_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        verbose_name="Тип уведомления"
    )
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    message = models.TextField(verbose_name="Сообщение")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    
    # Ссылка на связанный объект
    related_object_type = models.CharField(max_length=50, blank=True, verbose_name="Тип объекта")
    related_object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID объекта")
    
    # Дополнительные данные
    data = models.JSONField(default=dict, blank=True, verbose_name="Дополнительные данные")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Пометить как прочитанное"""
        self.is_read = True
        self.save()

class Friendship(models.Model):
    """Система друзей/партнёров"""
    from_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='friendships_sent'
    )
    to_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='friendships_received'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Ожидает подтверждения'),
            ('accepted', 'Принято'),
            ('rejected', 'Отклонено'),
            ('blocked', 'Заблокировано'),
        ],
        default='pending'
    )
    court_partner = models.BooleanField('Партнёр по площадке', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('from_user', 'to_user')
        verbose_name = 'Волейбольное знакомство'
        verbose_name_plural = 'Волейбольные знакомства'
    
    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.get_status_display()})"

class GameParticipation(models.Model):
    """Участие в играх"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Участник",
        related_name='game_participations'
    )
    game = models.ForeignKey(
        Game, 
        on_delete=models.CASCADE, 
        verbose_name="Игра",
        related_name='participations'
    )
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата записи")
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Ожидает подтверждения'),
            ('confirmed', 'Подтверждено'),
            ('rejected', 'Отклонено'),
            ('cancelled', 'Отменено'),
        ],
        default='pending',
        verbose_name="Статус"
    )
    comment = models.TextField(blank=True, verbose_name="Комментарий участника")
    
    class Meta:
        unique_together = ['user', 'game']
        verbose_name = "Участие в игре"
        verbose_name_plural = "Участия в играх"
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.username} → {self.game.title}"
    
    @property
    def can_cancel(self):
        """Можно ли отменить участие"""
        from datetime import datetime, timedelta
        game_datetime = datetime.combine(self.game.game_date, self.game.game_time)
        return (game_datetime - timedelta(hours=12)) > timezone.now()

class Review(models.Model):
    """Отзывы о площадках"""
    court = models.ForeignKey(
        VolleyballCourt,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="Площадка"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="Пользователь"
    )
    booking = models.ForeignKey(
        CourtBooking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='review',
        verbose_name="Бронирование"
    )
    
    # Оценки
    rating_overall = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Общая оценка"
    )
    rating_condition = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Состояние площадки"
    )
    rating_service = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Качество обслуживания"
    )
    rating_price = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Соотношение цена/качество"
    )
    
    # Текст отзыва
    title = models.CharField(max_length=200, verbose_name="Заголовок отзыва")
    comment = models.TextField(verbose_name="Комментарий")
    pros = models.TextField(blank=True, verbose_name="Достоинства")
    cons = models.TextField(blank=True, verbose_name="Недостатки")
    
    # Статус
    is_verified = models.BooleanField(default=False, verbose_name="Проверенный отзыв")
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано")
    
    # Технические поля
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        unique_together = ['court', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Отзыв от {self.user.username} на {self.court.name}"
    
    @property
    def average_rating(self):
        """Средняя оценка"""
        return (self.rating_overall + self.rating_condition + self.rating_service + self.rating_price) / 4

# Сигналы для автоматического создания профиля
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()