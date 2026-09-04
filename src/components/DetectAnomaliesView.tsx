import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { EvidenceItem, Finding, FinancialStatus, PreviousRequest } from '../types';
import { merchantSeverityLabel, merchantSeverityMessage, merchantSeverityBadgeClass } from '../severityPresentation';
import { useAnimatedNumber } from '../hooks/useAnimatedNumber';
import { formatINR, remainingRecoveryInr } from '../utils/money';
import { createRecoveryRequest } from '../services/recoveryRequestService';
import { getAnomalyEvidence } from '../services/anomalyService';
import { MetricMoney } from './MetricMoney';

interface DetectAnomaliesViewProps {
  anomalies: Finding[];
  selectedAnomalyId: string;
  onSelectAnomaly: (id: string) => void;
  onOpenSendRequest: (anomaly?: Finding) => void;
  onRecoverySent?: (request: PreviousRequest) => void;
  onSwitchToStatement: () => void;
  healthScore: number;
  totalLostAmount?: number;
  isLoading?: boolean;
  selectedPeriod?: string;
  financialStatus?: FinancialStatus | null;
}

function getSimpleIssueTitle(title: string, type: string): string {
  const t = (title || '').toLowerCase();
  const typ = (type || '').toLowerCase();
  if (t.includes('fee') || typ.includes('fee') || typ.includes('rate')) return 'Fee charged too much';
  if (typ.includes('uncredited') || t.includes('uncredited')) return 'Refund not received by customer';
  if (t.includes('duplicate') && t.includes('refund')) return 'Duplicate refund deducted';
  if (typ.includes('missing_settlement') || (t.includes('missing') && t.includes('settlement'))) {
    return 'Payment not settled to bank';
  }
  if (typ.includes('bank_credit') || t.includes('bank')) return 'Payment not received in bank';
  if (t.includes('discrepancy') || t.includes('difference')) return 'Settlement amount different';
  if (t.includes('delay') || typ.includes('delay')) return 'Settlement deposit delay';
  return title || 'Payment discrepancy';
}

