from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from myapp.models import Court
import decimal


def robots_txt(request):
    """Отображение файла robots.txt"""
    content = """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /accounts/
Disallow: /search/

Sitemap: https://volleymap.ru/sitemap.xml

# Блокировка для нежелательных страниц
Disallow: /*?*
Disallow: /login/
Disallow: /register/
Disallow: /logout/
"""
    return HttpResponse(content, content_type="text/plain")


def sitemap_xml(request):
    """Генерация файла sitemap.xml"""
    # Получаем все основные URL-адреса
    urls = [
        {'loc': request.build_absolute_uri(reverse('home')), 'lastmod': timezone.now().strftime('%Y-%m-%d'), 'changefreq': 'daily', 'priority': '1.0'},
        {'loc': request.build_absolute_uri(reverse('map')), 'lastmod': timezone.now().strftime('%Y-%m-%d'), 'changefreq': 'weekly', 'priority': '0.9'},
        {'loc': request.build_absolute_uri(reverse('event_calendar')), 'lastmod': timezone.now().strftime('%Y-%m-%d'), 'changefreq': 'daily', 'priority': '0.8'},
        {'loc': request.build_absolute_uri(reverse('search')), 'lastmod': timezone.now().strftime('%Y-%m-%d'), 'changefreq': 'weekly', 'priority': '0.7'},
        {'loc': request.build_absolute_uri(reverse('create_game')), 'lastmod': timezone.now().strftime('%Y-%m-%d'), 'changefreq': 'monthly', 'priority': '0.6'},
        {'loc': request.build_absolute_uri(reverse('create_court')), 'lastmod': timezone.now().strftime('%Y-%m-%d'), 'changefreq': 'monthly', 'priority': '0.5'},
    ]

    # Добавляем профили пользователей
    users = User.objects.filter(is_active=True)[:100]  # Ограничиваем количество для производительности
    for user in users:
        try:
            profile_url = request.build_absolute_uri(reverse('profile', kwargs={'user_id': user.id}))
            urls.append({
                'loc': profile_url,
                'lastmod': (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                'changefreq': 'weekly',
                'priority': '0.5'
            })
        except:
            pass  # Пропускаем, если не удается создать URL

    # Добавляем страницы площадок
    from .models import VolleyballCourt  # Импортируем внутри функции, чтобы избежать циклических импортов
    courts = VolleyballCourt.objects.filter(status='approved')[:100]  # Ограничиваем количество для производительности
    for court in courts:
        try:
            court_url = request.build_absolute_uri(reverse('court_detail', kwargs={'court_id': court.id}))
            # Используем дату создания или текущую дату, если поле не существует
            lastmod_date = court.created_at.strftime('%Y-%m-%d') if hasattr(court, 'created_at') else timezone.now().strftime('%Y-%m-%d')
            urls.append({
                'loc': court_url,
                'lastmod': lastmod_date,
                'changefreq': 'weekly',
                'priority': '0.6'
            })
        except:
            pass  # Пропускаем, если не удается создать URL

    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""

    for url in urls:
        xml_content += f"""  <url>
    <loc>{url['loc']}</loc>
    <lastmod>{url['lastmod']}</lastmod>
    <changefreq>{url['changefreq']}</changefreq>
    <priority>{url['priority']}</priority>
  </url>
"""

    xml_content += "</urlset>"

    return HttpResponse(xml_content, content_type="application/xml")