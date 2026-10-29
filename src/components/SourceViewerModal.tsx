'use client';

import React, { useState } from 'react';
import { X, ChevronLeft, ChevronRight, Copy, Check, FileText, AlertTriangle } from 'lucide-react';
import { ExtractedPage } from '@/types/analysis';

interface SourceViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  pages: ExtractedPage[];
  initialPageNumber: number;
  highlightQuote?: string;
  filename: string;
}

export default function SourceViewerModal({
  isOpen,
  onClose,
  pages,
  initialPageNumber,
  highlightQuote,
  filename,
}: SourceViewerModalProps) {
  const [currentPageNum, setCurrentPageNum] = useState<number>(initialPageNumber || 1);
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const totalPages = pages.length;
  const currentPage = pages.find((p) => p.pageNumber === currentPageNum) || pages[0];

  const handleCopy = () => {
    if (currentPage) {
      navigator.clipboard.writeText(currentPage.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const renderHighlightedText = (fullText: string, quoteToFind?: string) => {
    if (!quoteToFind || quoteToFind.trim().length === 0) {
      return <span>{fullText}</span>;
    }

    const cleanQuote = quoteToFind.trim().toLowerCase();
    const cleanFull = fullText.toLowerCase();

    const idx = cleanFull.indexOf(cleanQuote);
    if (idx === -1) {
      // If exact phrase not found (due to line breaks), render original text
      return <span>{fullText}</span>;
    }

    const before = fullText.substring(0, idx);
    const match = fullText.substring(idx, idx + quoteToFind.trim().length);
    const after = fullText.substring(idx + quoteToFind.trim().length);

    return (
      <>
        <span>{before}</span>
        <mark className="bg-amber-200 text-navy-900 font-semibold px-1 py-0.5 rounded border-b-2 border-amber-500">
          {match}
        </mark>
        <span>{after}</span>
      </>
    );
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-navy-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="relative w-full max-w-3xl bg-white rounded-2xl shadow-2xl border border-surface-border flex flex-col max-h-[85vh] overflow-hidden animate-in fade-in zoom-in-95">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-surface-border bg-slate-50">
          <div className="flex items-center space-x-3 overflow-hidden">
            <div className="w-8 h-8 rounded-lg bg-primary-light flex items-center justify-center text-primary flex-shrink-0">
              <FileText className="w-4 h-4" />
            </div>
            <div className="truncate">
              <h3 className="text-sm font-bold text-navy-900 truncate">Document Source Inspection</h3>
              <p className="text-xs text-ink-muted truncate">{filename}</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopy}
              className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-md text-xs font-medium border border-surface-border bg-white hover:bg-surface-hover text-ink-muted transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-status-success" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy Page'}</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-md text-ink-muted hover:text-navy-900 hover:bg-slate-200/60 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Page Switcher Subheader */}
        <div className="flex items-center justify-between px-6 py-2.5 bg-white border-b border-surface-border text-xs">
          <div className="flex items-center space-x-3">
            <button
              disabled={currentPageNum <= 1}
              onClick={() => setCurrentPageNum((prev) => Math.max(1, prev - 1))}
              className="p-1 rounded text-ink-muted hover:text-navy-900 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-100"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-semibold text-navy-900">
              Page {currentPageNum} of {totalPages}
            </span>
            <button
              disabled={currentPageNum >= totalPages}
              onClick={() => setCurrentPageNum((prev) => Math.min(totalPages, prev + 1))}
              className="p-1 rounded text-ink-muted hover:text-navy-900 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-100"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center space-x-3 text-ink-muted">
            {currentPage?.isUnreadableOrEmpty ? (
              <span className="inline-flex items-center text-status-warning font-medium gap-1">
                <AlertTriangle className="w-3.5 h-3.5" /> Scanned / Low Text Page
              </span>
            ) : (
              <span>{currentPage?.charCount || 0} characters</span>
            )}
          </div>
        </div>

        {/* Highlighted Quote Notice */}
        {highlightQuote && (
          <div className="px-6 py-2.5 bg-amber-50/70 border-b border-amber-200/60 text-xs flex items-center justify-between">
            <div className="truncate pr-4">
              <span className="font-semibold text-status-warning">Inspecting Citation: </span>
              <span className="italic text-slate-700 truncate">&ldquo;{highlightQuote}&rdquo;</span>
            </div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700 bg-amber-100 px-2 py-0.5 rounded">
              Cited
            </span>
          </div>
        )}

        {/* Content Body */}
        <div className="flex-1 p-6 overflow-y-auto font-mono text-xs leading-relaxed text-slate-800 whitespace-pre-wrap select-text bg-[#FAFAFA]">
          {currentPage?.text?.trim() ? (
            renderHighlightedText(currentPage.text, highlightQuote)
          ) : (
            <div className="text-center py-12 text-ink-muted">
              <AlertTriangle className="w-8 h-8 mx-auto text-amber-500 mb-2" />
              <p className="font-semibold">No extractable digital text on Page {currentPageNum}.</p>
              <p className="text-[11px] mt-1 text-slate-400">
                This page may be an image, handwritten note, or scanned graphic.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-surface-border bg-slate-50 flex items-center justify-between text-xs text-ink-muted">
          <span>Source verification view (read-only)</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-md text-xs font-semibold bg-navy-900 text-white hover:bg-navy-800"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}

