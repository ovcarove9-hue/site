# myapp/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Friendship, Notification

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        nickname = instance.username
        if nickname.startswith('+7'):
            nickname = nickname.replace('+7', '')
        UserProfile.objects.create(
            user=instance, 
            phone=instance.username,
            nickname=nickname[:20]
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

@receiver(post_save, sender=Friendship)
def create_friend_notification(sender, instance, created, **kwargs):
    if created and instance.status == 'pending':
        # Уведомление о запросе в друзья
        Notification.objects.create(
            user=instance.to_user,
            notification_type='friend_request',
            title='Новый запрос в друзья',
            message=f'{instance.from_user.profile.nickname} хочет добавить вас в друзья',
            related_user=instance.from_user,
            link=f'/user/{instance.from_user.id}/'
        )
    elif instance.status == 'accepted':
        # Уведомление о принятии дружбы
        Notification.objects.create(
            user=instance.from_user,
            notification_type='friend_accepted',
            title='Запрос в друзья принят',
            message=f'{instance.to_user.profile.nickname} принял(а) ваш запрос в друзья',
            related_user=instance.to_user,
            link=f'/user/{instance.to_user.id}/'
        )
    elif instance.status == 'rejected':
        # Уведомление об отклонении дружбы
        Notification.objects.create(
            user=instance.from_user,
            notification_type='friend_rejected',
            title='Запрос в друзья отклонен',
            message=f'{instance.to_user.profile.nickname} отклонил(а) ваш запрос в друзья',
            related_user=instance.to_user
        )