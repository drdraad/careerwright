"""Exact amounts from source text (Global Constraint 4: integer minor units, never floats).
A JSON number or numeric string becomes GBP pence only when it is exact to the penny;
otherwise the reason it cannot be read is returned, so the value stays unknown."""

import re
from decimal import Decimal, InvalidOperation

_AMOUNT = re.compile(r"^[0-9]+(\.[0-9]+)?$")


def minor_units(amount: object) -> int | str:
    """Pence for an amount in pounds, or the issue (`salary_invalid`, `salary_not_exact`)."""
    if isinstance(amount, bool) or not isinstance(amount, (int, float, str)):
        return "salary_invalid"
    text = str(amount).strip()
    if not _AMOUNT.match(text):
        return "salary_invalid"
    try:
        pence = Decimal(text) * 100
    except InvalidOperation:
        return "salary_invalid"
    if pence != pence.to_integral_value():
        return "salary_not_exact"
    return int(pence)
