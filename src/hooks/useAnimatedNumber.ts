import { useState, useEffect, useRef } from 'react';

/**
 * Motion designer-grade smooth number animator.
 * Uses easeOutExpo: fast initial climb with long, silky deceleration to rest.
 */
export function useAnimatedNumber(
  targetValue: number,
  durationMs: number = 900,
  startImmediately: boolean = true
): number {
  const [currentValue, setCurrentValue] = useState<number>(() => {
    if (typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return targetValue;
    }
    return 0;
  });

  const currentValRef = useRef(currentValue);
  currentValRef.current = currentValue;

  useEffect(() => {
    if (!startImmediately) return;

    if (typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setCurrentValue(targetValue);
      return;
    }

    let startTime: number | null = null;
    let animationFrameId: number;

    const startVal = currentValRef.current;
    const diff = targetValue - startVal;
    if (diff === 0) return;

    // easeOutExpo for fluid decelerating counter
    const easeOutExpo = (x: number): number => {
      return x === 1 ? 1 : 1 - Math.pow(2, -10 * x);
    };

    const isFloat = !Number.isInteger(targetValue);

    const step = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / durationMs, 1);
      const easedProgress = easeOutExpo(progress);

      const val = startVal + diff * easedProgress;
      setCurrentValue(isFloat ? Number(val.toFixed(2)) : Math.round(val));

      if (progress < 1) {
        animationFrameId = requestAnimationFrame(step);
      } else {
        setCurrentValue(targetValue);
      }
    };

    animationFrameId = requestAnimationFrame(step);

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [targetValue, durationMs, startImmediately]);

  return currentValue;
}

