import { Transition } from 'motion/react';

/** Overlay fade — ease-out expo, no bounce. */
export const overlayTransition: Transition = {
  duration: 0.32,
  ease: [0.22, 1, 0.36, 1],
};

/** Dialog / card spring — mass + damping, slight settle, no cartoon bounce. */
export const panelSpring: Transition = {
  type: 'spring',
  stiffness: 380,
  damping: 34,
  mass: 0.82,
};

export const panelEnter = { opacity: 0, scale: 0.95, y: 18 };
export const panelCenter = { opacity: 1, scale: 1, y: 0 };
export const panelExit = { opacity: 0, scale: 0.97, y: 10 };

/** Login mark entrance. */
export const visualSpring = (delay: number): Transition => ({
  type: 'spring',
  stiffness: 280,
  damping: 28,
  mass: 0.9,
  delay,
});

export const stageSpring: Transition = {
  type: 'spring',
  stiffness: 320,
  damping: 30,
  mass: 0.88,
  delay: 0.08,
};

export const popoverSpring: Transition = {
  type: 'spring',
  stiffness: 460,
  damping: 36,
  mass: 0.7,
};
