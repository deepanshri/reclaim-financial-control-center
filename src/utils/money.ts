const LAKH = 100_000;
const CRORE = 10_000_000;

export function formatINR(value?: number | null): string {
  if (value === undefined || value === null || !Number.isFinite(value)) {
    return '₹0.00';
  }
  // Sign sits outside the symbol (-₹1,234.50) to match the compact form.
  const sign = value < 0 ? '-' : '';
  return `${sign}₹${Math.abs(value).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function toTwoDecimals(value: number): number {
  return Math.round(value * 100) / 100;
}

function withUnit(sign: string, magnitude: number, unit: string): string {
  const rendered = magnitude.toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${sign}₹${rendered}${unit}`;
}

/**
 * Merchant-facing display of an INR amount using Indian lakh/crore notation so
 * large values fit a metric card (₹57,97,08,756 renders as ₹57.97Cr).
 * Display only — callers must keep using the raw number for any arithmetic.
 */
export function formatINRCompact(value?: number | null): string {
  if (value === undefined || value === null || !Number.isFinite(value)) {
    return '₹0.00';
  }

  const abs = Math.abs(value);
  const sign = value < 0 ? '-' : '';

  if (abs < LAKH) {
    return formatINR(value);
  }

  // Round within lakh first: an amount such as ₹99,99,999.50 rounds up across
  // the crore boundary and must read ₹1.00Cr rather than ₹100.00L.
  const inLakh = toTwoDecimals(abs / LAKH);
  if (inLakh < 100) {
    return withUnit(sign, inLakh, 'L');
  }
  return withUnit(sign, toTwoDecimals(abs / CRORE), 'Cr');
}

export function paiseToINR(paise?: number | null): number {
  if (paise === undefined || paise === null || Number.isNaN(paise)) return 0;
  return Math.round(paise) / 100;
}

/** Remaining eligible recovery in INR, rounded to paise. Never negative. */
export function remainingRecoveryInr(
  potential?: number | null,
  alreadyRequested?: number | null
): number {
  const potentialAmount = potential ?? 0;
  const requestedAmount = alreadyRequested ?? 0;
  return Math.max(0, Math.round((potentialAmount - requestedAmount) * 100) / 100);
}
