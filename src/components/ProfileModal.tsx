import React, { useEffect, useRef } from 'react';
import { UserProfile } from '../types';
import { ModalShell } from './ModalShell';

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSignOut: () => void;
  profile?: UserProfile | null;
}

export const ProfileModal: React.FC<ProfileModalProps> = ({
  isOpen,
  onClose,
  onSignOut,
  profile,
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

  const merchantName = profile?.merchant_name || profile?.companyName || 'Zenzo Commerce';
  const merchantId = profile?.merchant_id || 'mid_demo_ZC771042';
  const feeRate = profile?.contract?.fee_rate ? `${(profile.contract.fee_rate * 100).toFixed(2)}%` : '—';
  const initials = profile?.initials || 'ZC';
  const financeEmail = profile?.finance_email || profile?.email || 'finance@zenzocommerce.in';
  const settlementBank = profile?.settlement_bank || 'ICICI Bank Current Account •••• 4412';
  const demoStatus = profile?.demo_status || 'Synthetic demo dataset';

  return (
    <ModalShell
      isOpen={isOpen}
      onClose={onClose}
      panelRef={modalRef}
      labelledBy="profile-modal-title"
      panelClassName="bg-[#FFFFFF] dark:bg-[#1A1815] rounded-2xl border border-[#E2E2DC] dark:border-[#2D2824] modal-elevation max-w-2xl w-full text-[#1C1917] dark:text-[#F4F0E8] font-sans"
    >
            {/* Header */}
            <div className="p-7 bg-[#1C1917] dark:bg-[#161412] text-[#FAF7F2] flex justify-between items-center border-b border-[#2D2824]">
              <div className="flex items-center gap-3.5">
                <div className="relative w-12 h-12 rounded-2xl bg-[#282420] border border-white/10 overflow-hidden shrink-0 flex items-center justify-center text-[#FAF7F2] font-clash font-bold text-[18px]">
                  {initials}
                  <span className="absolute bottom-1 right-1 w-2.5 h-2.5 bg-[#2D5A43] dark:bg-[#4E9A70] border-2 border-[#1C1917] rounded-full"></span>
                </div>
                <div>
                  <h2 id="profile-modal-title" className="text-[22px] font-clash font-bold text-[#FAF7F2]">
                    {merchantName}
                  </h2>
                  <p className="text-[15px] text-[#A8A29E] font-mono mt-0.5">
                    Merchant ID: {merchantId}
                  </p>
                  <p className="text-[14px] text-[#A8A29E] mt-0.5">{demoStatus}</p>
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
              {/* Account Overview Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4.5 bg-[#F5F5F0] dark:bg-[#201D1A] rounded-2xl border border-[#E2E2DC] dark:border-[#2D2824]">
                  <span className="text-[14px] font-sans font-bold text-[#787168] dark:text-[#A8A29E] block mb-1 uppercase tracking-wider">
                    Payment Gateway
                  </span>
                  <span className="text-[16px] font-semibold text-[#1C1917] dark:text-[#FAF7F2] flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[#2D5A43] dark:bg-[#4E9A70]"></span>
                    Razorpay (demo dataset)
                  </span>
                </div>

                <div className="p-4.5 bg-[#F5F5F0] dark:bg-[#201D1A] rounded-2xl border border-[#E2E2DC] dark:border-[#2D2824]">
                  <span className="text-[14px] font-sans font-bold text-[#787168] dark:text-[#A8A29E] block mb-1 uppercase tracking-wider">
                    Contract Rate
                  </span>
                  <span className="text-[16px] font-mono font-bold text-[#2D5A43] dark:text-[#4E9A70] flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[19px]">verified</span>
                    {feeRate} MDR
                  </span>
                </div>
              </div>

              {/* Account Details */}
              <div className="space-y-4">
                <div>
                  <label className="block text-[14px] font-sans font-bold text-[#787168] dark:text-[#A8A29E] mb-1.5 uppercase tracking-wider">
                    Finance Contact Email
                  </label>
                  <div className="px-4 py-2.5 bg-[#F5F5F0] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-xl text-[16px] text-[#1C1917] dark:text-[#FAF7F2] font-sans">
                    {financeEmail}
                  </div>
                </div>

                <div>
                  <label className="block text-[14px] font-sans font-bold text-[#787168] dark:text-[#A8A29E] mb-1.5 uppercase tracking-wider">
                    Razorpay Merchant ID
                  </label>
                  <div className="px-4 py-2.5 bg-[#F5F5F0] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-xl text-[16px] text-[#1C1917] dark:text-[#FAF7F2] font-mono">
                    {merchantId}
                  </div>
                </div>

                <div>
                  <label className="block text-[14px] font-sans font-bold text-[#787168] dark:text-[#A8A29E] mb-1.5 uppercase tracking-wider">
                    Settlement Bank Account
                  </label>
                  <div className="px-4 py-2.5 bg-[#F5F5F0] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-xl text-[16px] text-[#1C1917] dark:text-[#FAF7F2] flex items-center justify-between">
                    <span className="font-sans text-[15px] font-medium">{settlementBank}</span>
                    <span className="text-[14px] font-sans font-bold text-[#C27803] dark:text-[#E59B22] bg-[#FEF7EC] dark:bg-[#322414] border border-[#F0CFBF] dark:border-[#4A261A] px-2.5 py-0.5 rounded-lg">
                      Demo
                    </span>
                  </div>
                </div>
              </div>

              {/* Modal Actions */}
              <div className="pt-3 border-t border-[#E2E2DC] dark:border-[#26221E] flex justify-between items-center">
                <button
                  type="button"
                  onClick={onSignOut}
                  className="text-[16px] font-medium text-[#B8522E] dark:text-[#E07A53] hover:text-[#963C1B] flex items-center gap-1.5 cursor-pointer transition-colors p-2 rounded-xl hover:bg-[#FDF3ED] dark:hover:bg-[#2A1810] active:scale-95"
                >
                  <span className="material-symbols-outlined text-[20px]">logout</span>
                  <span>Sign Out</span>
                </button>

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
