export function formatINR(value?: number | null): string {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '₹0.00';
  }
  return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
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
