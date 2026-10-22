'use client';

import React from 'react';
import { ExternalLink, CheckCircle2, AlertCircle, HelpCircle, ShieldAlert } from 'lucide-react';
import { EvidenceRecord } from '@/types';

interface EvidenceCardProps {
  evidence: EvidenceRecord;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ evidence }) => {
  const getConfidenceBadge = () => {
    switch (evidence.confidence_level) {
      case 'high':
        return (
          <span className="flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-950/70 text-emerald-300 border border-emerald-700/60">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            <span>CONFIDENCE: HIGH</span>
          </span>
        );
      case 'medium':
        return (
          <span className="flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-mono bg-cyan-950/70 text-cyan-300 border border-cyan-700/60">
            <HelpCircle className="w-3 h-3 text-cyan-400" />
            <span>CONFIDENCE: MEDIUM</span>
          </span>
        );
      case 'low':
        return (
          <span className="flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-mono bg-amber-950/70 text-amber-300 border border-amber-700/60">
            <AlertCircle className="w-3 h-3 text-amber-400" />
            <span>CONFIDENCE: LOW</span>
          </span>
        );
      default:
        return (
          <span className="flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
            <ShieldAlert className="w-3 h-3 text-slate-400" />
            <span>UNVERIFIED</span>
          </span>
        );
    }
  };

  return (
    <div className="glass-panel rounded-xl p-5 border border-cyber-border space-y-3 transition-all hover:border-slate-600">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h4 className="text-sm font-bold text-white line-clamp-1">{evidence.title}</h4>
        <div className="flex items-center space-x-2">
          {getConfidenceBadge()}
          <span className="text-[11px] font-mono text-slate-400 bg-cyber-card px-2 py-0.5 rounded border border-cyber-border">
            Rel: {(evidence.relevance_score * 100).toFixed(0)}% | Uncert: {(evidence.uncertainty_score * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Extracted Passage */}
      <blockquote className="text-xs text-slate-300 bg-cyber-bg/70 p-3 rounded-lg border-l-2 border-cyber-cyan font-mono leading-relaxed">
        "{evidence.extracted_passage}"
      </blockquote>

      {/* Inclusion Rationale */}
      <div className="flex items-start space-x-2 text-[11px] text-slate-400 bg-cyber-card/40 p-2.5 rounded-lg border border-cyber-border/40">
        <span className="font-mono text-cyber-cyan font-bold uppercase flex-shrink-0">Why Included:</span>
        <span className="leading-normal">{evidence.why_included}</span>
      </div>
    </div>
  );
};
