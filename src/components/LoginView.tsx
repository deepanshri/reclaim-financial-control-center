import React, { useEffect, useId, useState } from 'react';
import { motion, useReducedMotion } from 'motion/react';
import { useTheme } from '../context/ThemeContext';
import { overlayTransition, stageSpring } from '../motion/presets';
import { LoginFinanceVisuals } from './LoginFinanceVisuals';
import { login } from '../services/authService';
import { ApiError, fetchApi } from '../services/api';

interface LoginViewProps {
  onLoginSuccess: (merchantId?: string, merchantName?: string) => void;
}

interface FieldErrors {
  merchantId: string;
  password: string;
}

export const LoginView: React.FC<LoginViewProps> = ({ onLoginSuccess }) => {
  const { isDarkMode, toggleDarkMode } = useTheme();
  const reduceMotion = useReducedMotion();
  const merchantIdFieldId = useId();
  const passwordFieldId = useId();
  const merchantErrorId = useId();
  const passwordErrorId = useId();

  const [merchantId, setMerchantId] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<FieldErrors>({ merchantId: '', password: '' });
  const [formError, setFormError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [connectingSlowly, setConnectingSlowly] = useState(false);
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    // Silently pre-warm the backend (especially Render cold starts) as soon as login mounts
    fetchApi('/api/health').catch(() => {});
  }, []);

  const handleFillDemo = () => {
    setMerchantId('mid_demo_ZC771042');
    setPassword('ReclaimDemo!2026');
    setErrors({ merchantId: '', password: '' });
    setFormError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading || isExiting) return;

    const nextId = merchantId.trim();
    const nextPassword = password.trim();
    const nextErrors: FieldErrors = {
      merchantId: nextId ? '' : 'Enter your Merchant ID.',
      password: nextPassword ? '' : 'Enter your password.',
    };

    if (nextErrors.merchantId || nextErrors.password) {
      setErrors(nextErrors);
      return;
    }

    setErrors({ merchantId: '', password: '' });
    setFormError('');
    setIsLoading(true);
    setConnectingSlowly(false);

    const slowTimer = window.setTimeout(() => {
      setConnectingSlowly(true);
    }, 1200);

    try {
      const session = await login(nextId, nextPassword);
      window.clearTimeout(slowTimer);
      setIsExiting(true);
      window.setTimeout(() => {
        onLoginSuccess(session.merchant_id, session.merchant_name);
      }, 100);
    } catch (err: unknown) {
      window.clearTimeout(slowTimer);
      setIsLoading(false);
      setConnectingSlowly(false);
      if (err instanceof ApiError && err.status === 401) {
        setFormError('Those credentials were not accepted. Check the merchant ID and password.');
        return;
      }
      setFormError(err instanceof Error ? err.message : 'Unable to sign in. Try again.');
    }
  };

  return (
    <motion.div
      className="login-page relative min-h-dvh w-full overflow-x-hidden bg-[#F5F5F0] font-sans text-[#1C1917] selection:bg-[#1E4A73] selection:text-white dark:bg-[#141311] dark:text-[#F4F0E8]"
      initial={false}
      animate={
        isExiting
          ? { opacity: 0, scale: 0.96 }
          : { opacity: 1, scale: 1 }
      }
      transition={reduceMotion ? { duration: 0.2 } : overlayTransition}
    >
      <div className="login-bg-wash pointer-events-none absolute inset-0" aria-hidden="true" />

      <button
        type="button"
        onClick={toggleDarkMode}
        className="login-theme-toggle absolute right-5 top-5 z-20 flex h-10 w-10 cursor-pointer items-center justify-center rounded-xl border border-[#E2E2DC] bg-white text-[#57524C] transition-transform duration-200 hover:scale-105 hover:border-[#1E4A73] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#1E4A73] dark:border-[#2D2824] dark:bg-[#1C1917] dark:text-[#FAF7F2] sm:right-8 sm:top-6"
        title={isDarkMode ? 'Switch to light theme' : 'Switch to dark theme'}
        aria-label={isDarkMode ? 'Switch to light theme' : 'Switch to dark theme'}
      >
        <span className="material-symbols-outlined text-[20px]" aria-hidden="true">
          {isDarkMode ? 'light_mode' : 'dark_mode'}
        </span>
      </button>

      <LoginFinanceVisuals />

      <main className="login-main relative z-10 flex min-h-dvh items-center justify-center px-5 pointer-events-none sm:px-8">
        <motion.div
          className="login-stack w-full max-w-[520px] pointer-events-auto text-center"
          initial={reduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.97, y: 12 }}
          animate={reduceMotion ? { opacity: 1 } : { opacity: 1, scale: 1, y: 0 }}
          transition={reduceMotion ? { duration: 0.25 } : stageSpring}
        >
          <p className="login-brand font-heading text-[17px] font-medium tracking-wide text-[#1E4A73] dark:text-[#8BA4C2]">
            Reclaim
          </p>
          <h1 className="login-heading font-display font-medium leading-[1.2] text-[#1C1917] dark:text-[#FAF7F2]">
            Check your payments
            <span className="italic"> with confidence.</span>
          </h1>
          <p className="login-support mx-auto max-w-[42ch] font-sans font-normal text-[#44403C] dark:text-[#C5BFB8]">
            Reclaim checks your Razorpay payment records and helps you find money that may need attention.
          </p>

          <form onSubmit={handleSubmit} className="login-form text-left" noValidate>
            <div className="login-form-card rounded-xl bg-[#EAEAE4] dark:bg-[#201D1A]">
              <div>
                <label
                  htmlFor={merchantIdFieldId}
                  className="login-label mb-2 block font-ui text-[16px] font-medium text-[#44403C] dark:text-[#D6D3D1]"
                >
                  Merchant ID
                </label>
                <input
                  id={merchantIdFieldId}
                  name="merchantId"
                  type="text"
                  autoComplete="username"
                  value={merchantId}
                  onChange={(e) => {
                    setMerchantId(e.target.value);
                    if (errors.merchantId) {
                      setErrors((prev) => ({ ...prev, merchantId: '' }));
                    }
                  }}
                  placeholder="Enter Merchant Id"
                  aria-invalid={Boolean(errors.merchantId)}
                  aria-describedby={errors.merchantId ? merchantErrorId : undefined}
                  className={`login-field w-full rounded-lg border bg-white px-4 font-mono text-[18px] text-[#1C1917] placeholder:font-ui placeholder:text-[#8A847C] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#1E4A73] dark:bg-[#141311] dark:text-[#FAF7F2] ${
                    errors.merchantId
                      ? 'border-[#B8522E]'
                      : 'border-[#C8C4BB] dark:border-[#3A342E]'
                  }`}
                />
                {errors.merchantId ? (
                  <p id={merchantErrorId} role="alert" className="mt-2 text-[16px] font-medium text-[#B8522E]">
                    {errors.merchantId}
                  </p>
                ) : null}
              </div>

              <div>
                <label
                  htmlFor={passwordFieldId}
                  className="login-label mb-2 block font-ui text-[16px] font-medium text-[#44403C] dark:text-[#D6D3D1]"
                >
                  Password
                </label>
                <div className="relative">
                  <input
                    id={passwordFieldId}
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (errors.password) {
                        setErrors((prev) => ({ ...prev, password: '' }));
                      }
                    }}
                    placeholder="Enter your password"
                    aria-invalid={Boolean(errors.password)}
                    aria-describedby={errors.password ? passwordErrorId : undefined}
                    className={`login-field w-full rounded-lg border bg-white pl-4 pr-12 font-ui text-[18px] text-[#1C1917] placeholder:text-[#8A847C] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#1E4A73] dark:bg-[#141311] dark:text-[#FAF7F2] ${
                    errors.password
                      ? 'border-[#B8522E]'
                      : 'border-[#C8C4BB] dark:border-[#3A342E]'
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((open) => !open)}
                    className="absolute right-2 top-1/2 flex h-9 w-9 -translate-y-1/2 cursor-pointer items-center justify-center rounded-lg text-[#57524C] hover:text-[#1E4A73] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#1E4A73] dark:text-[#A8A29E]"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    <span className="material-symbols-outlined text-[20px]" aria-hidden="true">
                      {showPassword ? 'visibility_off' : 'visibility'}
                    </span>
                  </button>
                </div>
                {errors.password ? (
                  <p id={passwordErrorId} role="alert" className="mt-2 text-[16px] font-medium text-[#B8522E]">
                    {errors.password}
                  </p>
                ) : null}
              </div>
            </div>

            {formError ? (
              <p role="alert" className="login-form-error mt-3 text-[16px] font-medium text-[#B8522E]">
                {formError}
              </p>
            ) : null}

            <button
              type="submit"
              disabled={isLoading || isExiting}
              className="login-enter-btn w-full cursor-pointer rounded-xl bg-[#1E4A73] px-6 font-ui text-[18px] font-semibold tracking-normal text-white disabled:cursor-not-allowed disabled:opacity-70 dark:bg-[#2A5F8F] flex items-center justify-center gap-2.5 transition-all"
            >
              {isLoading ? (
                <>
                  <span className="inline-block h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  <span>{connectingSlowly ? 'Connecting to secure engine…' : 'Signing in…'}</span>
                </>
              ) : (
                'ENTER RECLAIM'
              )}
            </button>
          </form>

          <div className="login-demo leading-relaxed text-[#6B655E] dark:text-[#A8A29E] space-y-2">
            <p>
              Demo workspace with a synthetic dataset. Sign in with merchant ID{' '}
              <span className="font-mono font-semibold">mid_demo_ZC771042</span> and password{' '}
              <span className="font-mono font-semibold">ReclaimDemo!2026</span>.
            </p>
            <button
              type="button"
              onClick={handleFillDemo}
              className="inline-flex items-center gap-1.5 text-[15px] font-semibold text-[#1E4A73] dark:text-[#8BA4C2] hover:underline cursor-pointer bg-white dark:bg-[#1C1917] px-3.5 py-1.5 rounded-lg border border-[#E2E2DC] dark:border-[#2D2824] shadow-xs hover:border-[#1E4A73] transition-colors"
            >
              <span className="material-symbols-outlined text-[18px]">key</span>
              <span>1-Click Autofill Demo Credentials</span>
            </button>
          </div>
        </motion.div>
      </main>
    </motion.div>
  );
};
