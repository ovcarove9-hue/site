"""
Вспомогательные функции для приложения myapp
"""
from django.contrib.auth.models import User
from .models import UserProfile


def get_or_create_user_profile(user):
    """
    Получить или создать профиль пользователя
    """
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile


def validate_phone_number(phone):
    """
    Валидация номера телефона
    """
    import re
    if phone:
        phone = re.sub(r'[^\d+]', '', phone)
        if len(phone) < 10:
            return False
    return True


def calculate_age(birth_date):
    """
    Рассчитать возраст по дате рождения
    """
    from datetime import date
    if birth_date:
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return None


def format_phone_number(phone):
    """
    Форматировать номер телефона для отображения
    """
    import re
    digits_only = re.sub(r'[^\d]', '', phone)
    if len(digits_only) == 11 and digits_only.startswith('7'):
        digits_only = '8' + digits_only[1:]
    return digits_only