from django import forms
from .models import UserProfile, UserSettings, VolleyballCourt  # Добавьте VolleyballCourt
from django.contrib.auth.models import User
from .models import GameEvent, Location
from .models import Game
import re
from django import forms
from django.forms.widgets import DateTimeInput, TimeInput, DateInput
from .models import Game, GameParticipation
import datetime

class GameCreateForm(forms.ModelForm):
    """Форма создания игры"""
    
    class Meta:
        model = Game
        fields = [
            'title', 'description', 'court', 'custom_location',
            'start_time', 'end_time', 'game_type', 'skill_level',
            'max_players', 'min_players', 'is_private', 'price'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Еженедельная тренировка'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Опишите детали игры...'
            }),
            'start_time': DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'end_time': DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'max_players': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2,
                'max': 30
            }),
            'min_players': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2,
                'max': 12
            }),
            'court': forms.Select(attrs={'class': 'form-control'}),
            'custom_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Или укажите место вручную'
            }),
            'game_type': forms.Select(attrs={'class': 'form-control'}),
            'skill_level': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            if end_time <= start_time:
                raise forms.ValidationError("Время окончания должно быть позже времени начала")
            
            if start_time < datetime.datetime.now():
                raise forms.ValidationError("Нельзя создать игру в прошлом")
        
        return cleaned_data


class GameJoinForm(forms.ModelForm):
    """Форма вступления в игру"""
    
    class Meta:
        model = GameParticipation
        fields = []

