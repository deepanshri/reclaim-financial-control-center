import React, { useState } from 'react';
import { RecoveryRequest } from '../types';
import { useAnimatedNumber } from '../hooks/useAnimatedNumber';
import { MetricMoney } from './MetricMoney';

interface HistoryViewProps {
  requests: RecoveryRequest[];
  onViewRequest: (request: RecoveryRequest) => void;
  isLoading?: boolean;
}

export const HistoryView: React.FC<HistoryViewProps> = ({
  requests,
  onViewRequest,
  isLoading = false,
}) => {
  const [filterStatus, setFilterStatus] = useState<string>('All');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const resolvedRequests = requests.filter(
    (r) => r.status.toLowerCase() === 'resolved' || r.status.toLowerCase() === 'recovered'
  );
  const resolvedCount = resolvedRequests.length;

  const pendingRequests = requests.filter(
    (r) =>
      r.status.toLowerCase() === 'submitted' ||
      r.status.toLowerCase() === 'pending' ||
      r.status.toLowerCase() === 'under review' ||
      r.status.toLowerCase() === 'under_review'
  );
  const pendingCount = pendingRequests.length;

  const notRecoveredRequests = requests.filter(
    (r) =>
      r.status.toLowerCase() === 'not_recovered' ||
      r.status.toLowerCase() === 'not recovered' ||
      r.status.toLowerCase() === 'rejected' ||
      r.status.toLowerCase() === 'failed'
  );
  const notRecoveredCount = notRecoveredRequests.length;

  const totalRequested = requests.reduce(
    (sum, r) => sum + (r.amount_requested || 0),
    0
  );

  const totalRecovered = resolvedRequests.reduce(
    (sum, r) => sum + (r.amount_recovered || 0),
    0
  );

  const totalUnderReview = pendingRequests.reduce(
    (sum, r) => sum + (r.amount_requested || 0),
    0
  );

  const animatedTotal = useAnimatedNumber(requests.length, 700);
  const animatedResolved = useAnimatedNumber(resolvedCount, 700);
  const animatedPending = useAnimatedNumber(pendingCount, 700);

  const filteredRequests = requests.filter((req) => {
    const s = req.status.toLowerCase();
    let matchesStatus = true;
    if (filterStatus === 'Recovered') {
      matchesStatus = s === 'resolved' || s === 'recovered';
    } else if (filterStatus === 'Under Review') {
      matchesStatus = s === 'submitted' || s === 'pending' || s === 'under review' || s === 'under_review';
    } else if (filterStatus === 'Not Recovered') {
      matchesStatus = s === 'not_recovered' || s === 'not recovered' || s === 'rejected' || s === 'failed';
    }

    const refText = req.request_id || '';
    const subjText = req.subject || '';
    const toText = req.recipient || '';

    const matchesSearch =
      refText.toLowerCase().includes(searchTerm.toLowerCase()) ||
      subjText.toLowerCase().includes(searchTerm.toLowerCase()) ||
      toText.toLowerCase().includes(searchTerm.toLowerCase());

    return matchesStatus && matchesSearch;
  });

  return (
    <div id="history-view-container" className="p-8 lg:p-12 max-w-[1600px] mx-auto w-full space-y-10 text-[#1C1917] dark:text-[#F4F0E8] font-sans">
      {/* Header */}
      <div className="border-b border-[#E2E2DC] dark:border-[#26221E] pb-6 animate-entrance stagger-1">
        <div>
          <h1 className="font-display text-[32px] font-medium leading-[1.2] text-[#1C1917] dark:text-[#FAF7F2] sm:text-[38px]">
            Recovery Requests &amp; History
          </h1>
          <p className="text-[17px] text-[#57524C] dark:text-[#A8A29E] mt-1 font-sans">
            Track recovery requests sent to Razorpay for overcharged fees and uncredited payouts
          </p>
        </div>
      </div>

      {/* Summary KPI Panel */}
      <div className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-8 divide-y sm:divide-y-0 sm:divide-x divide-[#E2E2DC] dark:divide-[#26221E] grid grid-cols-1 sm:grid-cols-3 gap-8 sm:gap-0 animate-entrance stagger-2">
        <div className="sm:px-8 first:pl-0 space-y-2">
          <span className="text-[15px] font-sans text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider font-bold block">
            Requests Sent
          </span>
          <div className="text-[38px] font-sans font-bold text-[#1C1917] dark:text-[#FAF7F2] leading-none font-number">
            {animatedTotal}
          </div>
          <div className="pt-1 text-[#57524C] dark:text-[#A8A29E]">
            <MetricMoney
              value={totalRequested}
              className="text-[16px] text-[#57524C] dark:text-[#A8A29E]"
              exactClassName="mt-0.5 text-[12px] font-medium tabular-nums text-current/60 break-all"
            />
            <span className="text-[13px] text-[#787168] dark:text-[#A8A29E]">requested</span>
          </div>
        </div>

        <div className="sm:px-8 space-y-2">
          <span className="text-[15px] font-sans text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider font-bold block">
            Recovered
          </span>
          <div className="text-[38px] font-sans font-bold text-[#2D5A43] dark:text-[#4E9A70] leading-none font-number">
            {animatedResolved}
          </div>
          <div className="pt-1 text-[#2D5A43] dark:text-[#4E9A70]">
            <MetricMoney
              value={totalRecovered}
              className="text-[16px] text-[#2D5A43] dark:text-[#4E9A70]"
              exactClassName="mt-0.5 text-[12px] font-medium tabular-nums text-current/60 break-all"
            />
            <span className="text-[13px] text-[#2D5A43] dark:text-[#4E9A70]">recovered</span>
          </div>
        </div>

        <div className="sm:px-8 last:pr-0 space-y-2">
          <span className="text-[15px] font-sans text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider font-bold block">
            Under Review by Razorpay
          </span>
          <div className="text-[38px] font-sans font-bold text-[#B8731E] dark:text-[#E5A33C] leading-none font-number">
            {animatedPending}
          </div>
          <div className="pt-1 text-[#57524C] dark:text-[#A8A29E]">
            <MetricMoney
              value={totalUnderReview}
              className="text-[16px] text-[#57524C] dark:text-[#A8A29E]"
              exactClassName="mt-0.5 text-[12px] font-medium tabular-nums text-current/60 break-all"
            />
            <span className="text-[13px] text-[#787168] dark:text-[#A8A29E]">pending review</span>
          </div>
        </div>
      </div>

      {/* Filter & Search Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 animate-entrance stagger-3">
        <div className="relative flex-1 max-w-lg">
          <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-[24px] text-[#787168]">
            search
          </span>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by request ID or subject..."
            className="w-full bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-2xl pl-12 pr-5 py-3.5 text-[17px] text-[#1C1917] dark:text-[#FAF7F2] placeholder-[#787168] focus:outline-none focus:border-[#B8522E] card-elevation"
          />
        </div>

        <div className="flex items-center gap-3 overflow-x-auto pb-1 sm:pb-0">
          {['All', 'Recovered', 'Under Review', 'Not Recovered'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`filter-chip px-5 py-2.5 rounded-2xl text-[16px] font-semibold whitespace-nowrap cursor-pointer ${
                filterStatus === st ? 'is-active' : ''
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Requests List */}
      <div className="space-y-4 animate-entrance stagger-4">
        {isLoading ? (
          <div className="p-16 text-center text-[#787168] font-sans text-[18px]">Loading recovery requests...</div>
        ) : filteredRequests.length === 0 ? (
          <div className="p-16 text-center text-[#787168] font-sans text-[18px] bg-[#FFFFFF] dark:bg-[#1A1815] rounded-3xl border border-[#E2E2DC] dark:border-[#2D2824]">
            No recovery requests found matching your search.
          </div>
        ) : (
          filteredRequests.map((req) => {
            const s = req.status.toLowerCase();
            const isResolved = s === 'resolved' || s === 'recovered';
            const isNotRecovered = s === 'not_recovered' || s === 'not recovered' || s === 'rejected' || s === 'failed';
            const reqId = req.request_id;
            const amtReq = req.amount_requested;
            const amtRec = req.amount_recovered || 0;

            let badgeBg = 'bg-[#FEF7EC] text-[#B8731E] dark:bg-[#322414] dark:text-[#FCD34D] border border-[#F0CFBF] dark:border-[#4A261A]';
            let badgeText = 'Under Review';
            let badgeIcon = 'pending_actions';

            if (isResolved) {
              badgeBg = 'bg-[#EDF5F0] text-[#2D5A43] dark:bg-[#1C2E24] dark:text-[#6EE7B7] border border-[#CDE3D5] dark:border-[#1E382A]';
              badgeText = 'Recovered';
              badgeIcon = 'check_circle';
            } else if (isNotRecovered) {
              badgeBg = 'bg-[#FEE2E2] text-[#991B1B] dark:bg-[#381A1A] dark:text-[#F87171] border border-[#FECACA] dark:border-[#4A2020]';
              badgeText = 'Not Recovered';
              badgeIcon = 'cancel';
            }

            return (
              <button
                type="button"
                key={reqId}
                onClick={() => onViewRequest(req)}
                aria-label={`Open recovery request ${reqId}`}
                className="card-elevation card-interactive bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] hover:border-[#B8522E] dark:hover:border-[#E07A53] rounded-3xl p-6 sm:p-7 flex flex-col sm:flex-row sm:items-center justify-between gap-6 cursor-pointer text-left w-full"
              >
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-bold text-[16px] text-[#1C1917] dark:text-[#FAF7F2]">
                      {reqId}
                    </span>
                    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-[15px] font-sans font-bold ${badgeBg}`}>
                      <span className="material-symbols-outlined text-[16px]">{badgeIcon}</span>
                      {badgeText}
                    </span>
                    <span className="text-[15px] font-sans text-[#787168] dark:text-[#A8A29E]">
                      {req.created_date}
                    </span>
                  </div>

                  <h2 className="text-[19px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2]">
                    {req.subject}
                  </h2>
                  <p className="text-[17px] text-[#44403C] dark:text-[#D6D3D1] font-sans line-clamp-1 leading-relaxed">
                    {req.summary}
                  </p>
                </div>

                <div className="flex items-center justify-between sm:justify-end gap-6 pt-3 sm:pt-0 border-t sm:border-t-0 border-[#E2E2DC] dark:border-[#26221E]">
                  <div className="text-left sm:text-right">
                    <span className="text-[14px] font-sans text-[#787168] dark:text-[#A8A29E] uppercase font-bold block tracking-wider">
                      {isResolved ? 'Recovered Amount' : 'Requested Recovery'}
                    </span>
                    <span className={`font-sans text-[22px] font-bold font-number ${isResolved ? 'text-[#2D5A43] dark:text-[#4E9A70]' : 'text-[#B8522E] dark:text-[#E07A53]'}`}>
                      ₹{(isResolved ? amtRec : amtReq).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </div>

                  <span className="material-symbols-outlined text-[26px] text-[#787168] group-hover:text-[#1C1917]">
                    chevron_right
                  </span>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
};
