import React, { useEffect, useState } from 'react';
import { useTheme } from '../context/ThemeContext';
import { UserProfile } from '../types';
import { getWorkspaceSettings, saveWorkspaceSettings, WorkspaceSettings } from '../services/workspaceService';

interface SettingsViewProps {
  onTriggerSync: () => void;
  onDisconnect: () => void;
  profile?: UserProfile | null;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  onTriggerSync,
  onDisconnect,
  profile,
}) => {
  const [isSyncing, setIsSyncing] = useState(false);
  const [razorpayConnected, setRazorpayConnected] = useState(true);
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const { isDarkMode, toggleDarkMode } = useTheme();

  const merchantId = profile?.merchant_id || 'mid_demo_ZC771042';
  const feeRate = profile?.contract?.fee_rate ? `${(profile.contract.fee_rate * 100).toFixed(2)}% Fixed Fee` : 'Contracted MDR';

  const [feeVariancePercent, setFeeVariancePercent] = useState('0.10');
  const [slaDelayThresholdHours, setSlaDelayThresholdHours] = useState('24');
  const [autoDisputeThreshold, setAutoDisputeThreshold] = useState('1000');
  const [notificationEmail, setNotificationEmail] = useState(profile?.finance_email || 'finance@zenzocommerce.in');
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getWorkspaceSettings()
      .then((settings: WorkspaceSettings) => {
        if (cancelled) return;
        setFeeVariancePercent(settings.fee_variance_percent);
        setSlaDelayThresholdHours(settings.sla_delay_threshold_hours);
        setAutoDisputeThreshold(settings.auto_dispute_threshold);
        setNotificationEmail(settings.notification_email || profile?.finance_email || 'finance@zenzocommerce.in');
        setRazorpayConnected(settings.razorpay_connected);
      })
      .catch(() => {
        /* keep local defaults if settings have not been saved yet */
      });
    return () => {
      cancelled = true;
    };
  }, [profile?.finance_email]);

  const handleManualSync = () => {
    setIsSyncing(true);
    setTimeout(() => {
      setIsSyncing(false);
      onTriggerSync();
    }, 1200);
  };

  const handleToggleConnection = async () => {
    const next = !razorpayConnected;
    setRazorpayConnected(next);
    try {
      await saveWorkspaceSettings({
        fee_variance_percent: feeVariancePercent,
        sla_delay_threshold_hours: slaDelayThresholdHours,
        auto_dispute_threshold: autoDisputeThreshold,
        notification_email: notificationEmail,
        razorpay_connected: next,
      });
    } catch {
      setRazorpayConnected(!next);
      return;
    }
    if (!next) {
      onDisconnect();
    } else {
      onTriggerSync();
    }
  };

  const handleSavePreferences = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSaveError('');
    try {
      await saveWorkspaceSettings({
        fee_variance_percent: feeVariancePercent,
        sla_delay_threshold_hours: slaDelayThresholdHours,
        auto_dispute_threshold: autoDisputeThreshold,
        notification_email: notificationEmail,
        razorpay_connected: razorpayConnected,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : 'Could not save preferences.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      id="settings-view-container"
      className="p-6 sm:p-8 lg:p-12 max-w-[1400px] mx-auto w-full space-y-10 text-[#1C1917] dark:text-[#F4F0E8] font-sans transition-all duration-300"
    >
      {/* Header */}
      <div className="border-b border-[#E2E2DC] dark:border-[#26221E] pb-6">
        <h1 className="font-display text-[30px] font-medium leading-[1.2] text-[#1C1917] dark:text-[#FAF7F2] sm:text-[36px]">
          Settings &amp; Audit Preferences
        </h1>
        <p className="text-[17px] text-[#57524C] dark:text-[#A8A29E] mt-1 font-sans">
          Manage your Razorpay payment connection, fee alert rules, and audit preferences.
        </p>
      </div>

      <div className="space-y-8">
        {/* SECTION 1: Razorpay Connection */}
        <div className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-6 sm:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E2DC] dark:border-[#26221E] pb-5">
            <div className="flex items-center gap-3.5">
              <div className="w-12 h-12 rounded-2xl bg-[#0C2340] text-white flex items-center justify-center font-bold text-[17px] shrink-0">
                RZP
              </div>
              <div>
                <h2 className="text-[22px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2]">
                  Razorpay Connection
                </h2>
                <p className="text-[16px] text-[#57524C] dark:text-[#A8A29E]">
                  Automatic reconciliation of payments, fees, refunds, and bank settlements
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span
                className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-[15px] font-bold ${
                  razorpayConnected
                    ? 'bg-[#EDF5F0] text-[#2D5A43] dark:bg-[#15241C] dark:text-[#4E9A70]'
                    : 'bg-[#FDF3ED] text-[#B8522E] dark:bg-[#2A1810] dark:text-[#E07A53]'
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full ${
                    razorpayConnected ? 'bg-[#2D5A43] dark:bg-[#4E9A70]' : 'bg-[#B8522E] dark:bg-[#E07A53]'
                  }`}
                ></span>
                <span>{razorpayConnected ? 'Connected & Active' : 'Disconnected'}</span>
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            <div className="p-4 bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-2xl space-y-1">
              <span className="text-[14px] font-bold uppercase tracking-wider text-[#787168] dark:text-[#A8A29E] block">
                Merchant Account
              </span>
              <span className="text-[17px] font-bold text-[#1C1917] dark:text-[#FAF7F2] font-mono block">
                {merchantId}
              </span>
              <span className="text-[15px] text-[#57524C] dark:text-[#A8A29E]">
                {profile?.merchant_name || 'Zenzo Commerce'}
              </span>
            </div>

            <div className="p-4 bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-2xl space-y-1">
              <span className="text-[14px] font-bold uppercase tracking-wider text-[#787168] dark:text-[#A8A29E] block">
                Contracted Fee Schedule
              </span>
              <span className="text-[17px] font-bold text-[#2D5A43] dark:text-[#4E9A70] block">
                {feeRate}
              </span>
              <span className="text-[15px] text-[#57524C] dark:text-[#A8A29E]">
                MDR rate for standard payments
              </span>
            </div>

            <div className="p-4 bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-2xl space-y-1">
              <span className="text-[14px] font-bold uppercase tracking-wider text-[#787168] dark:text-[#A8A29E] block">
                Settlement Schedule
              </span>
              <span className="text-[17px] font-bold text-[#1C1917] dark:text-[#FAF7F2] block">
                T+1 Business Day
              </span>
              <span className="text-[15px] text-[#57524C] dark:text-[#A8A29E]">
                To ICICI Bank Primary A/C
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-4 pt-3">
            <button
              type="button"
              onClick={handleManualSync}
              disabled={isSyncing || !razorpayConnected}
              className="px-5 py-2.5 bg-[#FFFFFF] dark:bg-[#1E1B18] border border-[#D6D3D1] dark:border-[#2D2824] rounded-2xl text-[16px] font-bold text-[#1C1917] dark:text-[#FAF7F2] flex items-center gap-2 cursor-pointer shadow-xs hover:bg-[#F5F5F0] dark:hover:bg-[#282420] transition-colors disabled:opacity-50"
            >
              <span className={`material-symbols-outlined text-[20px] ${isSyncing ? 'animate-spin' : ''}`}>
                sync
              </span>
              <span>{isSyncing ? 'Checking Records...' : 'Check Records Now'}</span>
            </button>

            <button
              type="button"
              onClick={handleToggleConnection}
              className={`px-5 py-2.5 rounded-2xl text-[16px] font-bold border transition-colors cursor-pointer ${
                razorpayConnected
                  ? 'border-[#F0CFBF] text-[#B8522E] hover:bg-[#FDF3ED] dark:border-[#4A261A] dark:hover:bg-[#2A1810]'
                  : 'border-[#2D5A43] bg-[#2D5A43] text-white hover:bg-[#234734]'
              }`}
            >
              {razorpayConnected ? 'Disconnect Gateway' : 'Connect Razorpay'}
            </button>
          </div>
        </div>

        {/* SECTION 2: Audit Preferences & Alert Rules */}
        <div className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-6 sm:p-8 space-y-6">
          <div className="border-b border-[#E2E2DC] dark:border-[#26221E] pb-4">
            <h2 className="text-[22px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2]">
              Audit Preferences &amp; Alert Rules
            </h2>
            <p className="text-[16px] text-[#57524C] dark:text-[#A8A29E] mt-0.5">
              Configure how Reclaim monitors fee rate changes and notifies your team
            </p>
          </div>

          <form onSubmit={handleSavePreferences} className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label htmlFor="settings-alert-email" className="block text-[15px] font-bold uppercase tracking-wider text-[#787168] dark:text-[#A8A29E] mb-2">
                  Alert Email Address
                </label>
                <input
                  id="settings-alert-email"
                  type="email"
                  value={notificationEmail}
                  onChange={(e) => setNotificationEmail(e.target.value)}
                  className="w-full px-4 py-2.5 bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-2xl text-[16px] text-[#1C1917] dark:text-[#FAF7F2] font-medium focus:outline-none focus:border-[#B8522E]"
                />
                <span className="text-[15px] text-[#787168] dark:text-[#A8A29E] mt-1 block">
                  Daily audit summaries and anomaly alerts will be sent here
                </span>
              </div>

              <div>
                <label className="block text-[15px] font-bold uppercase tracking-wider text-[#787168] dark:text-[#A8A29E] mb-2">
                  Minimum Recovery Threshold
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-2.5 text-[16px] font-bold text-[#787168] dark:text-[#A8A29E]">₹</span>
                  <input
                    type="number"
                    value={autoDisputeThreshold}
                    onChange={(e) => setAutoDisputeThreshold(e.target.value)}
                    className="w-full pl-8 pr-4 py-2.5 bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-2xl text-[16px] text-[#1C1917] dark:text-[#FAF7F2] font-medium focus:outline-none focus:border-[#B8522E]"
                  />
                </div>
                <span className="text-[15px] text-[#787168] dark:text-[#A8A29E] mt-1 block">
                  Flag issues exceeding this cumulative financial impact
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <button
                type="submit"
                disabled={isSaving}
                className="px-6 py-2.5 bg-[#1C1917] dark:bg-[#B8522E] text-[#FAF7F2] rounded-2xl text-[16px] font-bold cursor-pointer hover:bg-[#2D2824] dark:hover:bg-[#A34423] transition-colors disabled:opacity-60"
              >
                {isSaving ? 'Saving…' : 'Save Preferences'}
              </button>
              {saveSuccess && (
                <span className="text-[15px] font-bold text-[#2D5A43] dark:text-[#4E9A70] flex items-center gap-1.5 animate-fade-in">
                  <span className="material-symbols-outlined text-[19px]">check_circle</span>
                  <span>Preferences saved successfully</span>
                </span>
              )}
              {saveError && (
                <span role="alert" className="text-[15px] font-medium text-[#B8522E]">
                  {saveError}
                </span>
              )}
            </div>
          </form>
        </div>

        {/* SECTION 3: Advanced Settings (Collapsible / Default Collapsed) */}
        <div className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl overflow-hidden">
          <button
            type="button"
            onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}
            className="w-full p-6 sm:p-7 flex items-center justify-between text-left cursor-pointer hover:bg-[#FAF9F5] dark:hover:bg-[#1E1B18] transition-colors"
          >
            <div>
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[22px] text-[#787168] dark:text-[#A8A29E]">settings_suggest</span>
                <h3 className="text-[20px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2]">
                  Advanced Audit Parameters
                </h3>
              </div>
              <p className="text-[15px] text-[#57524C] dark:text-[#A8A29E] mt-0.5">
                Technical reconciliation windows and MDR fee tolerance thresholds
              </p>
            </div>

            <span className="material-symbols-outlined text-[24px] text-[#787168] dark:text-[#A8A29E] transition-transform duration-200">
              {isAdvancedOpen ? 'expand_less' : 'expand_more'}
            </span>
          </button>

          {isAdvancedOpen && (
            <div className="p-6 sm:p-7 pt-0 border-t border-[#E2E2DC] dark:border-[#26221E] space-y-5 animate-fade-in">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 pt-4">
                <div>
                  <label className="block text-[15px] font-bold uppercase tracking-wider text-[#787168] dark:text-[#A8A29E] mb-2">
                    Fee Rate Tolerance (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={feeVariancePercent}
                    onChange={(e) => setFeeVariancePercent(e.target.value)}
                    className="w-full px-4 py-2.5 bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-2xl text-[16px] text-[#1C1917] dark:text-[#FAF7F2] font-medium"
                  />
                  <span className="text-[14px] text-[#787168] dark:text-[#A8A29E] mt-1 block">
                    Allowable fee variance before flagging an overcharge (default: 0.10%)
                  </span>
                </div>

                <div>
                  <label className="block text-[15px] font-bold uppercase tracking-wider text-[#787168] dark:text-[#A8A29E] mb-2">
                    Settlement SLA Delay Window (Hours)
                  </label>
                  <input
                    type="number"
                    value={slaDelayThresholdHours}
                    onChange={(e) => setSlaDelayThresholdHours(e.target.value)}
                    className="w-full px-4 py-2.5 bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-2xl text-[16px] text-[#1C1917] dark:text-[#FAF7F2] font-medium"
                  />
                  <span className="text-[14px] text-[#787168] dark:text-[#A8A29E] mt-1 block">
                    Grace period for bank settlement credit arrival (default: 24h)
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* SECTION 4: Theme Preferences */}
        <div className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-6 sm:p-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-[20px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2]">
              Display Theme
            </h3>
            <p className="text-[16px] text-[#57524C] dark:text-[#A8A29E] mt-0.5">
              Switch between Light Mode and Dark Mode for the control center
            </p>
          </div>

          <button
            type="button"
            onClick={toggleDarkMode}
            className="px-5 py-2.5 bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-2xl text-[16px] font-bold text-[#1C1917] dark:text-[#FAF7F2] flex items-center gap-2.5 cursor-pointer hover:border-[#B8522E] transition-colors"
          >
            <span className="material-symbols-outlined text-[20px]">
              {isDarkMode ? 'light_mode' : 'dark_mode'}
            </span>
            <span>{isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
