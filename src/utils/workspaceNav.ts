import { DashboardSubTab, NavigationTab } from '../types';

export interface WorkspaceRoute {
  tab: NavigationTab;
  sub: DashboardSubTab;
  period: string;
  isLogin: boolean;
}

const DEFAULT_PERIOD = '2026_H2';

export function parseWorkspaceLocation(pathname: string, search: string): WorkspaceRoute {
  const params = new URLSearchParams(search);
  const period = params.get('period') || DEFAULT_PERIOD;
  if (pathname === '/login') {
    return { tab: 'dashboard', sub: 'detect-anomalies', period, isLogin: true };
  }
  if (pathname === '/statement') {
    return { tab: 'dashboard', sub: 'statement', period, isLogin: false };
  }
  if (pathname === '/recovery') {
    return { tab: 'history', sub: 'detect-anomalies', period, isLogin: false };
  }
  if (pathname === '/reports') {
    return { tab: 'reports', sub: 'detect-anomalies', period, isLogin: false };
  }
  if (pathname === '/settings') {
    return { tab: 'settings', sub: 'detect-anomalies', period, isLogin: false };
  }
  if (pathname === '/help') {
    return { tab: 'support', sub: 'detect-anomalies', period, isLogin: false };
  }
  return { tab: 'dashboard', sub: 'detect-anomalies', period, isLogin: false };
}

export function workspacePath(tab: NavigationTab, sub: DashboardSubTab, period: string): string {
  let path = '/issues';
  if (tab === 'dashboard' && sub === 'statement') path = '/statement';
  else if (tab === 'history') path = '/recovery';
  else if (tab === 'reports') path = '/reports';
  else if (tab === 'settings') path = '/settings';
  else if (tab === 'support') path = '/help';
  return `${path}?period=${encodeURIComponent(period)}`;
}
