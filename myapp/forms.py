# myapp/forms.py

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import re
from datetime import datetime, timedelta, date
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from .models import (
    UserProfile,
    VolleyballCourt,
    Game,
    GameParticipation,
    CourtPhoto,
    CourtBooking,
    TimeSlot,
    Review
)

class PlayerProfileForm(forms.ModelForm):
    """Форма редактирования профиля игрока"""
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label='Имя',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ваше имя'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label='Фамилия',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ваша фамилия'
        })
    )
    
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'last_name', 'email',
            'district', 'age', 'skill_level',
            'bio', 'favorite_court', 'position',
            'city', 'playing_years', 'height',
            'jump_reach', 'play_style', 'play_days'
        ]
        
        widgets = {
            'district': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: ЦАО, СВАО, Центральный район'
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 14,
                'max': 100
            }),
            'skill_level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Расскажите о себе: опыт в волейболе, стиль игры, достижения...'
            }),
            'favorite_court': forms.Select(attrs={
                'class': 'form-control'
            }),
            'position': forms.Select(attrs={
                'class': 'form-control'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваш город'
            }),
            'playing_years': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 50
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 1,
                'min': 100,
                'max': 250
            }),
            'jump_reach': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 1,
                'min': 0,
                'max': 150
            }),
            'play_style': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: атакующий, тактический, защитный'
            }),
            'play_days': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: вечера будних, выходные'
            }),
        }
        
        labels = {
            'district': 'Район проживания',
            'age': 'Возраст',
            'skill_level': 'Уровень игры',
            'bio': 'О себе',
            'favorite_court': 'Любимая площадка',
            'position': 'Позиция в волейболе',
            'city': 'Город',
            'playing_years': 'Лет в волейболе',
            'height': 'Рост (см)',
            'jump_reach': 'Высота прыжка (см)',
            'play_style': 'Стиль игры',
            'play_days': 'Предпочитаемые дни для игры',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Заполняем данные пользователя
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
        
        # Ограничиваем список площадок только одобренными
        self.fields['favorite_court'].queryset = VolleyballCourt.objects.filter(
            status='approved',
            is_active=True
        ).order_by('name')
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        if profile.user:
            profile.user.first_name = self.cleaned_data['first_name']
            profile.user.last_name = self.cleaned_data['last_name']
            profile.user.email = self.cleaned_data['email']
            
            if commit:
                profile.user.save()
        
        if commit:
            profile.save()
        
        return profile

# ============================================================================
# КАСТОМНЫЕ ПОЛЯ ДЛЯ МНОЖЕСТВЕННОЙ ЗАГРУЗКИ ФАЙЛОВ
# ============================================================================

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)
    
    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(file_data, initial) for file_data in data]
        else:
            result = single_file_clean(data, initial)
        return result

# ============================================================================
# ФОРМА РЕГИСТРАЦИИ
# ============================================================================

