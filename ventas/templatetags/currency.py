from django import template
register = template.Library()

@register.filter
def clp(value):
    """Formatea números como CLP: 1.234.567,89"""
    try:
        n = float(value)
    except (TypeError, ValueError):
        return value
    entero, _, dec = f"{n:,.2f}".partition(".")
    entero = entero.replace(",", ".")
    return f"{entero},{dec}"

@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return ""
