import { fetchApi } from './api';
import { StatementResponse } from '../types';

export interface StatementParams {
  period?: string;
  year?: number;
  month?: string;
  page?: number;
  pageSize?: number;
  q?: string;
}

export async function getStatementData(params?: StatementParams): Promise<StatementResponse> {
  const queryParts: string[] = [];
  if (params?.period) queryParts.push(`period=${encodeURIComponent(params.period)}`);
  if (params?.year) queryParts.push(`year=${params.year}`);
  if (params?.month) queryParts.push(`month=${encodeURIComponent(params.month)}`);
  if (params?.page) queryParts.push(`page=${params.page}`);
  if (params?.pageSize) queryParts.push(`page_size=${params.pageSize}`);
  if (params?.q) queryParts.push(`q=${encodeURIComponent(params.q)}`);

  const queryString = queryParts.length > 0 ? `?${queryParts.join('&')}` : '';
  return fetchApi<StatementResponse>(`/api/statement${queryString}`);
}
