export type NavigationTab = 'dashboard' | 'history' | 'reports' | 'settings' | 'support';
export type DashboardSubTab = 'detect-anomalies' | 'statement';

export type PeriodKey =
  | '2024_H1'
  | '2024_H2'
  | '2025_H1'
  | '2025_H2'
  | '2026_H1'
  | '2026_H2';

export interface PeriodInfo {
  key: string;
  label: string;
  year: number;
  half: string;
  start: string;
  end: string;
  review_status: 'healthy' | 'needs_review' | 'action_needed' | 'action_required' | string;
  severity_level?: 'healthy' | 'needs_review' | 'action_needed' | string;
  severity_label?: string;
  severity_message?: string;
  is_action_required: boolean;
  confirmed_finding_count: number;
  confirmed_loss_inr: number;
}

export interface UserProfile {
  merchant_name: string;
  merchant_id: string;
  currency: string;
  payment_provider: string;
  dataset_period: {
    start: string;
    end: string;
    years: number[];
  };
  contract: {
    fee_rate: number;
    effective_from: string;
    effective_to: string;
  };
  demo_status: string;
  notes?: string;
  dataset_type?: string;
  finance_email?: string;
  settlement_bank?: string;
  initials?: string;
  // Aliases for components
  companyName?: string;
  connectedAccount?: string;
  email?: string;
  connectionStatus?: string;
  accountStatus?: string;
}

export interface EvidenceItem {
  evidence_id: string;
  source_record_id: string;
  transaction_id?: string;
  reference_id: string;
  date: string;
  method: string;
  gross_amount: number;
  expected_value: string | number;
  actual_value: string | number;
  difference: string | number;
  financial_impact: number;
  evidence_note: string;
  // Aliases
  transactionId?: string;
  amount?: number;
  expectedFee?: number;
  actualFee?: number;
}

export interface Finding {
  finding_id?: string;
  anomaly_id?: string;
  id?: string;
  type: string;
  status: string;
  title: string;
  description?: string;
  simple_explanation?: string;
  financial_impact?: number;
  financial_impact_inr?: number;
  recoverable_amount?: number;
  recoverable_amount_inr?: number;
  is_recovery_eligible?: boolean;
  recovery_ineligibility_reason?: string;
  currency?: string;
  affected_transaction_count?: number;
  affected_transactions?: number;
  detected_at?: string;
  start_date?: string;
  end_date?: string;
  confidence?: number;
  root_cause_reference?: string;
  source_record_ids?: string[];
  evidence_count?: number;
  evidence?: EvidenceItem[];
  evidence_logs?: EvidenceItem[];
  verification_method_a?: string;
  verification_method_b?: string;
  is_verified?: boolean;
  expected_value?: string | number;
  actual_value?: string | number;
  difference?: string | number;
  // Legacy aliases
  reference?: string;
  reference_id?: string;
  date?: string;
  detectedDate?: string;
  potentialImpact?: number;
  severity?: 'high' | 'medium' | 'low';
  whyItOccurred?: string;
  explanationDetails?: string;
  affectedTransactionsCount?: number;
  promoExpiryDate?: string;
  previousFee?: string;
  standardFee?: string;
  appliedFrom?: string;
  expectedFeeRate?: string;
  actualFeeRate?: string;
  evidenceLogs?: {
    transactionId: string;
    amount: number;
    expectedFee: number;
    actualFee: number;
    method?: string;
    date?: string;
  }[];
  additionalCount?: number;
}

export type Anomaly = Finding;

export interface FinancialStatus {
  period?: string;
  period_label?: string;
  period_start?: string;
  period_end?: string;
  year?: number | null;
  currency: string;
  total_payment_volume_inr: number;
  total_fees_inr: number;
  total_refunds_inr: number;
  total_settlements_inr: number;
  confirmed_loss_inr: number;
  money_affected_inr?: number;
  potential_recovery_inr?: number;
  /** Compatibility alias of potential_recovery_inr. Not Money Affected. */
  potential_loss_inr: number;
  recovery_requested_inr: number;
  recovered_inr: number;
  recovery_requests_count?: number;
  recovery_requested_amount?: number;
  recovered_requests_count?: number;
  recovered_amount?: number;
  under_review_count?: number;
  under_review_amount?: number;
  under_review_inr?: number;
  not_recovered_count?: number;
  not_recovered_amount?: number;
  not_recovered_inr?: number;
  confirmed_finding_count: number;
  under_review_finding_count: number;
  total_finding_count: number;
  health_score: number;
  severity_level?: 'healthy' | 'needs_review' | 'action_needed' | string;
  severity_label?: string;
  severity_message?: string;
  is_action_required?: boolean;
  review_status?: string;
}