class CustomUserRegistrationForm(UserCreationForm):
    """Форма регистрации с фамилией и позицией"""
    
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Фамилия",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите вашу фамилию'
        })
    )
    
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email'
        })
    )
    
    position = forms.ChoiceField(
        choices=UserProfile.POSITION_CHOICES,
        required=True,
        label="Ваша позиция в волейболе",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'last_name', 'email', 'position', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите имя пользователя'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите пароль'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Повторите пароль'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем классы ко всем полям
        for field_name in self.fields:
            if field_name not in ['username', 'last_name', 'email', 'position']:
                self.fields[field_name].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Создаем профиль пользователя
            UserProfile.objects.create(
                user=user,
                position=self.cleaned_data['position']
            )
        return user

# ============================================================================
# ОСТАЛЬНЫЕ ФОРМЫ
# ============================================================================

class CourtSuggestionForm(forms.ModelForm):
    """Форма для предложения новой площадки"""
    
    photos = MultipleFileField(
        label='Фотографии площадки',
        required=False,
        help_text='Можно выбрать несколько изображений'
    )
    
    accept_rules = forms.BooleanField(
        required=True,
        label='Я подтверждаю, что предоставленная информация точна и соответствует правилам сообщества'
    )
    
    # Координаты
    latitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.000001',
            'placeholder': '55.7558'
        })
    )
    
    longitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.000001',
            'placeholder': '37.6173'
        })
    )
    
    class Meta:
        model = VolleyballCourt
        fields = [
            'name', 'city', 'address', 'description',
            'court_type', 'surface', 'courts_count',
            'is_free', 'price_per_hour', 'price_details',
            'is_lighted', 'has_showers', 'has_locker_rooms',
            'has_equipment_rental', 'has_parking', 'has_cafe',
            'opening_time', 'closing_time', 'working_days',
            'phone', 'website', 'email',
            'photo_url', 'tags',
            'min_booking_hours', 'max_booking_hours', 'advance_booking_days',
            'booking_enabled'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Спорткомплекс "Чемпион"'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Москва',
                'value': 'Москва'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Полный адрес с улицей и домом'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Опишите площадку: покрытие, состояние, особенности...'
            }),
            'price_details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Детали оплаты: скидки, абонементы, условия аренды...'
            }),
            'opening_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            }),
            'closing_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            }),
            'working_days': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Пн-Вс'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (XXX) XXX-XX-XX'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@example.com'
            }),
            'photo_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://imgur.com/...'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'волейбол, спорт, площадка, турниры'
            }),
            'courts_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 20
            }),
            'price_per_hour': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 50
            }),
            'court_type': forms.Select(attrs={'class': 'form-control'}),
            'surface': forms.Select(attrs={'class': 'form-control'}),
            'min_booking_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 24
            }),
            'max_booking_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 24
            }),
            'advance_booking_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 365
            }),
            'booking_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
        help_texts = {
            'photo_url': 'Загрузите фото на imgur.com и вставьте прямую ссылку',
            'tags': 'Укажите через запятую ключевые слова для поиска',
            'min_booking_hours': 'Минимальное количество часов для бронирования',
            'max_booking_hours': 'Максимальное количество часов для бронирования',
            'advance_booking_days': 'На сколько дней вперед можно бронировать',
        }
    
    def clean_phone(self):
        """Валидация телефона"""
        phone = self.cleaned_data.get('phone')
        if phone:
            phone = re.sub(r'[^\d+]', '', phone)
            if len(phone) < 10:
                raise forms.ValidationError('Некорректный номер телефона')
        return phone
    
    def clean_price_per_hour(self):
        """Валидация цены"""
        price = self.cleaned_data.get('price_per_hour')
        is_free = self.cleaned_data.get('is_free', False)
        
        if is_free and price and price > 0:
            raise forms.ValidationError('Для бесплатной площадки цена должна быть 0')
        
        return price
    
    def clean_min_booking_hours(self):
        min_hours = self.cleaned_data.get('min_booking_hours')
        max_hours = self.cleaned_data.get('max_booking_hours')
        
        if min_hours and max_hours and min_hours > max_hours:
            raise ValidationError("Минимальное время брони не может быть больше максимального")
        
        return min_hours
    
    def clean(self):
        cleaned_data = super().clean()
        opening = cleaned_data.get('opening_time')
        closing = cleaned_data.get('closing_time')
        
        if opening and closing and opening >= closing:
            raise ValidationError("Время открытия должно быть раньше времени закрытия")
        
        return cleaned_data

