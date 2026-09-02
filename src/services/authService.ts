import { fetchApi, setSessionToken } from './api';

export interface AuthSession {
  token: string;
  merchant_id: string;
  merchant_name: string;
  expires_at: string;
  dataset_type: string;
}

export async function login(merchantId: string, password: string): Promise<AuthSession> {
  const session = await fetchApi<AuthSession>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ merchant_id: merchantId, password }),
  });
  setSessionToken(session.token);
  return session;
}

export async function logout(): Promise<void> {
  try {
    await fetchApi('/api/auth/logout', { method: 'POST' });
  } finally {
    setSessionToken(null);
  }
}

export async function getCurrentSession(): Promise<{ merchant_id: string; merchant_name: string }> {
  return fetchApi('/api/auth/me');
}
