# handler.py
from django.shortcuts import render

def handler404(request, exception):
    """Обработчик 404 ошибки"""
    return render(request, 'myapp/404.html', status=404)

def handler500(request):
    """Обработчик 500 ошибки"""
    return render(request, 'myapp/500.html', status=500)

def handler403(request, exception):
    """Обработчик 403 ошибки"""
    return render(request, 'myapp/403.html', status=403)

def handler400(request, exception):
    """Обработчик 400 ошибки"""
    return render(request, 'myapp/400.html', status=400)