class CourtPhotoForm(forms.ModelForm):
    """Форма для загрузки фото"""
    class Meta:
        model = CourtPhoto
        fields = ['photo', 'is_main']
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'is_main': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CourtBookingForm(forms.ModelForm):
    """Форма бронирования площадки"""
    
    booking_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'id': 'booking_date_input'
        }),
        label="Дата бронирования"
    )
    
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control',
            'id': 'start_time_input'
        }),
        label="Время начала"
    )
    
    hours = forms.IntegerField(
        min_value=1,
        max_value=24,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'hours_input',
            'min': 1,
            'max': 24
        }),
        label="Количество часов",
        help_text="Минимум 1 час, максимум 24 часа"
    )
    
    participants_count = forms.IntegerField(
        min_value=2,
        max_value=50,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'participants_input',
            'min': 2,
            'max': 50
        }),
        label="Количество участников",
        initial=6
    )
    
    participants_emails = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Введите email участников через запятую'
        }),
        label="Email участников (необязательно)",
        help_text="Участники получат уведомления о бронировании"
    )
    
    class Meta:
        model = CourtBooking
        fields = [
            'booking_date', 'start_time', 'hours', 'participants_count',
            'contact_name', 'contact_phone', 'contact_email',
            'special_requests', 'participants_emails'
        ]
        
        widgets = {
            'contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваше имя'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (999) 123-45-67'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ваш@email.com'
            }),
            'special_requests': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Особые пожелания, уровень игроков, необходимое оборудование...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.court = kwargs.pop('court', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.court:
            self.fields['hours'].widget.attrs['min'] = self.court.min_booking_hours
            self.fields['hours'].widget.attrs['max'] = self.court.max_booking_hours
            self.fields['hours'].initial = self.court.min_booking_hours
            
            today = date.today()
            max_date = today + timedelta(days=self.court.advance_booking_days)
            self.fields['booking_date'].widget.attrs['min'] = today.isoformat()
            self.fields['booking_date'].widget.attrs['max'] = max_date.isoformat()
            
            if self.court.opening_time:
                self.fields['start_time'].widget.attrs['min'] = self.court.opening_time.strftime('%H:%M')
            if self.court.closing_time:
                self.fields['start_time'].widget.attrs['max'] = self.court.closing_time.strftime('%H:%M')
        
        if self.user and self.user.is_authenticated:
            profile = getattr(self.user, 'profile', None)
            if profile:
                self.fields['contact_name'].initial = self.user.get_full_name() or self.user.username
                self.fields['contact_email'].initial = self.user.email
    
    def clean_booking_date(self):
        booking_date = self.cleaned_data.get('booking_date')
        today = date.today()
        
        if booking_date < today:
            raise ValidationError("Нельзя забронировать площадку на прошедшую дату")
        
        if self.court and booking_date > today + timedelta(days=self.court.advance_booking_days):
            raise ValidationError(
                f"Максимальный срок бронирования - {self.court.advance_booking_days} дней вперед"
            )
        
        return booking_date
    
    def clean_start_time(self):
        start_time = self.cleaned_data.get('start_time')
        
        if self.court and start_time:
            if start_time < self.court.opening_time:
                raise ValidationError(
                    f"Площадка открывается в {self.court.opening_time.strftime('%H:%M')}"
                )
            
            hours = self.cleaned_data.get('hours', 1)
            end_time_dt = datetime.combine(date.today(), start_time) + timedelta(hours=hours)
            end_time = end_time_dt.time()
            
            if end_time > self.court.closing_time:
                raise ValidationError(
                    f"Площадка закрывается в {self.court.closing_time.strftime('%H:%M')}. "
                    f"Пожалуйста, выберите меньшее количество часов или более раннее время начала."
                )
        
        return start_time
    
    def clean_hours(self):
        hours = self.cleaned_data.get('hours')
        
        if self.court:
            if hours < self.court.min_booking_hours:
                raise ValidationError(
                    f"Минимальное время бронирования: {self.court.min_booking_hours} час(а/ов)"
                )
            if hours > self.court.max_booking_hours:
                raise ValidationError(
                    f"Максимальное время бронирования: {self.court.max_booking_hours} час(а/ов)"
                )
        
        return hours
    
    def clean_participants_emails(self):
        emails = self.cleaned_data.get('participants_emails', '')
        if emails:
            email_list = [email.strip() for email in emails.split(',')]
            valid_emails = []
            invalid_emails = []
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            for email in email_list:
                if email and re.match(email_regex, email):
                    valid_emails.append(email)
                elif email:
                    invalid_emails.append(email)
            
            if invalid_emails:
                raise ValidationError(
                    f"Некорректные email адреса: {', '.join(invalid_emails)}"
                )
            
            return ', '.join(valid_emails)
        
        return emails
    
    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get('booking_date')
        start_time = cleaned_data.get('start_time')
        hours = cleaned_data.get('hours', 1)
        
        if booking_date and start_time and self.court:
            start_datetime = datetime.combine(booking_date, start_time)
            end_datetime = start_datetime + timedelta(hours=hours)
            
            overlapping_bookings = CourtBooking.objects.filter(
                court=self.court,
                booking_date=booking_date,
                status__in=['confirmed', 'pending']
            ).exclude(
                Q(end_time__lte=start_time) | Q(start_time__gte=end_datetime.time())
            )
            
            if overlapping_bookings.exists():
                raise ValidationError(
                    "Выбранное время уже занято или пересекается с другим бронированием. "
                    "Пожалуйста, выберите другое время."
                )
        
        return cleaned_data

class QuickBookingForm(forms.Form):
    """Форма быстрого бронирования (для попапов)"""
    booking_date = forms.DateField(widget=forms.HiddenInput(), required=True)
    start_time = forms.TimeField(widget=forms.HiddenInput(), required=True)
    hours = forms.IntegerField(widget=forms.HiddenInput(), initial=1, required=True)

class TimeSlotForm(forms.ModelForm):
    """Форма для управления временными слотами"""
    class Meta:
        model = TimeSlot
        fields = ['date', 'start_time', 'end_time', 'is_available', 'is_blocked', 'price']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_blocked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class GameCreationForm(forms.ModelForm):
    """Форма создания новой игры"""
    
    use_court_booking = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'use_court_booking'
        }),
        label="Забронировать площадку для игры"
    )
    
    court_booking = forms.ModelChoiceField(
        queryset=CourtBooking.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'court_booking_select',
            'disabled': True
        }),
        label="Выберите бронирование"
    )
    
    # ДОБАВИМ ВЫБОР ПЛОЩАДКИ
    court = forms.ModelChoiceField(
        queryset=VolleyballCourt.objects.none(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'court_select'
        }),
        label="Выберите площадку *"
    )
    
    class Meta:
        model = Game
        fields = [
            'title', 'meeting_type', 'sport_type', 'game_date', 'game_time',
            'end_time', 'location', 'custom_location', 'court', 'description',
            'min_players', 'max_players', 'skill_level', 'price',
            'is_private', 'contact_name', 'contact_phone'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Вечерняя игра для любителей'}),
            'meeting_type': forms.Select(attrs={'class': 'form-control'}),
            'sport_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Опишите детали игры...'}),
            'game_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'game_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'court': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Адрес или название площадки'}),
            'custom_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Другое место проведения'}),
            'max_players': forms.NumberInput(attrs={'class': 'form-control', 'min': 2, 'max': 30}),
            'min_players': forms.NumberInput(attrs={'class': 'form-control', 'min': 2, 'max': 30}),
            'skill_level': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': 50, 'min': 0}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ваше имя'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (XXX) XXX-XX-XX'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['court'].queryset = VolleyballCourt.objects.filter(
                status='approved', 
                is_active=True
            ).order_by('name')
            
            self.fields['court_booking'].queryset = CourtBooking.objects.filter(
                user=self.user,
                status='confirmed',
                booking_date__gte=date.today()
            ).order_by('booking_date', 'start_time')
    
    def clean(self):
        cleaned_data = super().clean()
        game_date = cleaned_data.get('game_date')
        game_time = cleaned_data.get('game_time')
        end_time = cleaned_data.get('end_time')
        use_court_booking = cleaned_data.get('use_court_booking')
        court_booking = cleaned_data.get('court_booking')
        court = cleaned_data.get('court')
        
        # Если выбрана площадка, проверяем доступность
        if court and game_date and game_time and end_time:
            # Проверяем, что площадка одобрена
            if court.status != 'approved':
                raise ValidationError("Выбранная площадка еще не одобрена администрацией")
            
            # Проверяем время работы площадки
            if game_time < court.opening_time:
                raise ValidationError(
                    f"Площадка открывается в {court.opening_time.strftime('%H:%M')}"
                )
            
            if end_time > court.closing_time:
                raise ValidationError(
                    f"Площадка закрывается в {court.closing_time.strftime('%H:%M')}"
                )
            
            # Проверяем, что на это время нет других игр
            conflicting_games = Game.objects.filter(
                court=court,
                game_date=game_date,
                is_active=True
            ).exclude(
                Q(end_time__lte=game_time) | Q(game_time__gte=end_time)
            )
            
            if conflicting_games.exists():
                raise ValidationError(
                    "На выбранное время уже запланирована другая игра на этой площадке"
                )
        
        # Автоматически заполняем поле location, если выбрана площадка
        if court and not cleaned_data.get('location'):
            cleaned_data['location'] = f"{court.name}, {court.address}"
        
        if use_court_booking and not court_booking:
            raise ValidationError("При выборе опции бронирования необходимо выбрать конкретное бронирование")
        
        if court_booking:
            if game_date != court_booking.booking_date:
                raise ValidationError("Дата игры должна совпадать с датой бронирования площадки")
            
            booking_end_time = (
                datetime.combine(court_booking.booking_date, court_booking.start_time) +
                timedelta(hours=court_booking.hours)
            ).time()
            
            if game_time < court_booking.start_time or (end_time and end_time > booking_end_time):
                raise ValidationError(
                    f"Игра должна проходить в рамках забронированного времени: "
                    f"{court_booking.start_time.strftime('%H:%M')} - "
                    f"{booking_end_time.strftime('%H:%M')}"
                )
        
        if game_date and game_time and end_time:
            game_datetime_start = datetime.combine(game_date, game_time)
            game_datetime_end = datetime.combine(game_date, end_time)
            
            if game_datetime_end <= game_datetime_start:
                raise ValidationError('Время окончания должно быть позже времени начала')
            
            if game_datetime_start < datetime.now():
                raise ValidationError('Нельзя создать игру в прошлом')
        
        return cleaned_data

