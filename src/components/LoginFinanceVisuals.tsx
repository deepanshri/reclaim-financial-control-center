import React from 'react';
import { motion, useReducedMotion } from 'motion/react';
import { visualSpring } from '../motion/presets';

const visualClass =
  'login-visual absolute hidden overflow-visible lg:block pointer-events-auto cursor-default will-change-transform';

interface VisualSlotProps {
  className: string;
  from: { x: number; y: number };
  delay: number;
  restRotate: number;
  hoverRotate: number;
  children: React.ReactNode;
}

function VisualSlot({ className, from, delay, restRotate, hoverRotate, children }: VisualSlotProps) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.div
      className={`${visualClass} ${className}`}
      initial={reduceMotion ? { opacity: 0, rotate: restRotate } : { opacity: 0, scale: 0.96, x: from.x, y: from.y, rotate: restRotate }}
      animate={{ opacity: 1, scale: 1, x: 0, y: 0, rotate: restRotate }}
      whileHover={
        reduceMotion
          ? undefined
          : {
              scale: 1.07,
              y: -10,
              rotate: hoverRotate,
              transition: { type: 'spring', stiffness: 380, damping: 22 },
            }
      }
      transition={reduceMotion ? { duration: 0.22, delay } : visualSpring(delay)}
    >
      {children}
    </motion.div>
  );
}

export const LoginFinanceVisuals: React.FC = () => {
  return (
    <div className="pointer-events-none absolute inset-0 z-[1] select-none" aria-hidden="true">
      <VisualSlot
        className="left-[1.5%] top-[6%] xl:left-[3%] xl:top-[7%]"
        from={{ x: -14, y: -10 }}
        delay={0}
        restRotate={-8}
        hoverRotate={-12}
      >
        <CoinBankMark />
      </VisualSlot>

      <VisualSlot
        className="right-[1.5%] top-[5%] xl:right-[2.5%] xl:top-[6%]"
        from={{ x: 14, y: -10 }}
        delay={0.05}
        restRotate={7}
        hoverRotate={11}
      >
        <BanknoteStackMark />
      </VisualSlot>

      <VisualSlot
        className="bottom-[6%] left-[1.5%] xl:bottom-[8%] xl:left-[3%]"
        from={{ x: -14, y: 10 }}
        delay={0.1}
        restRotate={-6}
        hoverRotate={-10}
      >
        <AuditGraphMark />
      </VisualSlot>

      <VisualSlot
        className="bottom-[5%] right-[1.5%] xl:bottom-[7%] xl:right-[3%]"
        from={{ x: 14, y: 10 }}
        delay={0.15}
        restRotate={18}
        hoverRotate={24}
      >
        <RupeeFolderMark />
      </VisualSlot>
    </div>
  );
};

function CoinBankMark() {
  return (
    <svg viewBox="0 0 200 200" fill="none" className="h-auto w-full overflow-visible">
      <circle cx="100" cy="100" r="86" fill="#C5A059" />
      <circle cx="100" cy="100" r="74" fill="#D8BC78" />
      <circle cx="100" cy="100" r="68" fill="#C5A059" />
      <circle cx="100" cy="100" r="68" stroke="#A8843A" strokeWidth="2.2" />
      <g fill="#1E4A73">
        <polygon points="100,50 148,86 52,86" />
        <rect x="56" y="86" width="88" height="10" />
        <rect x="64" y="96" width="10" height="42" />
        <rect x="84" y="96" width="10" height="42" />
        <rect x="106" y="96" width="10" height="42" />
        <rect x="126" y="96" width="10" height="42" />
        <rect x="52" y="138" width="96" height="14" />
      </g>
    </svg>
  );
}

function BanknoteStackMark() {
  return (
    <svg viewBox="0 0 220 180" fill="none" className="h-auto w-full overflow-visible">
      <g transform="rotate(-16 110 90)">
        <rect x="38" y="78" width="148" height="78" rx="8" fill="#214332" />
      </g>
      <g transform="rotate(-8 110 90)">
        <rect x="34" y="58" width="148" height="78" rx="8" fill="#2D5A43" />
      </g>
      <g transform="rotate(-2 110 90)">
        <rect x="32" y="38" width="148" height="78" rx="8" fill="#3A6E52" stroke="#CDE3D5" strokeWidth="1.5" />
        <rect x="44" y="50" width="124" height="54" rx="4" fill="#EDF5F0" fillOpacity="0.28" />
        <path
          d="M96 64h28M96 76h28M96 76h12c9 0 16 5 16 13s-7 14-16 14H96m0 0 18 14"
          stroke="#fff"
          strokeWidth="3.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <rect x="68" y="108" width="76" height="12" rx="2" fill="#E8D5A3" />
      </g>
    </svg>
  );
}

function AuditGraphMark() {
  return (
    <svg viewBox="0 0 220 170" fill="none" className="h-auto w-full overflow-visible">
      <path d="M30 140H198" className="stroke-[#1C1917]/16 dark:stroke-white/15" strokeWidth="1.4" />
      <path d="M30 26v114" className="stroke-[#1C1917]/16 dark:stroke-white/15" strokeWidth="1.4" />
      <path
        d="M38 132L62 118L84 104L104 112L122 128L168 48"
        className="stroke-[#1C1917] dark:stroke-[#E8E2D8]"
        strokeWidth="5.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M156 62L168 48L154 56"
        className="stroke-[#1C1917] dark:stroke-[#E8E2D8]"
        strokeWidth="5.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M176 34l10-16M186 30l8-16M194 28l6-14"
        stroke="#C5A059"
        strokeWidth="3.2"
        strokeLinecap="round"
      />
      <circle cx="122" cy="128" r="5.5" fill="#C45C38" />
    </svg>
  );
}

function RupeeFolderMark() {
  return (
    <svg viewBox="0 0 220 200" fill="none" className="h-auto w-full overflow-visible">
      <path
        d="M40 54h46l16 18h92a10 10 0 0 1 10 10v80a10 10 0 0 1-10 10H40a10 10 0 0 1-10-10V64A10 10 0 0 1 40 54Z"
        className="stroke-[#1C1917] dark:stroke-[#E8E2D8]"
        strokeWidth="7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <g
        className="stroke-[#1C1917] dark:stroke-[#E8E2D8]"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        transform="translate(71 78) scale(3.9)"
      >
        <path d="M6 3h12" />
        <path d="M6 8h12" />
        <path d="M9 13c6.667 0 6.667-10 0-10" />
        <path d="M6 13h3" />
        <path d="m6 13 8.5 8" />
      </g>
    </svg>
  );
}
