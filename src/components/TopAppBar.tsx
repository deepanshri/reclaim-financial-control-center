import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { DashboardSubTab, NavigationTab, PeriodInfo, RecoveryRequest } from '../types';
import { useTheme } from '../context/ThemeContext';
import { popoverSpring } from '../motion/presets';
import { PeriodSelector } from './PeriodSelector';

interface TopAppBarProps {
  onOpenMobileSidebar?: () => void;
  currentTab: NavigationTab;
  dashboardSubTab: DashboardSubTab;
  onSelectDashboardSubTab: (subTab: DashboardSubTab) => void;
  onOpenSendRequest?: () => void;
  selectedPeriod: string;
  onChangePeriod: (period: string) => void;
  breadcrumbs?: string[];
  unreadNotifications?: number;
  recoveryRequests?: RecoveryRequest[];
  onViewRequest?: (request: RecoveryRequest) => void;
  onNavigateToHistory?: () => void;
  availablePeriods?: PeriodInfo[];
}

export const TopAppBar: React.FC<TopAppBarProps> = ({
  currentTab,
  dashboardSubTab,
  onSelectDashboardSubTab,
  selectedPeriod,
  onChangePeriod,
  breadcrumbs,
  unreadNotifications = 0,
  recoveryRequests = [],
  onViewRequest,
  onNavigateToHistory,
  onOpenMobileSidebar,
  availablePeriods = [],
}) => {
  const { isDarkMode, toggleDarkMode } = useTheme();
  const [isNotificationsOpen, setIsNotificationsOpen] = React.useState(false);
  const [hasUnread, setHasUnread] = React.useState(true);
  const notificationRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (notificationRef.current && !notificationRef.current.contains(event.target as Node)) {
        setIsNotificationsOpen(false);
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsNotificationsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const formatCurrency = (amount: number) => {
    return `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const getStatusBadge = (status: string) => {
    const s = (status || '').toLowerCase();
    if (s === 'refunded' || s === 'resolved' || s === 'completed' || s === 'recovered') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[14px] font-sans font-bold bg-[#EDF5F0] dark:bg-[#15241C] text-[#2D5A43] dark:text-[#4E9A70] border border-[#CDE3D5] dark:border-[#1E382A]">
          <span className="material-symbols-outlined text-[15px]">check_circle</span>
          Recovered
        </span>
      );
    }
    if (s === 'under_review' || s === 'review' || s === 'in_review' || s === 'under review' || s === 'submitted' || s === 'pending') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[14px] font-sans font-bold bg-[#F0F4F8] dark:bg-[#16202A] text-[#2B5B84] dark:text-[#79B0DF] border border-[#CFDFEC] dark:border-[#1E3547]">
          <span className="material-symbols-outlined text-[15px]">pending_actions</span>
          Under Review
        </span>
      );
    }
    if (s === 'not_recovered' || s === 'not recovered' || s === 'rejected' || s === 'failed') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[14px] font-sans font-bold bg-[#FEE2E2] dark:bg-[#2D1616] text-[#991B1B] dark:text-[#F87171] border border-[#FECACA] dark:border-[#4A2020]">
          <span className="material-symbols-outlined text-[15px]">cancel</span>
          Not Recovered
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[14px] font-sans font-bold bg-[#FDF3ED] dark:bg-[#2A1810] text-[#B8522E] dark:text-[#E07A53] border border-[#F0CFBF] dark:border-[#4A261A]">
        <span className="material-symbols-outlined text-[15px]">send</span>
        Recovery Requested
      </span>
    );
  };

  return (
    <header
      id="top-app-bar"
      className="sticky top-0 z-40 flex h-20 items-center justify-between border-b border-[#E2E2DC] bg-[#F5F5F0]/95 px-6 font-ui transition-colors duration-300 backdrop-blur-md lg:px-10 dark:border-[#26221E] dark:bg-[#141311]/95"
    >
      {/* Left Area: Navigation Tabs or Breadcrumbs */}
      <div className="flex items-center gap-5 lg:gap-8">
        <button
          onClick={onOpenMobileSidebar}
          className="lg:hidden flex items-center text-[#787168] hover:text-[#1C1917] dark:hover:text-[#FAF7F2] cursor-pointer p-2"
          aria-label="Open mobile navigation"
        >
          <span className="material-symbols-outlined text-[30px]">menu</span>
        </button>

        {breadcrumbs && breadcrumbs.length > 0 ? (
          <nav className="flex items-center gap-2.5 text-[17px] text-[#787168] dark:text-[#9E978E] font-medium" aria-label="Breadcrumb">
            {breadcrumbs.map((crumb, idx) => (
              <React.Fragment key={idx}>
                {idx > 0 && (
                  <span className="material-symbols-outlined text-[20px] text-[#8C8273]">
                    chevron_right
                  </span>
                )}
                <span
                  className={
                    idx === breadcrumbs.length - 1
                      ? 'text-[#1C1917] dark:text-[#FAF7F2] font-bold'
                      : 'text-[#787168] dark:text-[#9E978E] hover:text-[#1C1917] dark:hover:text-[#FAF7F2] cursor-pointer transition-colors'
                  }
                >
                  {crumb}
                </span>
              </React.Fragment>
            ))}
          </nav>
        ) : (
          <div className="flex items-center gap-3">
            <button
              onClick={() => onSelectDashboardSubTab('detect-anomalies')}
              className={`px-4.5 py-2.5 rounded-2xl text-[17px] font-semibold transition-all duration-200 cursor-pointer ${
                dashboardSubTab === 'detect-anomalies'
                  ? 'bg-[#1C1917] text-[#FAF7F2] dark:bg-[#B8522E] dark:text-[#FAF7F2] shadow-sm'
                  : 'text-[#57524C] dark:text-[#A8A29E] hover:bg-[#EBEBE6] dark:hover:bg-[#201D1A]'
              }`}
            >
              Payment Issues
            </button>
            <button
              onClick={() => onSelectDashboardSubTab('statement')}
              className={`px-4.5 py-2.5 rounded-2xl text-[17px] font-semibold transition-all duration-200 cursor-pointer ${
                dashboardSubTab === 'statement'
                  ? 'bg-[#1C1917] text-[#FAF7F2] dark:bg-[#B8522E] dark:text-[#FAF7F2] shadow-sm'
                  : 'text-[#57524C] dark:text-[#A8A29E] hover:bg-[#EBEBE6] dark:hover:bg-[#201D1A]'
              }`}
            >
              Statement
            </button>
          </div>
        )}
      </div>

      {/* Right Area: Period Switcher, Dark Mode & Notifications */}
      <div className="flex items-center gap-3.5">
        <PeriodSelector
          selectedPeriod={selectedPeriod}
          availablePeriods={availablePeriods}
          onChangePeriod={(period) => {
            setIsNotificationsOpen(false);
            onChangePeriod(period);
          }}
        />

        {/* Large Dark Mode Quick Toggle */}
        <button
          id="btn-top-theme-toggle"
          onClick={toggleDarkMode}
          aria-label="Toggle Dark Mode"
          className="w-11 h-11 flex items-center justify-center rounded-2xl bg-[#FFFFFF] dark:bg-[#1E1B18] hover:bg-[#F5F5F0] dark:hover:bg-[#282420] text-[#787168] dark:text-[#9E978E] hover:text-[#1C1917] dark:hover:text-[#FAF7F2] transition-all duration-200 cursor-pointer active:scale-95 border border-[#E2E2DC] dark:border-[#2D2824] card-elevation"
          title={isDarkMode ? 'Switch to Light Warm Paper' : 'Switch to Dark Obsidian'}
        >
          <span className="material-symbols-outlined text-[24px]">
            {isDarkMode ? 'light_mode' : 'dark_mode'}
          </span>
        </button>

        {/* Notifications Popover Container */}
        <div className="relative" ref={notificationRef}>
          <button
            id="btn-notifications"
            aria-label="Notifications"
            aria-expanded={isNotificationsOpen}
            onClick={() => {
              setIsNotificationsOpen(!isNotificationsOpen);
            }}
            className="relative w-11 h-11 flex items-center justify-center rounded-2xl bg-[#FFFFFF] dark:bg-[#1E1B18] hover:bg-[#F5F5F0] dark:hover:bg-[#282420] text-[#787168] dark:text-[#9E978E] hover:text-[#1C1917] dark:hover:text-[#FAF7F2] transition-all duration-200 cursor-pointer border border-[#E2E2DC] dark:border-[#2D2824] card-elevation active:scale-95"
          >
            <span className="material-symbols-outlined text-[24px]">notifications</span>
            {hasUnread && (unreadNotifications > 0 || recoveryRequests.length > 0) && (
              <span className="absolute top-2.5 right-2.5 w-2.5 h-2.5 bg-[#B8522E] dark:bg-[#E07A53] border-2 border-[#FFFFFF] dark:border-[#1E1B18] rounded-full"></span>
            )}
          </button>

          {/* Notifications Dropdown Panel */}
          <AnimatePresence>
            {isNotificationsOpen && (
              <motion.div
                key="notifications-popover"
                id="notifications-popover"
                initial={{ opacity: 0, y: -8, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -6, scale: 0.97 }}
                transition={popoverSpring}
                className="absolute right-0 top-full mt-2.5 w-[420px] max-w-[92vw] bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl shadow-2xl overflow-hidden z-50"
              >
                {/* Header */}
                <div className="p-5 border-b border-[#E2E2DC] dark:border-[#26221E] flex items-center justify-between bg-[#F5F5F0]/50 dark:bg-[#201D1A]/50">
                  <div className="flex items-center gap-2.5">
                    <h3 className="text-[19px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2]">
                      Notifications
                    </h3>
                    <span className="px-2 py-0.5 rounded-full bg-[#1C1917] dark:bg-[#B8522E] text-[#FAF7F2] text-[14px] font-bold font-mono">
                      {recoveryRequests.length}
                    </span>
                  </div>
                  {hasUnread && (
                    <button
                      onClick={() => setHasUnread(false)}
                      className="text-[15px] font-semibold text-[#B8522E] dark:text-[#E07A53] hover:underline cursor-pointer"
                    >
                      Mark all as read
                    </button>
                  )}
                </div>

                {/* Notification Items List */}
                <div className="max-h-[380px] overflow-y-auto divide-y divide-[#E2E2DC] dark:divide-[#26221E]">
                  {recoveryRequests.length > 0 ? (
                    recoveryRequests.map((req) => {
                      const reqId = req.request_id || req.reference || 'REQ-2026-0891';
                      const amount = req.amount_requested || req.amount || 0;
                      const issueTitle = req.subject || req.summary || req.issue || 'Payment Recovery Request';
                      const date = req.created_date || req.date || 'Recent';

                      return (
                        <div
                          key={reqId}
                          onClick={() => {
                            if (onViewRequest) {
                              onViewRequest(req);
                              setIsNotificationsOpen(false);
                            } else if (onNavigateToHistory) {
                              onNavigateToHistory();
                              setIsNotificationsOpen(false);
                            }
                          }}
                          className="p-4.5 hover:bg-[#F5F5F0] dark:hover:bg-[#201D1A] transition-colors cursor-pointer space-y-2 group"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <span className="text-[15px] font-bold text-[#1C1917] dark:text-[#FAF7F2] font-mono group-hover:text-[#B8522E] dark:group-hover:text-[#E07A53] transition-colors">
                                {reqId}
                              </span>
                              {getStatusBadge(req.status)}
                            </div>
                            <span className="text-[14px] font-mono text-[#787168] dark:text-[#A8A29E]">
                              {date}
                            </span>
                          </div>

                          <p className="text-[15px] text-[#44403C] dark:text-[#D6D3D1] font-medium line-clamp-2">
                            {issueTitle}
                          </p>

                          <div className="flex items-center justify-between pt-1">
                            <div className="flex items-center gap-1.5 text-[15px]">
                              <span className="text-[#787168] dark:text-[#A8A29E]">Amount:</span>
                              <span className="font-mono font-bold text-[#1C1917] dark:text-[#FAF7F2]">
                                {formatCurrency(amount)}
                              </span>
                            </div>
                            <span className="text-[14px] font-semibold text-[#B8522E] dark:text-[#E07A53] flex items-center gap-0.5 group-hover:translate-x-0.5 transition-transform">
                              <span>View details</span>
                              <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                            </span>
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="p-8 text-center space-y-2">
                      <span className="material-symbols-outlined text-[38px] text-[#787168] dark:text-[#A8A29E]">
                        notifications_none
                      </span>
                      <h4 className="text-[17px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2]">
                        No Requests Yet
                      </h4>
                      <p className="text-[15px] text-[#787168] dark:text-[#A8A29E] max-w-xs mx-auto">
                        Sent and reviewed recovery requests will appear here with live resolution updates.
                      </p>
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div className="p-3.5 bg-[#F5F5F0]/70 dark:bg-[#201D1A]/70 border-t border-[#E2E2DC] dark:border-[#26221E] text-center">
                  <button
                    type="button"
                    onClick={() => {
                      if (onNavigateToHistory) {
                        onNavigateToHistory();
                        setIsNotificationsOpen(false);
                      }
                    }}
                    className="text-[15px] font-semibold text-[#1C1917] dark:text-[#FAF7F2] hover:text-[#B8522E] dark:hover:text-[#E07A53] flex items-center justify-center gap-1.5 w-full py-1.5 cursor-pointer transition-colors"
                  >
                    <span>View All Recovery Requests</span>
                    <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
};
