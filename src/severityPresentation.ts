/** Merchant-facing severity labels and colors. Internal engine keys are unchanged. */

export type MerchantSeverity = 'monitor' | 'intermediate' | 'action_needed' | 'urgent_action';

/**
 * Engine → merchant mapping:
 * action_needed / action_required → URGENT ACTION (strong red)
 * needs_review                   → ACTION NEEDED (red)
 * intermediate / watch           → INTERMEDIATE (orange)
 * healthy / default              → MONITOR (yellow/gold)
 */
export function merchantSeverity(level?: string): MerchantSeverity {
  const value = (level || '').toLowerCase().trim();
  if (
    value === 'action_needed' ||
    value === 'action_required' ||
    value === 'action' ||
    value === 'urgent' ||
    value === 'urgent_action'
  ) {
    return 'urgent_action';
  }
  if (value === 'needs_review' || value === 'review') {
    return 'action_needed';
  }
  if (value === 'intermediate' || value === 'watch' || value === 'caution') {
    return 'intermediate';
  }
  return 'monitor';
}

export function merchantSeverityLabel(level?: string): string {
  const severity = merchantSeverity(level);
  if (severity === 'urgent_action') return 'URGENT ACTION';
  if (severity === 'action_needed') return 'ACTION NEEDED';
  if (severity === 'intermediate') return 'INTERMEDIATE';
  return 'MONITOR';
}

export function merchantSeverityMessage(level?: string): string {
  const severity = merchantSeverity(level);
  if (severity === 'urgent_action') {
    return 'A significant amount is affected and needs immediate attention.';
  }
  if (severity === 'action_needed') {
    return 'A meaningful amount is affected and should be reviewed.';
  }
  if (severity === 'intermediate') {
    return 'This period needs attention, but the impact is not yet in the highest band.';
  }
  return 'A small difference was found, but no immediate action is needed.';
}

export function merchantSeverityIcon(level?: string): string {
  const severity = merchantSeverity(level);
  if (severity === 'urgent_action') return 'error';
  if (severity === 'action_needed') return 'priority_high';
  if (severity === 'intermediate') return 'warning';
  return 'verified_user';
}

/** Status text/icon color — semantic, not used as a full-row fill. */
export function merchantSeverityTextClass(level?: string): string {
  const severity = merchantSeverity(level);
  if (severity === 'urgent_action') {
    return 'text-[#991B1B] dark:text-[#F87171]';
  }
  if (severity === 'action_needed') {
    return 'text-[#B91C1C] dark:text-[#FCA5A5]';
  }
  if (severity === 'intermediate') {
    return 'text-[#C27803] dark:text-[#E59B22]';
  }
  return 'text-[#8A6B00] dark:text-[#E8D48A]';
}

export function merchantSeverityBadgeClass(level?: string): string {
  const severity = merchantSeverity(level);
  if (severity === 'urgent_action') {
    return 'bg-[#991B1B]/12 text-[#991B1B] dark:bg-[#7F1D1D]/40 dark:text-[#F87171]';
  }
  if (severity === 'action_needed') {
    return 'bg-[#B91C1C]/12 text-[#B91C1C] dark:bg-[#7F1D1D]/30 dark:text-[#FCA5A5]';
  }
  if (severity === 'intermediate') {
    return 'bg-[#C27803]/15 text-[#C27803] dark:text-[#E59B22]';
  }
  return 'bg-[#E8C547]/30 text-[#8A6B00] dark:bg-[#3D3510] dark:text-[#E8D48A]';
}

export function merchantSeverityBannerClass(level?: string): string {
  const severity = merchantSeverity(level);
  if (severity === 'urgent_action') {
    return 'bg-[#FDF2F2] dark:bg-[#2A1212] border-[#F2C4C4] dark:border-[#4D1919]';
  }
  if (severity === 'action_needed') {
    return 'bg-[#FDF3F0] dark:bg-[#2A1612] border-[#F2C4B7] dark:border-[#4D2319]';
  }
  if (severity === 'intermediate') {
    return 'bg-[#FEF8EC] dark:bg-[#281E10] border-[#FADBA8] dark:border-[#4B371B]';
  }
  return 'bg-[#FEF9E7] dark:bg-[#2A2410] border-[#E8D48B] dark:border-[#5C4E1A]';
}

export function merchantSeverityIconWrapClass(level?: string): string {
  const severity = merchantSeverity(level);
  if (severity === 'urgent_action') return 'bg-[#991B1B] text-white';
  if (severity === 'action_needed') return 'bg-[#B91C1C] text-white';
  if (severity === 'intermediate') return 'bg-[#C27803] text-white';
  return 'bg-[#C9A227] text-white';
}

export function merchantSeverityAmountClass(level?: string): string {
  const severity = merchantSeverity(level);
  if (severity === 'urgent_action') return 'text-[#991B1B] dark:text-[#F87171]';
  if (severity === 'action_needed') return 'text-[#B91C1C] dark:text-[#FCA5A5]';
  if (severity === 'intermediate') return 'text-[#C27803] dark:text-[#E59B22]';
  return 'text-[#8A6B00] dark:text-[#E8D48A]';
}

/** Row/option chrome. Selected state uses the product surface — never browser blue. */
export function merchantSeverityOptionClass(level?: string, selected?: boolean): string {
  const statusColor = merchantSeverityTextClass(level);
  if (selected) {
    return `bg-[#EAE8E3] text-[#1C1917] dark:bg-[#2A2622] dark:text-[#FAF7F2] ${statusColor}`;
  }
  return statusColor;
}
