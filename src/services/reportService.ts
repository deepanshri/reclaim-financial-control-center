import { fetchApi } from './api';
import { ReportsResponse } from '../types';

export async function getReportsData(period?: string, year?: number): Promise<ReportsResponse> {
  const queryParts: string[] = [];
  if (period) queryParts.push(`period=${encodeURIComponent(period)}`);
  if (year) queryParts.push(`year=${year}`);
  const query = queryParts.length > 0 ? `?${queryParts.join('&')}` : '';
  return fetchApi<ReportsResponse>(`/api/reports${query}`);
}
