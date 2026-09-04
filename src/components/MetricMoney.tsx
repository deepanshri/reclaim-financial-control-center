import React from 'react';
import { formatINR, formatINRCompact } from '../utils/money';

interface MetricMoneyProps {
  value: number;
  className?: string;
  exactClassName?: string;
}

export const MetricMoney: React.FC<MetricMoneyProps> = ({
  value,
  className = '',
  exactClassName = 'mt-1 text-[12px] sm:text-[13px] font-medium tabular-nums text-[#787168] dark:text-[#A8A29E] truncate block',
}) => {
  const exact = formatINR(value);
  const compact = formatINRCompact(value);
  const showExact = compact !== exact;

  return (
    <div className="min-w-0 max-w-full overflow-hidden" title={exact}>
      <div className={`font-sans font-bold tabular-nums tracking-tight leading-tight truncate ${className}`}>
        {compact}
      </div>
      {showExact ? (
        <div className={exactClassName} title={exact}>
          {exact}
        </div>
      ) : null}
    </div>
  );
};
