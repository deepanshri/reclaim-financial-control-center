import React, { useEffect, useRef } from 'react';
import { PreviousRequest } from '../types';
import { ModalShell } from './ModalShell';

interface RequestDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  request: PreviousRequest | null;
}

export const RequestDetailModal: React.FC<RequestDetailModalProps> = ({
  isOpen,
  onClose,
  request,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && modalRef.current) {
      const focusableElements = modalRef.current.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      const firstElement = focusableElements[0] as HTMLElement;
      const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

      if (firstElement) {
        firstElement.focus();
      }

      const handleTabKey = (e: KeyboardEvent) => {
        if (e.key === 'Tab') {
          if (e.shiftKey) {
            if (document.activeElement === firstElement) {
              lastElement.focus();
              e.preventDefault();
            }
          } else {
            if (document.activeElement === lastElement) {
              firstElement.focus();
              e.preventDefault();
            }
          }
        }
      };

      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === 'Escape') onClose();
      };

      document.addEventListener('keydown', handleTabKey);
      document.addEventListener('keydown', handleEscape);
      return () => {
        document.removeEventListener('keydown', handleTabKey);
        document.removeEventListener('keydown', handleEscape);
      };
    }
  }, [isOpen, onClose]);

  const reqId = request?.request_id || request?.reference || '';
  const reqDate = request?.created_date || request?.date || '';
  const reqAmount = request?.amount_requested || request?.amount || 0;
  const isResolved = request?.status?.toLowerCase() === 'resolved';

  if (!request) {
    return (
      <ModalShell
        isOpen={false}
        onClose={onClose}
        panelClassName="hidden"
      >
        <div />
      </ModalShell>
    );
  }

  return (
    <ModalShell
      isOpen={isOpen}
      onClose={onClose}
      panelRef={modalRef}
      panelClassName="bg-[#FFFFFF] dark:bg-[#1A1815] rounded-2xl border border-[#E2E2DC] dark:border-[#2D2824] modal-elevation max-w-2xl w-full text-[#1C1917] dark:text-[#F4F0E8] font-sans"
    >
            {/* Header */}
            <div className="p-7 bg-[#1C1917] dark:bg-[#161412] text-[#FAF7F2] flex justify-between items-center border-b border-[#2D2824]">
              <div className="flex items-center gap-3.5">
                <div className="w-11 h-11 rounded-xl bg-[#282420] flex items-center justify-center text-[#FAF7F2] shadow-xs">
                  <span className="material-symbols-outlined text-[26px]">outgoing_mail</span>
                </div>
                <div>
                  <h2 className="text-[22px] font-clash font-bold text-[#FAF7F2]">
                    Recovery Request Details
                  </h2>
                  <p className="text-[15px] text-[#A8A29E] font-sans mt-0.5">
                    {reqId} • Sent on {reqDate}
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                aria-label="Close modal"
                className="text-[#A8A29E] hover:text-[#FAF7F2] p-2 rounded-xl hover:bg-[#282420] cursor-pointer transition-colors duration-150 active:scale-95"
              >
                <span className="material-symbols-outlined text-[24px]">close</span>
              </button>
            </div>

            {/* Content Body */}
            <div className="p-7 sm:p-8 space-y-5">
              <div className="flex justify-between items-center bg-[#F5F5F0] dark:bg-[#201D1A] p-4.5 rounded-2xl border border-[#E2E2DC] dark:border-[#2D2824]">
                <div>
                  <span className="block text-[14px] font-sans font-bold text-[#787168] dark:text-[#A8A29E] mb-1 uppercase tracking-wider">
                    Request Status
                  </span>
                  <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FFFFFF] dark:bg-[#1A1815] text-[#1C1917] dark:text-[#FAF7F2] text-[15px] font-semibold border border-[#E2E2DC] dark:border-[#2D2824] shadow-2xs font-sans">
                    <span className={`w-2 h-2 rounded-full ${isResolved ? 'bg-[#2D5A43] dark:bg-[#4E9A70]' : (request.status.toLowerCase().includes('not') || request.status.toLowerCase().includes('reject')) ? 'bg-[#DC2626]' : 'bg-[#B8731E] dark:bg-[#E5A33C]'}`}></span>
                    {isResolved ? 'Recovered' : (request.status.toLowerCase().includes('not') || request.status.toLowerCase().includes('reject')) ? 'Not Recovered' : 'Under Review'}
                  </span>
                </div>
                <div className="text-right">
                  <span className="block text-[14px] font-sans font-bold text-[#787168] dark:text-[#A8A29E] mb-1 uppercase tracking-wider">
                    {isResolved ? 'Recovered Amount' : 'Requested Recovery'}
                  </span>
                  <span className={`text-[24px] font-number font-bold ${isResolved ? 'text-[#2D5A43] dark:text-[#4E9A70]' : 'text-[#B8522E] dark:text-[#E07A53]'}`}>
                    ₹{(isResolved && request.amount_recovered ? request.amount_recovered : reqAmount).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-[14px] font-sans font-bold text-[#787168] dark:text-[#A8A29E] mb-1.5 uppercase tracking-wider">
                  Recipient
                </label>
                <div className="px-4 py-2.5 bg-[#F5F5F0] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-xl text-[16px] text-[#1C1917] dark:text-[#FAF7F2] font-sans">
                  {request.recipient || request.to || 'Razorpay Support'}
                </div>
              </div>

              <div>
                <label className="block text-[14px] font-sans font-bold text-[#787168] dark:text-[#A8A29E] mb-1.5 uppercase tracking-wider">
                  Subject &amp; Issue
                </label>
                <div className="px-4 py-2.5 bg-[#F5F5F0] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-xl text-[16px] text-[#1C1917] dark:text-[#FAF7F2] font-semibold">
                  {request.subject || request.issue}
                </div>
              </div>

              <div>
                <label className="block text-[14px] font-sans font-bold text-[#787168] dark:text-[#A8A29E] mb-1.5 uppercase tracking-wider">
                  Summary
                </label>
                <div className="px-4 py-3 bg-[#F5F5F0] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-xl text-[16px] text-[#44403C] dark:text-[#D6D3D1] leading-relaxed font-sans">
                  {request.summary}
                </div>
              </div>

              <div className="p-4 bg-[#F5F5F0] dark:bg-[#201D1A] rounded-xl border border-[#E2E2DC] dark:border-[#2D2824] space-y-2.5">
                <span className="text-[14px] font-sans font-bold text-[#787168] dark:text-[#A8A29E] block uppercase tracking-wider">
                  Proof Attached
                </span>
                <div className="flex flex-wrap gap-2 text-[15px] font-sans">
                  <span className="bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] px-3 py-1.5 rounded-lg text-[#44403C] dark:text-[#D6D3D1] flex items-center gap-1.5 shadow-2xs">
                    <span className="material-symbols-outlined text-[17px] text-[#2D5A43] dark:text-[#4E9A70]">table_chart</span>
                    payment_records.csv
                  </span>
                  <span className="bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] px-3 py-1.5 rounded-lg text-[#44403C] dark:text-[#D6D3D1] flex items-center gap-1.5 shadow-2xs">
                    <span className="material-symbols-outlined text-[17px] text-[#2D5A43] dark:text-[#4E9A70]">picture_as_pdf</span>
                    fee_contract_proof.pdf
                  </span>
                </div>
              </div>

              {/* Close Action */}
              <div className="pt-2 flex justify-end border-t border-[#E2E2DC] dark:border-[#26221E]">
                <button
                  type="button"
                  onClick={onClose}
                  className="btn-secondary-action px-6 py-2.5 bg-[#F5F5F0] dark:bg-[#201D1A] text-[#1C1917] dark:text-[#FAF7F2] rounded-xl text-[16px] font-medium cursor-pointer transition-colors border border-[#E2E2DC] dark:border-[#2D2824] hover:bg-[#EBEBE6] active:scale-98"
                >
                  Close
                </button>
              </div>
            </div>
    </ModalShell>
  );
};
