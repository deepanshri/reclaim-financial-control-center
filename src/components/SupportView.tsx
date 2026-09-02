import React, { useState } from 'react';
import { createSupportTicket } from '../services/workspaceService';

interface AuditStage {
  id: number;
  title: string;
  shortDesc: string;
  detailedDesc: string;
  icon: string;
  tag: string;
}

const AUDIT_STAGES: AuditStage[] = [
  {
    id: 1,
    title: 'Payment Received',
    shortDesc: 'We record customer payments.',
    detailedDesc: 'Every customer transaction from your store or checkout is logged with its timestamp, gross amount, and order ID.',
    icon: 'point_of_sale',
    tag: 'Step 1 · Ingestion',
  },
  {
    id: 2,
    title: 'Payment Checked',
    shortDesc: 'We compare with gateway records.',
    detailedDesc: 'We cross-reference the payment against Razorpay gateway reports to ensure the payment ID exists and was correctly processed.',
    icon: 'sync_alt',
    tag: 'Step 2 · Verification',
  },
  {
    id: 3,
    title: 'Money Reconciled',
    shortDesc: 'We check fees, refunds and bank deposits.',
    detailedDesc: 'We verify that MDR fee rates match your contracted rate, customer refunds were only deducted once, and bank deposits arrived on time.',
    icon: 'calculate',
    tag: 'Step 3 · Reconciliation',
  },
  {
    id: 4,
    title: 'Discrepancy Found & Evidence Prepared',
    shortDesc: 'We show what went wrong and prepare proof.',
    detailedDesc: 'If discrepancies are found, we calculate the exact lost amount and generate deterministic audit evidence ready for recovery with Razorpay desk.',
    icon: 'verified',
    tag: 'Step 4 · Resolution',
  },
];

