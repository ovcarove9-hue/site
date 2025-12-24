# myapp/admin_urls.py
from django.urls import path
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from .models import VolleyballCourt
from django.utils import timezone

@staff_member_required
def approve_court(request, court_id):
    """Одобрить площадку"""
    court = get_object_or_404(VolleyballCourt, id=court_id)
    
    if request.method == 'POST':
        comment = request.POST.get('comment', '')
        court.approve(request.user, comment)
        messages.success(request, f'✅ Площадка "{court.name}" одобрена')
    else:
        court.status = 'approved'
        court.reviewed_by = request.user
        court.reviewed_at = timezone.now()
        court.is_verified = True
        court.save()
        messages.success(request, f'✅ Площадка "{court.name}" одобрена')
    
    return redirect('admin:myapp_volleyballcourt_changelist')

@staff_member_required
def reject_court(request, court_id):
    """Отклонить площадку"""
    court = get_object_or_404(VolleyballCourt, id=court_id)
    
    if request.method == 'POST':
        comment = request.POST.get('comment', '')
        court.reject(request.user, comment)
        messages.error(request, f'❌ Площадка "{court.name}" отклонена')
    else:
        court.status = 'rejected'
        court.reviewed_by = request.user
        court.reviewed_at = timezone.now()
        court.save()
        messages.error(request, f'❌ Площадка "{court.name}" отклонена')
    
    return redirect('admin:myapp_volleyballcourt_changelist')

@staff_member_required
def request_info_court(request, court_id):
    """Запросить информацию"""
    court = get_object_or_404(VolleyballCourt, id=court_id)
    
    if request.method == 'POST':
        comment = request.POST.get('comment', '')
        court.request_info(request.user, comment)
        messages.warning(request, f'❓ Запрошена информация по площадке "{court.name}"')
    else:
        court.status = 'needs_info'
        court.reviewed_by = request.user
        court.reviewed_at = timezone.now()
        court.save()
        messages.warning(request, f'❓ Запрошена информация по площадке "{court.name}"')
    
    return redirect('admin:myapp_volleyballcourt_changelist')

class ModerationDashboard(TemplateView):
    """Дашборд модератора"""
    template_name = 'admin/moderation_dashboard.html'
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Статистика
        from django.db.models import Count
        from .models import VolleyballCourt
        
        stats = VolleyballCourt.objects.aggregate(
            total=Count('id'),
            pending=Count('id', filter=models.Q(status='pending')),
            approved=Count('id', filter=models.Q(status='approved')),
            rejected=Count('id', filter=models.Q(status='rejected')),
            needs_info=Count('id', filter=models.Q(status='needs_info')),
        )
        
        # Последние предложения
        recent_courts = VolleyballCourt.objects.filter(
            status='pending'
        ).select_related('suggested_by').order_by('-created_at')[:10]
        
        context.update({
            'stats': stats,
            'recent_courts': recent_courts,
            'title': 'Панель модерации площадок'
        })
        return context

# URL patterns
urlpatterns = [
    path('court/<int:court_id>/approve/', approve_court, name='approve_court'),
    path('court/<int:court_id>/reject/', reject_court, name='reject_court'),
    path('court/<int:court_id>/request-info/', request_info_court, name='request_info_court'),
    path('moderation-dashboard/', ModerationDashboard.as_view(), name='moderation_dashboard'),
]