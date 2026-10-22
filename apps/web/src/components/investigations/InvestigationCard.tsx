'use client';

import React from 'react';
import Link from 'next/link';
import { Compass, Clock, ArrowRight, ShieldCheck, AlertTriangle, Layers } from 'lucide-react';
import { Investigation } from '@/types';

interface InvestigationCardProps {
  investigation: Investigation;
}

export const InvestigationCard: React.FC<InvestigationCardProps> = ({ investigation }) => {
  const getStatusBadge = () => {
    switch (investigation.status) {
      case 'running':
        return (
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-cyan-950/60 text-cyber-cyan border border-cyber-cyan/30">
            <span className="w-1.5 h-1.5 rounded-full bg-cyber-cyan animate-ping"></span>
            <span>DISCOVERING</span>
          </span>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-emerald-950/60 text-cyber-emerald border border-cyber-emerald/30">
            <ShieldCheck className="w-3 h-3 text-cyber-emerald" />
            <span>COMPLETED</span>
          </span>
        );
      case 'cancelled':
        return (
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-slate-800 text-slate-400 border border-slate-700">
            <span>CANCELLED</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-amber-950/60 text-cyber-amber border border-cyber-amber/30">
            <Clock className="w-3 h-3 text-cyber-amber" />
            <span>PENDING</span>
          </span>
        );
    }
  };

  return (
    <div className="glass-panel glass-panel-hover rounded-xl p-5 border border-cyber-border flex flex-col justify-between group">
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          {getStatusBadge()}
          <span className="text-[11px] font-mono text-slate-400">
            {new Date(investigation.created_at).toLocaleDateString()}
          </span>
        </div>

        <h3 className="text-base font-bold text-white group-hover:text-cyber-cyan transition-colors line-clamp-1 mb-1">
          {investigation.title}
        </h3>

        <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono mb-4">
          <span className="px-1.5 py-0.5 rounded bg-cyber-card border border-cyber-border uppercase text-[10px] text-cyber-cyan">
            {investigation.clue_type}
          </span>
          <span className="truncate">Target: {investigation.target_clue}</span>
        </div>

        {/* Progress & Depth Bar */}
        <div className="space-y-1.5 mb-4">
          <div className="flex justify-between text-[11px] font-mono text-slate-400">
            <span className="flex items-center gap-1">
              <Layers className="w-3 h-3 text-slate-400" />
              Depth: {investigation.current_depth} / {investigation.max_depth}
            </span>
            <span>{investigation.progress_percent}%</span>
          </div>
          <div className="w-full h-1.5 bg-cyber-bg rounded-full overflow-hidden border border-cyber-border/40">
            <div
              className="h-full bg-gradient-to-r from-cyber-cyan to-cyber-emerald rounded-full transition-all duration-500"
              style={{ width: `${investigation.progress_percent}%` }}
            ></div>
          </div>
        </div>
      </div>

      <div className="pt-3 border-t border-cyber-border/60 flex items-center justify-between">
        <span className="text-[11px] text-slate-400 font-mono truncate max-w-[200px]">
          {investigation.stop_reason || 'In progress...'}
        </span>
        <Link
          href={`/investigations/${investigation.id}`}
          className="flex items-center space-x-1 text-xs font-semibold text-cyber-cyan hover:underline group-hover:translate-x-1 transition-transform"
        >
          <span>View Lead Graph</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
