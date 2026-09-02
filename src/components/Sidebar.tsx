import React from 'react';
import { NavigationTab } from '../types';

interface SidebarProps {
  isMobileOpen?: boolean;
  onMobileClose?: () => void;
  currentTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  onOpenNewAudit: () => void;
  onOpenProfile?: () => void;
  anomaliesCount?: number;
  merchantName?: string;
  merchantId?: string;
  initials?: string;
  demoStatus?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  onOpenNewAudit,
  onOpenProfile = () => {},
  anomaliesCount = 0,
  isMobileOpen = false,
  onMobileClose = () => {},
  merchantName = 'Zenzo Commerce',
  merchantId = 'mid_demo_ZC771042',
  initials = 'ZC',
  demoStatus = 'Synthetic demo dataset',
}) => {
  return (
    <>
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-[#1C1917]/50 backdrop-blur-xs z-40 lg:hidden transition-opacity duration-300"
          onClick={onMobileClose}
        />
      )}
      <aside
        aria-label="Main navigation"
        id="side-nav-bar"
        className={`fixed left-0 top-0 z-40 flex h-dvh w-[300px] min-w-[300px] max-w-[300px] shrink-0 select-none flex-col border-r border-[#E2E2DC] bg-[#EBEBE6] px-5 py-7 font-ui text-[#1C1917] transition-transform duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] dark:border-[#26221E] dark:bg-[#181614] dark:text-[#F4F0E8] ${
          isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Brand & Company Identity */}
        <div className="space-y-4 mb-6">
          <div className="flex items-center gap-3.5 px-2 pt-1">
            <div className="w-11 h-11 rounded-2xl bg-[#1C1917] dark:bg-[#B8522E] flex items-center justify-center shrink-0 text-[#FAF7F2] shadow-md transition-transform duration-300 hover:scale-105">
              <span className="material-symbols-outlined text-[24px]">account_balance</span>
            </div>
            <div>
              <h1 className="font-heading text-[24px] font-semibold leading-tight text-[#1C1917] dark:text-[#FAF7F2]">
                Reclaim
              </h1>
              <p className="text-[15px] text-[#57524C] dark:text-[#A8A29E] font-medium">
                Financial Control Center
              </p>
            </div>
          </div>

          {/* Company / Account Card (Clickable Large Profile Tile) */}
          <button
            type="button"
            id="sidebar-company-tile"
            onClick={onOpenProfile}
            className="w-full text-left flex items-center justify-between p-3.5 rounded-2xl bg-[#FFFFFF] dark:bg-[#201D1A] hover:bg-[#F5F5F0] dark:hover:bg-[#282420] border border-[#E2E2DC] dark:border-[#2D2824] hover:border-[#B8522E] dark:hover:border-[#E07A53] transition-all duration-200 cursor-pointer group card-elevation active:scale-[0.98]"
            title="View Merchant Profile & Settings"
          >
            <div className="flex items-center gap-3 min-w-0">
              <div className="relative flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-full border border-[#D5D5CD] bg-[#E2E2DC] font-heading text-[16px] font-semibold text-[#1C1917] dark:border-[#3A342E] dark:bg-[#2D2824] dark:text-[#FAF7F2]">
                {initials}
                <span className="absolute bottom-0 right-0 w-3 h-3 bg-[#2D5A43] dark:bg-[#4E9A70] border-2 border-[#FFFFFF] dark:border-[#201D1A] rounded-full"></span>
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-[17px] font-bold text-[#1C1917] dark:text-[#FAF7F2] leading-tight truncate group-hover:text-[#B8522E] dark:group-hover:text-[#E07A53] transition-colors">
                  {merchantName}
                </span>
                <span className="text-[15px] text-[#57524C] dark:text-[#A8A29E] font-mono mt-0.5">
                  {merchantId}
                </span>
              </div>
            </div>
            <span className="material-symbols-outlined text-[22px] text-[#787168] dark:text-[#A8A29E] group-hover:text-[#1C1917] dark:group-hover:text-[#FAF7F2] transition-transform duration-200 group-hover:translate-x-1">
              chevron_right
            </span>
          </button>
        </div>

        {/* Large New Audit CTA Button */}
        <button
          id="btn-new-audit-sidebar"
          onClick={onOpenNewAudit}
          className="w-full btn-primary-action bg-[#1C1917] dark:bg-[#B8522E] text-[#FAF7F2] py-3.5 px-5 rounded-2xl font-semibold text-[17px] mb-6 flex items-center justify-center gap-2.5 cursor-pointer shadow-md hover:shadow-lg transition-all active:scale-[0.98]"
        >
          <span className="material-symbols-outlined text-[22px]">add_circle</span>
          <span>Review Payment Issues</span>
        </button>

        {/* Main Navigation */}
        <div className="flex-1 flex flex-col gap-1.5 overflow-y-auto pr-0.5">
          <div className="px-3.5 py-1.5 text-[14px] font-sans uppercase text-[#787168] dark:text-[#A8A29E] tracking-wider font-bold">
            Navigation
          </div>

          <button
            id="nav-dashboard"
            onClick={() => {
              onSelectTab('dashboard');
              onMobileClose();
            }}
            className={`w-full nav-tile-action flex items-center justify-between px-4 py-3.5 rounded-2xl text-[17px] font-medium transition-all duration-200 cursor-pointer ${
              currentTab === 'dashboard'
                ? 'bg-[#FFFFFF] dark:bg-[#201D1A] text-[#1C1917] dark:text-[#FAF7F2] card-elevation font-bold border border-[#E2E2DC] dark:border-[#2D2824]'
                : 'text-[#44403C] dark:text-[#D6D3D1] hover:bg-[#F5F5F0] dark:hover:bg-[#201D1A]'
            }`}
          >
            <div className="flex items-center gap-3">
              <span className={`material-symbols-outlined text-[24px] ${currentTab === 'dashboard' ? 'text-[#B8522E] dark:text-[#E07A53]' : 'text-[#787168] dark:text-[#A8A29E]'}`}>
                space_dashboard
              </span>
              <span>Dashboard</span>
            </div>
            {anomaliesCount > 0 && (
              <span className="px-2.5 py-1 rounded-full text-[15px] font-mono font-bold bg-[#FDF3ED] text-[#B8522E] dark:bg-[#2A1810] dark:text-[#E07A53] border border-[#F0CFBF] dark:border-[#4A261A]">
                {anomaliesCount}
              </span>
            )}
          </button>

          <button
            id="nav-history"
            onClick={() => {
              onSelectTab('history');
              onMobileClose();
            }}
            className={`w-full nav-tile-action flex items-center gap-3 px-4 py-3.5 rounded-2xl text-[17px] font-medium transition-all duration-200 cursor-pointer ${
              currentTab === 'history'
                ? 'bg-[#FFFFFF] dark:bg-[#201D1A] text-[#1C1917] dark:text-[#FAF7F2] card-elevation font-bold border border-[#E2E2DC] dark:border-[#2D2824]'
                : 'text-[#44403C] dark:text-[#D6D3D1] hover:bg-[#F5F5F0] dark:hover:bg-[#201D1A]'
            }`}
          >
            <span className={`material-symbols-outlined text-[24px] ${currentTab === 'history' ? 'text-[#B8522E] dark:text-[#E07A53]' : 'text-[#787168] dark:text-[#A8A29E]'}`}>
              history
            </span>
            <span>Recovery Requests</span>
          </button>

          <button
            id="nav-reports"
            onClick={() => {
              onSelectTab('reports');
              onMobileClose();
            }}
            className={`w-full nav-tile-action flex items-center gap-3 px-4 py-3.5 rounded-2xl text-[17px] font-medium transition-all duration-200 cursor-pointer ${
              currentTab === 'reports'
                ? 'bg-[#FFFFFF] dark:bg-[#201D1A] text-[#1C1917] dark:text-[#FAF7F2] card-elevation font-bold border border-[#E2E2DC] dark:border-[#2D2824]'
                : 'text-[#44403C] dark:text-[#D6D3D1] hover:bg-[#F5F5F0] dark:hover:bg-[#201D1A]'
            }`}
          >
            <span className={`material-symbols-outlined text-[24px] ${currentTab === 'reports' ? 'text-[#B8522E] dark:text-[#E07A53]' : 'text-[#787168] dark:text-[#A8A29E]'}`}>
              analytics
            </span>
            <span>Reports</span>
          </button>

          <div className="pt-5 px-3.5 py-1.5 text-[14px] font-sans uppercase text-[#787168] dark:text-[#A8A29E] tracking-wider font-bold">
            Settings &amp; Help
          </div>

          <button
            id="nav-settings"
            onClick={() => {
              onSelectTab('settings');
              onMobileClose();
            }}
            className={`w-full nav-tile-action flex items-center gap-3 px-4 py-3.5 rounded-2xl text-[17px] font-medium transition-all duration-200 cursor-pointer ${
              currentTab === 'settings'
                ? 'bg-[#FFFFFF] dark:bg-[#201D1A] text-[#1C1917] dark:text-[#FAF7F2] card-elevation font-bold border border-[#E2E2DC] dark:border-[#2D2824]'
                : 'text-[#44403C] dark:text-[#D6D3D1] hover:bg-[#F5F5F0] dark:hover:bg-[#201D1A]'
            }`}
          >
            <span className={`material-symbols-outlined text-[24px] ${currentTab === 'settings' ? 'text-[#B8522E] dark:text-[#E07A53]' : 'text-[#787168] dark:text-[#A8A29E]'}`}>
              tune
            </span>
            <span>Settings</span>
          </button>

          <button
            id="nav-support"
            onClick={() => {
              onSelectTab('support');
              onMobileClose();
            }}
            className={`w-full nav-tile-action flex items-center gap-3 px-4 py-3.5 rounded-2xl text-[17px] font-medium transition-all duration-200 cursor-pointer ${
              currentTab === 'support'
                ? 'bg-[#FFFFFF] dark:bg-[#201D1A] text-[#1C1917] dark:text-[#FAF7F2] card-elevation font-bold border border-[#E2E2DC] dark:border-[#2D2824]'
                : 'text-[#44403C] dark:text-[#D6D3D1] hover:bg-[#F5F5F0] dark:hover:bg-[#201D1A]'
            }`}
          >
            <span className={`material-symbols-outlined text-[24px] ${currentTab === 'support' ? 'text-[#B8522E] dark:text-[#E07A53]' : 'text-[#787168] dark:text-[#A8A29E]'}`}>
              help_outline
            </span>
            <span>Help</span>
          </button>
        </div>

        {/* Footer Status Info */}
        <div className="pt-4 border-t border-[#E2E2DC] dark:border-[#26221E] space-y-2">
          <div className="flex items-center justify-between text-[15px] text-[#787168] dark:text-[#9E978E] font-sans">
            <span className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#C27803] dark:bg-[#E59B22]"></span>
              Demo dataset
            </span>
            <span className="font-semibold" title={demoStatus}>
              6 Periods
            </span>
          </div>
        </div>
      </aside>
    </>
  );
};
