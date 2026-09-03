from typing import List, Optional

from fastapi import HTTPException, status

from app.core.exceptions import InvalidPeriodError
from app.services.data_repository import DEFAULT_PERIOD, PERIOD_KEYS, data_repository


def available_period_keys() -> List[str]:
    keys = list(data_repository.period_keys())
    return keys or list(PERIOD_KEYS)


def resolve_period_key(period: Optional[str] = None, year: Optional[int] = None) -> str:
    """
    Resolve a client period argument.

    Omitted period still defaults to the current demo period.
    An explicitly provided unknown period is a client error — never silent substitution.
    Period resolution does not parse CSV files.
    """
    known = set(available_period_keys())

    if period:
        cleaned = period.strip().replace("-", "_").replace(" ", "_").upper()
        if cleaned in known:
            return cleaned
        for key in PERIOD_KEYS:
            if key.replace("_", "") == cleaned.replace("_", "") and key in known:
                return key
        raise InvalidPeriodError(period, sorted(known))

    if year is not None:
        yr_str = str(year)
        for key in (f"{yr_str}_H2", f"{yr_str}_H1"):
            if key in known:
                return key
        raise InvalidPeriodError(str(year), sorted(known))

    if DEFAULT_PERIOD in known:
        return DEFAULT_PERIOD
    if known:
        return sorted(known)[-1]
    raise InvalidPeriodError(None, list(PERIOD_KEYS))


def period_or_400(period: Optional[str] = None, year: Optional[int] = None) -> str:
    try:
        return resolve_period_key(period, year)
    except InvalidPeriodError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_period",
                "message": f"Unknown period '{exc.period}'.",
                "valid_periods": exc.valid,
            },
        ) from exc
