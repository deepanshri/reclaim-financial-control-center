"""Integer-paise money helpers. Never accumulate IEEE floats for INR amounts."""

from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

PAISE_QUANT = Decimal("1")
INR_QUANT = Decimal("0.01")


def inr_to_paise(value: Any) -> int:
    if value is None or value == "":
        return 0
    try:
        quantized = (Decimal(str(value)) * Decimal(100)).quantize(PAISE_QUANT, rounding=ROUND_HALF_EVEN)
    except Exception:
        return 0
    return int(quantized)


def paise_to_inr_decimal(paise: int) -> Decimal:
    return (Decimal(int(paise)) / Decimal(100)).quantize(INR_QUANT, rounding=ROUND_HALF_EVEN)


def paise_to_inr(paise: int) -> float:
    """JSON-friendly INR with exactly two decimal places."""
    return float(paise_to_inr_decimal(paise))
