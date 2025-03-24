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