import React, { useEffect, useRef, useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { TopAppBar } from './components/TopAppBar';
import { DetectAnomaliesView } from './components/DetectAnomaliesView';
import { StatementView } from './components/StatementView';
import { HistoryView } from './components/HistoryView';
import { ReportsView } from './components/ReportsView';
import { SettingsView } from './components/SettingsView';
import { SupportView } from './components/SupportView';
import { SendRequestModal } from './components/SendRequestModal';
import { RequestDetailModal } from './components/RequestDetailModal';
import { NewAuditModal } from './components/NewAuditModal';
import { ProfileModal } from './components/ProfileModal';
import { LoginView } from './components/LoginView';
import { Toast, ToastMessage } from './components/Toast';
import {
  DashboardSubTab,
  FinancialStatus,
  Finding,
  NavigationTab,
  PeriodInfo,
  PreviousRequest,
  RecoveryRequest,
  UserProfile,
} from './types';
import {
  ApiError,
  getAnomalies,
  getDashboardData,
  getRecoveryRequests,
  getSessionToken,
  getUserProfile,
  logout as logoutSession,
} from './services';
import { downloadReportPdf, downloadStatementCsv } from './services/workspaceService';
import { parseWorkspaceLocation, workspacePath } from './utils/workspaceNav';
import { remainingRecoveryInr } from './utils/money';

const initialRoute =
  typeof window !== 'undefined'
    ? parseWorkspaceLocation(window.location.pathname, window.location.search)
    : { tab: 'dashboard' as NavigationTab, sub: 'detect-anomalies' as DashboardSubTab, period: '2026_H2', isLogin: false };

export function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => Boolean(getSessionToken()));
  const [currentTab, setCurrentTab] = useState<NavigationTab>(initialRoute.tab);
  const [dashboardSubTab, setDashboardSubTab] = useState<DashboardSubTab>(initialRoute.sub);
  const [selectedPeriod, setSelectedPeriod] = useState<string>(initialRoute.period);

  const [anomalies, setAnomalies] = useState<Finding[]>([]);
  const [selectedAnomalyId, setSelectedAnomalyId] = useState<string>('');
  const [recoveryRequests, setRecoveryRequests] = useState<RecoveryRequest[]>([]);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [financialStatus, setFinancialStatus] = useState<FinancialStatus | null>(null);
  const [availablePeriods, setAvailablePeriods] = useState<PeriodInfo[]>([]);
  const [healthScore, setHealthScore] = useState<number>(62);
  const [totalLostAmount, setTotalLostAmount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [isSendRequestModalOpen, setIsSendRequestModalOpen] = useState(false);
  const [selectedRequestForDetail, setSelectedRequestForDetail] = useState<PreviousRequest | null>(null);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [selectedAnomalyForRequest, setSelectedAnomalyForRequest] = useState<Finding | null>(null);
  const [claimScope, setClaimScope] = useState<'period' | 'finding'>('period');
  const [isNewAuditModalOpen, setIsNewAuditModalOpen] = useState(false);

  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const liveDataRequestId = useRef(0);

  const clearPeriodScopedState = () => {
    setAnomalies([]);
    setFinancialStatus(null);
    setRecoveryRequests([]);
    setTotalLostAmount(0);
    setHealthScore(0);
    setSelectedAnomalyId('');
  };

  const addToast = (toast: Omit<ToastMessage, 'id'>) => {
    const id = `toast-${Date.now()}`;
    const newToast = { ...toast, id };
    setToasts((prev) => [...prev, newToast]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  };

  const handleDismissToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const syncUrl = (tab: NavigationTab, sub: DashboardSubTab, period: string, replace = false) => {
    const next = workspacePath(tab, sub, period);
    const current = `${window.location.pathname}${window.location.search}`;
    if (current === next) return;
    if (replace) {
      window.history.replaceState({ tab, sub, period }, '', next);
    } else {
      window.history.pushState({ tab, sub, period }, '', next);
    }
  };

  const selectTab = (tab: NavigationTab) => {
    setCurrentTab(tab);
    if (tab !== 'dashboard') {
      setDashboardSubTab('detect-anomalies');
      syncUrl(tab, 'detect-anomalies', selectedPeriod);
      return;
    }
    syncUrl(tab, dashboardSubTab, selectedPeriod);
  };

  const fetchLiveData = async (period: string, isStale?: () => boolean): Promise<boolean> => {
    const requestId = ++liveDataRequestId.current;
    const stale = () => isStale?.() === true || liveDataRequestId.current !== requestId;
    setIsLoading(true);
    setError(null);

    try {
      const [dashData, findings, reqs, profile] = await Promise.all([
        getDashboardData(period),
        getAnomalies(period),
        getRecoveryRequests(period),
        getUserProfile(period),
      ]);

      if (stale()) return false;

      const status = dashData.financial_status;
      if (status.period && status.period !== period) {
        return false;
      }

      setAnomalies(findings);
      setRecoveryRequests(reqs);
      setUserProfile(profile);
      setFinancialStatus({ ...status, period: status.period || period });
      if (dashData.available_periods && dashData.available_periods.length > 0) {
        setAvailablePeriods(dashData.available_periods);
      }
      setHealthScore(status.health_score);
      setTotalLostAmount(status.money_affected_inr ?? status.confirmed_loss_inr);

      const confirmed = findings.filter((f) => f.status.toLowerCase() === 'confirmed');
      if (confirmed.length > 0) {
        if (!confirmed.some((f) => (f.finding_id || f.id) === selectedAnomalyId)) {
          setSelectedAnomalyId(confirmed[0].finding_id || confirmed[0].id || '');
        }
      } else if (findings.length > 0) {
        setSelectedAnomalyId(findings[0].finding_id || findings[0].id || '');
      }
      return true;
    } catch (err: unknown) {
      if (stale()) return false;
      if (err instanceof ApiError && err.status === 401) {
        setIsAuthenticated(false);
        window.history.replaceState({}, '', '/login');
        return false;
      }
      const msg = err instanceof Error ? err.message : 'Unable to connect to financial server';
      setError(msg);
      addToast({
        type: 'error',
        title: 'Connection Issue',
        message: msg,
      });
      return false;
    } finally {
      if (!stale()) {
        setIsLoading(false);
      }
    }
  };

  useEffect(() => {
    if (!isAuthenticated) return;
    let cancelled = false;
    fetchLiveData(selectedPeriod, () => cancelled);
    return () => {
      cancelled = true;
    };
  }, [selectedPeriod, isAuthenticated]);

  useEffect(() => {
    const onUnauthorized = () => {
      setIsAuthenticated(false);
      if (window.location.pathname !== '/login') {
        window.history.replaceState({}, '', '/login');
      }
    };
    window.addEventListener('reclaim:unauthorized', onUnauthorized);
    return () => window.removeEventListener('reclaim:unauthorized', onUnauthorized);
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      if (window.location.pathname !== '/login') {
        window.history.replaceState({}, '', '/login');
      }
      return;
    }
    syncUrl(currentTab, dashboardSubTab, selectedPeriod, true);
  }, [isAuthenticated]);

  useEffect(() => {
    const onPopState = () => {
      const route = parseWorkspaceLocation(window.location.pathname, window.location.search);
      if (route.isLogin) {
        setIsAuthenticated(false);
        return;
      }
      setCurrentTab(route.tab);
      setDashboardSubTab(route.sub);
      if (route.period && route.period !== selectedPeriod) {
        liveDataRequestId.current += 1;
        setIsLoading(true);
        clearPeriodScopedState();
        setSelectedPeriod(route.period);
      }
    };
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, [selectedPeriod]);

  const handleChangePeriod = (period: string) => {
    if (period === selectedPeriod) return;
    liveDataRequestId.current += 1;
    setIsLoading(true);
    clearPeriodScopedState();
    setSelectedPeriod(period);
    syncUrl(currentTab, dashboardSubTab, period);
  };

  const confirmedAnomalies = anomalies.filter(
    (a) => a.status.toLowerCase() === 'confirmed'
  );

  const handleOpenSendRequest = (anomaly?: Finding) => {
    if (anomaly) {
      setSelectedAnomalyForRequest(anomaly);
      setClaimScope('finding');
    } else {
      setSelectedAnomalyForRequest(null);
      setClaimScope('period');
    }
    setIsSendRequestModalOpen(true);
  };

  const handleSendSuccess = (newRequest: PreviousRequest) => {
    setRecoveryRequests((prev) => [newRequest, ...prev.filter((r) => r.request_id !== newRequest.request_id)]);
    addToast({
      type: 'success',
      title: 'Recovery Request Sent',
      message: `Recovery request ${newRequest.request_id || newRequest.reference} recorded with verified audit evidence.`,
    });
    fetchLiveData(selectedPeriod);
  };

  const handleInvestigateAnomaly = (anomalyId: string) => {
    setSelectedAnomalyId(anomalyId);
    setCurrentTab('dashboard');
    setDashboardSubTab('detect-anomalies');
    syncUrl('dashboard', 'detect-anomalies', selectedPeriod);
  };

  const handleAuditComplete = () => {
    fetchLiveData(selectedPeriod);
    addToast({
      type: 'success',
      title: 'Audit Complete',
      message: `Audited all transactions for ${selectedPeriod.replace('_', ' ')}. Ledger is up to date.`,
    });
  };

  const handleExportCsv = async () => {
    try {
      await downloadStatementCsv(selectedPeriod);
      addToast({
        type: 'success',
        title: 'CSV downloaded',
        message: `Payment records for ${selectedPeriod.replace('_', ' ')} saved.`,
      });
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 401) return;
      addToast({
        type: 'error',
        title: 'Export failed',
        message: err instanceof Error ? err.message : 'Could not download the statement CSV.',
      });
    }
  };

  const handleExportPdf = async () => {
    try {
      await downloadReportPdf(selectedPeriod);
      addToast({
        type: 'success',
        title: 'PDF downloaded',
        message: `Period report for ${selectedPeriod.replace('_', ' ')} saved.`,
      });
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 401) return;
      addToast({
        type: 'error',
        title: 'Export failed',
        message: err instanceof Error ? err.message : 'Could not download the PDF report.',
      });
    }
  };

  const handleTriggerSync = async () => {
    const refreshed = await fetchLiveData(selectedPeriod);
    if (refreshed) {
      addToast({
        type: 'success',
        title: 'Ledger refreshed',
        message: 'Reloaded the current synthetic period from the audit engine.',
      });
    }
  };

  const handleDisconnect = () => {
    addToast({
      type: 'warning',
      title: 'Dataset connection paused',
      message: 'Automatic refresh paused. Re-enable the connection in Settings.',
    });
  };

  if (!isAuthenticated) {
    return (
      <LoginView
        onLoginSuccess={(enteredMerchantId, merchantName) => {
          setIsAuthenticated(true);
          setCurrentTab('dashboard');
          setDashboardSubTab('detect-anomalies');
          window.history.replaceState({}, '', workspacePath('dashboard', 'detect-anomalies', selectedPeriod));
          addToast({
            type: 'success',
            title: 'Workspace Active',
            message: `Signed in to ${merchantName || 'Zenzo Commerce'} (${enteredMerchantId || 'mid_demo_ZC771042'})`,
          });
        }}
      />
    );
  }

  const breadcrumbs =
    currentTab === 'settings'
      ? ['Settings', 'Connected Accounts']
      : currentTab === 'reports'
      ? ['Reports', `Audit Analytics (${selectedPeriod.replace('_', ' ')})`]
      : currentTab === 'history'
      ? ['Recovery Requests']
      : currentTab === 'support'
      ? ['Support', 'Help Center']
      : undefined;

  return (
    <div className="min-h-screen bg-[#F5F5F0] dark:bg-[#141311] text-[#1C1917] dark:text-[#F4F0E8] flex transition-colors duration-300 font-sans">
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <Sidebar
        currentTab={currentTab}
        onSelectTab={selectTab}
        onOpenNewAudit={() => setIsNewAuditModalOpen(true)}
        onOpenProfile={() => setIsProfileModalOpen(true)}
        anomaliesCount={confirmedAnomalies.length}
        isMobileOpen={isMobileSidebarOpen}
        onMobileClose={() => setIsMobileSidebarOpen(false)}
        merchantName={userProfile?.merchant_name}
        merchantId={userProfile?.merchant_id}
        initials={userProfile?.initials}
        demoStatus={userProfile?.demo_status}
      />

      <div className="flex-1 lg:ml-[300px] min-w-0 flex flex-col min-h-screen animate-workspace-entrance">
        <TopAppBar
          onOpenMobileSidebar={() => setIsMobileSidebarOpen(true)}
          currentTab={currentTab}
          dashboardSubTab={dashboardSubTab}
          onSelectDashboardSubTab={(sub) => {
            setCurrentTab('dashboard');
            setDashboardSubTab(sub);
            syncUrl('dashboard', sub, selectedPeriod);
          }}
          onOpenSendRequest={() => handleOpenSendRequest()}
          selectedPeriod={selectedPeriod}
          onChangePeriod={handleChangePeriod}
          breadcrumbs={breadcrumbs}
          unreadNotifications={recoveryRequests.length}
          recoveryRequests={recoveryRequests}
          onViewRequest={(req) => setSelectedRequestForDetail(req)}
          onNavigateToHistory={() => {
            setCurrentTab('history');
            syncUrl('history', 'detect-anomalies', selectedPeriod);
          }}
          availablePeriods={availablePeriods}
        />

        {error && (
          <div className="bg-[#FDF3ED] dark:bg-[#2A1810] border-b border-[#F0CFBF] dark:border-[#4A261A] px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-3 text-[15px] text-[#B8522E] dark:text-[#E07A53]">
            <div className="flex items-center gap-2 min-w-0">
              <span className="material-symbols-outlined text-[20px]" aria-hidden="true">cloud_off</span>
              <span>{error}</span>
            </div>
            <button
              type="button"
              onClick={() => fetchLiveData(selectedPeriod)}
              className="px-3 py-1 bg-[#1C1917] dark:bg-[#B8522E] text-[#FAF7F2] rounded-lg text-[15px] font-medium cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#B8522E]"
            >
              Retry
            </button>
          </div>
        )}

        <main id="main-content" className="flex-1 pb-16" tabIndex={-1}>
          {currentTab === 'dashboard' && (
            <>
              {dashboardSubTab === 'detect-anomalies' ? (
                <DetectAnomaliesView
                  key={selectedPeriod}
                  anomalies={anomalies}
                  selectedAnomalyId={selectedAnomalyId}
                  onSelectAnomaly={setSelectedAnomalyId}
                  onOpenSendRequest={handleOpenSendRequest}
                  onRecoverySent={handleSendSuccess}
                  onSwitchToStatement={() => {
                    setDashboardSubTab('statement');
                    syncUrl('dashboard', 'statement', selectedPeriod);
                  }}
                  healthScore={healthScore}
                  totalLostAmount={totalLostAmount}
                  isLoading={isLoading}
                  selectedPeriod={selectedPeriod}
                  financialStatus={financialStatus}
                />
              ) : (
                <StatementView
                  onSwitchToAnomalies={() => {
                    setDashboardSubTab('detect-anomalies');
                    syncUrl('dashboard', 'detect-anomalies', selectedPeriod);
                  }}
                  onExportCsv={handleExportCsv}
                  selectedPeriod={selectedPeriod}
                />
              )}
            </>
          )}

          {currentTab === 'history' && (
            <HistoryView
              requests={recoveryRequests}
              onViewRequest={(req) => setSelectedRequestForDetail(req)}
              isLoading={isLoading}
            />
          )}

          {currentTab === 'reports' && (
            <ReportsView
              key={selectedPeriod}
              selectedPeriod={selectedPeriod}
              onInvestigateAnomaly={handleInvestigateAnomaly}
              onExportPdf={handleExportPdf}
              financialStatus={financialStatus}
              anomalies={anomalies}
              feeRateLabel={
                userProfile?.contract?.fee_rate
                  ? `${(userProfile.contract.fee_rate * 100).toFixed(2)}% contracted MDR`
                  : 'Contracted MDR rate'
              }
              settlementBank={userProfile?.settlement_bank}
            />
          )}

          {currentTab === 'settings' && (
            <SettingsView
              onTriggerSync={handleTriggerSync}
              onDisconnect={handleDisconnect}
              profile={userProfile}
            />
          )}

          {currentTab === 'support' && <SupportView />}
        </main>
      </div>

      <SendRequestModal
        isOpen={isSendRequestModalOpen}
        onClose={() => setIsSendRequestModalOpen(false)}
        onSendSuccess={handleSendSuccess}
        initialAnomaly={selectedAnomalyForRequest}
        defaultClaimAmount={remainingRecoveryInr(
          financialStatus?.potential_recovery_inr ?? financialStatus?.potential_loss_inr,
          financialStatus?.recovery_requested_inr
        )}
        selectedPeriod={selectedPeriod}
        claimScope={claimScope}
      />

      <NewAuditModal
        isOpen={isNewAuditModalOpen}
        onClose={() => setIsNewAuditModalOpen(false)}
        onAuditComplete={handleAuditComplete}
        selectedPeriod={selectedPeriod}
      />

      <RequestDetailModal
        isOpen={selectedRequestForDetail !== null}
        onClose={() => setSelectedRequestForDetail(null)}
        request={selectedRequestForDetail}
      />

      <ProfileModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        profile={userProfile}
        onSignOut={async () => {
          try {
            await logoutSession();
          } catch {
            // session is cleared locally regardless
          }
          setIsProfileModalOpen(false);
          setIsAuthenticated(false);
        }}
      />

      <Toast toasts={toasts} onDismiss={handleDismissToast} />
    </div>
  );
}
export default App;
