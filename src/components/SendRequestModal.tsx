import React, { useState, useEffect, useRef } from 'react';
import { Finding, PreviousRequest } from '../types';
import { ModalShell } from './ModalShell';
import { createRecoveryRequest } from '../services/recoveryRequestService';
import { formatINR } from '../utils/money';

interface SendRequestModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSendSuccess: (newRequest: PreviousRequest) => void;
  initialAnomaly?: Finding | null;
  defaultClaimAmount?: number;
  selectedPeriod: string;
  claimScope: 'period' | 'finding';
}

export const SendRequestModal: React.FC<SendRequestModalProps> = ({
  isOpen,
  onClose,
  onSendSuccess,
  initialAnomaly,
  defaultClaimAmount = 0,
  selectedPeriod,
  claimScope,
}) => {
  const [recipient, setRecipient] = useState('Razorpay Support (disputes@razorpay.com)');
  const formatClaim = (val: number) => formatINR(val);
  const [claimAmount, setClaimAmount] = useState(formatClaim(defaultClaimAmount));
  const [selectedIssue, setSelectedIssue] = useState('Combined period recovery');
  const [detailsText, setDetailsText] = useState(
    'Our settlement audit identified recovery-eligible findings in this period. Please review the attached evidence and credit the verified difference to our registered bank account.'
  );
  const [mailSubject, setMailSubject] = useState('Recovery claim for Combined period recovery');
  const [isSending, setIsSending] = useState(false);
  const [sendError, setSendError] = useState('');
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && modalRef.current) {
      const messageField = modalRef.current.querySelector(
        '#recovery-request-message'
      ) as HTMLTextAreaElement | null;
      const focusableElements = modalRef.current.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      const firstElement = (messageField || focusableElements[0]) as HTMLElement;
      const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

      if (messageField) {
        messageField.focus();
        const end = messageField.value.length;
        messageField.setSelectionRange(end, end);
      } else if (firstElement) {
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

      document.addEventListener('keydown', handleTabKey);
      return () => document.removeEventListener('keydown', handleTabKey);
    }
  }, [isOpen]);

  useEffect(() => {
    if (claimScope === 'finding' && initialAnomaly) {
      const impact =
        initialAnomaly.recoverable_amount_inr ??
        initialAnomaly.recoverable_amount ??
        initialAnomaly.financial_impact ??
        0;
      setClaimAmount(formatClaim(impact));
      setSelectedIssue(initialAnomaly.title || 'Payment discrepancy');

      const count = initialAnomaly.affected_transaction_count || initialAnomaly.affected_transactions || 1;
      setDetailsText(
        `Dispute finding ${initialAnomaly.finding_id || initialAnomaly.id}: ${
          initialAnomaly.simple_explanation || initialAnomaly.description || initialAnomaly.title
        } Affects ${count.toLocaleString('en-IN')} payment record(s). Please review the attached audit proof and credit ${formatINR(impact)}.`
      );
      setMailSubject(`Recovery claim for ${initialAnomaly.title || 'Payment discrepancy'}`);
    } else {
      setClaimAmount(formatClaim(defaultClaimAmount));
      setSelectedIssue(`Combined recovery · ${selectedPeriod.replace('_', ' ')}`);
      setDetailsText(
        `Combined recovery request for ${selectedPeriod.replace('_', ' ')}. Potential recovery ${formatINR(
          defaultClaimAmount
        )} is calculated from confirmed eligible findings in this period. Please review the attached audit proof and credit the verified amount.`
      );
      setMailSubject(`Recovery claim · Zenzo Commerce · ${selectedPeriod.replace('_', ' ')}`);
    }
    setSendError('');
  }, [initialAnomaly, isOpen, defaultClaimAmount, claimScope, selectedPeriod]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isSending) {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isSending, onClose]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!detailsText.trim() || !mailSubject.trim() || isSending) return;
    setIsSending(true);
    setSendError('');

    try {
      const created = await createRecoveryRequest({
        period: selectedPeriod,
        summary: detailsText.trim(),
        recipient,
        subject: mailSubject.trim() || `Recovery claim for ${selectedIssue}`,
        claim_scope: claimScope,
        finding_id: claimScope === 'finding' ? initialAnomaly?.finding_id || initialAnomaly?.id : undefined,
      });
      onSendSuccess({
        ...created,
        status: created.status || 'Submitted',
        amount: created.amount_requested,
        reference: created.request_id,
        to: created.recipient,
      });
      onClose();
    } catch (err: unknown) {
      setSendError(err instanceof Error ? err.message : 'Could not send the recovery request.');
    } finally {
      setIsSending(false);
    }
  };

  return (
    <ModalShell
      isOpen={isOpen}
      onClose={onClose}
      closeOnBackdrop={!isSending}
      panelRef={modalRef}
      labelledBy="recovery-request-title"
      panelClassName="bg-[#FFFFFF] dark:bg-[#1A1815] rounded-2xl border border-[#E2E2DC] dark:border-[#2D2824] modal-elevation max-w-xl w-full text-[#1C1917] dark:text-[#F4F0E8] font-sans"
    >
        {/* Modal Header */}
        <div className="p-6 bg-[#1C1917] dark:bg-[#161412] text-[#FAF7F2] flex justify-between items-center border-b border-[#2D2824]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#282420] text-[#FAF7F2] flex items-center justify-center">
              <span className="material-symbols-outlined text-[21px]">send</span>
            </div>
            <div>
              <h2 id="recovery-request-title" className="text-[20px] font-clash font-bold text-[#FAF7F2]">
                Recovery Request
              </h2>
              <p className="text-[15px] text-[#A8A29E] font-sans">
                Review and send recovery details to Razorpay
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isSending}
            aria-label="Close modal"
            className="text-[#A8A29E] hover:text-[#FAF7F2] p-1.5 rounded-lg hover:bg-[#282420] cursor-pointer transition-colors duration-150"
          >
            <span className="material-symbols-outlined text-[22px]">close</span>
          </button>
        </div>

        {/* Modal Form */}
        <form onSubmit={handleSend} className="p-6 sm:p-7 space-y-5">
          {/* Target Issue Banner */}
          <div className="p-4 bg-[#F5F5F0] dark:bg-[#201D1A] rounded-xl border border-[#E2E2DC] dark:border-[#2D2824] flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-[14px] font-semibold uppercase tracking-wider text-[#787168] dark:text-[#A8A29E] font-sans">
                Issue
              </span>
              <span className="text-[16px] font-sans font-bold text-[#1C1917] dark:text-[#FAF7F2] block">
                {selectedIssue}
              </span>
            </div>
            <div className="text-right">
              <span className="text-[14px] font-sans font-bold text-[#787168] dark:text-[#A8A29E] block uppercase">
                Potential Recovery
              </span>
              <span className="text-[18px] font-number font-bold text-[#B8522E] dark:text-[#E07A53]">
                {claimAmount}
              </span>
            </div>
          </div>

          {/* Recipient */}
          <div className="space-y-1.5">
            <label htmlFor="recovery-request-recipient" className="block text-[15px] font-sans font-bold text-[#787168] dark:text-[#A8A29E] uppercase">
              Send To
            </label>
            <input
              id="recovery-request-recipient"
              type="text"
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-[#F5F5F0] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-xl text-[16px] text-[#1C1917] dark:text-[#FAF7F2] font-sans focus:outline-none"
            />
          </div>

          <div className="space-y-1.5">
            <label htmlFor="recovery-request-subject" className="block text-[15px] font-sans font-bold text-[#787168] dark:text-[#A8A29E] uppercase">
              Subject
            </label>
            <input
              id="recovery-request-subject"
              type="text"
              value={mailSubject}
              onChange={(e) => setMailSubject(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-[#F5F5F0] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-xl text-[16px] text-[#1C1917] dark:text-[#FAF7F2] font-sans focus:outline-none"
            />
          </div>

          {/* Details / Message */}
          <div className="space-y-1.5">
            <label
              htmlFor="recovery-request-message"
              className="block text-[15px] font-sans font-medium text-[#57524C] dark:text-[#A8A29E]"
            >
              Why we're requesting this
            </label>
            <textarea
              id="recovery-request-message"
              name="recoveryMessage"
              rows={5}
              required
              value={detailsText}
              onChange={(e) => setDetailsText(e.target.value)}
              placeholder="Write the note Razorpay should read."
              className="w-full min-h-[128px] cursor-text resize-y rounded-md border border-[#C8C4BB] bg-white px-3.5 py-3 text-[16px] leading-relaxed text-[#1C1917] font-sans outline-none focus:border-[#1E4A73] focus:ring-2 focus:ring-[#1E4A73]/15 dark:border-[#3A342E] dark:bg-[#141311] dark:text-[#FAF7F2]"
            />
            <p className="text-[15px] text-[#6B655E] dark:text-[#A8A29E]">
              The claimed amount is calculated on the server from eligible findings. The note is stored with the request.
            </p>
            {sendError ? (
              <p role="alert" className="text-[15px] font-medium text-[#B8522E]">
                {sendError}
              </p>
            ) : null}
          </div>

          {/* Attached Proof Files Notice */}
          <div className="space-y-2">
            <span className="block text-[15px] font-sans font-bold text-[#787168] dark:text-[#A8A29E] uppercase">
              Proof Attached
            </span>
            <div className="flex flex-wrap gap-2 text-[15px] font-sans">
              <span className="px-3 py-1.5 rounded-lg bg-[#F5F5F0] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] text-[#44403C] dark:text-[#D6D3D1] flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[17px] text-[#2D5A43] dark:text-[#4E9A70]">description</span>
                payment_records.csv
              </span>
              <span className="px-3 py-1.5 rounded-lg bg-[#F5F5F0] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] text-[#44403C] dark:text-[#D6D3D1] flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[17px] text-[#2D5A43] dark:text-[#4E9A70]">picture_as_pdf</span>
                fee_contract_proof.pdf
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="pt-3 border-t border-[#E2E2DC] dark:border-[#26221E] flex items-center justify-between">
            <button
              type="button"
              onClick={onClose}
              disabled={isSending}
              className="btn-secondary-action px-5 py-2.5 bg-[#F5F5F0] dark:bg-[#201D1A] text-[#1C1917] dark:text-[#FAF7F2] rounded-xl text-[16px] font-medium cursor-pointer transition-colors border border-[#E2E2DC] dark:border-[#2D2824] hover:bg-[#EBEBE6]"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={isSending || !detailsText.trim() || !mailSubject.trim()}
              className="btn-primary-action px-6 py-2.5 bg-[#1C1917] dark:bg-[#B8522E] text-[#FAF7F2] rounded-xl text-[16px] font-medium flex items-center gap-2 cursor-pointer transition-all disabled:opacity-50 shadow-xs hover:shadow-md"
            >
              {isSending ? (
                <>
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  <span>Sending Request...</span>
                </>
              ) : (
                <>
                  <span>Send Recovery Request</span>
                  <span className="material-symbols-outlined text-[18px]">send</span>
                </>
              )}
            </button>
          </div>
        </form>
    </ModalShell>
  );
};
