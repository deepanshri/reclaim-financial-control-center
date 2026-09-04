export function formatINR(value?: number | null): string {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '₹0.00';
  }
  return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/** Compact units so large amounts fit in metric cards (e.g. 50K). */
export function formatINRCompact(value?: number | null): string {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '₹0.00';
  }
  const abs = Math.abs(value);
  const sign = value < 0 ? '-' : '';
  if (abs >= 1_000_000_000) {
    return `${sign}₹${(abs / 1_000_000_000).toLocaleString('en-US', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 2,
    })}B`;
  }
  if (abs >= 1_000_000) {
    return `${sign}₹${(abs / 1_000_000).toLocaleString('en-US', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 2,
    })}M`;
  }
  if (abs >= 1_000) {
    return `${sign}₹${(abs / 1_000).toLocaleString('en-US', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 2,
    })}K`;
  }
  return formatINR(value);
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
