from django import template
from decimal import Decimal, InvalidOperation, ROUND_DOWN

register = template.Library()


@register.filter
def clp(value):
    """Formatea números como CLP sin decimales, con separador de miles con punto.

    Acepta `Decimal`, `int`, `float` o cadenas y devuelve '10.000' estilo chileno.
    """
    try:
        if value is None or value == '':
            return value
        # Normalizar a Decimal
        try:
            val = Decimal(value)
        except InvalidOperation:
            val = Decimal(str(value))

        # Truncar/convertir a entero (pesos completos)
        val_int = int(val.quantize(Decimal('1'), rounding=ROUND_DOWN))
        return f"{val_int:,}".replace(",", ".")
    except Exception:
        return value