class CourtSuggestionForm(forms.ModelForm):
    """Форма для предложения новой площадки"""
    
    # Добавляем поле подтверждения правил
    accept_rules = forms.BooleanField(
        required=True,
        label='Я подтверждаю, что предоставленная информация точна и соответствует правилам сообщества'
    )
    
    class Meta:
        model = VolleyballCourt
        fields = [
            'name', 'city', 'address', 'court_type', 'description',
            'is_free', 'price_per_hour', 'price_details',
            'is_lighted', 'has_showers', 'has_locker_rooms', 
            'has_equipment_rental', 'has_parking', 'has_cafe',
            'opening_time', 'closing_time', 'working_days',
            'phone', 'website', 'email',
            'courts_count', 'surface',
            'photo_url', 'tags'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Спорткомплекс "Чемпион"'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Москва'
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
                'placeholder': 'Например: Пн-Пт 8:00-22:00, Сб-Вс 9:00-20:00'
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
        }
        
        help_texts = {
            'photo_url': 'Загрузите фото на imgur.com и вставьте прямую ссылку',
            'tags': 'Укажите через запятую ключевые слова для поиска',
        }
    
    def clean_phone(self):
        """Валидация телефона"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Удаляем все символы кроме цифр и +
            phone = re.sub(r'[^\d+]', '', phone)
            if len(phone) < 10:
                raise forms.ValidationError('Некорректный номер телефона')
        return phone
    
    def clean_price_per_hour(self):
        """Валидация цены"""
        price = self.cleaned_data.get('price_per_hour')
        is_free = self.cleaned_data.get('is_free', False)
        
        if is_free and price > 0:
            raise forms.ValidationError('Для бесплатной площадки цена должна быть 0')
        
        return price

class CourtCoordinatesForm(forms.Form):
    """Форма для указания координат"""
    latitude = forms.DecimalField(
        label='Широта',
        max_digits=9,
        decimal_places=6,
        required=False,
        help_text='Например: 55.7558 (Москва)'
    )
    longitude = forms.DecimalField(
        label='Долгота',
        max_digits=9,
        decimal_places=6,
        required=False,
        help_text='Например: 37.6173 (Москва)'
    )
    
    def clean(self):
        """Проверка, что либо оба поля заполнены, либо оба пустые"""
        cleaned_data = super().clean()
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')
        
        if bool(latitude) != bool(longitude):
            raise forms.ValidationError(
                'Заполните оба поля координат или оставьте оба пустыми'
            )
        
        # Проверка диапазонов
        if latitude and longitude:
            if not (-90 <= latitude <= 90):
                raise forms.ValidationError('Широта должна быть между -90 и 90')
            if not (-180 <= longitude <= 180):
                raise forms.ValidationError('Долгота должна быть между -180 и 180')
        
        return cleaned_data

class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = [
            'title', 'game_type', 'description', 'date', 
            'start_time', 'end_time', 'court', 'location',
            'max_players', 'min_skill_level', 'game_format',
            'price_type', 'price_per_player', 'requirements',
            'is_public'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Вечерняя игра для любителей'
            }),
            'game_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Опишите детали игры...'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            }),
            'court': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Адрес или название площадки'
            }),
            'max_players': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2,
                'max': 30
            }),
            'min_skill_level': forms.Select(attrs={'class': 'form-control'}),
            'game_format': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '6v6, 4v4, 2v2'
            }),
            'price_type': forms.Select(attrs={'class': 'form-control'}),
            'price_per_player': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 50,
                'min': 0
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Требования к игрокам...'
            }),
        }
        help_texts = {
            'location': 'Укажите, если нет подходящей площадки в списке',
            'game_format': 'Формат игры: 6×6, 4×4, 2×2 и т.д.',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if date and start_time and end_time:
            from datetime import datetime
            game_datetime_start = datetime.combine(date, start_time)
            game_datetime_end = datetime.combine(date, end_time)
            
            if game_datetime_end <= game_datetime_start:
                raise forms.ValidationError('Время окончания должно быть позже времени начала')
            
            if game_datetime_start < datetime.now():
                raise forms.ValidationError('Нельзя создать игру в прошлом')
        
        return cleaned_data

class GameEventForm(forms.ModelForm):
    class Meta:
        model = GameEvent
        fields = [
            'title', 'description', 'date', 'start_time', 'end_time',
            'location', 'game_type', 'skill_level', 'max_players',
            'is_free', 'price'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['location'].queryset = Location.objects.filter(is_active=True)


class SearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        label='Поиск',
        widget=forms.TextInput(attrs={'placeholder': 'Поиск игроков...'})
    )
    city = forms.CharField(required=False, label='Город')
    position = forms.ChoiceField(
        required=False,
        choices=[('', 'Любая позиция')] + UserProfile.POSITION_CHOICES,
        label='Позиция'
    )
    skill_level = forms.ChoiceField(
        required=False,
        choices=[('', 'Любой уровень')] + UserProfile.SKILL_LEVEL_CHOICES,
        label='Уровень'
    )
    min_age = forms.IntegerField(required=False, label='Минимальный возраст', min_value=18, max_value=80)
    max_age = forms.IntegerField(required=False, label='Максимальный возраст', min_value=18, max_value=80)

class FriendSearchForm(forms.Form):
    """Форма поиска друзей"""
    SEARCH_TYPE_CHOICES = [
        ('all', 'Все пользователи'),
        ('friends', 'Мои друзья'),
        ('not_friends', 'Еще не друзья'),
    ]
    
    search_type = forms.ChoiceField(
        label='Тип поиска',
        choices=SEARCH_TYPE_CHOICES,
        initial='all',
        widget=forms.RadioSelect(attrs={'class': 'search-type-radio'})
    )
    
    query = forms.CharField(
        label='Поиск',
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Имя, город, интересы...',
            'class': 'form-control'
        })
    )
    
    city = forms.CharField(
        label='Город',
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Введите город',
            'class': 'form-control'
        })
    )
    
    min_age = forms.IntegerField(
        label='Возраст от',
        required=False,
        min_value=16,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '18'
        })
    )
    
    max_age = forms.IntegerField(
        label='до',
        required=False,
        min_value=16,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '60'
        })
    )
    
    interests = forms.CharField(
        label='Интересы',
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'волейбол, спорт, музыка...',
            'class': 'form-control'
        })
    )

class ProfileEditForm(forms.ModelForm):
    """Форма редактирования профиля"""
    first_name = forms.CharField(
        label='Имя',
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    last_name = forms.CharField(
        label='Фамилия',
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'city', 'age', 'position', 'positions', 
            'skill_level', 'playing_years', 'height', 'interests',
            'telegram', 'vk'
        ]
        
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Расскажите о себе...'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваш город'
            }),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'position': forms.Select(attrs={'class': 'form-control'}),
            'positions': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: связующий, доигровщик'
            }),
            'skill_level': forms.Select(attrs={'class': 'form-control'}),
            'playing_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'height': forms.NumberInput(attrs={'class': 'form-control'}),
            'interests': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: волейбол, музыка, путешествия'
            }),
            'telegram': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '@username'
            }),
            'vk': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'id или username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

class AvatarUploadForm(forms.ModelForm):
    """Форма загрузки аватара"""
    class Meta:
        model = UserProfile
        fields = ['avatar']
        widgets = {
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }

class SettingsForm(forms.ModelForm):
    """Форма настроек"""
    class Meta:
        model = UserSettings
        fields = ['show_email', 'show_age', 'show_last_online', 
                 'notifications_enabled', 'private_profile']
        
        widgets = {
            'show_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_age': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_last_online': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notifications_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'private_profile': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

