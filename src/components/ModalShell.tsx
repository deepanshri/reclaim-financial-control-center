import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { AnimatePresence, motion, useReducedMotion } from 'motion/react';
import {
  overlayTransition,
  panelCenter,
  panelEnter,
  panelExit,
  panelSpring,
} from '../motion/presets';

interface ModalShellProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  panelClassName: string;
  panelRef?: React.Ref<HTMLDivElement>;
  labelledBy?: string;
  backdropId?: string;
  closeOnBackdrop?: boolean;
}

export const ModalShell: React.FC<ModalShellProps> = ({
  isOpen,
  onClose,
  children,
  panelClassName,
  panelRef,
  labelledBy,
  backdropId,
  closeOnBackdrop = true,
}) => {
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    if (!isOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isOpen]);

  if (typeof document === 'undefined') return null;

  const overlayT = reduceMotion ? { duration: 0.2 } : overlayTransition;
  const panelT = reduceMotion
    ? { duration: 0.2, ease: [0.22, 1, 0.36, 1] as const }
    : panelSpring;
  const enter = reduceMotion ? { opacity: 0 } : panelEnter;
  const center = reduceMotion ? { opacity: 1 } : panelCenter;
  const leave = reduceMotion ? { opacity: 0 } : panelExit;

  return createPortal(
    <AnimatePresence>
      {isOpen ? (
        <motion.div
          key="modal-backdrop"
          id={backdropId}
          role="presentation"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={overlayT}
          onClick={(e) => {
            if (closeOnBackdrop && e.target === e.currentTarget) onClose();
          }}
          className="fixed inset-0 z-[80] flex items-center justify-center bg-[#1C1917]/50 p-4 backdrop-blur-[2px] sm:p-6"
        >
          <motion.div
            key="modal-panel"
            ref={panelRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby={labelledBy}
            tabIndex={-1}
            initial={enter}
            animate={center}
            exit={leave}
            transition={panelT}
            className={`max-h-[min(90vh,880px)] overflow-y-auto ${panelClassName}`}
          >
            {children}
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>,
    document.body
  );
};
