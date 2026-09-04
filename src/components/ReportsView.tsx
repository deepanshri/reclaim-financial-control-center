import React, { useEffect, useState, useMemo } from 'react';
import {
  MonthlyReportItem,
  ReportsResponse,
  FinancialStatus,
  Finding,
} from '../types';
import { getReportsData } from '../services/reportService';
import { MetricMoney } from './MetricMoney';
import { useAnimatedNumber } from '../hooks/useAnimatedNumber';
import {
  merchantSeverityLabel,
  merchantSeverityBadgeClass,
  merchantSeverityBannerClass,
  merchantSeverityIcon,
  merchantSeverityIconWrapClass,
  merchantSeverityAmountClass,
} from '../severityPresentation';

interface ReportsViewProps {
  selectedPeriod?: string;
  onInvestigateAnomaly?: (anomalyId: string) => void;
  onExportPdf?: () => void;
  financialStatus?: FinancialStatus | null;
  anomalies?: Finding[];
  feeRateLabel?: string;
  settlementBank?: string;
}

// Plain English mapping for anomaly issue types
const ISSUE_META: Record<string, { label: string; description: string; icon: string }> = {
  fee_rate_increase: {
    label: 'Fee charged too much',
    description: 'Applied fee rate exceeded the contracted MDR for this merchant.',
    icon: 'percent',
  },
  duplicate_refund: {
    label: 'Duplicate refund debited',
    description: 'The same customer refund was deducted more than once from your settlement.',
    icon: 'content_copy',
  },
  missing_settlement: {
    label: 'Payment not settled to bank',
    description: 'Payment was captured by gateway but never included in any bank settlement batch.',
    icon: 'account_balance_wallet',
  },
  bank_credit_missing: {
    label: 'Payment not received in bank',
    description: 'Gateway marked the batch as settled, but matching UTR credit was not found in the bank statement.',
    icon: 'search_off',
  },
  settlement_amount_discrepancy: {
    label: 'Settlement amount different from calculation',
    description: 'Net bank deposit received was short compared to gross minus legitimate fees.',
    icon: 'difference',
  },
  uncredited_refund: {
    label: 'Refund not received by customer',
    description: 'A customer refund was deducted from your account, but the customer did not receive the credit.',
    icon: 'history_toggle_off',
  },
  settlement_delay: {
    label: 'Settlement delay beyond SLA',
    description: 'Payout arrived later than normal T+1 processing window.',
    icon: 'schedule',
  },
};

const MONTH_NAMES: Record<string, string> = {
  '01': 'Jan',
  '02': 'Feb',
  '03': 'Mar',
  '04': 'Apr',
  '05': 'May',
  '06': 'Jun',
  '07': 'Jul',
  '08': 'Aug',
  '09': 'Sep',
  '10': 'Oct',
  '11': 'Nov',
  '12': 'Dec',
};

function formatMonthLabel(monthKey: string): string {
  if (!monthKey) return '';
  const parts = monthKey.split('-');
  if (parts.length === 2 && MONTH_NAMES[parts[1]]) {
    return `${MONTH_NAMES[parts[1]]} ${parts[0]}`;
  }
  return monthKey;
}

function formatMonthShort(monthKey: string): string {
  if (!monthKey) return '';
  const parts = monthKey.split('-');
  if (parts.length === 2 && MONTH_NAMES[parts[1]]) {
    return MONTH_NAMES[parts[1]];
  }
  return monthKey;
}

function findingImpactInr(finding: Finding): number {
  const raw = finding.financial_impact ?? finding.financial_impact_inr ?? 0;
  const value = Number(raw);
  return Number.isFinite(value) ? value : 0;
}

