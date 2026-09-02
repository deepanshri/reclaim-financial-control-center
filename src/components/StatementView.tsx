import React, { useEffect, useState } from 'react';
import { StatementActivityItem, StatementSummary } from '../types';
import { getStatementData } from '../services/statementService';
import { useAnimatedNumber } from '../hooks/useAnimatedNumber';

interface StatementViewProps {
  selectedPeriod?: string;
  selectedMonth?: string;
  onSwitchToAnomalies: () => void;
  onExportCsv: () => void;
}

export const StatementView: React.FC<StatementViewProps> = ({
  selectedPeriod = '2026_H2',
  onSwitchToAnomalies,
  onExportCsv,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('All');
  const [currentPage, setCurrentPage] = useState(1);
  const [items, setItems] = useState<StatementActivityItem[]>([]);
  const [summary, setSummary] = useState<StatementSummary>({
    total_payments_inr: 0,
    fees_deducted_inr: 0,
    bank_deposits_inr: 0,
    matching_rate_percent: 100.0,
  });
  const [totalRecords, setTotalRecords] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryTick, setRetryTick] = useState(0);

  const PAGE_SIZE = 25;
  const periodLabel = selectedPeriod.replace('_', ' ');

  useEffect(() => {
    let isCancelled = false;
    const handle = window.setTimeout(async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await getStatementData({
          period: selectedPeriod,
          page: currentPage,
          pageSize: PAGE_SIZE,
          q: searchTerm.trim() || undefined,
        });
        if (!isCancelled) {
          setItems(response.items);
          setSummary(response.summary);
          setTotalRecords(response.total);
        }
      } catch (err: unknown) {
        if (!isCancelled) {
          const msg = err instanceof Error ? err.message : 'Failed to load statement ledger';
          setError(msg);
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }, searchTerm ? 280 : 0);
    return () => {
      isCancelled = true;
      window.clearTimeout(handle);
    };
  }, [selectedPeriod, currentPage, searchTerm, retryTick]);

  // Animated metric counters
  const animatedPayments = useAnimatedNumber(summary.total_payments_inr, 850);
  const animatedFees = useAnimatedNumber(summary.fees_deducted_inr, 850);
  const animatedSettlements = useAnimatedNumber(summary.bank_deposits_inr, 850);

  const filteredData = items.filter((item) => {
    const txId = item.transaction_id || item.id || '';
    const matchesSearch =
      txId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.date.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = typeFilter === 'All' || item.type === typeFilter;
    return matchesSearch && matchesType;
  });

  const totalPages = Math.ceil(totalRecords / PAGE_SIZE) || 1;

  return (
    <div id="statement-view-container" className="p-8 lg:p-12 max-w-[1600px] mx-auto w-full space-y-10 text-[#1C1917] dark:text-[#F4F0E8] font-sans">
      {/* Header & Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-5 border-b border-[#E2E2DC] dark:border-[#26221E] pb-6 animate-entrance stagger-1">
        <div>
          <h1 className="font-display text-[32px] font-medium leading-[1.2] text-[#1C1917] dark:text-[#FAF7F2] sm:text-[38px]">
            Statement
          </h1>
          <p className="text-[17px] text-[#57524C] dark:text-[#A8A29E] mt-1 font-sans">
            Your payment records for {periodLabel}. Bank deposits and refunds may show the actual T+1 date after the last calendar month.
          </p>
        </div>

        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={onExportCsv}
            className="btn-secondary-action px-6 py-3 rounded-2xl text-[17px] font-semibold flex items-center gap-2.5 cursor-pointer border border-[#D6D3D1] bg-[#FFFFFF] text-[#1C1917] hover:bg-[#F0EDE6] dark:border-[#3A342E] dark:bg-[#282420]! dark:text-[#FAF7F2]! dark:hover:bg-[#322C28]!"
          >
            <span className="material-symbols-outlined text-[22px]">download</span>
            <span>Download CSV</span>
          </button>
        </div>
      </div>

      {/* 4 Summary Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 animate-entrance stagger-2">
        <div className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-6 lg:p-7 space-y-2.5 overflow-hidden">
          <span className="text-[15px] lg:text-[15px] font-sans text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider font-bold block">
            Customer Payments
          </span>
          <div className="text-[21px] lg:text-[23px] xl:text-[28px] font-sans font-bold text-[#1C1917] dark:text-[#FAF7F2] font-number leading-tight tracking-normal">
            ₹{animatedPayments.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <span className="text-[15px] lg:text-[15px] text-[#2D5A43] dark:text-[#4E9A70] font-sans font-medium flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[18px]">check_circle</span>
            Total payments received
          </span>
        </div>

        <div className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-6 lg:p-7 space-y-2.5 overflow-hidden">
          <span className="text-[15px] lg:text-[15px] font-sans text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider font-bold block">
            Gateway Fees
          </span>
          <div className="text-[21px] lg:text-[23px] xl:text-[28px] font-sans font-bold text-[#B8522E] dark:text-[#E07A53] font-number leading-tight tracking-normal">
            ₹{animatedFees.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <span className="text-[15px] lg:text-[15px] text-[#57524C] dark:text-[#A8A29E] font-sans font-medium">
            Fees and GST paid
          </span>
        </div>

        <div className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-6 lg:p-7 space-y-2.5 overflow-hidden">
          <span className="text-[15px] lg:text-[15px] font-sans text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider font-bold block">
            Bank Deposits
          </span>
          <div className="text-[21px] lg:text-[23px] xl:text-[28px] font-sans font-bold text-[#2D5A43] dark:text-[#4E9A70] font-number leading-tight tracking-normal">
            ₹{animatedSettlements.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <span className="text-[15px] lg:text-[15px] text-[#2D5A43] dark:text-[#4E9A70] font-sans font-medium flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[18px]">account_balance</span>
            Money sent to your bank
          </span>
        </div>

        <div className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-6 lg:p-7 space-y-2.5 overflow-hidden">
          <span className="text-[15px] lg:text-[15px] font-sans text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider font-bold block">
            Verification Rate
          </span>
          <div className="text-[21px] lg:text-[23px] xl:text-[28px] font-sans font-bold text-[#1C1917] dark:text-[#FAF7F2] font-number leading-tight tracking-normal">
            {summary.matching_rate_percent.toFixed(1)}%
          </div>
          <span className="text-[15px] lg:text-[15px] text-[#57524C] dark:text-[#A8A29E] font-sans font-medium">
            Checked automatically
          </span>
        </div>
      </div>

      {/* Large Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 animate-entrance stagger-3">
        <div className="relative flex-1 max-w-lg">
          <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-[24px] text-[#787168]">
            search
          </span>
          <input
            id="statement-search"
            type="text"
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            placeholder="Search by Payment ID, UTR number, or date..."
            aria-label="Search statement records"
            className="w-full bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-2xl pl-12 pr-5 py-3.5 text-[17px] text-[#1C1917] dark:text-[#FAF7F2] placeholder-[#787168] focus:outline-none focus:border-[#B8522E] card-elevation"
          />
        </div>

        <div className="flex items-center gap-2.5 overflow-x-auto">
          {['All', 'Payment', 'Fee', 'Bank Deposit', 'Refund'].map((t) => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={`filter-chip px-4 py-2.5 rounded-2xl text-[16px] font-semibold cursor-pointer ${
                typeFilter === t ? 'is-active' : ''
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Large Ledger Table */}
      <div className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl overflow-hidden animate-entrance stagger-4">
        {isLoading ? (
          <div className="p-16 text-center text-[#787168] font-sans text-[18px]">Loading payments...</div>
        ) : error ? (
          <div className="p-16 text-center space-y-3">
            <p className="text-[#B8522E] font-sans text-[18px]">{error}</p>
            <button
              type="button"
              onClick={() => setRetryTick((n) => n + 1)}
              className="px-4 py-2 bg-[#1C1917] dark:bg-[#B8522E] text-[#FAF7F2] rounded-xl text-[15px] font-medium cursor-pointer"
            >
              Retry
            </button>
          </div>
        ) : filteredData.length === 0 ? (
          <div className="p-16 text-center text-[#787168] font-sans text-[18px]">
            {searchTerm.trim()
              ? 'No transactions found matching your search.'
              : 'No payment records are available for this period.'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[17px] border-collapse font-sans">
              <thead>
                <tr className="bg-[#F5F5F0] dark:bg-[#201D1A] text-[#787168] dark:text-[#A8A29E] border-b border-[#E2E2DC] dark:border-[#2D2824]">
                  <th className="py-4 px-6 font-bold">Date &amp; Time</th>
                  <th className="py-4 px-6 font-bold">Transaction ID</th>
                  <th className="py-4 px-6 font-bold">Type</th>
                  <th className="py-4 px-6 font-bold">Method / Rate</th>
                  <th className="py-4 px-6 font-bold">Status</th>
                  <th className="py-4 px-6 font-bold text-right">Amount (₹)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E2DC] dark:divide-[#2D2824]">
                {filteredData.map((item) => (
                  <tr key={item.id} className="hover:bg-[#FAF9F5] dark:hover:bg-[#1C1917] transition-colors">
                    <td className="py-4 px-6 font-sans text-[16px] text-[#44403C] dark:text-[#D6D3D1]">
                      {item.date}
                    </td>
                    <td className="py-4 px-6 font-sans font-bold text-[16px] text-[#1C1917] dark:text-[#FAF7F2] font-mono">
                      {item.transaction_id || item.id}
                    </td>
                    <td className="py-4 px-6">
                      <span className="inline-flex items-center px-3 py-1 rounded-xl text-[15px] font-semibold bg-[#F5F5F0] dark:bg-[#23201C] text-[#44403C] dark:text-[#D6D3D1]">
                        {item.type}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-[16px] text-[#57524C] dark:text-[#A8A29E] font-sans font-medium">
                      {item.fee_rate ? item.fee_rate : item.method || 'UPI'}
                    </td>
                    <td className="py-4 px-6 text-[16px]">
                      <span className="text-[#2D5A43] dark:text-[#4E9A70] font-bold">
                        {item.status}
                      </span>
                    </td>
                    <td className={`py-4 px-6 text-right font-sans font-bold text-[17px] font-number ${
                      item.is_negative
                        ? 'text-[#B8522E] dark:text-[#E07A53]'
                        : 'text-[#1C1917] dark:text-[#FAF7F2]'
                    }`}>
                      {item.is_negative ? '-' : '+'}₹{item.amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="py-4.5 px-6 bg-[#F5F5F0] dark:bg-[#201D1A] border-t border-[#E2E2DC] dark:border-[#2D2824] flex items-center justify-between text-[16px] text-[#57524C] dark:text-[#A8A29E]">
          <span>
            Showing {Math.min((currentPage - 1) * PAGE_SIZE + 1, totalRecords)} to{' '}
            {Math.min(currentPage * PAGE_SIZE, totalRecords)} of {totalRecords} transactions
          </span>
          <div className="flex items-center gap-3">
            <button
              disabled={currentPage <= 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              className="px-4 py-2 bg-[#FFFFFF] dark:bg-[#1E1B18] border border-[#E2E2DC] dark:border-[#2D2824] rounded-xl disabled:opacity-40 cursor-pointer font-medium card-elevation"
            >
              Previous
            </button>
            <span className="font-sans font-bold">{currentPage} / {totalPages}</span>
            <button
              disabled={currentPage >= totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              className="px-4 py-2 bg-[#FFFFFF] dark:bg-[#1E1B18] border border-[#E2E2DC] dark:border-[#2D2824] rounded-xl disabled:opacity-40 cursor-pointer font-medium card-elevation"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
