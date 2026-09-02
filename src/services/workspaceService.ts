import { downloadFile, fetchApi } from './api';

export async function downloadStatementCsv(period: string): Promise<void> {
  await downloadFile(`/api/exports/statement.csv?period=${encodeURIComponent(period)}`, `reclaim-statement-${period}.csv`);
}

export async function downloadReportPdf(period: string): Promise<void> {
  await downloadFile(`/api/exports/report.pdf?period=${encodeURIComponent(period)}`, `reclaim-report-${period}.pdf`);
}

export async function runPeriodAudit(period: string): Promise<{ run_id: string; finding_count: number }> {
  return fetchApi('/api/audits', {
    method: 'POST',
    body: JSON.stringify({ period }),
  });
}

export interface WorkspaceSettings {
  fee_variance_percent: string;
  sla_delay_threshold_hours: string;
  auto_dispute_threshold: string;
  notification_email: string;
  razorpay_connected: boolean;
}

export async function getWorkspaceSettings(): Promise<WorkspaceSettings> {
  return fetchApi('/api/settings');
}

export async function saveWorkspaceSettings(payload: WorkspaceSettings): Promise<WorkspaceSettings> {
  return fetchApi('/api/settings', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export async function createSupportTicket(subject: string, description: string): Promise<{ ticket_id: string }> {
  return fetchApi('/api/support/tickets', {
    method: 'POST',
    body: JSON.stringify({ subject, description }),
  });
}