class GameJoinForm(forms.ModelForm):
    """Форма вступления в игру"""
    class Meta:
        model = GameParticipation
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Можете добавить комментарий...'
            })
        }

class ReviewForm(forms.ModelForm):
    """Форма для отзыва о площадке"""
    class Meta:
        model = Review
        fields = [
            'rating_overall', 'rating_condition', 'rating_service', 'rating_price',
            'title', 'comment', 'pros', 'cons'
        ]
        widgets = {
            'rating_overall': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5, 'type': 'range', 'step': 1}),
            'rating_condition': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5, 'type': 'range', 'step': 1}),
            'rating_service': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5, 'type': 'range', 'step': 1}),
            'rating_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5, 'type': 'range', 'step': 1}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Краткий заголовок отзыва'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Подробный отзыв о площадке...'}),
            'pros': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Что понравилось...'}),
            'cons': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Что можно улучшить...'}),
        }
        labels = {
            'rating_overall': 'Общая оценка',
            'rating_condition': 'Состояние площадки',
            'rating_service': 'Обслуживание',
            'rating_price': 'Соотношение цена/качество',
            'title': 'Заголовок отзыва',
            'comment': 'Комментарий',
            'pros': 'Достоинства',
            'cons': 'Недостатки',
        }

class SearchForm(forms.Form):
    """Форма поиска"""
    query = forms.CharField(required=False, label='Поиск', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Поиск игроков...'}))
    city = forms.CharField(required=False, label='Город', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Город'}))
    position = forms.ChoiceField(required=False, choices=[('', 'Любая позиция')] + UserProfile.POSITION_CHOICES, label='Позиция', widget=forms.Select(attrs={'class': 'form-control'}))
    skill_level = forms.ChoiceField(required=False, choices=[('', 'Любой уровень')] + UserProfile.SKILL_LEVEL_CHOICES, label='Уровень', widget=forms.Select(attrs={'class': 'form-control'}))
    min_age = forms.IntegerField(required=False, label='Минимальный возраст', min_value=18, max_value=80, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    max_age = forms.IntegerField(required=False, label='Максимальный возраст', min_value=18, max_value=80, widget=forms.NumberInput(attrs={'class': 'form-control'}))

class CourtSearchForm(forms.Form):
    """Форма поиска площадок"""
    city = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Город', 'value': 'Москва'}), label='Город', initial='Москва')
    court_type = forms.ChoiceField(required=False, choices=[('', 'Любой тип')] + VolleyballCourt.COURT_TYPES, widget=forms.Select(attrs={'class': 'form-control'}), label='Тип площадки')
    is_free = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}), label='Только бесплатные')
    has_lighting = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}), label='С освещением')
    min_price = forms.DecimalField(required=False, max_digits=8, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'от', 'min': 0}), label='Цена от')
    max_price = forms.DecimalField(required=False, max_digits=8, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'до', 'min': 0}), label='до')

