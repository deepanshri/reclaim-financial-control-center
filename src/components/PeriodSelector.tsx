import React from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { PeriodInfo } from '../types';
import { popoverSpring } from '../motion/presets';
import { merchantSeverityIcon, merchantSeverityLabel, merchantSeverityTextClass } from '../severityPresentation';

interface PeriodOption {
  value: string;
  label: string;
  engineLevel: string;
  statusLabel: string;
}

const PERIOD_CATALOG: Array<{ value: string; label: string }> = [
  { value: '2026_H2', label: '2026 · Jul–Dec' },
  { value: '2026_H1', label: '2026 · Jan–Jun' },
  { value: '2025_H2', label: '2025 · Jul–Dec' },
  { value: '2025_H1', label: '2025 · Jan–Jun' },
  { value: '2024_H2', label: '2024 · Jul–Dec' },
  { value: '2024_H1', label: '2024 · Jan–Jun' },
];

function periodLabelFromInfo(info: PeriodInfo): string {
  const half = info.half || info.key.slice(-2);
  const months = half === 'H1' ? 'Jan–Jun' : 'Jul–Dec';
  return `${info.year} · ${months}`;
}

function optionsFromPeriods(availablePeriods: PeriodInfo[]): PeriodOption[] {
  if (availablePeriods.length > 0) {
    return availablePeriods.map((info) => {
      const engineLevel = info.severity_level || info.review_status || 'healthy';
      return {
        value: info.key,
        label: periodLabelFromInfo(info),
        engineLevel,
        statusLabel: info.severity_label || merchantSeverityLabel(engineLevel),
      };
    });
  }
  return PERIOD_CATALOG.map((item) => ({
    value: item.value,
    label: item.label,
    engineLevel: '',
    statusLabel: '',
  }));
}

interface PeriodSelectorProps {
  selectedPeriod: string;
  availablePeriods: PeriodInfo[];
  onChangePeriod: (period: string) => void;
}

