'use client';

import React, { useEffect, useState } from 'react';
import { CheckCircle2, Loader2, Sparkles, FileText, Search, ShieldCheck } from 'lucide-react';

interface AnalysisProgressProps {
  filename: string;
}

const STAGES = [
  { id: 1, label: 'Validating Document Format & Limits', icon: FileText, delay: 0 },
  { id: 2, label: 'Extracting Page Text & Mapping Boundaries', icon: Search, delay: 1800 },
  { id: 3, label: 'Running Substance Analysis with Groq AI', icon: Sparkles, delay: 4200 },
  { id: 4, label: 'Cross-Verifying Verbatim Citations', icon: ShieldCheck, delay: 9000 },
];

export default function AnalysisProgress({ filename }: AnalysisProgressProps) {
  const [currentStep, setCurrentStep] = useState(1);

  useEffect(() => {
    const t1 = setTimeout(() => setCurrentStep(2), 2000);
    const t2 = setTimeout(() => setCurrentStep(3), 4500);
    const t3 = setTimeout(() => setCurrentStep(4), 9500);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, []);

  return (
    <div className="w-full max-w-xl mx-auto bg-white rounded-2xl border border-surface-border p-8 shadow-sm space-y-6 text-center animate-in fade-in">
      {/* Icon Spinner */}
      <div className="mx-auto w-16 h-16 rounded-full bg-primary-light flex items-center justify-center text-primary relative">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>

      <div className="space-y-1">
        <h3 className="text-lg font-bold text-navy-900">Analyzing Document</h3>
        <p className="text-xs text-ink-muted truncate max-w-md mx-auto">{filename}</p>
      </div>

      {/* Steps List */}
      <div className="space-y-3 text-left max-w-md mx-auto pt-2">
        {STAGES.map((stage) => {
          const isDone = currentStep > stage.id;
          const isActive = currentStep === stage.id;
          const Icon = stage.icon;

          return (
            <div
              key={stage.id}
              className={`flex items-center space-x-3 p-3 rounded-lg border transition-all ${
                isActive
                  ? 'border-primary bg-primary-light/30 shadow-xs'
                  : isDone
                  ? 'border-emerald-200 bg-emerald-50/40 text-slate-700'
                  : 'border-surface-border bg-slate-50/50 opacity-60'
              }`}
            >
              <div className="flex-shrink-0">
                {isDone ? (
                  <CheckCircle2 className="w-5 h-5 text-status-success" />
                ) : isActive ? (
                  <Loader2 className="w-5 h-5 text-primary animate-spin" />
                ) : (
                  <Icon className="w-5 h-5 text-slate-400" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p
                  className={`text-xs font-semibold ${
                    isActive ? 'text-primary' : isDone ? 'text-navy-900' : 'text-slate-500'
                  }`}
                >
                  {stage.label}
                </p>
              </div>
              {isActive && (
                <span className="text-[10px] font-bold uppercase tracking-wider text-primary px-2 py-0.5 rounded-full bg-primary-light">
                  In Progress
                </span>
              )}
            </div>
          );
        })}
      </div>

      <p className="text-xs text-ink-muted italic">
        Processing in isolated server memory. Analysis typically takes 10 to 25 seconds depending on document length.
      </p>
    </div>
  );
}

