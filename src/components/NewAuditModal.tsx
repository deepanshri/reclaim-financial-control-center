import React, { useState, useEffect } from 'react';
import { ModalShell } from './ModalShell';
import { runPeriodAudit } from '../services/workspaceService';

interface NewAuditModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAuditComplete: () => void;
  selectedPeriod: string;
}

export const NewAuditModal: React.FC<NewAuditModalProps> = ({
  isOpen,
  onClose,
  onAuditComplete,
  selectedPeriod,
}) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isAuditing, setIsAuditing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [auditReady, setAuditReady] = useState(false);
  const [auditError, setAuditError] = useState('');

  const steps = [
    { title: '1. Find Issues', desc: 'Scanning your customer payments, fees, and refunds' },
    { title: '2. Check Why It Happened', desc: 'Comparing actual fees charged against your contracted MDR' },
    { title: '3. Calculate Money Lost', desc: 'Adding up the exact amount of extra fees and missing refunds' },
    { title: '4. Prepare Recovery Requests', desc: 'Creating proof documents so you can claim your money back' },
  ];

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isOpen && isAuditing) {
      if (currentStepIndex < steps.length) {
        timer = setTimeout(() => {
          setCurrentStepIndex((prev) => prev + 1);
          setProgress(((currentStepIndex + 1) / steps.length) * 100);
        }, 850);
      } else if (auditReady) {
        timer = setTimeout(() => {
          setIsAuditing(false);
          onAuditComplete();
          onClose();
        }, 500);
      }
    }
    return () => clearTimeout(timer);
  }, [isOpen, isAuditing, currentStepIndex, auditReady]);

  useEffect(() => {
    if (!isOpen) {
      setIsAuditing(false);
      setCurrentStepIndex(0);
      setProgress(0);
      setAuditReady(false);
      setAuditError('');
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isAuditing) {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isAuditing, onClose]);

  const handleStartAudit = async () => {
    setIsAuditing(true);
    setCurrentStepIndex(0);
    setProgress(15);
    setAuditReady(false);
    setAuditError('');
    try {
      await runPeriodAudit(selectedPeriod);
      setAuditReady(true);
      setProgress((prev) => Math.max(prev, 90));
    } catch (err: unknown) {
      setIsAuditing(false);
      setAuditReady(false);
      setAuditError(err instanceof Error ? err.message : 'The payment check could not be completed.');
    }
  };

  return (
    <ModalShell
      isOpen={isOpen}
      onClose={onClose}
      closeOnBackdrop={!isAuditing}
      backdropId="new-audit-modal"
      labelledBy="new-audit-title"
      panelClassName="bg-[#FCFAF6] dark:bg-[#1A1815] rounded-2xl border border-[#E5DFD3] dark:border-[#2D2824] modal-elevation max-w-2xl w-full text-[#1C1917] dark:text-[#F4F0E8]"
    >
            {/* Modal Header */}
            <div className="p-7 bg-[#1C1917] dark:bg-[#161412] text-[#FAF7F2] flex justify-between items-center border-b border-[#2D2824]">
              <div>
                <h3 id="new-audit-title" className="font-heading text-[22px] font-semibold tracking-normal text-[#FAF7F2]">
                  Review Payment Issues
                </h3>
                <p className="text-[15px] text-[#B8B0A2] mt-0.5 font-sans">
                  Checking your payments, fees, refunds, and bank deposits
                </p>
              </div>
              <button
                onClick={onClose}
                aria-label="Close modal"
                className="text-[#9E978E] hover:text-[#FAF7F2] p-2 rounded-xl hover:bg-[#282420] cursor-pointer transition-colors duration-150 active:scale-95"
              >
                <span className="material-symbols-outlined text-[24px]">close</span>
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-7 sm:p-8 space-y-6">
              {/* Progress bar */}
              <div>
                <div className="flex justify-between text-[15px] font-medium text-[#6E675D] dark:text-[#A8A196] mb-2 font-sans">
                  <span>Check Progress</span>
                  <span className="font-heading text-[16px] font-semibold text-[#1C1917] dark:text-[#FAF7F2]">{Math.round(progress)}%</span>
                </div>
                <div className="w-full h-2 bg-[#EAE4D8] dark:bg-[#282420] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#B8522E] dark:bg-[#E07A53] transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] rounded-full"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
              </div>

              {/* Steps list */}
              <div className="space-y-3">
                {steps.map((step, idx) => {
                  const isDone = isAuditing ? idx < currentStepIndex : false;
                  const isActive = isAuditing && idx === currentStepIndex;

                  return (
                    <div
                      key={idx}
                      className={`p-4 rounded-xl border transition-all duration-300 flex items-start gap-4 ${
                        isActive
                          ? 'bg-[#F4EFE6] dark:bg-[#201D1A] border-[#B8522E] dark:border-[#E07A53] shadow-xs'
                          : isDone
                          ? 'bg-[#EDF5F0] dark:bg-[#15241C] border-[#CDE3D5] dark:border-[#1E382A]'
                          : 'bg-[#F4EFE6]/50 dark:bg-[#201D1A]/50 border-[#E0DBD0] dark:border-[#2D2824]'
                      }`}
                    >
                      <div
                        className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5 text-[15px] font-mono font-medium transition-all duration-300 ${
                          isDone
                            ? 'bg-[#2D5A43] dark:bg-[#4E9A70] text-white'
                            : isActive
                            ? 'bg-[#B8522E] dark:bg-[#E07A53] text-white animate-pulse'
                            : 'bg-[#EAE4D8] dark:bg-[#282420] text-[#787168] dark:text-[#9E978E]'
                        }`}
                      >
                        {isDone ? (
                          <span className="material-symbols-outlined text-[17px]">check</span>
                        ) : (
                          idx + 1
                        )}
                      </div>
                      <div>
                        <h4
                          className={`text-[17px] font-medium leading-tight ${
                            isActive
                              ? 'text-[#1C1917] dark:text-[#FAF7F2] font-semibold'
                              : isDone
                              ? 'text-[#2D5A43] dark:text-[#4E9A70]'
                              : 'text-[#524C45] dark:text-[#C8BFB2]'
                          }`}
                        >
                          {step.title}
                        </h4>
                        <p className="text-[15px] text-[#6E675D] dark:text-[#A8A196] mt-1">{step.desc}</p>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Modal Actions */}
              {auditError ? (
                <p role="alert" className="text-[15px] font-medium text-[#B8522E]">
                  {auditError}
                </p>
              ) : null}
              <div className="pt-2 flex justify-end gap-3 border-t border-[#E5DFD3] dark:border-[#26221E]">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={isAuditing}
                  className="btn-secondary-action px-5 py-2.5 border border-[#E0DBD0] dark:border-[#2D2824] rounded-xl text-[15px] font-medium text-[#524C45] dark:text-[#C8BFB2] hover:bg-[#F4EFE6] dark:hover:bg-[#201D1A] cursor-pointer disabled:opacity-50 transition-colors active:scale-98"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleStartAudit}
                  disabled={isAuditing}
                  className="btn-primary-action px-6 py-2.5 bg-[#1C1917] dark:bg-[#B8522E] text-[#FAF7F2] hover:bg-[#2C2724] dark:hover:bg-[#A34424] rounded-xl text-[15px] font-medium flex items-center gap-2 cursor-pointer shadow-xs transition-all disabled:opacity-50 active:scale-98"
                >
                  <span className={`material-symbols-outlined text-[18px] ${isAuditing ? 'animate-spin' : ''}`}>
                    {isAuditing ? 'sync' : 'play_arrow'}
                  </span>
                  <span>{isAuditing ? 'Checking Payments...' : 'Start Payment Check'}</span>
                </button>
              </div>
            </div>
    </ModalShell>
  );
};