export const DetectAnomaliesView: React.FC<DetectAnomaliesViewProps> = ({
  anomalies,
  onRecoverySent,
  onSwitchToStatement,
  healthScore,
  isLoading = false,
  selectedPeriod = '2026_H2',
  financialStatus,
}) => {
  // Track which issues have their proof expanded
  const [expandedProofIds, setExpandedProofIds] = useState<Record<string, boolean>>({});
  const [evidenceById, setEvidenceById] = useState<Record<string, EvidenceItem[]>>({});
  const [loadingProofIds, setLoadingProofIds] = useState<Record<string, boolean>>({});
  const [isComposerOpen, setIsComposerOpen] = useState(false);
  const [mailSubject, setMailSubject] = useState('');
  const [mailBody, setMailBody] = useState('');
  const [isSendingRequest, setIsSendingRequest] = useState(false);
  const [sendRequestError, setSendRequestError] = useState('');

  const toggleProof = (id: string, existing?: EvidenceItem[]) => {
    setExpandedProofIds((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
    const opening = !expandedProofIds[id];
    if (!opening || evidenceById[id]) return;
    if (existing && existing.length > 0) {
      setEvidenceById((prev) => ({ ...prev, [id]: existing }));
      return;
    }
    setLoadingProofIds((prev) => ({ ...prev, [id]: true }));
    getAnomalyEvidence(id, selectedPeriod)
      .then((res) => {
        setEvidenceById((prev) => ({ ...prev, [id]: res.evidence || [] }));
      })
      .catch(() => {
        setEvidenceById((prev) => ({ ...prev, [id]: [] }));
      })
      .finally(() => {
        setLoadingProofIds((prev) => ({ ...prev, [id]: false }));
      });
  };

  // Helper currency formatter
  const formatCurrency = (val?: number) => formatINR(val);

  // Filter ONLY confirmed findings
  const confirmedAnomalies = anomalies.filter(
    (a) => a.status?.toLowerCase() === 'confirmed'
  );

  const periodReady = financialStatus?.period === selectedPeriod;
  const confirmedLoss =
    periodReady
      ? (financialStatus?.money_affected_inr ?? financialStatus?.confirmed_loss_inr ?? 0)
      : 0;

  const severityLevel = periodReady ? financialStatus?.severity_level || 'healthy' : 'healthy';
  const severityLabel = periodReady
    ? financialStatus?.severity_label || merchantSeverityLabel(severityLevel)
    : merchantSeverityLabel('healthy');
  const severityMessage = periodReady
    ? financialStatus?.severity_message || merchantSeverityMessage(severityLevel)
    : merchantSeverityMessage('healthy');

  const isMonitor = merchantSeverityLabel(severityLevel) === 'MONITOR';

  // Animated counters — Potential Recovery is an independent backend field.
  const animatedHealthScore = useAnimatedNumber(healthScore, 650);
  const animatedTotalImpact = useAnimatedNumber(confirmedLoss, 650);
  const potentialRecoveryAmount = periodReady
    ? (financialStatus?.potential_recovery_inr ?? financialStatus?.potential_loss_inr ?? 0)
    : 0;
  const remainingRecovery = remainingRecoveryInr(
    potentialRecoveryAmount,
    periodReady ? financialStatus?.recovery_requested_inr : 0
  );
  const animatedPotential = useAnimatedNumber(potentialRecoveryAmount, 650);

  if (isLoading || !periodReady) {
    return (
      <div
        id="detect-anomalies-workspace"
        className="p-6 sm:p-8 lg:p-12 max-w-[1600px] mx-auto w-full space-y-8 font-sans"
      >
        <p className="text-[16px] text-[#787168] dark:text-[#A8A29E]">
          Preparing this period's audit…
        </p>
        <div className="h-12 bg-[#E2E2DC]/50 dark:bg-[#26221E]/50 rounded-2xl w-80 animate-pulse"></div>
        <div className="h-44 bg-[#FFFFFF] dark:bg-[#1A1815] rounded-3xl border border-[#E2E2DC] dark:border-[#2D2824] p-8 animate-pulse shadow-sm"></div>
        <div className="space-y-6">
          <div className="h-56 bg-[#FFFFFF] dark:bg-[#1A1815] rounded-3xl border border-[#E2E2DC] dark:border-[#2D2824] animate-pulse shadow-sm"></div>
          <div className="h-56 bg-[#FFFFFF] dark:bg-[#1A1815] rounded-3xl border border-[#E2E2DC] dark:border-[#2D2824] animate-pulse shadow-sm"></div>
        </div>
      </div>
    );
  }

  // Format Period Display Label
  const periodLabel = selectedPeriod.replace('_', ' ');

  const issueLabels = Array.from(
    new Set(confirmedAnomalies.map((item) => getSimpleIssueTitle(item.title, item.type)))
  );
  const draftSubject = `Recovery claim · Zenzo Commerce · ${periodLabel}`;
  const draftSummaryLine1 = `Razorpay settlement audit for ${periodLabel} found ${confirmedAnomalies.length} confirmed ${
    confirmedAnomalies.length === 1 ? 'issue' : 'issues'
  }${issueLabels.length ? `: ${issueLabels.slice(0, 3).join('; ')}` : ''}.`;
  const draftSummaryLine2 = `Money affected is ${formatCurrency(confirmedLoss)}. Eligible recovery is ${formatCurrency(potentialRecoveryAmount)}.`;
  const draftBody = `Dear Razorpay Support,

${draftSummaryLine1}
${draftSummaryLine2}

Please review the attached payment, settlement, and bank-credit evidence and credit ${formatCurrency(
    remainingRecovery > 0 ? remainingRecovery : potentialRecoveryAmount
  )} to our registered settlement account.

Regards,
Zenzo Commerce Finance`;

  const handleRevealComposer = () => {
    setMailSubject(draftSubject);
    setMailBody(draftBody);
    setSendRequestError('');
    setIsComposerOpen(true);
  };

  const handleSendComposedRequest = async () => {
    if (!mailSubject.trim() || !mailBody.trim() || isSendingRequest || remainingRecovery <= 0) return;
    setIsSendingRequest(true);
    setSendRequestError('');
    try {
      const created = await createRecoveryRequest({
        period: selectedPeriod,
        summary: mailBody.trim(),
        recipient: 'Razorpay Support (disputes@razorpay.com)',
        subject: mailSubject.trim(),
        claim_scope: 'period',
      });
      onRecoverySent?.({
        ...created,
        status: created.status || 'Submitted',
        amount: created.amount_requested,
        reference: created.request_id,
        to: created.recipient,
      });
      setIsComposerOpen(false);
    } catch (err: unknown) {
      setSendRequestError(err instanceof Error ? err.message : 'Could not send the recovery request.');
    } finally {
      setIsSendingRequest(false);
    }
  };

  const getIssueDetails = (anom: Finding) => {
    const t = (anom.title || '').toLowerCase();
    const typ = (anom.type || '').toLowerCase();

    if (t.includes('fee') || typ.includes('fee') || typ.includes('rate')) {
      return {
        badge: 'Fee Overcharge',
        explanation: anom.simple_explanation || anom.description || 'Fee charged on these payments differed from the contracted MDR.',
        expected: anom.expected_value || 'Contracted MDR',
        actual: anom.actual_value || 'Applied MDR',
        difference: anom.difference || formatCurrency(anom.financial_impact),
        icon: 'percent',
      };
    }
    if (typ.includes('uncredited') || t.includes('uncredited')) {
      return {
        badge: 'Refund Not Credited',
        explanation: anom.simple_explanation || anom.description || 'A customer refund was deducted from your account, but the customer did not receive the credit.',
        expected: anom.expected_value || formatCurrency(anom.financial_impact),
        actual: anom.actual_value || '₹0.00 credited to customer',
        difference: formatCurrency(anom.financial_impact),
        icon: 'history_toggle_off',
      };
    }
    if (t.includes('duplicate') && t.includes('refund')) {
      return {
        badge: 'Duplicate Refund',
        explanation: anom.simple_explanation || anom.description || 'The same customer refund was deducted twice from your settlement deposits.',
        expected: anom.expected_value || 'Single legitimate refund',
        actual: anom.actual_value || 'Refund processed twice',
        difference: formatCurrency(anom.financial_impact),
        icon: 'content_copy',
      };
    }
    if (typ.includes('missing_settlement') || (t.includes('missing') && t.includes('settlement'))) {
      return {
        badge: 'Unsettled Payment',
        explanation: anom.simple_explanation || anom.description || 'Customer payment was captured by Razorpay but was never included in any bank settlement.',
        expected: anom.expected_value || formatCurrency(anom.financial_impact),
        actual: anom.actual_value || '₹0.00 Payout',
        difference: formatCurrency(anom.financial_impact),
        icon: 'account_balance_wallet',
      };
    }
    if (typ.includes('bank_credit') || t.includes('ifsc') || t.includes('bank')) {
      return {
        badge: 'Missing Bank Credit',
        explanation: anom.simple_explanation || anom.description || 'Settlement was marked processed by the gateway, but the money was not received in your bank account.',
        expected: anom.expected_value || formatCurrency(anom.financial_impact),
        actual: anom.actual_value || '₹0.00 in Bank',
        difference: formatCurrency(anom.financial_impact),
        icon: 'search_off',
      };
    }
    if (t.includes('discrepancy') || t.includes('difference') || t.includes('short')) {
      return {
        badge: 'Settlement Discrepancy',
        explanation: 'Net bank deposit received was short compared to gross payment volume minus agreed fees.',
        expected: anom.expected_value || 'Net Batch Total',
        actual: anom.actual_value || 'Short Deposit',
        difference: formatCurrency(anom.financial_impact),
        icon: 'difference',
      };
    }
    return {
      badge: 'Reconciliation Difference',
      explanation: anom.simple_explanation || anom.description || 'Payment settlement amount differs from agreed records.',
      expected: anom.expected_value || 'Agreed Rate',
      actual: anom.actual_value || 'Applied Rate',
      difference: formatCurrency(anom.financial_impact),
      icon: 'receipt_long',
    };
  };

  return (
    <div
      id="detect-anomalies-workspace"
      className="p-6 sm:p-8 lg:p-12 max-w-[1600px] mx-auto w-full space-y-8 text-[#1C1917] dark:text-[#F4F0E8] font-sans transition-all duration-300"
    >
      {/* 1. Header & Period Status Banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-[#E2E2DC] dark:border-[#26221E] pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="font-display text-[30px] font-medium leading-[1.2] text-[#1C1917] dark:text-[#FAF7F2] sm:text-[36px]">
              Payment Issues · {periodLabel}
            </h1>
            <span
              className={`text-[15px] font-extrabold px-3 py-0.5 rounded-full uppercase tracking-wider ${merchantSeverityBadgeClass(severityLevel)}`}
            >
              {severityLabel}
            </span>
          </div>
          <p className="text-[17px] text-[#57524C] dark:text-[#A8A29E] mt-1 font-sans">
            {severityMessage} {confirmedAnomalies.length > 0 ? `${confirmedAnomalies.length} payment issues identified from your Razorpay records.` : 'All payments and settlements are fully reconciled.'}
          </p>
        </div>

        <button
          onClick={onSwitchToStatement}
          className="btn-secondary-action px-5 py-2.5 bg-[#FFFFFF] dark:bg-[#1E1B18] border border-[#D6D3D1] dark:border-[#2D2824] rounded-2xl text-[16px] font-bold text-[#1C1917] dark:text-[#FAF7F2] flex items-center gap-2 cursor-pointer"
        >
          <span className="material-symbols-outlined text-[21px]">receipt_long</span>
          <span>View Statement</span>
        </button>
      </div>

      {/* 2. Compact Financial Summary Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        {/* Metric 1: Money Affected */}
        <div className="card-elevation min-w-0 bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-6">
          <span className="text-[15px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider block">
            Money Affected
          </span>
          <div className="mt-1">
            <MetricMoney
              value={animatedTotalImpact}
              className="text-[24px] sm:text-[26px] text-[#B8522E] dark:text-[#E07A53]"
            />
          </div>
          <span className="text-[15px] text-[#57524C] dark:text-[#A8A29E] mt-1 block">
            {isMonitor
              ? 'Small differences within non-claimable threshold'
              : `${confirmedAnomalies.length} ${confirmedAnomalies.length === 1 ? 'payment issue' : 'payment issues'} found`}
          </span>
        </div>

        {/* Metric 2: Potential Recovery */}
        <div className="card-elevation min-w-0 bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-6">
          <span className="text-[15px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider block">
            Potential Recovery
          </span>
          <div className="mt-1">
            <MetricMoney
              value={animatedPotential}
              className="text-[24px] sm:text-[26px] text-[#C27803] dark:text-[#E59B22]"
            />
          </div>
          <span className="text-[15px] text-[#57524C] dark:text-[#A8A29E] mt-1 block">
            {potentialRecoveryAmount > 0 ? 'Amount eligible for recovery' : 'No dispute required'}
          </span>
        </div>

        {/* Metric 3: Health Score */}
        <div className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-6">
          <span className="text-[15px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider block">
            Audit Health Score
          </span>
          <div className="text-[28px] sm:text-[30px] font-bold font-number text-[#1C1917] dark:text-[#FAF7F2] mt-1">
            {animatedHealthScore}/100
          </div>
          <span className="text-[15px] text-[#2D5A43] dark:text-[#4E9A70] font-semibold mt-1 block">
            {isMonitor ? 'No immediate action is needed' : 'Action recommended'}
          </span>
        </div>
      </div>

      {/* 3. Payment Issues Workspace (STATEMENT | WHY IT HAPPENED Parallel Rows) */}
      <div className="space-y-5">
        <div className="flex items-center justify-between px-1">
          <h2 className="text-[20px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2]">
            Audit Workspace ({confirmedAnomalies.length} {confirmedAnomalies.length === 1 ? 'Issue' : 'Issues'})
          </h2>
          <span className="text-[15px] text-[#787168] dark:text-[#A8A29E]">
            Review statement details and verified root causes below
          </span>
        </div>

        {/* Synchronized Paired Rows */}
        {confirmedAnomalies.length > 0 ? (
          <div className="space-y-5">
            {confirmedAnomalies.map((anom, idx) => {
              const anomId = anom.finding_id || anom.anomaly_id || anom.id || `issue-${idx}`;
              const title = getSimpleIssueTitle(anom.title, anom.type);
              const details = getIssueDetails(anom);
              const impact = anom.financial_impact || 0;
              const isProofOpen = !!expandedProofIds[anomId];
              const affectedCount = anom.affected_transactions || anom.affected_transaction_count || 1;
              const evidenceItems = evidenceById[anomId] || anom.evidence || anom.evidence_logs || [];
              const referenceId =
                anom.reference_id ||
                anom.reference ||
                anom.source_record_ids?.[0] ||
                evidenceItems[0]?.reference_id ||
                evidenceItems[0]?.source_record_id ||
                'Unavailable';
              const dateStr = anom.detected_at
                ? new Date(anom.detected_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
                : anom.date || 'Date unavailable';

              return (
                <div
                  key={anomId}
                  id={`issue-row-${anomId}`}
                  className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] rounded-3xl border border-[#E2E2DC] dark:border-[#2D2824] p-6 sm:p-7"
                >
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                    
                    {/* ── LEFT COLUMN: STATEMENT ── */}
                    <div className="lg:col-span-5 p-5 rounded-2xl bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] space-y-3.5">
                      <div className="flex items-center justify-between">
                        <span className="text-[14px] font-bold uppercase tracking-wider text-[#787168] dark:text-[#A8A29E]">
                          STATEMENT · ISSUE #{idx + 1}
                        </span>
                        <span className="font-mono text-[14px] font-bold text-[#57524C] dark:text-[#A8A29E] bg-[#EAE8E3] dark:bg-[#2C2824] px-2.5 py-0.5 rounded-md">
                          {referenceId}
                        </span>
                      </div>

                      <div>
                        <h3 className="text-[20px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2] leading-snug">
                          {title}
                        </h3>
                        <p className="text-[15px] text-[#787168] dark:text-[#A8A29E] mt-0.5 font-sans">
                          {dateStr}
                        </p>
                      </div>

                      <div className="pt-3 border-t border-[#E2E2DC] dark:border-[#2D2824] flex items-center justify-between">
                        <div>
                          <span className="text-[14px] font-bold uppercase text-[#787168] dark:text-[#A8A29E] block">
                            Amount Affected
                          </span>
                          <span className="text-[22px] font-bold font-number text-[#B8522E] dark:text-[#E07A53] block">
                            {formatCurrency(impact)}
                          </span>
                        </div>

                        <span className="text-[15px] font-semibold text-[#57524C] dark:text-[#D6D3D1] bg-[#FFFFFF] dark:bg-[#1A1815] px-3 py-1.5 rounded-xl border border-[#E2E2DC] dark:border-[#2D2824]">
                          {affectedCount} {affectedCount === 1 ? 'payment' : 'payments'}
                        </span>
                      </div>
                    </div>

                    {/* ── RIGHT COLUMN: WHY IT HAPPENED ── */}
                    <div className="lg:col-span-7 space-y-4">
                      <div className="space-y-2.5">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="material-symbols-outlined text-[20px] text-[#B8522E] dark:text-[#E07A53]">
                              {details.icon}
                            </span>
                            <span className="text-[15px] font-bold uppercase tracking-wider text-[#787168] dark:text-[#A8A29E]">
                              WHY IT HAPPENED
                            </span>
                          </div>
                          <span className="text-[15px] font-bold px-2.5 py-0.5 rounded-md bg-[#EDF5F0] text-[#2D5A43] dark:bg-[#15241C] dark:text-[#4E9A70]">
                            {details.badge}
                          </span>
                        </div>

                        <p className="text-[17px] text-[#1C1917] dark:text-[#FAF7F2] font-sans leading-relaxed">
                          {details.explanation}
                        </p>

                        {/* Expected vs Actual Pill Bar */}
                        <div className="p-3 bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-2xl flex flex-wrap items-center justify-between gap-3 text-[15px]">
                          <div>
                            <span className="text-[14px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase block">
                              Expected
                            </span>
                            <span className="font-bold text-[#2D5A43] dark:text-[#4E9A70]">
                              {details.expected}
                            </span>
                          </div>
                          <div>
                            <span className="text-[14px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase block">
                              Charged / Actual
                            </span>
                            <span className="font-bold text-[#B8522E] dark:text-[#E07A53]">
                              {details.actual}
                            </span>
                          </div>
                          <div>
                            <span className="text-[14px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase block">
                              Difference
                            </span>
                            <span className="font-bold text-[#B8522E] dark:text-[#E07A53]">
                              {details.difference}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Action: Show / Hide Proof Toggle Only (No Individual Recovery Request Button) */}
                      <div>
                        <button
                          type="button"
                          id={`btn-proof-${anomId}`}
                          onClick={() => toggleProof(anomId, anom.evidence || anom.evidence_logs)}
                          className="px-4 py-2 rounded-xl border border-[#D6D3D1] dark:border-[#2D2824] bg-[#FFFFFF] dark:bg-[#1E1B18] text-[#1C1917] dark:text-[#FAF7F2] text-[16px] font-bold flex items-center gap-2 cursor-pointer hover:bg-[#F5F5F0] dark:hover:bg-[#282420] transition-colors active:scale-95"
                        >
                          <span className="material-symbols-outlined text-[19px] transition-transform duration-200">
                            {isProofOpen ? 'expand_less' : 'visibility'}
                          </span>
                          <span>{isProofOpen ? 'Hide Proof' : 'Show Proof'}</span>
                        </button>
                      </div>

                      {/* ── EXPANDABLE PROOF PANEL (Statement Table Only) ── */}
                      <AnimatePresence initial={false}>
                        {isProofOpen && (
                          <motion.div
                            key={`proof-panel-${anomId}`}
                            id={`proof-panel-${anomId}`}
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
                            className="overflow-hidden"
                          >
                            <div className="p-4 sm:p-5 rounded-2xl bg-[#FAF9F5] dark:bg-[#1E1B18] border border-[#E2E2DC] dark:border-[#2D2824] space-y-3 mt-3">
                              <div className="flex items-center justify-between border-b border-[#E2E2DC] dark:border-[#26221E] pb-2.5">
                                <span className="text-[15px] font-bold uppercase tracking-wider text-[#1C1917] dark:text-[#FAF7F2] flex items-center gap-1.5">
                                  <span className="material-symbols-outlined text-[18px] text-[#2D5A43] dark:text-[#4E9A70]">receipt_long</span>
                                  <span>Statement Proof</span>
                                </span>
                                <span className="text-[15px] text-[#787168] dark:text-[#A8A29E] font-medium">
                                  {evidenceItems.length > 0 ? `${evidenceItems.length} ${evidenceItems.length === 1 ? 'Record' : 'Records'}` : referenceId}
                                </span>
                              </div>

                              {/* Evidence Statement Records Table */}
                              {loadingProofIds[anomId] ? (
                                <p className="py-2 text-[15px] text-[#787168] dark:text-[#A8A29E]">Loading proof…</p>
                              ) : evidenceItems.length > 0 ? (
                                <div className="overflow-x-auto">
                                  <table className="w-full text-left text-[15px] border-collapse font-sans">
                                    <thead>
                                      <tr className="border-b border-[#E2E2DC] dark:border-[#2D2824] text-[#787168] dark:text-[#A8A29E]">
                                        <th className="py-2.5 px-3 font-bold uppercase tracking-wider text-[14px]">Record ID</th>
                                        <th className="py-2.5 px-3 font-bold uppercase tracking-wider text-[14px]">Date / Method</th>
                                        <th className="py-2.5 px-3 font-bold uppercase tracking-wider text-[14px]">Expected</th>
                                        <th className="py-2.5 px-3 font-bold uppercase tracking-wider text-[14px]">Actual</th>
                                        <th className="py-2.5 px-3 font-bold uppercase tracking-wider text-[14px] text-right">Difference</th>
                                      </tr>
                                    </thead>
                                    <tbody className="divide-y divide-[#E2E2DC] dark:divide-[#2D2824]">
                                      {evidenceItems.slice(0, 5).map((ev, eIdx) => (
                                        <tr key={ev.evidence_id || `ev-${eIdx}`} className="hover:bg-[#FFFFFF] dark:hover:bg-[#141311] transition-colors">
                                          <td className="py-2.5 px-3 font-mono font-bold text-[#1C1917] dark:text-[#FAF7F2]">
                                            {ev.transaction_id || ev.source_record_id || ev.reference_id || 'rec_001'}
                                          </td>
                                          <td className="py-2.5 px-3 text-[#57524C] dark:text-[#A8A29E]">
                                            {ev.date || '—'} · {ev.method || 'payment'}
                                          </td>
                                          <td className="py-2.5 px-3 font-mono text-[#2D5A43] dark:text-[#4E9A70]">
                                            {typeof ev.expected_value === 'number' ? `₹${ev.expected_value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : ev.expected_value}
                                          </td>
                                          <td className="py-2.5 px-3 font-mono text-[#B8522E] dark:text-[#E07A53]">
                                            {typeof ev.actual_value === 'number' ? `₹${ev.actual_value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : ev.actual_value}
                                          </td>
                                          <td className="py-2.5 px-3 font-mono font-bold text-right text-[#B8522E] dark:text-[#E07A53]">
                                            {typeof ev.difference === 'number' ? `₹${ev.difference.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : ev.difference}
                                          </td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              ) : (
                                <div className="py-2 text-[15px] text-[#57524C] dark:text-[#A8A29E]">
                                  {referenceId !== 'Unavailable'
                                    ? <>Ledger statement record: <span className="font-mono font-bold text-[#1C1917] dark:text-[#FAF7F2]">{referenceId}</span></>
                                    : 'Statement-level proof is attached to this finding. Open the period statement for the underlying records.'}
                                </div>
                              )}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>

                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-10 text-center bg-[#FFFFFF] dark:bg-[#1A1815] rounded-3xl border border-[#E2E2DC] dark:border-[#2D2824] space-y-3">
            <span className="material-symbols-outlined text-[44px] text-[#2D5A43] dark:text-[#4E9A70]">check_circle</span>
            <h3 className="text-[22px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2]">
              All Payments Reconciled
            </h3>
            <p className="text-[16px] text-[#57524C] dark:text-[#A8A29E] max-w-md mx-auto">
              No material payment discrepancies detected in {periodLabel}. Payments, fees, and bank settlements line up for this period.
            </p>
          </div>
        )}

        {confirmedAnomalies.length > 0 && (
          <div
            id="primary-recovery-action-card"
            className="card-elevation p-7 sm:p-8 bg-[#FAF9F5] dark:bg-[#201D1A] border-2 border-[#B8522E]/30 dark:border-[#B8522E]/40 rounded-3xl space-y-5"
          >
            <div>
              <span className="text-[14px] font-bold text-[#B8522E] dark:text-[#E07A53] uppercase tracking-wider block">
                Razorpay dispute desk
              </span>
              <h3 className="text-[24px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2] mt-0.5">
                Send Request
              </h3>
            </div>

            <div className="space-y-3">
              <div>
                <span className="text-[13px] font-bold uppercase tracking-wider text-[#787168] dark:text-[#A8A29E] block">
                  Subject
                </span>
                <p className="text-[17px] font-semibold text-[#1C1917] dark:text-[#FAF7F2] mt-1">
                  {draftSubject}
                </p>
              </div>
              <div>
                <span className="text-[13px] font-bold uppercase tracking-wider text-[#787168] dark:text-[#A8A29E] block">
                  Summary
                </span>
                <p className="text-[16px] text-[#57524C] dark:text-[#A8A29E] mt-1 leading-relaxed max-w-3xl">
                  {draftSummaryLine1}
                  <br />
                  {draftSummaryLine2}
                </p>
              </div>
            </div>

            {!isComposerOpen ? (
              <button
                id="btn-primary-send-recovery-request"
                type="button"
                onClick={handleRevealComposer}
                className="btn-primary-action px-7 py-3.5 bg-[#B8522E] hover:bg-[#A34423] text-[#FAF7F2] rounded-2xl text-[17px] font-bold flex items-center gap-3 cursor-pointer shadow-md hover:shadow-lg transition-all"
              >
                <span className="material-symbols-outlined text-[22px]">send</span>
                <span>Send request</span>
              </button>
            ) : (
              <div className="space-y-4 pt-1 border-t border-[#E2E2DC] dark:border-[#2D2824]">
                <div className="space-y-1.5">
                  <span className="block text-[14px] font-bold uppercase tracking-wider text-[#787168] dark:text-[#A8A29E]">
                    To
                  </span>
                  <p className="text-[16px] text-[#1C1917] dark:text-[#FAF7F2]">
                    Razorpay Support (disputes@razorpay.com)
                  </p>
                </div>
                <div className="space-y-1.5">
                  <label htmlFor="payment-issues-mail-subject" className="block text-[14px] font-bold uppercase tracking-wider text-[#787168] dark:text-[#A8A29E]">
                    Email subject
                  </label>
                  <input
                    id="payment-issues-mail-subject"
                    type="text"
                    value={mailSubject}
                    onChange={(e) => setMailSubject(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-[#E2E2DC] dark:border-[#2D2824] bg-white dark:bg-[#141311] text-[16px] text-[#1C1917] dark:text-[#FAF7F2] font-sans outline-none focus:border-[#B8522E] focus:ring-2 focus:ring-[#B8522E]/15"
                  />
                </div>
                <div className="space-y-1.5">
                  <label htmlFor="payment-issues-mail-body" className="block text-[14px] font-bold uppercase tracking-wider text-[#787168] dark:text-[#A8A29E]">
                    Email body
                  </label>
                  <textarea
                    id="payment-issues-mail-body"
                    rows={8}
                    value={mailBody}
                    onChange={(e) => setMailBody(e.target.value)}
                    className="w-full min-h-[180px] resize-y px-3.5 py-3 rounded-xl border border-[#E2E2DC] dark:border-[#2D2824] bg-white dark:bg-[#141311] text-[16px] leading-relaxed text-[#1C1917] dark:text-[#FAF7F2] font-sans outline-none focus:border-[#B8522E] focus:ring-2 focus:ring-[#B8522E]/15"
                  />
                </div>
                {remainingRecovery <= 0 ? (
                  <p className="text-[15px] text-[#57524C] dark:text-[#A8A29E]">
                    Eligible recovery for this period is already on a claim. You can still edit the draft; a duplicate amount will not be sent.
                  </p>
                ) : null}
                {sendRequestError ? (
                  <p role="alert" className="text-[15px] font-medium text-[#B8522E]">
                    {sendRequestError}
                  </p>
                ) : null}
                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    onClick={handleSendComposedRequest}
                    disabled={isSendingRequest || remainingRecovery <= 0 || !mailSubject.trim() || !mailBody.trim()}
                    className="btn-primary-action px-6 py-3 bg-[#1C1917] dark:bg-[#B8522E] text-[#FAF7F2] rounded-2xl text-[16px] font-bold flex items-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSendingRequest ? 'Sending…' : 'Send to Razorpay'}
                    <span className="material-symbols-outlined text-[18px]">send</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsComposerOpen(false)}
                    disabled={isSendingRequest}
                    className="px-5 py-3 rounded-2xl text-[16px] font-semibold text-[#57524C] dark:text-[#A8A29E] hover:bg-[#EBEBE6] dark:hover:bg-[#282420] cursor-pointer"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
