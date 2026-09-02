import React from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'motion/react';
import { panelSpring } from '../motion/presets';

export interface ToastMessage {
  id: string;
  type: 'success' | 'warning' | 'info' | 'error';
  title: string;
  message: string;
}

interface ToastProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

export const Toast: React.FC<ToastProps> = ({ toasts, onDismiss }) => {
  const layer = (
    <div
      className="pointer-events-none fixed bottom-6 right-6 z-[90] flex w-full max-w-sm flex-col gap-2.5"
      aria-live="polite"
      aria-relevant="additions"
      role="status"
    >
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, y: 16, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.97 }}
            transition={panelSpring}
            className="pointer-events-auto bg-[#1C1917] dark:bg-[#1A1815] text-[#FAF7F2] p-4 rounded-xl shadow-2xl border border-[#36302A] dark:border-[#2D2824] flex items-start justify-between gap-3"
          >
            <div className="flex items-start gap-3">
              <span
                className={`material-symbols-outlined text-[21px] mt-0.5 ${
                  toast.type === 'success'
                    ? 'text-[#4E9A70]'
                    : toast.type === 'warning'
                    ? 'text-[#E5A33C]'
                    : toast.type === 'error'
                    ? 'text-[#E07A53]'
                    : 'text-[#878076]'
                }`}
              >
                {toast.type === 'success'
                  ? 'check_circle'
                  : toast.type === 'warning'
                  ? 'warning'
                  : toast.type === 'error'
                  ? 'error'
                  : 'info'}
              </span>
              <div>
                <h4 className="text-[15px] font-medium text-[#FAF7F2] leading-tight font-sans">{toast.title}</h4>
                <p className="text-[15px] text-[#B8B0A2] mt-0.5 leading-snug font-sans">{toast.message}</p>
              </div>
            </div>
            <button
              onClick={() => onDismiss(toast.id)}
              className="text-[#878076] hover:text-[#FAF7F2] p-1 cursor-pointer transition-colors active:scale-90"
              aria-label="Dismiss notification"
            >
              <span className="material-symbols-outlined text-[18px]">close</span>
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );

  if (typeof document === 'undefined') return layer;
  return createPortal(layer, document.body);
};
