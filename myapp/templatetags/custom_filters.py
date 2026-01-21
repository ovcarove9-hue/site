from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Получить значение из словаря по ключу"""
    return dictionary.get(key)

@register.filter
def get_item_or_default(dictionary, key, default=None):
    """Получить значение из словаря или значение по умолчанию"""
    return dictionary.get(key, default)