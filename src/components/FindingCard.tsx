'use client';

import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  FileText,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  ExternalLink,
  ShieldCheck,
  Scale,
} from 'lucide-react';

interface FindingCardProps {
  type: 'fact' | 'clue' | 'inconsistency' | 'gap' | 'question';
  title: string;
  description: string;
  sourcePages?: number[];
  sourceQuotes?: string[];
  significance?: 'high' | 'medium' | 'low';
  confidence?: 'high' | 'medium' | 'low';
  verificationNeeded?: boolean;
  alternativeExplanations?: string[];
  quoteVerified?: boolean;
  onOpenSourcePage: (pageNumber: number, quote?: string) => void;
}

export default function FindingCard({
  type,
  title,
  description,
  sourcePages = [],
  sourceQuotes = [],
  significance,
  confidence,
  verificationNeeded,
  alternativeExplanations = [],
  quoteVerified = true,
  onOpenSourcePage,
}: FindingCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Type styling & badges
  const typeConfig = {
    fact: {
      label: 'Direct Fact',
      badgeBg: 'bg-emerald-50 text-emerald-800 border-emerald-200',
      borderLeft: 'border-l-emerald-600',
      badgeIcon: CheckCircle2,
      kind: 'direct_statement',
    },
    clue: {
      label: 'Potential Clue',
      badgeBg: 'bg-blue-50 text-blue-800 border-blue-200',
      borderLeft: 'border-l-blue-600',
      badgeIcon: FileText,
      kind: 'ai_interpretation',
    },
    inconsistency: {
      label: 'Potential Inconsistency',
      badgeBg: 'bg-amber-50 text-amber-800 border-amber-200',
      borderLeft: 'border-l-amber-600',
      badgeIcon: AlertTriangle,
      kind: 'unverified_hypothesis',
    },
    gap: {
      label: 'Information Gap',
      badgeBg: 'bg-purple-50 text-purple-800 border-purple-200',
      borderLeft: 'border-l-purple-600',
      badgeIcon: HelpCircle,
      kind: 'ai_interpretation',
    },
    question: {
      label: 'Investigation Question',
      badgeBg: 'bg-indigo-50 text-indigo-800 border-indigo-200',
      borderLeft: 'border-l-indigo-600',
      badgeIcon: Scale,
      kind: 'ai_interpretation',
    },
  }[type];

  const TypeIcon = typeConfig.badgeIcon;

  return (
    <div
      className={`bg-white rounded-xl border border-surface-border border-l-4 ${typeConfig.borderLeft} shadow-xs hover:shadow-sm transition-all overflow-hidden`}
    >
      <div className="p-5 space-y-3">
        {/* Top Badges Row */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${typeConfig.badgeBg}`}
            >
              <TypeIcon className="w-3.5 h-3.5" />
              {typeConfig.label}
            </span>

            {/* Classification Nature Badge */}
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-surface-bg text-ink-muted border border-surface-border">
              {typeConfig.kind === 'direct_statement'
                ? 'Document Statement'
                : typeConfig.kind === 'ai_interpretation'
                ? 'AI Interpretation'
                : 'Hypothesis for Review'}
            </span>

            {significance && (
              <span
                className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded ${
                  significance === 'high'
                    ? 'bg-amber-100 text-amber-800 border border-amber-200'
                    : significance === 'medium'
                    ? 'bg-blue-100 text-blue-800 border border-blue-200'
                    : 'bg-slate-100 text-slate-700 border border-slate-200'
                }`}
                title="Priority level for lawyer review (not a legal determination)"
              >
                {significance} Review Priority
              </span>
            )}

            {confidence && (
              <span className="text-[10px] uppercase font-medium text-ink-muted px-2 py-0.5 rounded bg-surface-bg border border-surface-border">
                Confidence: {confidence}
              </span>
            )}
          </div>

          {/* Verification Badge */}
          {sourceQuotes.length > 0 && (
            <span
              className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-md ${
                quoteVerified
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-amber-50 text-amber-700 border border-amber-200'
              }`}
            >
              {quoteVerified ? (
                <>
                  <ShieldCheck className="w-3.5 h-3.5 text-status-success" />
                  <span>Verified in Source</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-3.5 h-3.5 text-status-warning" />
                  <span>Citation Review Recommended</span>
                </>
              )}
            </span>
          )}
        </div>

        {/* Title */}
        <h4 className="text-sm font-bold text-navy-900 leading-snug">{title}</h4>

        {/* Short Explanation */}
        <p className="text-xs text-ink-muted leading-relaxed">{description}</p>

        {/* Source Page Citation Links */}
        {sourcePages.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-[11px] font-medium text-ink-muted">Cited Pages:</span>
            {sourcePages.map((pageNum, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => onOpenSourcePage(pageNum, sourceQuotes[idx] || sourceQuotes[0])}
                className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-surface-bg hover:bg-primary-light hover:text-primary hover:border-primary border border-surface-border text-xs font-semibold text-navy-900 transition-colors"
                title={`Inspect Page ${pageNum} text in source modal`}
              >
                <span>Page {pageNum}</span>
                <ExternalLink className="w-3 h-3 ml-0.5 text-ink-muted group-hover:text-primary" />
              </button>
            ))}
          </div>
        )}

        {/* Expandable Section for Detailed Quotes & Explanations */}
        {(sourceQuotes.length > 0 || alternativeExplanations.length > 0 || verificationNeeded) && (
          <div className="pt-2 border-t border-surface-border">
            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              className="inline-flex items-center space-x-1 text-xs font-semibold text-primary hover:text-primary-hover transition-colors"
            >
              <span>{isExpanded ? 'Hide Supporting Evidence' : 'Show Supporting Evidence & Quotes'}</span>
              {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {isExpanded && (
              <div className="mt-3 space-y-3 p-3.5 bg-surface-bg rounded-lg border border-surface-border text-xs">
                {/* Quotations */}
                {sourceQuotes.length > 0 && (
                  <div className="space-y-1.5">
                    <p className="font-bold text-navy-900 text-[11px] uppercase tracking-wider">
                      Verbatim Document Quotation{sourceQuotes.length > 1 ? 's' : ''}:
                    </p>
                    {sourceQuotes.map((quote, qIdx) => (
                      <blockquote
                        key={qIdx}
                        className="pl-3 border-l-2 border-primary/60 italic text-slate-700 font-mono text-[11.5px] leading-relaxed bg-white/70 py-1 rounded-r"
                      >
                        &ldquo;{quote}&rdquo;
                      </blockquote>
                    ))}
                  </div>
                )}

                {/* Alternative Explanations (for Inconsistencies) */}
                {alternativeExplanations.length > 0 && (
                  <div className="space-y-1 pt-1">
                    <p className="font-bold text-navy-900 text-[11px] uppercase tracking-wider">
                      Potential Alternative / Benign Explanations:
                    </p>
                    <ul className="list-disc list-inside space-y-1 text-slate-600">
                      {alternativeExplanations.map((alt, altIdx) => (
                        <li key={altIdx}>{alt}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Verification Notice */}
                {verificationNeeded && (
                  <p className="text-[11px] text-ink-muted italic">
                    Note: This item was flagged as a preliminary clue and requires independent corroboration against primary records.
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

