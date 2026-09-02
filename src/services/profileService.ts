import { fetchApi } from './api';
import { DatasetStatusResponse, UserProfile } from '../types';

export async function getUserProfile(period?: string): Promise<UserProfile> {
  const query = period ? `?period=${encodeURIComponent(period)}` : '';
  return fetchApi<UserProfile>(`/api/merchant${query}`);
}

export async function getDatasetStatus(period?: string): Promise<DatasetStatusResponse> {
  const query = period ? `?period=${encodeURIComponent(period)}` : '';
  return fetchApi<DatasetStatusResponse>(`/api/dataset/status${query}`);
}
