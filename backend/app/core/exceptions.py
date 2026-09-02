from typing import Optional


class InvalidPeriodError(ValueError):
    def __init__(self, period: Optional[str], valid: list[str]):
        self.period = period
        self.valid = valid
        super().__init__(f"Unknown period '{period}'")
