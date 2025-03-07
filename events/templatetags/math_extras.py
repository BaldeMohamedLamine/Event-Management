from django import template

register = template.Library()

@register.filter
def div(value, arg):
    """Divise value par arg. Retourne 0 si arg est 0."""
    try:
        value = float(value)
        arg = float(arg)
        if arg == 0:
            return 0
        return value / arg
    except (ValueError, TypeError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiplie value par arg."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def minus(value, arg):
    """Soustrait `arg` de `value`."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value