export const SupportView: React.FC = () => {
  const [activeStageId, setActiveStageId] = useState<number>(1);
  const [ticketSubject, setTicketSubject] = useState('');
  const [ticketDescription, setTicketDescription] = useState('');
  const [ticketSubmitted, setTicketSubmitted] = useState(false);
  const [ticketError, setTicketError] = useState('');
  const [ticketId, setTicketId] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const activeStage = AUDIT_STAGES.find((s) => s.id === activeStageId) || AUDIT_STAGES[0];

  const handleSubmitTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticketSubject || !ticketDescription || isSubmitting) return;
    setIsSubmitting(true);
    setTicketError('');
    try {
      const created = await createSupportTicket(ticketSubject.trim(), ticketDescription.trim());
      setTicketId(created.ticket_id);
      setTicketSubmitted(true);
      setTicketSubject('');
      setTicketDescription('');
    } catch (err: unknown) {
      setTicketError(err instanceof Error ? err.message : 'Could not send the message.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      id="support-view-container"
      className="p-6 sm:p-8 lg:p-12 max-w-[1600px] mx-auto w-full space-y-10 text-[#1C1917] dark:text-[#F4F0E8] font-sans transition-all duration-300"
    >
      {/* Header */}
      <div className="border-b border-[#E2E2DC] dark:border-[#26221E] pb-6">
        <h1 className="font-display text-[30px] font-medium leading-[1.2] text-[#1C1917] dark:text-[#FAF7F2] sm:text-[36px]">
          Help &amp; Audit Guide
        </h1>
        <p className="text-[17px] text-[#57524C] dark:text-[#A8A29E] mt-1 font-sans">
          Understand how Reclaim continuously audits your Razorpay merchant records and contact our support desk.
        </p>
      </div>

      {/* 1. Interactive 4-Stage Audit Journey */}
      <div className="card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E2E2DC] dark:border-[#26221E] pb-4">
          <div>
            <span className="text-[14px] font-bold text-[#B8522E] dark:text-[#E07A53] uppercase tracking-wider block">
              How The Audit Works
            </span>
            <h2 className="text-[22px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2] mt-0.5">
              4-Step Automated Reconciliation Cycle
            </h2>
          </div>
          <span className="text-[15px] text-[#787168] dark:text-[#A8A29E]">
            Click any step to learn more
          </span>
        </div>

        {/* 4 Stage Interactive Stepper Rail */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {AUDIT_STAGES.map((stage) => {
            const isActive = stage.id === activeStageId;
            return (
              <div
                key={stage.id}
                onClick={() => setActiveStageId(stage.id)}
                className={`p-5 rounded-2xl border transition-all duration-200 cursor-pointer flex flex-col justify-between min-h-[140px] ${
                  isActive
                    ? 'bg-[#FAF9F5] dark:bg-[#201D1A] border-[#B8522E] shadow-sm'
                    : 'bg-[#FFFFFF] dark:bg-[#1A1815] border-[#E2E2DC] dark:border-[#2D2824] hover:border-[#D6D3D1]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-[14px] font-bold uppercase tracking-wider ${isActive ? 'text-[#B8522E] dark:text-[#E07A53]' : 'text-[#787168] dark:text-[#A8A29E]'}`}>
                    {stage.tag}
                  </span>
                  <span className={`material-symbols-outlined text-[22px] ${isActive ? 'text-[#B8522E] dark:text-[#E07A53]' : 'text-[#787168] dark:text-[#A8A29E]'}`}>
                    {stage.icon}
                  </span>
                </div>

                <div className="mt-3">
                  <h3 className="text-[17px] font-bold text-[#1C1917] dark:text-[#FAF7F2] leading-snug">
                    {stage.title}
                  </h3>
                  <p className="text-[15px] text-[#57524C] dark:text-[#A8A29E] mt-1 line-clamp-2">
                    {stage.shortDesc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Active Stage Detailed Banner */}
        <div className="p-5 rounded-2xl bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-[#B8522E]/10 dark:bg-[#B8522E]/20 text-[#B8522E] dark:text-[#E07A53] flex items-center justify-center shrink-0 mt-0.5">
            <span className="material-symbols-outlined text-[24px]">{activeStage.icon}</span>
          </div>
          <div>
            <span className="text-[17px] font-bold text-[#1C1917] dark:text-[#FAF7F2] block">
              {activeStage.tag}: {activeStage.title}
            </span>
            <p className="text-[16px] text-[#57524C] dark:text-[#A8A29E] mt-1 leading-relaxed font-sans">
              {activeStage.detailedDesc}
            </p>
          </div>
        </div>
      </div>

      {/* 2. Direct Assistance & Contact Audit Team Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
        {/* Left Column: Direct Assistance Info */}
        <div className="lg:col-span-5 card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-6 sm:p-8 space-y-6 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="w-11 h-11 rounded-2xl bg-[#EDF5F0] dark:bg-[#15241C] text-[#2D5A43] dark:text-[#4E9A70] flex items-center justify-center">
              <span className="material-symbols-outlined text-[26px]">support_agent</span>
            </div>
            <div>
              <span className="text-[14px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider block mb-1">
                Audit Assistance
              </span>
              <h2 className="text-[22px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2] leading-tight">
                Payment Audit &amp; Recovery Support
              </h2>
            </div>
            <p className="text-[#57524C] dark:text-[#A8A29E] text-[16px] leading-relaxed font-sans">
              Have questions about an identified payment issue or need assistance reviewing your Razorpay contract fees? Our financial audit specialists are here to assist.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] space-y-3">
            <div className="flex items-center gap-3 text-[16px]">
              <span className="material-symbols-outlined text-[20px] text-[#2D5A43] dark:text-[#4E9A70]">mail</span>
              <span className="font-semibold text-[#1C1917] dark:text-[#FAF7F2]">audit@reclaim.finance</span>
            </div>
            <div className="flex items-center gap-3 text-[16px]">
              <span className="material-symbols-outlined text-[20px] text-[#2D5A43] dark:text-[#4E9A70]">schedule</span>
              <span className="text-[#57524C] dark:text-[#A8A29E]">Mon–Fri, 9:00 AM – 6:00 PM IST</span>
            </div>
          </div>
        </div>

        {/* Right Column: Send a Message Form */}
        <div className="lg:col-span-7 card-elevation bg-[#FFFFFF] dark:bg-[#1A1815] border border-[#E2E2DC] dark:border-[#2D2824] rounded-3xl p-6 sm:p-8 space-y-5">
          <div>
            <h2 className="text-[22px] font-clash font-bold text-[#1C1917] dark:text-[#FAF7F2]">
              Send a Question to the Audit Team
            </h2>
            <p className="text-[16px] text-[#57524C] dark:text-[#A8A29E] mt-1 font-sans">
              We respond to all merchant payment and fee inquiries within one business day.
            </p>
          </div>

          {ticketSubmitted ? (
            <div className="p-6 rounded-2xl bg-[#EDF5F0] dark:bg-[#15241C] border border-[#CDE3D5] dark:border-[#1E382A] text-center space-y-2 animate-fade-in">
              <span className="material-symbols-outlined text-[34px] text-[#2D5A43] dark:text-[#4E9A70]">check_circle</span>
              <h3 className="text-[19px] font-bold text-[#1C1917] dark:text-[#FAF7F2]">
                Message Received
              </h3>
              <p className="text-[16px] text-[#2D5A43] dark:text-[#4E9A70] font-sans">
                Ticket {ticketId} was recorded. Our payment audit desk will review your query.
              </p>
              <button
                type="button"
                onClick={() => setTicketSubmitted(false)}
                className="text-[15px] font-medium text-[#2D5A43] underline cursor-pointer"
              >
                Send another message
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmitTicket} className="space-y-4">
              <div>
                <label htmlFor="support-subject" className="block text-[14px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider mb-1.5">
                  Subject
                </label>
                <input
                  id="support-subject"
                  type="text"
                  required
                  minLength={3}
                  value={ticketSubject}
                  onChange={(e) => setTicketSubject(e.target.value)}
                  placeholder="e.g. Question about contracted MDR fee schedule"
                  className="w-full px-4 py-2.5 bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-2xl text-[16px] text-[#1C1917] dark:text-[#FAF7F2] font-medium focus:outline-none focus:border-[#B8522E] transition-colors"
                />
              </div>

              <div>
                <label htmlFor="support-message" className="block text-[14px] font-bold text-[#787168] dark:text-[#A8A29E] uppercase tracking-wider mb-1.5">
                  Message Details
                </label>
                <textarea
                  id="support-message"
                  rows={4}
                  required
                  minLength={8}
                  value={ticketDescription}
                  onChange={(e) => setTicketDescription(e.target.value)}
                  placeholder="Describe your question, transaction ID, or specific settlement batch you would like us to check..."
                  className="w-full px-4 py-2.5 bg-[#FAF9F5] dark:bg-[#201D1A] border border-[#E2E2DC] dark:border-[#2D2824] rounded-2xl text-[16px] text-[#1C1917] dark:text-[#FAF7F2] font-medium focus:outline-none focus:border-[#B8522E] transition-colors resize-none"
                />
              </div>

              {ticketError ? (
                <p role="alert" className="text-[15px] font-medium text-[#B8522E]">
                  {ticketError}
                </p>
              ) : null}
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-6 py-3 bg-[#1C1917] dark:bg-[#B8522E] text-[#FAF7F2] rounded-2xl text-[16px] font-bold flex items-center justify-center gap-2 cursor-pointer shadow-xs hover:bg-[#2D2824] dark:hover:bg-[#A34423] transition-all disabled:opacity-60"
              >
                <span className="material-symbols-outlined text-[20px]">send</span>
                <span>{isSubmitting ? 'Sending…' : 'Send Message'}</span>
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
