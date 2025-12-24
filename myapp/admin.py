# myapp/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from .models import VolleyballCourt, UserProfile, Game, GameParticipation, Friendship

class VolleyballCourtAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'city',
        'status_badge',
        'type_badge',
        'price_display',
        'suggested_by_link',
        'reviewed_by_link',
        'created_at',
        'actions_column'
    ]
    
    list_filter = [
        'status',
        'court_type',
        'is_free',
        'is_verified',
        'is_active',
        'created_at',
        'city'
    ]
    
    search_fields = [
        'name',
        'city',
        'address',
        'description',
        'suggested_by__username',
        'suggested_by__email'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'suggested_by',
        'reviewed_by',
        'reviewed_at'
    ]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'city', 'address', 'description', 'court_type', 'surface')
        }),
        ('Контакты и цены', {
            'fields': ('phone', 'email', 'website', 'is_free', 'price_per_hour', 'price_details')
        }),
        ('Удобства', {
            'fields': ('is_lighted', 'has_parking', 'has_showers', 'has_locker_rooms', 
                      'has_equipment_rental', 'has_cafe', 'courts_count')
        }),
        ('Время работы', {
            'fields': ('opening_time', 'closing_time', 'working_days')
        }),
        ('Модерация', {
            'fields': ('status', 'moderator_comment', 'suggested_by', 'reviewed_by', 'reviewed_at')
        }),
        ('Техническая информация', {
            'fields': ('is_active', 'is_verified', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # actions должен быть СПИСКОМ строк, а не методом
    actions = ['approve_selected', 'reject_selected', 'request_info_selected']
    
    def status_badge(self, obj):
        """Цветной бейдж статуса"""
        colors = {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger',
            'needs_info': 'info'
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.status, 'secondary'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'
    
    def type_badge(self, obj):
        """Бейдж типа площадки"""
        colors = {
            'indoor': 'primary',
            'outdoor': 'success',
            'beach': 'warning'
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.court_type, 'secondary'),
            obj.get_court_type_display()
        )
    type_badge.short_description = 'Тип'
    
    def price_display(self, obj):
        """Отображение цены"""
        if obj.is_free:
            return format_html('<span class="badge bg-success">Бесплатно</span>')
        return f"{obj.price_per_hour} ₽/час"
    price_display.short_description = 'Цена'
    
    def suggested_by_link(self, obj):
        """Ссылка на пользователя, предложившего площадку"""
        if obj.suggested_by:
            url = reverse('admin:auth_user_change', args=[obj.suggested_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.suggested_by.username)
        return '-'
    suggested_by_link.short_description = 'Предложил'
    
    def reviewed_by_link(self, obj):
        """Ссылка на модератора"""
        if obj.reviewed_by:
            url = reverse('admin:auth_user_change', args=[obj.reviewed_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.reviewed_by.username)
        return '-'
    reviewed_by_link.short_description = 'Проверил'
    
    def actions_column(self, obj):
        """Кнопки действий в колонке"""
        buttons = []
        
        if obj.status != 'approved':
            approve_url = reverse('admin:myapp_volleyballcourt_change', args=[obj.id])
            buttons.append(
                f'<a href="{approve_url}" class="button">✅</a>'
            )
        
        return format_html(' '.join(buttons)) if buttons else '-'
    actions_column.short_description = 'Действия'
    
    # Методы для действий
    def approve_selected(self, request, queryset):
        """Одобрить выбранные площадки"""
        updated = queryset.update(
            status='approved',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
            is_verified=True
        )
        self.message_user(request, f'✅ Одобрено {updated} площадок')
    approve_selected.short_description = '✅ Одобрить выбранные'
    
    def reject_selected(self, request, queryset):
        """Отклонить выбранные площадки"""
        updated = queryset.update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'❌ Отклонено {updated} площадок')
    reject_selected.short_description = '❌ Отклонить выбранные'
    
    def request_info_selected(self, request, queryset):
        """Запросить информацию по выбранным"""
        updated = queryset.update(
            status='needs_info',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'❓ Запрошена информация по {updated} площадкам')
    request_info_selected.short_description = '❓ Запросить информацию'
    
    # Показывать только площадки на модерации обычным пользователям
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(suggested_by=request.user)

# Упрощенная версия, если всё ещё есть ошибки
class SimpleVolleyballCourtAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'status', 'court_type', 'created_at']
    list_filter = ['status', 'court_type', 'city']
    search_fields = ['name', 'city', 'address']
    readonly_fields = ['created_at', 'updated_at', 'suggested_by']

# Регистрация моделей
admin.site.register(VolleyballCourt, SimpleVolleyballCourtAdmin)  # Используйте простую версию
admin.site.register(UserProfile)
admin.site.register(Game)
admin.site.register(GameParticipation)
admin.site.register(Friendship)