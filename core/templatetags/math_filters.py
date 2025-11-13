from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    """Subtract the arg from the value."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def make_list(value):
    """Convert an integer to a list of that length."""
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return range(0)