export const ReportsView: React.FC<ReportsViewProps> = ({
  selectedPeriod = '2026_H2',
  onInvestigateAnomaly,
  onExportPdf,
  financialStatus = null,
  anomalies = [],
  feeRateLabel = 'Contracted MDR rate',
  settlementBank = 'Settlement bank',
}) => {
  const [reportData, setReportData] = useState<ReportsResponse | null>(null);
  const [hoveredMonthIndex, setHoveredMonthIndex] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [retryTick, setRetryTick] = useState(0);

  useEffect(() => {
    let isCancelled = false;
    async function loadReports() {
      setIsLoading(true);
      setError(null);
      setReportData(null);
      try {
        const repRes = await getReportsData(selectedPeriod);
        if (!isCancelled) {
          if (repRes.period && repRes.period !== selectedPeriod) {
            setError('Report data did not match the selected audit period.');
            setReportData(null);
          } else {
            setReportData({ ...repRes, period: repRes.period || selectedPeriod });
          }
        }
      } catch (err: unknown) {
        if (!isCancelled) {
          const msg = err instanceof Error ? err.message : 'Failed to load report analytics';
          setError(msg);
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    loadReports();
    return () => {
      isCancelled = true;
    };
  }, [selectedPeriod, retryTick]);

  const statusForPeriod = financialStatus?.period === selectedPeriod ? financialStatus : null;
  const reportsForPeriod = reportData?.period === selectedPeriod ? reportData : null;
  const periodReady = Boolean(statusForPeriod && reportsForPeriod);

  const confirmedLoss = statusForPeriod
    ? (statusForPeriod.money_affected_inr ?? statusForPeriod.confirmed_loss_inr ?? 0)
    : 0;
  const potentialLoss = statusForPeriod
    ? (statusForPeriod.potential_recovery_inr ?? statusForPeriod.potential_loss_inr ?? 0)
    : 0;
  const recoveredAmount = statusForPeriod
    ? (statusForPeriod.recovered_inr ?? reportsForPeriod?.total_amount_recovered_inr ?? 0)
    : 0;
  const requestedAmount = statusForPeriod?.recovery_requested_inr ?? 0;
  const underReviewAmount = statusForPeriod?.under_review_inr ?? 0;
  const notRecoveredAmount = statusForPeriod?.not_recovered_inr ?? 0;

  const totalGrossVolume = statusForPeriod
    ? (statusForPeriod.total_payment_volume_inr ?? reportsForPeriod?.total_gross_volume_inr ?? 0)
    : 0;
  const totalFees = statusForPeriod
    ? (statusForPeriod.total_fees_inr ?? reportsForPeriod?.total_fees_inr ?? 0)
    : 0;
  const totalRefunds = statusForPeriod
    ? (statusForPeriod.total_refunds_inr ?? reportsForPeriod?.total_refunds_inr ?? 0)
    : 0;
  const totalSettlements = statusForPeriod
    ? (statusForPeriod.total_settlements_inr ?? reportsForPeriod?.total_settlements_inr ?? 0)
    : 0;

  // Animated counters for smooth transitions
  const animLoss = useAnimatedNumber(confirmedLoss, 650);
  const animPotential = useAnimatedNumber(potentialLoss, 650);
  const animRecovered = useAnimatedNumber(recoveredAmount, 650);
  const animVolume = useAnimatedNumber(totalGrossVolume, 650);
  const animFees = useAnimatedNumber(totalFees, 650);
  const animRefunds = useAnimatedNumber(totalRefunds, 650);
  const animSettlements = useAnimatedNumber(totalSettlements, 650);

  const monthlyList: MonthlyReportItem[] = useMemo(() => {
    return reportsForPeriod?.monthly_breakdown || [];
  }, [reportsForPeriod]);

  const totalTransactionCount = useMemo(() => {
    return monthlyList.reduce((acc, m) => acc + (m.transaction_count || 0), 0);
  }, [monthlyList]);

  // Group confirmed anomalies by type for Issue Breakdown
  const confirmedAnomalies = useMemo(() => {
    return anomalies.filter((a) => a.status.toLowerCase() === 'confirmed');
  }, [anomalies]);

  const issueBreakdown = useMemo(() => {
    const map = new Map<
      string,
      {
        type: string;
        title: string;
        plainTitle: string;
        description: string;
        icon: string;
        impact: number;
        count: number;
        anomalyIds: string[];
      }
    >();

    for (const anom of confirmedAnomalies) {
      const typeKey = anom.type || 'other';
      const meta = ISSUE_META[typeKey] || {
        label: anom.title || 'Reconciliation Discrepancy',
        description: anom.root_cause_reference || anom.description || 'Discrepancy identified in payment records.',
        icon: 'error_outline',
      };

      const existing = map.get(typeKey);
      if (existing) {
        existing.impact += findingImpactInr(anom);
        existing.count += Number(anom.affected_transaction_count || anom.affected_transactions || 1);
        existing.anomalyIds.push(anom.finding_id || anom.anomaly_id || '');
      } else {
        map.set(typeKey, {
          type: typeKey,
          title: anom.title,
          plainTitle: meta.label,
          description: meta.description,
          icon: meta.icon,
          impact: findingImpactInr(anom),
          count: Number(anom.affected_transaction_count || anom.affected_transactions || 1),
          anomalyIds: [anom.finding_id || anom.anomaly_id || ''],
        });
      }
    }

    return Array.from(map.values()).sort((a, b) => b.impact - a.impact);
  }, [confirmedAnomalies]);

  const severityLevel = statusForPeriod?.severity_level || 'healthy';
  const severityLabel = statusForPeriod?.severity_label || merchantSeverityLabel(severityLevel);
  const detectedIssueCount = statusForPeriod?.confirmed_finding_count ?? confirmedAnomalies.length;
  const hasNoAuditData =
    periodReady &&
    totalGrossVolume === 0 &&
    detectedIssueCount === 0 &&
    monthlyList.every((month) => (month.gross_volume_inr || 0) === 0);

  // Chart Dynamic Dimensions
  const chartWidth = 900;
  const chartHeight = 260;
  const paddingX = 60;
  const paddingBottom = 45;
  const paddingTop = 30;

  const maxVolume = useMemo(() => {
    const maxVal = Math.max(...monthlyList.map((m) => m.gross_volume_inr), 10000);
    return Math.ceil(maxVal * 1.15);
  }, [monthlyList]);

  const maxLoss = useMemo(() => {
    return Math.max(...monthlyList.map((m) => m.loss_detected_inr), 0);
  }, [monthlyList]);

  const chartPoints = useMemo(() => {
    if (monthlyList.length === 0) return [];
    const usableWidth = chartWidth - paddingX * 2;
    const usableHeight = chartHeight - paddingTop - paddingBottom;
    const step = monthlyList.length > 1 ? usableWidth / (monthlyList.length - 1) : usableWidth / 2;

    return monthlyList.map((m, idx) => {
      const x = paddingX + idx * step;
      const yVolume = chartHeight - paddingBottom - (m.gross_volume_inr / maxVolume) * usableHeight;
      return {
        idx,
        x,
        yVolume,
        data: m,
      };
    });
  }, [monthlyList, maxVolume, chartWidth, chartHeight, paddingX, paddingTop, paddingBottom]);

  // Generate smooth SVG paths
  const volumePath = useMemo(() => {
    if (chartPoints.length === 0) return '';
    return chartPoints.reduce((acc, pt, idx) => `${acc} ${idx === 0 ? 'M' : 'L'} ${pt.x},${pt.yVolume}`, '');
  }, [chartPoints]);

  const volumeAreaPath = useMemo(() => {
    if (chartPoints.length === 0) return '';
    const last = chartPoints[chartPoints.length - 1];
    const first = chartPoints[0];
    const bottomY = chartHeight - paddingBottom;
    return `${volumePath} L ${last.x},${bottomY} L ${first.x},${bottomY} Z`;
  }, [chartPoints, volumePath, chartHeight, paddingBottom]);

  const activeMonth = hoveredMonthIndex !== null && chartPoints[hoveredMonthIndex] ? chartPoints[hoveredMonthIndex].data : null;

  if (error && !reportData) {
    return (
      <div className="p-6 sm:p-8 lg:p-12 max-w-[1600px] mx-auto w-full space-y-4 font-sans">
        <h1 className="font-display text-[30px] font-medium">Reports &amp; Analytics</h1>
        <p className="text-[16px] text-[#B8522E]">{error}</p>
        <button
          type="button"
          onClick={() => setRetryTick((n) => n + 1)}
          className="px-4 py-2 bg-[#1C1917] dark:bg-[#B8522E] text-[#FAF7F2] rounded-xl text-[15px] font-medium cursor-pointer"
        >
          Retry
        </button>
      </div>
    );
  }

  if (isLoading || !periodReady) {
    return (
      <div className="p-6 sm:p-8 lg:p-12 max-w-[1600px] mx-auto w-full space-y-8 font-sans">
        <p className="text-[16px] text-[#787168] dark:text-[#A8A29E]">
          Preparing this period's audit…
        </p>
        <div className="h-12 bg-[#E2E2DC]/50 dark:bg-[#26221E]/50 rounded-2xl w-80 animate-pulse"></div>
        <div className="h-44 bg-[#FFFFFF] dark:bg-[#1A1815] rounded-3xl border border-[#E2E2DC] dark:border-[#2D2824] p-8 animate-pulse shadow-sm"></div>
        <div className="space-y-6">
          <div className="h-56 bg-[#FFFFFF] dark:bg-[#1A1815] rounded-3xl border border-[#E2E2DC] dark:border-[#2D2824] animate-pulse shadow-sm"></div>
          <div className="h-56 bg-[#FFFFFF] dark:bg-[#1A1815] rounded-3xl border border-[#E2E2DC] dark:border-[#2D2824] animate-pulse shadow-sm"></div>
        </div>
        {error ? (
          <p className="text-[16px] text-[#B8522E]">{error}</p>
        ) : null}
      </div>
    );
  }

  if (hasNoAuditData) {
    return (
      <div
        id="reports-analytics-view"
        className="p-6 sm:p-8 lg:p-12 max-w-[1600px] mx-auto w-full space-y-10 text-[#1C1917] dark:text-[#F4F0E8] font-sans"
      >
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 border-b border-[#E2E2DC] dark:border-[#26221E] pb-6">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="font-display text-[30px] font-medium leading-[1.2] text-[#1C1917] dark:text-[#FAF7F2] sm:text-[36px]">
                Reports &amp; Analytics
              </h1>
              <span className="text-[15px] font-bold px-3 py-1 bg-[#EAE8E3] dark:bg-[#282420] text-[#57524C] dark:text-[#D6D3D1] rounded-full uppercase tracking-wider">
                {selectedPeriod.replace('_', ' ')}
              </span>
            </div>
            <p className="text-[17px] text-[#57524C] dark:text-[#A8A29E] mt-1 font-sans">
              Independent audit reconciliation across customer payments, gateway fees, bank deposits, and recoveries.
            </p>
          </div>
        </div>
        <div className="card-elevation rounded-3xl border border-dashed border-[#E2E2DC] bg-[#FAF9F5] px-8 py-16 text-center dark:border-[#2D2824] dark:bg-[#1A1815]">
          <span className="material-symbols-outlined text-[42px] text-[#787168] dark:text-[#A8A29E]">folder_off</span>
          <h2 className="mt-4 text-[22px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2]">
            No audit data available for this period.
          </h2>
          <p className="mx-auto mt-2 max-w-md text-[16px] text-[#57524C] dark:text-[#A8A29E]">
            This audit period has no payment ledger or confirmed findings in the source dataset. Figures from other periods are not shown.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      id="reports-analytics-view"
      className="p-6 sm:p-8 lg:p-12 max-w-[1600px] mx-auto w-full space-y-10 text-[#1C1917] dark:text-[#F4F0E8] font-sans transition-all duration-300"
    >
      {/* 1. Header & Period Selector */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 border-b border-[#E2E2DC] dark:border-[#26221E] pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="font-display text-[30px] font-medium leading-[1.2] text-[#1C1917] dark:text-[#FAF7F2] sm:text-[36px]">
              Reports &amp; Analytics
            </h1>
            <span className="text-[15px] font-bold px-3 py-1 bg-[#EAE8E3] dark:bg-[#282420] text-[#57524C] dark:text-[#D6D3D1] rounded-full uppercase tracking-wider">
              {selectedPeriod.replace('_', ' ')}
            </span>
          </div>
          <p className="text-[17px] text-[#57524C] dark:text-[#A8A29E] mt-1 font-sans">
            Independent audit reconciliation across customer payments, gateway fees, bank deposits, and recoveries.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <button
            id="btn-export-report-pdf"
            onClick={onExportPdf || (() => window.print())}
            className="btn-secondary-action px-5 py-2.5 bg-[#FFFFFF] dark:bg-[#1E1B18] border border-[#D6D3D1] dark:border-[#2D2824] rounded-2xl text-[16px] font-bold text-[#1C1917] dark:text-[#FAF7F2] flex items-center gap-2 cursor-pointer"
          >
            <span className="material-symbols-outlined text-[21px]">picture_as_pdf</span>
            <span>Export Report</span>
          </button>
        </div>
      </div>

      {/* 2. Period Status & Explanation Banner */}
      <div
        id="report-period-status-banner"
        className={`p-6 rounded-3xl border flex flex-col md:flex-row items-start md:items-center justify-between gap-5 transition-colors ${merchantSeverityBannerClass(severityLevel)}`}
      >
        <div className="flex items-start gap-4">
          <div
            className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 ${merchantSeverityIconWrapClass(severityLevel)}`}
          >
            <span className="material-symbols-outlined text-[26px]">
              {merchantSeverityIcon(severityLevel)}
            </span>
          </div>
          <div>
            <div className="flex items-center gap-3">
              <span
                className={`text-[15px] font-extrabold px-3 py-0.5 rounded-full uppercase tracking-wider ${merchantSeverityBadgeClass(severityLevel)}`}
              >
                {severityLabel}
              </span>
              <span className="text-[15px] text-[#787168] dark:text-[#A8A29E] font-medium">
                Audit Period {selectedPeriod.replace('_', ' ')}
                {statusForPeriod?.period_start && statusForPeriod?.period_end
                  ? ` · ${statusForPeriod.period_start} to ${statusForPeriod.period_end}`
                  : ''}
              </span>
            </div>
            <p className="text-[17px] sm:text-[18px] font-semibold text-[#1C1917] dark:text-[#FAF7F2] mt-1.5 leading-snug">
              {severityLevel === 'action_needed'
                ? `A significant amount is affected and needs immediate attention: ₹${confirmedLoss.toLocaleString('en-IN', { minimumFractionDigits: 2 })} across ${detectedIssueCount} detected issues.`
                : severityLevel === 'needs_review'
                ? `A meaningful amount is affected and should be reviewed: ₹${confirmedLoss.toLocaleString('en-IN', { minimumFractionDigits: 2 })} across ${detectedIssueCount} detected issues.`
                : `A small difference was found (₹${confirmedLoss.toLocaleString('en-IN', { minimumFractionDigits: 2 })}), but no immediate action is needed.`}
            </p>
            <p className="text-[16px] text-[#57524C] dark:text-[#A8A29E] mt-0.5">
              {statusForPeriod?.severity_message ||
                'All transaction records have been cross-checked against gateway ledgers and bank credits.'}
            </p>
          </div>
        </div>

        {confirmedLoss > 0 && (
          <div className="text-right shrink-0">
            <span className="text-[14px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider block">
              Total Confirmed Impact
            </span>
            <MetricMoney
              value={confirmedLoss}
              className={`text-[22px] sm:text-[26px] ${merchantSeverityAmountClass(severityLevel)}`}
            />
          </div>
        )}
      </div>

      {/* 3. Top Financial Summary Cards (Strong Visual Hierarchy) */}
      <div className="space-y-4">
        <h2 className="text-[20px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2]">
          Financial Position Summary
        </h2>

        {/* Primary Hero Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Hero 1: Money Affected (Financial Impact) */}
          <div className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border-2 border-[#B8522E]/30 dark:border-[#B8522E]/40 rounded-3xl p-6 sm:p-7 relative overflow-hidden group hover:border-[#B8522E] transition-colors">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[15px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider">
                Money Affected (Financial Loss)
              </span>
              <span className="w-8 h-8 rounded-xl bg-[#B8522E]/10 dark:bg-[#B8522E]/20 text-[#B8522E] dark:text-[#E07A53] flex items-center justify-center">
                <span className="material-symbols-outlined text-[20px]">trending_down</span>
              </span>
            </div>
            <MetricMoney
              value={animLoss}
              className="text-[26px] sm:text-[30px] text-[#B8522E] dark:text-[#E07A53]"
            />
            <p className="text-[15px] text-[#57524C] dark:text-[#A8A29E] mt-3 leading-relaxed">
              {confirmedLoss < 100000
                ? 'Minor settlement rounding adjustments within normal tolerance.'
                : `${detectedIssueCount} confirmed issues found across fee rates, settlements, and refunds.`}
            </p>
          </div>

          {/* Hero 2: Potential Recovery */}
          <div className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-6 sm:p-7 relative overflow-hidden group hover:border-[#C27803] transition-colors">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[15px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider">
                Potential Recovery
              </span>
              <span className="w-8 h-8 rounded-xl bg-[#C27803]/10 dark:bg-[#C27803]/20 text-[#C27803] dark:text-[#E59B22] flex items-center justify-center">
                <span className="material-symbols-outlined text-[20px]">price_check</span>
              </span>
            </div>
            <MetricMoney
              value={animPotential}
              className="text-[26px] sm:text-[30px] text-[#C27803] dark:text-[#E59B22]"
            />
            <p className="text-[15px] text-[#57524C] dark:text-[#A8A29E] mt-3 leading-relaxed">
              Total amount eligible to be recovered via gateway merchant dispute tickets.
            </p>
          </div>

          {/* Hero 3: Recovered Amount */}
          <div className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-6 sm:p-7 relative overflow-hidden group hover:border-[#2D5A43] transition-colors">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[15px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider">
                Recovered to Bank
              </span>
              <span className="w-8 h-8 rounded-xl bg-[#2D5A43]/10 dark:bg-[#2D5A43]/20 text-[#2D5A43] dark:text-[#4E9A70] flex items-center justify-center">
                <span className="material-symbols-outlined text-[20px]">account_balance</span>
              </span>
            </div>
            <MetricMoney
              value={animRecovered}
              className="text-[26px] sm:text-[30px] text-[#2D5A43] dark:text-[#4E9A70]"
            />
            <p className="text-[15px] text-[#57524C] dark:text-[#A8A29E] mt-3 leading-relaxed">
              Direct bank credits received and confirmed for resolved dispute claims.
            </p>
          </div>
        </div>

        {/* Secondary Supporting Metrics Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-[#FAF9F5] dark:bg-[#1E1B18] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-5">
          <div className="min-w-0 space-y-1">
            <span className="text-[14px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider block">
              Customer Payments
            </span>
            <MetricMoney
              value={animVolume}
              className="text-[18px] sm:text-[20px] text-[#1C1917] dark:text-[#FAF7F2]"
            />
            <span className="text-[15px] text-[#57524C] dark:text-[#A8A29E]">
              {totalTransactionCount.toLocaleString('en-IN')} transactions
            </span>
          </div>

          <div className="min-w-0 space-y-1">
            <span className="text-[14px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider block">
              Payment Fees (MDR + GST)
            </span>
            <MetricMoney
              value={animFees}
              className="text-[18px] sm:text-[20px] text-[#1C1917] dark:text-[#FAF7F2]"
            />
            <span className="text-[15px] text-[#57524C] dark:text-[#A8A29E]">{feeRateLabel}</span>
          </div>

          <div className="min-w-0 space-y-1">
            <span className="text-[14px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider block">
              Customer Refunds
            </span>
            <MetricMoney
              value={animRefunds}
              className="text-[18px] sm:text-[20px] text-[#1C1917] dark:text-[#FAF7F2]"
            />
            <span className="text-[15px] text-[#57524C] dark:text-[#A8A29E]">
              {monthlyList.reduce((acc, m) => acc + (m.refunds_inr > 0 ? 1 : 0), 0) > 0 ? 'Normal customer returns' : '0 refunds'}
            </span>
          </div>

          <div className="min-w-0 space-y-1">
            <span className="text-[14px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider block">
              Net Bank Settlements
            </span>
            <MetricMoney
              value={animSettlements}
              className="text-[18px] sm:text-[20px] text-[#1C1917] dark:text-[#FAF7F2]"
            />
            <span className="text-[15px] text-[#57524C] dark:text-[#A8A29E]">{settlementBank}</span>
          </div>
        </div>
      </div>

      {/* 4. Primary Chart — Monthly Financial Activity (Interactive SVG) */}
      <div className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div>
            <h2 className="text-[22px] sm:text-[24px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2]">
              Monthly Financial Activity
            </h2>
            <p className="text-[16px] text-[#57524C] dark:text-[#A8A29E] mt-0.5 font-sans">
              Customer payment volume and detected issue impact across the 6 calendar months
            </p>
          </div>

          <div className="flex items-center gap-5 text-[15px] font-bold">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-[#1C1917] dark:bg-[#FAF7F2]"></span>
              <span className="text-[#57524C] dark:text-[#A8A29E]">Payment Volume</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-[#B8522E]"></span>
              <span className="text-[#B8522E] dark:text-[#E07A53]">Money Affected</span>
            </div>
          </div>
        </div>

        {/* Dynamic Chart Container */}
        {monthlyList.length > 0 && (
          <div className="w-full relative pt-2">
            <svg
              viewBox={`0 0 ${chartWidth} ${chartHeight}`}
              className="w-full h-64 sm:h-72 overflow-visible select-none"
            >
              <defs>
                <linearGradient id="reportsVolumeGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#1C1917" stopOpacity="0.12" />
                  <stop offset="100%" stopColor="#1C1917" stopOpacity="0.0" />
                </linearGradient>
                <linearGradient id="reportsVolumeGradientDark" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#FAF7F2" stopOpacity="0.16" />
                  <stop offset="100%" stopColor="#FAF7F2" stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {/* Grid Lines */}
              {[0.25, 0.5, 0.75, 1.0].map((ratio, i) => {
                const y = chartHeight - paddingBottom - ratio * (chartHeight - paddingTop - paddingBottom);
                const val = maxVolume * ratio;
                return (
                  <g key={i}>
                    <line
                      x1={paddingX}
                      y1={y}
                      x2={chartWidth - paddingX}
                      y2={y}
                      stroke="currentColor"
                      className="text-[#E2E2DC] dark:text-[#26221E]"
                      strokeDasharray="4 4"
                      strokeWidth="1"
                    />
                    <text
                      x={paddingX - 10}
                      y={y + 4}
                      textAnchor="end"
                      className="text-[14px] fill-[#787168] dark:fill-[#A8A29E] font-number font-medium"
                    >
                      ₹{(val / 100000).toFixed(1)}L
                    </text>
                  </g>
                );
              })}

              {/* Area Fill */}
              {volumeAreaPath && (
                <path
                  d={volumeAreaPath}
                  className="fill-[#1C1917]/10 dark:fill-[#FAF7F2]/10 transition-all duration-300"
                />
              )}

              {/* Volume Line */}
              {volumePath && (
                <path
                  d={volumePath}
                  fill="none"
                  className="stroke-[#1C1917] dark:stroke-[#FAF7F2] transition-all duration-300"
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              )}

              {/* Monthly Data Points, Bars & Highlight Pins */}
              {chartPoints.map((pt, idx) => {
                const isHovered = hoveredMonthIndex === idx;
                const hasLoss = pt.data.loss_detected_inr > 0;
                return (
                  <g
                    key={idx}
                    className="cursor-pointer group"
                    onMouseEnter={() => setHoveredMonthIndex(idx)}
                    onMouseLeave={() => setHoveredMonthIndex(null)}
                    onClick={() => setHoveredMonthIndex(isHovered ? null : idx)}
                  >
                    {/* Hover Column Indicator */}
                    {isHovered && (
                      <line
                        x1={pt.x}
                        y1={paddingTop}
                        x2={pt.x}
                        y2={chartHeight - paddingBottom}
                        stroke="#B8522E"
                        strokeWidth="1.5"
                        strokeDasharray="3 3"
                        className="animate-pulse"
                      />
                    )}

                    {/* Volume Point */}
                    <circle
                      cx={pt.x}
                      cy={pt.yVolume}
                      r={isHovered ? 7 : 5}
                      className={`transition-all duration-200 ${
                        hasLoss
                          ? 'fill-[#B8522E] stroke-white dark:stroke-[#1A1815]'
                          : 'fill-[#1C1917] dark:fill-[#FAF7F2] stroke-white dark:stroke-[#1A1815]'
                      }`}
                      strokeWidth="2.5"
                    />

                    {/* Issue Tag for Months with Loss */}
                    {hasLoss && (
                      <g transform={`translate(${pt.x}, ${Math.max(paddingTop + 10, pt.yVolume - 24)})`}>
                        <rect
                          x="-42"
                          y="-10"
                          width="84"
                          height="20"
                          rx="10"
                          className="fill-[#B8522E] shadow-sm"
                        />
                        <text
                          x="0"
                          y="4"
                          textAnchor="middle"
                          className="text-[14px] fill-white font-number font-bold tracking-tight"
                        >
                          ₹{pt.data.loss_detected_inr >= 1000 ? `${(pt.data.loss_detected_inr / 1000).toFixed(1)}k` : pt.data.loss_detected_inr.toFixed(0)} loss
                        </text>
                      </g>
                    )}

                    {/* Month Label */}
                    <text
                      x={pt.x}
                      y={chartHeight - 12}
                      textAnchor="middle"
                      className={`text-[15px] font-sans font-bold transition-colors ${
                        isHovered
                          ? 'fill-[#B8522E] dark:fill-[#E07A53]'
                          : 'fill-[#57524C] dark:fill-[#A8A29E]'
                      }`}
                    >
                      {formatMonthShort(pt.data.month)}
                    </text>
                  </g>
                );
              })}
            </svg>

            {/* Interactive Month Detail Card */}
            {activeMonth && (
              <div className="mt-4 p-4 bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-2xl flex flex-wrap items-center justify-between gap-4 animate-fade-in">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[#1C1917] dark:bg-[#FAF7F2] text-white dark:text-[#1C1917] flex items-center justify-center font-bold text-[16px]">
                    {formatMonthShort(activeMonth.month)}
                  </div>
                  <div>
                    <h4 className="text-[17px] font-bold text-[#1C1917] dark:text-[#FAF7F2]">
                      {formatMonthLabel(activeMonth.month)} Summary
                    </h4>
                    <p className="text-[15px] text-[#787168] dark:text-[#A8A29E]">
                      {activeMonth.transaction_count.toLocaleString('en-IN')} customer payments processed
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-6 text-[16px]">
                  <div>
                    <span className="text-[14px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase block">
                      Payment Volume
                    </span>
                    <span className="font-bold font-number text-[#1C1917] dark:text-[#FAF7F2]">
                      ₹{activeMonth.gross_volume_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  </div>

                  <div>
                    <span className="text-[14px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase block">
                      Fees Paid
                    </span>
                    <span className="font-bold font-number text-[#57524C] dark:text-[#D6D3D1]">
                      ₹{activeMonth.fees_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  </div>

                  <div>
                    <span className="text-[14px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase block">
                      Refunds
                    </span>
                    <span className="font-bold font-number text-[#57524C] dark:text-[#D6D3D1]">
                      ₹{activeMonth.refunds_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  </div>

                  <div>
                    <span className="text-[14px] font-bold text-[#B8522E] dark:text-[#E07A53] uppercase block">
                      Money Affected
                    </span>
                    <span className="font-bold font-number text-[#B8522E] dark:text-[#E07A53]">
                      ₹{activeMonth.loss_detected_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  </div>

                  {activeMonth.amount_recovered_inr > 0 && (
                    <div>
                      <span className="text-[14px] font-bold text-[#2D5A43] dark:text-[#4E9A70] uppercase block">
                        Recovered
                      </span>
                      <span className="font-bold font-number text-[#2D5A43] dark:text-[#4E9A70]">
                        ₹{activeMonth.amount_recovered_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 5. Issue Breakdown & Recovery Journey Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column: Issue Breakdown */}
        <div className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-6 sm:p-8 space-y-6">
          <div className="flex items-center justify-between border-b border-[#E2E2DC] dark:border-[#26221E] pb-4">
            <div>
              <h3 className="text-[21px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2]">
                Where Money Was Affected
              </h3>
              <p className="text-[15px] text-[#57524C] dark:text-[#A8A29E] mt-0.5">
                Exact breakdown of detected discrepancies by problem category
              </p>
            </div>
            <span className="text-[15px] font-bold px-3 py-1 bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-full text-[#57524C] dark:text-[#D6D3D1]">
              {issueBreakdown.length} {issueBreakdown.length === 1 ? 'Category' : 'Categories'}
            </span>
          </div>

          {issueBreakdown.length > 0 ? (
            <div className="space-y-4">
              {issueBreakdown.map((item) => (
                <div
                  key={item.type}
                  className="p-4 bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:border-[#B8522E]/40 transition-colors"
                >
                  <div className="flex items-start gap-3.5">
                    <div className="w-10 h-10 rounded-xl bg-[#B8522E]/10 dark:bg-[#B8522E]/20 text-[#B8522E] dark:text-[#E07A53] flex items-center justify-center shrink-0 mt-0.5">
                      <span className="material-symbols-outlined text-[22px]">{item.icon}</span>
                    </div>
                    <div>
                      <h4 className="text-[17px] font-bold text-[#1C1917] dark:text-[#FAF7F2]">
                        {item.plainTitle}
                      </h4>
                      <p className="text-[15px] text-[#57524C] dark:text-[#A8A29E] mt-0.5">
                        {item.description}
                      </p>
                      <span className="inline-block mt-1 text-[14px] font-bold text-[#787168] dark:text-[#A8A29E]">
                        {item.count} {item.count === 1 ? 'transaction affected' : 'transactions affected'}
                      </span>
                    </div>
                  </div>

                  <div className="text-right shrink-0 w-full sm:w-auto flex sm:flex-col justify-between items-center sm:items-end">
                    <div>
                      <span className="text-[14px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase block sm:hidden">
                        Impact
                      </span>
                      <span className="text-[19px] font-bold font-number text-[#B8522E] dark:text-[#E07A53]">
                        ₹{item.impact.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </span>
                    </div>

                    {item.anomalyIds[0] && onInvestigateAnomaly && (
                      <button
                        onClick={() => onInvestigateAnomaly(item.anomalyIds[0])}
                        className="mt-1.5 text-[15px] font-bold text-[#B8522E] hover:underline flex items-center gap-1 cursor-pointer"
                      >
                        <span>Investigate</span>
                        <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center bg-[#FAF9F5] dark:bg-[#201D1A] rounded-2xl border border-dashed border-[#E2E2DC] dark:border-[#2D2824]">
              <span className="material-symbols-outlined text-[38px] text-[#2D5A43] dark:text-[#4E9A70]">check_circle</span>
              <h4 className="text-[18px] font-bold text-[#1C1917] dark:text-[#FAF7F2] mt-2">
                No Material Discrepancies Found
              </h4>
              <p className="text-[16px] text-[#57524C] dark:text-[#A8A29E] mt-1">
                Your payment transactions and settlements in this audit period are completely balanced.
              </p>
            </div>
          )}
        </div>

        {/* Right Column: Recovery Summary & Funnel */}
        <div className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-6 sm:p-8 space-y-6 flex flex-col justify-between">
          <div className="space-y-6">
            <div className="border-b border-[#E2E2DC] dark:border-[#26221E] pb-4">
              <h3 className="text-[21px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2]">
                Recovery Status &amp; Progress
              </h3>
              <p className="text-[15px] text-[#57524C] dark:text-[#A8A29E] mt-0.5">
                Status of dispute claims filed with Razorpay merchant desk
              </p>
            </div>

            {/* Visual Funnel */}
            <div className="space-y-3.5">
              {/* Funnel Step 1: Potential Recovery */}
              <div className="p-4 bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-2xl flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#C27803]/15 text-[#C27803] flex items-center justify-center font-bold text-[15px]">
                    1
                  </div>
                  <div>
                    <span className="text-[16px] font-bold text-[#1C1917] dark:text-[#FAF7F2] block">
                      Potential Recovery Identified
                    </span>
                    <span className="text-[15px] text-[#787168] dark:text-[#A8A29E]">
                      Total eligible financial discrepancy
                    </span>
                  </div>
                </div>
                <span className="text-[18px] font-bold font-number text-[#C27803]">
                  ₹{potentialLoss.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
              </div>

              {/* Funnel Step 2: Requested */}
              <div className="p-4 bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-2xl flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#57524C]/15 text-[#57524C] dark:text-[#FAF7F2] flex items-center justify-center font-bold text-[15px]">
                    2
                  </div>
                  <div>
                    <span className="text-[16px] font-bold text-[#1C1917] dark:text-[#FAF7F2] block">
                      Dispute Claims Submitted
                    </span>
                    <span className="text-[15px] text-[#787168] dark:text-[#A8A29E]">
                      Formal recovery requests sent to gateway
                    </span>
                  </div>
                </div>
                <span className="text-[18px] font-bold font-number text-[#1C1917] dark:text-[#FAF7F2]">
                  ₹{requestedAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
              </div>

              {/* Funnel Step 3: Outcomes Breakdown */}
              <div className="p-4 bg-[#FFFFFF] dark:bg-[#1E1B18] border border-[#E2E2DC] dark:border-[#2D2824] rounded-2xl space-y-3">
                <span className="text-[15px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider block">
                  Dispute Outcomes
                </span>

                <div className="space-y-2.5">
                  {/* Recovered */}
                  <div className="flex items-center justify-between text-[16px]">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-[#2D5A43]"></span>
                      <span className="font-semibold text-[#1C1917] dark:text-[#FAF7F2]">
                        Recovered &amp; Credited
                      </span>
                    </div>
                    <span className="font-bold font-number text-[#2D5A43] dark:text-[#4E9A70]">
                      ₹{recoveredAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  </div>

                  {/* Under Review */}
                  <div className="flex items-center justify-between text-[16px]">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-[#C27803]"></span>
                      <span className="font-semibold text-[#1C1917] dark:text-[#FAF7F2]">
                        Under Active Review
                      </span>
                    </div>
                    <span className="font-bold font-number text-[#C27803] dark:text-[#E59B22]">
                      ₹{underReviewAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  </div>

                  {/* Not Recovered */}
                  <div className="flex items-center justify-between text-[16px]">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-[#787168]"></span>
                      <span className="font-semibold text-[#787168] dark:text-[#A8A29E]">
                        Not Recovered / Closed
                      </span>
                    </div>
                    <span className="font-bold font-number text-[#787168] dark:text-[#A8A29E]">
                      ₹{notRecoveredAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actionable Insight */}
          <div className="p-4 bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-2xl flex items-start gap-3">
            <span className="material-symbols-outlined text-[22px] text-[#B8522E] shrink-0 mt-0.5">lightbulb</span>
            <p className="text-[15px] text-[#57524C] dark:text-[#A8A29E] leading-relaxed">
              {severityLevel === 'action_needed'
                ? 'Tip: Track under-review recovery requests in the Recovery Requests tab to confirm bank credit once resolved.'
                : severityLevel === 'needs_review'
                ? 'Tip: Review the unsettled payment with your payment desk to initiate a claim.'
                : 'Tip: MONITOR periods have only a small difference. No claim ticket is needed.'}
            </p>
          </div>
        </div>
      </div>

      {/* 6. Month-by-Month Summary Table (6 Calendar Months Clean View) */}
      <div className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl overflow-hidden">
        <div className="p-6 sm:p-7 border-b border-[#E2E2DC] dark:border-[#26221E] flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div>
            <h3 className="text-[22px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2]">
              Month-by-Month Audit Breakdown
            </h3>
            <p className="text-[16px] text-[#57524C] dark:text-[#A8A29E] mt-0.5">
              Monthly records for {selectedPeriod.replace('_', ' ')}
            </p>
          </div>
          <span className="text-[15px] font-bold px-3 py-1 bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-full text-[#57524C] dark:text-[#D6D3D1]">
            6 Calendar Months
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-[16px] border-collapse font-sans">
            <thead>
              <tr className="bg-[#FAF9F5] dark:bg-[#201D1A] text-[#787168] dark:text-[#A8A29E] border-b border-[#E2E2DC] dark:border-[#2D2824]">
                <th className="py-3.5 px-6 font-bold uppercase tracking-wider text-[14px]">Month</th>
                <th className="py-3.5 px-6 font-bold uppercase tracking-wider text-[14px]">Payments Count</th>
                <th className="py-3.5 px-6 font-bold uppercase tracking-wider text-[14px]">Total Payments Value</th>
                <th className="py-3.5 px-6 font-bold uppercase tracking-wider text-[14px]">Fees Paid</th>
                <th className="py-3.5 px-6 font-bold uppercase tracking-wider text-[14px]">Refunds</th>
                <th className="py-3.5 px-6 font-bold uppercase tracking-wider text-[14px]">Money Affected</th>
                <th className="py-3.5 px-6 font-bold uppercase tracking-wider text-[14px] text-right">Recovered</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E2DC] dark:divide-[#2D2824]">
              {monthlyList.map((row) => {
                const hasLoss = row.loss_detected_inr > 0;
                return (
                  <tr
                    key={row.month}
                    className={`hover:bg-[#FAF9F5] dark:hover:bg-[#1E1B18] transition-colors ${
                      hasLoss ? 'bg-[#FFFDFB] dark:bg-[#1D1714]' : ''
                    }`}
                  >
                    <td className="py-4 px-6 font-bold text-[#1C1917] dark:text-[#FAF7F2] flex items-center gap-2">
                      <span>{formatMonthLabel(row.month)}</span>
                      {hasLoss && (
                        <span className="w-2 h-2 rounded-full bg-[#B8522E]" title="Discrepancy detected"></span>
                      )}
                    </td>
                    <td className="py-4 px-6 font-number text-[#57524C] dark:text-[#D6D3D1]">
                      {row.transaction_count.toLocaleString('en-IN')}
                    </td>
                    <td className="py-4 px-6 font-bold font-number text-[#1C1917] dark:text-[#FAF7F2]">
                      ₹{row.gross_volume_inr.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="py-4 px-6 font-number text-[#57524C] dark:text-[#D6D3D1]">
                      ₹{row.fees_inr.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="py-4 px-6 font-number text-[#57524C] dark:text-[#D6D3D1]">
                      ₹{row.refunds_inr.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="py-4 px-6 font-bold font-number">
                      {hasLoss ? (
                        <span className="text-[#B8522E] dark:text-[#E07A53] font-bold">
                          ₹{row.loss_detected_inr.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                      ) : (
                        <span className="text-[#787168] dark:text-[#A8A29E]">₹0.00</span>
                      )}
                    </td>
                    <td className="py-4 px-6 font-bold font-number text-right">
                      {row.amount_recovered_inr > 0 ? (
                        <span className="text-[#2D5A43] dark:text-[#4E9A70]">
                          ₹{row.amount_recovered_inr.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                      ) : (
                        <span className="text-[#787168] dark:text-[#A8A29E]">₹0.00</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
