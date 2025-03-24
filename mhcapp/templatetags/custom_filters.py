from django import template

register = template.Library()

@register.filter
def status_badge_class(status):
    if status == 'requested':
        return 'warning'
    elif status == 'completed':
        return 'success'
    elif status == 'canceled':
        return 'danger'
    else:
        return 'secondary'
    
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def split_reference(value, delimiter=", "):
    return value.split(delimiter)