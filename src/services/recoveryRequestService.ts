import { fetchApi } from './api';
import { RecoveryRequest } from '../types';

export async function getRecoveryRequests(period?: string, status?: string): Promise<RecoveryRequest[]> {
  const queryParts: string[] = [];
  if (period) queryParts.push(`period=${encodeURIComponent(period)}`);
  if (status) queryParts.push(`status=${encodeURIComponent(status)}`);
  const query = queryParts.length > 0 ? `?${queryParts.join('&')}` : '';
  return fetchApi<RecoveryRequest[]>(`/api/recovery-requests${query}`);
}

export async function getRecoveryRequestById(requestId: string, period?: string): Promise<RecoveryRequest> {
  const query = period ? `?period=${encodeURIComponent(period)}` : '';
  return fetchApi<RecoveryRequest>(`/api/recovery-requests/${encodeURIComponent(requestId)}${query}`);
}

export interface CreateRecoveryPayload {
  period: string;
  summary: string;
  recipient?: string;
  subject?: string;
  finding_id?: string;
  claim_scope: 'period' | 'finding';
}

export async function createRecoveryRequest(payload: CreateRecoveryPayload): Promise<RecoveryRequest> {
  const idempotencyKey = `recovery:${payload.period}:${payload.claim_scope}:${payload.finding_id || 'all'}`;
  return fetchApi<RecoveryRequest>('/api/recovery-requests', {
    method: 'POST',
    headers: { 'Idempotency-Key': idempotencyKey },
    body: JSON.stringify(payload),
  });
}
