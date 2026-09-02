import { fetchApi } from './api';
import { DashboardResponse, PeriodInfo } from '../types';

export async function getDashboardData(period?: string, year?: number): Promise<DashboardResponse> {
  const queryParts: string[] = [];
  if (period) queryParts.push(`period=${encodeURIComponent(period)}`);
  if (year) queryParts.push(`year=${year}`);
  const query = queryParts.length > 0 ? `?${queryParts.join('&')}` : '';
  return fetchApi<DashboardResponse>(`/api/dashboard${query}`);
}

export async function getAvailablePeriods(): Promise<PeriodInfo[]> {
  return fetchApi<PeriodInfo[]>('/api/dataset/periods');
}
