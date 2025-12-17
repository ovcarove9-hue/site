# myapp/admin.py
from django.contrib import admin
from .models import VolleyballCourt, Game, UserProfile, Friendship

@admin.register(VolleyballCourt)
class VolleyballCourtAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'status', 'suggested_by', 'created_at')
    list_filter = ('status', 'city', 'court_type')
    search_fields = ('name', 'city', 'address')
    actions = ['approve_courts', 'reject_courts']  # Простой список строк
    
    def approve_courts(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f"{queryset.count()} площадок одобрено")
    approve_courts.short_description = "Одобрить выбранные"
    
    def reject_courts(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} площадок отклонено")
    reject_courts.short_description = "Отклонить выбранные"

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'start_time', 'game_type', 'created_by')
    list_filter = ('game_type', 'date')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'position', 'skill_level')

@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'status', 'created_at')