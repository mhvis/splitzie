import decimal

from django import template

register = template.Library()


@register.filter
def euro(amount):
    # locale.setlocale(locale.LC_ALL, 'nl_NL')
    # return locale.currency(amount)
    # Todo: choose some locale
    # if amount < 0:
    #     return f"-€ {-amount}".replace(".", ",")
    # else:
    #     return mark_safe(f"&nbsp;€ {amount}".replace(".", ","))
    return f"-€{-amount}" if amount < 0 else f"€{amount}"


@register.filter
def cents(amount: decimal.Decimal):
    """Converts the euro amount to cents with type int."""
    return int(
        amount.shift(2).to_integral_exact(
            context=decimal.Context(traps=[decimal.Inexact])
        )
    )
