from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Настройка админ-панели
admin.site.site_header = "VolleyMap - Администрирование"
admin.site.site_title = "VolleyMap Admin"
admin.site.index_title = "Панель управления VolleyMap"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('myapp.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)