export interface DashboardFindingSummary {
  finding_id: string;
  anomaly_id?: string;
  type: string;
  status: string;
  title: string;
  description: string;
  simple_explanation: string;
  financial_impact_inr: number;
  recoverable_amount_inr?: number;
  is_recovery_eligible?: boolean;
  recovery_ineligibility_reason?: string;
  affected_transaction_count: number;
  affected_transactions?: number;
  detected_at: string;
  confidence: number;
}

export interface DashboardResponse {
  financial_status: FinancialStatus;
  confirmed_findings: DashboardFindingSummary[];
  under_review_findings: DashboardFindingSummary[];
  available_periods?: PeriodInfo[];
  last_synced: string;
}

export interface StatementActivityItem {
  id: string;
  date: string;
  timestamp?: number;
  transaction_id?: string;
  type: 'Payment' | 'Fee' | 'Bank Deposit' | 'Refund' | 'Settlement' | 'Adjustment' | string;
  status: string;
  amount: number;
  is_negative?: boolean;
  fee_rate?: string;
  feeRate?: string;
  method?: string;
  transactionId?: string;
  isNegative?: boolean;
}

export type StatementLedgerItem = StatementActivityItem;

export interface StatementSummary {
  total_payments_inr: number;
  fees_deducted_inr: number;
  bank_deposits_inr: number;
  matching_rate_percent: number;
}

export interface StatementResponse {
  items: StatementActivityItem[];
  total: number;
  page: number;
  page_size: number;
  summary: StatementSummary;
  period?: string;
}

export interface RecoveryRequest {
  request_id?: string;
  finding_id?: string;
  created_date?: string;
  resolved_date?: string | null;
  status: string;
  amount_requested?: number;
  amount_recovered?: number;
  recipient?: string;
  subject?: string;
  summary?: string;
  evidence_count?: number;
  // Aliases
  id?: string;
  date?: string;
  issue?: string;
  amount?: number;
  reference?: string;
  to?: string;
  attachments?: {
    name: string;
    size: string;
    type: 'csv' | 'pdf' | 'json';
  }[];
}

export type PreviousRequest = RecoveryRequest;

export interface MonthlyReportItem {
  month: string;
  transaction_count: number;
  gross_volume_inr: number;
  fees_inr: number;
  refunds_inr: number;
  settlements_inr: number;
  loss_detected_inr: number;
  amount_recovered_inr: number;
}

export interface ReportsResponse {
  period?: string;
  year?: number | null;
  monthly_breakdown: MonthlyReportItem[];
  total_gross_volume_inr: number;
  total_fees_inr: number;
  total_refunds_inr: number;
  total_settlements_inr: number;
  total_loss_detected_inr: number;
  total_amount_recovered_inr: number;
}

export interface DatasetStatusResponse {
  merchant_name: string;
  payment_provider: string;
  dataset_start_date: string;
  dataset_end_date: string;
  payment_record_count: number;
  refund_record_count: number;
  settlement_record_count: number;
  reconciliation_record_count: number;
  confirmed_anomaly_count: number;
  under_review_anomaly_count: number;
  recovery_request_count: number;
}

export interface UnmatchedTransaction {
  id: string;
  txnId: string;
  time: string;
  date: string;
  gateway: string;
  source: string;
  varianceReason: string;
  amount: number;
  riskScore: 'High' | 'Medium' | 'Low';
  anomalyId?: string;
}

export interface SyncHistoryItem {
  id: string;
  dateTime: string;
  status: 'Success' | 'Partial' | 'Failed';
  recordsProcessed: string;
}

export interface DataMappingItem {
  sourceField: string;
  targetField: string;
  description: string;
}
