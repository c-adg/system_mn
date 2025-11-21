from django import template

register = template.Library()

@register.filter
def clp(value):
    """Formatea números como CLP: 10.000"""
    try:
        value = float(value)
        return f"{value:,.0f}".replace(",", ".")
    except:
        return value