export const PeriodSelector: React.FC<PeriodSelectorProps> = ({
  selectedPeriod,
  availablePeriods,
  onChangePeriod,
}) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const [activeIndex, setActiveIndex] = React.useState(0);
  const rootRef = React.useRef<HTMLDivElement>(null);
  const optionRefs = React.useRef<Array<HTMLButtonElement | null>>([]);

  const periodOptions = React.useMemo(
    () => optionsFromPeriods(availablePeriods),
    [availablePeriods]
  );

  const selectedIndex = Math.max(
    0,
    periodOptions.findIndex((opt) => opt.value === selectedPeriod)
  );
  const currentOption = periodOptions[selectedIndex] || periodOptions[0];

  React.useEffect(() => {
    if (isOpen) {
      setActiveIndex(selectedIndex);
    }
  }, [isOpen, selectedIndex]);

  React.useEffect(() => {
    const handlePointerDown = (event: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const selectPeriod = (value: string) => {
    onChangePeriod(value);
    setIsOpen(false);
  };

  const moveActive = (nextIndex: number) => {
    const bounded = (nextIndex + periodOptions.length) % periodOptions.length;
    setActiveIndex(bounded);
    optionRefs.current[bounded]?.scrollIntoView({ block: 'nearest' });
  };

  const handleTriggerKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      if (!isOpen) {
        setIsOpen(true);
        return;
      }
      moveActive(event.key === 'ArrowDown' ? activeIndex + 1 : activeIndex - 1);
      return;
    }
    if (event.key === 'Home' && isOpen) {
      event.preventDefault();
      moveActive(0);
      return;
    }
    if (event.key === 'End' && isOpen) {
      event.preventDefault();
      moveActive(periodOptions.length - 1);
      return;
    }
    if ((event.key === 'Enter' || event.key === ' ') && isOpen) {
      event.preventDefault();
      const option = periodOptions[activeIndex];
      if (option) selectPeriod(option.value);
      return;
    }
    if (event.key === 'Escape' && isOpen) {
      event.preventDefault();
      setIsOpen(false);
    }
  };

  const listboxId = 'audit-period-listbox';
  const activeOption = periodOptions[activeIndex];
  const activeOptionId = activeOption ? `audit-period-option-${activeOption.value}` : undefined;

  return (
    <div className="relative" ref={rootRef}>
      <button
        id="period-select-button"
        type="button"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-controls={listboxId}
        aria-activedescendant={isOpen ? activeOptionId : undefined}
        aria-label={`Audit period ${currentOption?.label || selectedPeriod}${
          currentOption?.statusLabel ? `, status ${currentOption.statusLabel}` : ''
        }`}
        onClick={() => setIsOpen((open) => !open)}
        onKeyDown={handleTriggerKeyDown}
        className="flex h-11 min-w-[16.5rem] max-w-full items-center gap-2.5 rounded-2xl border border-[#E2E2DC] bg-white px-3.5 text-left text-[#1C1917] shadow-[0_1px_2px_rgba(28,25,23,0.04)] transition-colors duration-200 hover:border-[#C5BFB8] hover:bg-[#FAF9F5] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#B8522E] sm:min-w-[20.5rem] dark:border-[#2D2824] dark:bg-[#1E1B18] dark:text-[#FAF7F2] dark:hover:border-[#4A453F] dark:hover:bg-[#241F1C]"
      >
        <span
          className="material-symbols-outlined shrink-0 text-[20px] text-[#57524C] dark:text-[#9E978E]"
          aria-hidden="true"
        >
          calendar_month
        </span>
        <span className="min-w-0 flex-1 truncate font-sans text-[16px] font-semibold tracking-tight">
          {currentOption?.label || selectedPeriod.replace('_', ' ')}
        </span>
        {currentOption?.statusLabel ? (
          <span
            className={`inline-flex min-w-[7.75rem] shrink-0 items-center justify-end gap-1 whitespace-nowrap text-[12px] font-extrabold uppercase tracking-[0.08em] ${merchantSeverityTextClass(
              currentOption.engineLevel
            )}`}
          >
            <span className="material-symbols-outlined text-[16px]" aria-hidden="true">
              {merchantSeverityIcon(currentOption.engineLevel)}
            </span>
            {currentOption.statusLabel}
          </span>
        ) : null}
        <span
          className={`material-symbols-outlined shrink-0 text-[20px] text-[#57524C] transition-transform duration-200 dark:text-[#9E978E] ${
            isOpen ? 'rotate-180' : ''
          }`}
          aria-hidden="true"
        >
          expand_more
        </span>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            key="period-dropdown"
            id={listboxId}
            role="listbox"
            aria-label="Half-year audit periods"
            initial={{ opacity: 0, y: -8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.99 }}
            transition={popoverSpring}
            className="absolute right-0 top-full z-50 mt-2 w-[min(calc(100vw-2rem),22.5rem)] min-w-full overflow-hidden rounded-2xl border border-[#E2E2DC] bg-white p-1.5 shadow-[0_12px_40px_rgba(28,25,23,0.14)] dark:border-[#2D2824] dark:bg-[#1A1815] dark:shadow-[0_12px_40px_rgba(0,0,0,0.45)]"
          >
            {periodOptions.map((option, index) => {
              const isSelected = option.value === selectedPeriod;
              const isActive = index === activeIndex;
              return (
                <button
                  key={option.value}
                  id={`audit-period-option-${option.value}`}
                  ref={(el) => {
                    optionRefs.current[index] = el;
                  }}
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  onMouseEnter={() => setActiveIndex(index)}
                  onClick={() => selectPeriod(option.value)}
                  className={`grid min-h-[48px] w-full grid-cols-[minmax(0,1fr)_minmax(7.75rem,auto)] items-center gap-4 rounded-xl px-3.5 py-2.5 text-left transition-colors duration-150 ${
                    isSelected
                      ? 'bg-[#EAE8E3] dark:bg-[#2A2622]'
                      : isActive
                        ? 'bg-[#F5F5F0] dark:bg-[#241F1C]'
                        : 'bg-transparent'
                  }`}
                >
                  <span className="flex min-w-0 items-center gap-2.5">
                    {isSelected ? (
                      <span
                        className="h-1.5 w-1.5 shrink-0 rounded-full bg-[#B8522E]"
                        aria-hidden="true"
                      />
                    ) : (
                      <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-transparent" aria-hidden="true" />
                    )}
                    <span
                      className={`truncate font-sans text-[16px] ${
                        isSelected
                          ? 'font-bold text-[#1C1917] dark:text-[#FAF7F2]'
                          : 'font-semibold text-[#44403C] dark:text-[#E8E2D8]'
                      }`}
                    >
                      {option.label}
                    </span>
                  </span>
                  {option.statusLabel ? (
                    <span
                      className={`inline-flex min-w-[7.75rem] items-center justify-end gap-1 whitespace-nowrap text-[12px] font-extrabold uppercase tracking-[0.08em] ${merchantSeverityTextClass(
                        option.engineLevel
                      )}`}
                    >
                      <span className="material-symbols-outlined text-[15px]" aria-hidden="true">
                        {merchantSeverityIcon(option.engineLevel)}
                      </span>
                      {option.statusLabel}
                    </span>
                  ) : (
                    <span className="min-w-[7.75rem]" />
                  )}
                </button>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
