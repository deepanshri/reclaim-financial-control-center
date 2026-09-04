import { useState, useEffect, useRef } from 'react';

/**
 * Motion designer-grade smooth number animator.
 * Uses easeOutExpo: fast initial climb with long, silky deceleration to rest.
 */
function shouldSkipAnimation(): boolean {
  if (typeof window === 'undefined') return true;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return true;
  // requestAnimationFrame is paused in background tabs, which would otherwise
  // leave the counter stuck at its starting value.
  return typeof document !== 'undefined' && document.hidden;
}

export function useAnimatedNumber(
  targetValue: number,
  durationMs: number = 900,
  startImmediately: boolean = true
): number {
  const [currentValue, setCurrentValue] = useState<number>(() =>
    shouldSkipAnimation() ? targetValue : 0
  );

  const currentValRef = useRef(currentValue);
  currentValRef.current = currentValue;

  useEffect(() => {
    if (!startImmediately) return;

    if (shouldSkipAnimation()) {
      setCurrentValue(targetValue);
      return;
    }

    let startTime: number | null = null;
    let animationFrameId: number;

    const startVal = currentValRef.current;
    const diff = targetValue - startVal;
    if (diff === 0) return;

    // If the tab is hidden mid-animation, jump straight to the final value.
    const onVisibilityChange = () => {
      if (document.hidden) {
        cancelAnimationFrame(animationFrameId);
        setCurrentValue(targetValue);
      }
    };
    document.addEventListener('visibilitychange', onVisibilityChange);

    // Safety net: never leave a stale intermediate value on screen.
    const failsafe = window.setTimeout(() => {
      cancelAnimationFrame(animationFrameId);
      setCurrentValue(targetValue);
    }, durationMs + 400);

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
      window.clearTimeout(failsafe);
      document.removeEventListener('visibilitychange', onVisibilityChange);
    };
  }, [targetValue, durationMs, startImmediately]);

  return currentValue;
}

