import { fetchApi } from './api';
import { EvidenceItem, Finding } from '../types';

export interface FindingEvidenceResponse {
  finding_id: string;
  title: string;
  financial_impact: number;
  evidence_count: number;
  evidence: EvidenceItem[];
}

export async function getAnomalies(period?: string, year?: number, status?: string): Promise<Finding[]> {
  const queryParts: string[] = [];
  if (period) queryParts.push(`period=${encodeURIComponent(period)}`);
  if (year) queryParts.push(`year=${year}`);
  if (status) queryParts.push(`status=${encodeURIComponent(status)}`);

  const query = queryParts.length > 0 ? `?${queryParts.join('&')}` : '';
  return fetchApi<Finding[]>(`/api/anomalies${query}`);
}

export async function getAnomalyById(findingId: string, period?: string): Promise<Finding> {
  const query = period ? `?period=${encodeURIComponent(period)}` : '';
  return fetchApi<Finding>(`/api/anomalies/${encodeURIComponent(findingId)}${query}`);
}

export async function getAnomalyEvidence(findingId: string, period?: string): Promise<FindingEvidenceResponse> {
  const query = period ? `?period=${encodeURIComponent(period)}` : '';
  return fetchApi<FindingEvidenceResponse>(`/api/anomalies/${encodeURIComponent(findingId)}/evidence${query}`);
}
