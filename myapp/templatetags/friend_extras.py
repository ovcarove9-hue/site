from django import template
from myapp.models import Friendship

register = template.Library()

@register.filter
def get_friend_requests_count(user):
    """Возвращает количество входящих заявок в друзья"""
    if user.is_authenticated:
        return Friendship.objects.filter(
            to_user=user,
            status='pending'
        ).count()
    return 0