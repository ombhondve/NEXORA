'use client';

import React from 'react';
import { ExternalLink, CheckCircle2, AlertCircle, HelpCircle, ShieldAlert, Globe, Clock, Sparkles } from 'lucide-react';
import { EvidenceRecord } from '@/types';

interface EvidenceCardProps {
  evidence: EvidenceRecord;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ evidence }) => {
  const isSimulated = evidence.is_simulated || evidence.connector_name === 'mock_demo' || evidence.source_verification_status === 'simulated';

  const getVerificationBadge = () => {
    if (isSimulated) {
      return (
        <span className="flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono bg-rose-950/80 text-rose-300 border border-rose-700/60 font-semibold">
          <ShieldAlert className="w-3 h-3 text-rose-400" />
          <span>SIMULATED DEMO</span>
        </span>
      );
    }
    switch (evidence.source_verification_status) {
      case 'primary':
        return (
          <span className="flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950/80 text-emerald-300 border border-emerald-700/60 font-semibold">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            <span>PRIMARY SOURCE</span>
          </span>
        );
      case 'secondary':
        return (
          <span className="flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-950/80 text-cyan-300 border border-cyan-700/60">
            <Globe className="w-3 h-3 text-cyan-400" />
            <span>SECONDARY SOURCE</span>
          </span>
        );
      default:
        return (
          <span className="flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
            <HelpCircle className="w-3 h-3 text-slate-400" />
            <span>UNVERIFIED</span>
          </span>
        );
    }
  };

  const getConfidenceBadge = () => {
    switch (evidence.confidence_level) {
      case 'high':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950/70 text-emerald-300 border border-emerald-700/60">
            CONFIDENCE: HIGH
          </span>
        );
      case 'medium':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-950/70 text-cyan-300 border border-cyan-700/60">
            CONFIDENCE: MEDIUM
          </span>
        );
      case 'low':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-950/70 text-amber-300 border border-amber-700/60">
            CONFIDENCE: LOW
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
            UNVERIFIED
          </span>
        );
    }
  };

  return (
    <div className={`glass-panel rounded-xl p-5 border ${isSimulated ? 'border-rose-900/50 bg-rose-950/10' : 'border-cyber-border'} space-y-3 transition-all hover:border-slate-600`}>
      {/* Top Provenance Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-cyber-border/40">
        <div className="flex flex-wrap items-center gap-2">
          {evidence.connector_name && (
            <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-cyber-card text-cyber-cyan border border-cyber-border font-bold">
              {evidence.connector_name}
            </span>
          )}
          {getVerificationBadge()}
          {evidence.publication_date && (
            <span className="text-[10px] font-mono text-slate-400 flex items-center gap-1">
              <Clock className="w-2.5 h-2.5" /> Published: {evidence.publication_date}
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {getConfidenceBadge()}
          <span className="text-[10px] font-mono text-slate-400 bg-cyber-card px-2 py-0.5 rounded border border-cyber-border">
            Relevance: {(evidence.relevance_score * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Simulated Warning Banner */}
      {isSimulated && (
        <div className="p-2.5 bg-rose-950/40 rounded-lg border border-rose-800/60 text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>Simulated demo record generated for offline testing; excluded from verified findings.</span>
        </div>
      )}

      {/* Title & Clickable Source URL */}
      <div className="space-y-1">
        <h4 className="text-sm font-bold text-white line-clamp-1">{evidence.title}</h4>
        {evidence.source_url && (
          <a
            href={evidence.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center space-x-1.5 text-xs font-mono text-cyber-cyan hover:underline break-all"
          >
            <Globe className="w-3 h-3 flex-shrink-0" />
            <span className="truncate max-w-lg">{evidence.source_url}</span>
            <ExternalLink className="w-3 h-3 flex-shrink-0" />
          </a>
        )}
      </div>

      {/* Extracted Passage */}
      <blockquote className="text-xs text-slate-300 bg-cyber-bg/70 p-3 rounded-lg border-l-2 border-cyber-cyan font-mono leading-relaxed">
        &quot;{evidence.extracted_passage}&quot;
      </blockquote>

      {/* Inclusion Rationale */}
      <div className="flex items-start space-x-2 text-[11px] text-slate-400 bg-cyber-card/40 p-2.5 rounded-lg border border-cyber-border/40">
        <span className="font-mono text-cyber-cyan font-bold uppercase flex-shrink-0">Inclusion Rationale:</span>
        <span className="leading-normal">{evidence.why_included}</span>
      </div>
    </div>
  );
};