class FriendSearchForm(forms.Form):
    """Форма поиска друзей"""
    SEARCH_TYPE_CHOICES = [
        ('all', 'Все пользователи'),
        ('friends', 'Мои друзья'),
        ('not_friends', 'Еще не друзья'),
    ]
    
    search_type = forms.ChoiceField(label='Тип поиска', choices=SEARCH_TYPE_CHOICES, initial='all', widget=forms.RadioSelect(attrs={'class': 'search-type-radio'}))
    query = forms.CharField(label='Поиск', required=False, widget=forms.TextInput(attrs={'placeholder': 'Имя, город, интересы...', 'class': 'form-control'}))
    city = forms.CharField(label='Город', required=False, widget=forms.TextInput(attrs={'placeholder': 'Введите город', 'class': 'form-control'}))
    min_age = forms.IntegerField(label='Возраст от', required=False, min_value=16, max_value=100, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '18'}))
    max_age = forms.IntegerField(label='до', required=False, min_value=16, max_value=100, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '60'}))
    interests = forms.CharField(label='Интересы', required=False, widget=forms.TextInput(attrs={'placeholder': 'волейбол, спорт, музыка...', 'class': 'form-control'}))

class ProfileEditForm(forms.ModelForm):
    """Форма редактирования профиля"""
    first_name = forms.CharField(label='Имя', max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Фамилия', max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email', required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'city', 'age', 'position', 'positions',
            'skill_level', 'playing_years', 'height', 'jump_reach',
            'play_style', 'preferred_venue', 'play_days',
            'telegram', 'vk', 'whatsapp',
            'notify_bookings', 'notify_messages', 'notify_news'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Расскажите о себе...'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ваш город'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'position': forms.Select(attrs={'class': 'form-control'}),
            'positions': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: связующий, доигровщик'}),
            'skill_level': forms.Select(attrs={'class': 'form-control'}),
            'playing_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'height': forms.NumberInput(attrs={'class': 'form-control'}),
            'jump_reach': forms.NumberInput(attrs={'class': 'form-control'}),
            'play_style': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: атакующий, тактический, защитный'}),
            'preferred_venue': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Предпочитаемая площадка'}),
            'play_days': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: вечера будних, выходные'}),
            'telegram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@username'}),
            'vk': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'id или username'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7XXXXXXXXXX'}),
            'notify_bookings': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_messages': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_news': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        if profile.user:
            profile.user.first_name = self.cleaned_data['first_name']
            profile.user.last_name = self.cleaned_data['last_name']
            profile.user.email = self.cleaned_data['email']
            if commit:
                profile.user.save()
        if commit:
            profile.save()
        return profile

class AvatarUploadForm(forms.ModelForm):
    """Форма загрузки аватара"""
    class Meta:
        model = UserProfile
        fields = ['avatar']
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
        }

class BookingFilterForm(forms.Form):
    """Форма фильтрации бронирований"""
    STATUS_CHOICES = [
        ('', 'Все статусы'),
        ('pending', '⏳ Ожидает подтверждения'),
        ('confirmed', '✅ Подтверждено'),
        ('cancelled', '❌ Отменено'),
        ('completed', '🏐 Завершено'),
    ]
    
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-control'}), label='Статус')
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), label='С даты')
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), label='По дату')
    court = forms.ModelChoiceField(queryset=VolleyballCourt.objects.filter(is_active=True), required=False, widget=forms.Select(attrs={'class': 'form-control'}), label='Площадка')