'use client';

import React, { useState } from 'react';
import {
  FileText,
  Download,
  RotateCcw,
  ShieldCheck,
  AlertTriangle,
  HelpCircle,
  Scale,
  Sparkles,
  Search,
  Filter,
  CheckCircle2,
  Calendar,
  Layers,
  Info,
} from 'lucide-react';
import { CompleteAnalysisResult } from '@/types/analysis';
import FindingCard from './FindingCard';
import SourceViewerModal from './SourceViewerModal';
import { formatBytes } from '@/lib/utils';

interface ResultsDashboardProps {
  result: CompleteAnalysisResult;
  onReset: () => void;
}

type TabType = 'all' | 'facts' | 'clues' | 'inconsistencies' | 'gaps' | 'questions';

export default function ResultsDashboard({ result, onReset }: ResultsDashboardProps) {
  const { metadata, analysis, pages } = result;

  const [activeTab, setActiveTab] = useState<TabType>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [priorityFilter, setPriorityFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);

  // Source Viewer Modal State
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [selectedPageNum, setSelectedPageNum] = useState<number>(1);
  const [selectedHighlightQuote, setSelectedHighlightQuote] = useState<string | undefined>(undefined);

  const handleOpenSourcePage = (pageNum: number, quote?: string) => {
    setSelectedPageNum(pageNum);
    setSelectedHighlightQuote(quote);
    setInspectorOpen(true);
  };

  const handleDownloadReport = async () => {
    setIsGeneratingReport(true);
    setReportError(null);
    try {
      const response = await fetch('/api/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(result),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'Failed to generate PDF report.');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Investigation_Report_${metadata.filename.replace(/\.pdf$/i, '')}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: unknown) {
      setReportError(err instanceof Error ? err.message : 'Error generating report');
    } finally {
      setIsGeneratingReport(false);
    }
  };

  // Counts
  const factsCount = analysis.importantFacts?.length || 0;
  const cluesCount = analysis.potentialClues?.length || 0;
  const inconsistenciesCount = analysis.inconsistencies?.length || 0;
  const gapsCount = analysis.informationGaps?.length || 0;
  const questionsCount = analysis.investigationQuestions?.length || 0;
  const totalFindings = factsCount + cluesCount + inconsistenciesCount + gapsCount + questionsCount;

  // Filter items based on tab, search query, and priority
  const matchesSearch = (text: string) => {
    if (!searchQuery.trim()) return true;
    return text.toLowerCase().includes(searchQuery.toLowerCase());
  };

  const filteredFacts = (analysis.importantFacts || []).filter(
    (f) =>
      (activeTab === 'all' || activeTab === 'facts') &&
      (matchesSearch(f.title) || matchesSearch(f.description) || matchesSearch(f.sourceQuote))
  );

  const filteredClues = (analysis.potentialClues || []).filter(
    (c) =>
      (activeTab === 'all' || activeTab === 'clues') &&
      (priorityFilter === 'all' || c.significance === priorityFilter) &&
      (matchesSearch(c.title) || matchesSearch(c.description))
  );

  const filteredInconsistencies = (analysis.inconsistencies || []).filter(
    (inc) =>
      (activeTab === 'all' || activeTab === 'inconsistencies') &&
      (matchesSearch(inc.title) || matchesSearch(inc.description))
  );

  const filteredGaps = (analysis.informationGaps || []).filter(
    (g) =>
      (activeTab === 'all' || activeTab === 'gaps') &&
      (matchesSearch(g.question) || matchesSearch(g.reason))
  );

  const filteredQuestions = (analysis.investigationQuestions || []).filter(
    (q) =>
      (activeTab === 'all' || activeTab === 'questions') &&
      (matchesSearch(q.question) || matchesSearch(q.reason))
  );

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6 pb-12 animate-in fade-in">
      {/* Top Banner / Summary Card */}
      <div className="bg-white rounded-2xl border border-surface-border p-6 shadow-xs space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold uppercase tracking-wider text-primary px-2 py-0.5 rounded bg-primary-light">
                Analysis Complete
              </span>
              <span className="text-xs text-ink-muted">
                {new Date(metadata.analyzedAt).toLocaleDateString()} at{' '}
                {new Date(metadata.analyzedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
            <h2 className="text-xl font-bold text-navy-900 truncate max-w-2xl">{metadata.filename}</h2>
            <div className="flex flex-wrap items-center gap-3 text-xs text-ink-muted pt-1">
              <span>{formatBytes(metadata.fileSizeBytes)}</span>
              <span>•</span>
              <span>
                {metadata.analyzedPages} of {metadata.totalPages} pages analyzed
              </span>
              <span>•</span>
              <span className="capitalize">{metadata.analysisMode} Review</span>
              <span>•</span>
              <span className="font-mono text-[11px]">Model: {metadata.modelUsed}</span>
            </div>
          </div>

          {/* Action CTAs */}
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleDownloadReport}
              disabled={isGeneratingReport}
              className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-lg text-sm font-semibold bg-primary hover:bg-primary-hover text-white shadow-xs transition-colors disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              <span>{isGeneratingReport ? 'Generating PDF...' : 'Download PDF Report'}</span>
            </button>
            <button
              onClick={onReset}
              className="inline-flex items-center space-x-1.5 px-4 py-2.5 rounded-lg text-sm font-semibold border border-surface-border bg-white hover:bg-surface-hover text-navy-900 transition-colors"
            >
              <RotateCcw className="w-4 h-4 text-ink-muted" />
              <span>Analyze Another Document</span>
            </button>
          </div>
        </div>

        {reportError && (
          <div className="p-3 bg-red-50 border border-red-200 text-status-error text-xs rounded-lg">
            {reportError}
          </div>
        )}

        {/* Quick KPI Stat Boxes */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-2 border-t border-surface-border">
          <div className="p-3 bg-surface-bg rounded-lg border border-surface-border">
            <span className="text-[11px] font-bold uppercase tracking-wider text-ink-muted">Total Findings</span>
            <p className="text-xl font-black text-navy-900 mt-0.5">{totalFindings}</p>
          </div>
          <div className="p-3 bg-emerald-50/50 rounded-lg border border-emerald-100">
            <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800">Direct Facts</span>
            <p className="text-xl font-black text-emerald-900 mt-0.5">{factsCount}</p>
          </div>
          <div className="p-3 bg-blue-50/50 rounded-lg border border-blue-100">
            <span className="text-[11px] font-bold uppercase tracking-wider text-blue-800">Potential Clues</span>
            <p className="text-xl font-black text-blue-900 mt-0.5">{cluesCount}</p>
          </div>
          <div className="p-3 bg-amber-50/50 rounded-lg border border-amber-100">
            <span className="text-[11px] font-bold uppercase tracking-wider text-amber-800">Inconsistencies</span>
            <p className="text-xl font-black text-amber-900 mt-0.5">{inconsistenciesCount}</p>
          </div>
          <div className="p-3 bg-purple-50/50 rounded-lg border border-purple-100">
            <span className="text-[11px] font-bold uppercase tracking-wider text-purple-800">Information Gaps</span>
            <p className="text-xl font-black text-purple-900 mt-0.5">{gapsCount}</p>
          </div>
          <div className="p-3 bg-indigo-50/50 rounded-lg border border-indigo-100">
            <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-800">Questions</span>
            <p className="text-xl font-black text-indigo-900 mt-0.5">{questionsCount}</p>
          </div>
        </div>

        {/* Executive Summary Card */}
        <div className="bg-surface-bg rounded-xl p-5 border border-surface-border space-y-2">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-navy-900">
            <Sparkles className="w-4 h-4 text-primary" />
            <span>Executive Document Summary</span>
          </div>
          <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-line">
            {analysis.documentSummary}
          </p>
        </div>

        {/* Citations Quality Metric */}
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-ink-muted bg-white p-3 rounded-lg border border-surface-border">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-status-success" />
            <span>
              Verbatim Citation Check:{' '}
              <strong className="text-navy-900">{metadata.verifiedQuotesCount} quotations verified</strong> in source
              text ({metadata.unverifiedQuotesCount} flagged for review)
            </span>
          </div>
          <button
            onClick={() => handleOpenSourcePage(1)}
            className="text-xs font-semibold text-primary hover:text-primary-hover underline"
          >
            Open Source Document Inspector
          </button>
        </div>
      </div>

      {/* Tabs and Filters */}
      <div className="space-y-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          {/* Navigation Tabs */}
          <div className="flex flex-wrap items-center gap-1.5 p-1 bg-white rounded-xl border border-surface-border">
            <button
              onClick={() => setActiveTab('all')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'all'
                  ? 'bg-navy-900 text-white shadow-xs'
                  : 'text-ink-muted hover:text-navy-900 hover:bg-slate-100'
              }`}
            >
              All Findings ({totalFindings})
            </button>
            <button
              onClick={() => setActiveTab('facts')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'facts'
                  ? 'bg-navy-900 text-white shadow-xs'
                  : 'text-ink-muted hover:text-navy-900 hover:bg-slate-100'
              }`}
            >
              Facts ({factsCount})
            </button>
            <button
              onClick={() => setActiveTab('clues')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'clues'
                  ? 'bg-navy-900 text-white shadow-xs'
                  : 'text-ink-muted hover:text-navy-900 hover:bg-slate-100'
              }`}
            >
              Clues ({cluesCount})
            </button>
            <button
              onClick={() => setActiveTab('inconsistencies')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'inconsistencies'
                  ? 'bg-navy-900 text-white shadow-xs'
                  : 'text-ink-muted hover:text-navy-900 hover:bg-slate-100'
              }`}
            >
              Inconsistencies ({inconsistenciesCount})
            </button>
            <button
              onClick={() => setActiveTab('gaps')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'gaps'
                  ? 'bg-navy-900 text-white shadow-xs'
                  : 'text-ink-muted hover:text-navy-900 hover:bg-slate-100'
              }`}
            >
              Gaps ({gapsCount})
            </button>
            <button
              onClick={() => setActiveTab('questions')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'questions'
                  ? 'bg-navy-900 text-white shadow-xs'
                  : 'text-ink-muted hover:text-navy-900 hover:bg-slate-100'
              }`}
            >
              Questions ({questionsCount})
            </button>
          </div>

          {/* Search Input & Priority Filter */}
          <div className="flex items-center space-x-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted" />
              <input
                type="text"
                placeholder="Search findings..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-surface-border bg-white text-navy-900 focus:outline-none focus:ring-1 focus:ring-primary w-44 sm:w-56"
              />
            </div>

            {activeTab === 'clues' && (
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value as any)}
                className="px-2.5 py-1.5 text-xs rounded-lg border border-surface-border bg-white text-navy-900 focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="all">All Priorities</option>
                <option value="high">High Priority</option>
                <option value="medium">Medium Priority</option>
                <option value="low">Low Priority</option>
              </select>
            )}
          </div>
        </div>

        {/* Findings List */}
        <div className="space-y-3">
          {/* Direct Facts */}
          {filteredFacts.map((fact, idx) => (
            <FindingCard
              key={fact.id || `fact-${idx}`}
              type="fact"
              title={fact.title}
              description={fact.description}
              sourcePages={[fact.sourcePage]}
              sourceQuotes={[fact.sourceQuote]}
              confidence={fact.confidence}
              quoteVerified={fact.quoteVerified}
              onOpenSourcePage={handleOpenSourcePage}
            />
          ))}

          {/* Potential Clues */}
          {filteredClues.map((clue, idx) => (
            <FindingCard
              key={clue.id || `clue-${idx}`}
              type="clue"
              title={clue.title}
              description={clue.description}
              sourcePages={clue.sourcePages}
              sourceQuotes={clue.sourceQuotes}
              significance={clue.significance}
              verificationNeeded={clue.verificationNeeded}
              quoteVerified={clue.quoteVerified}
              onOpenSourcePage={handleOpenSourcePage}
            />
          ))}

          {/* Inconsistencies */}
          {filteredInconsistencies.map((inc, idx) => (
            <FindingCard
              key={inc.id || `inc-${idx}`}
              type="inconsistency"
              title={inc.title}
              description={inc.description}
              sourcePages={inc.sourcePages}
              sourceQuotes={inc.sourceQuotes}
              alternativeExplanations={inc.alternativeExplanations}
              quoteVerified={inc.quoteVerified}
              onOpenSourcePage={handleOpenSourcePage}
            />
          ))}

          {/* Gaps */}
          {filteredGaps.map((gap, idx) => (
            <FindingCard
              key={gap.id || `gap-${idx}`}
              type="gap"
              title={gap.question}
              description={gap.reason}
              sourcePages={gap.relatedPages}
              onOpenSourcePage={handleOpenSourcePage}
            />
          ))}

          {/* Questions */}
          {filteredQuestions.map((q, idx) => (
            <FindingCard
              key={q.id || `q-${idx}`}
              type="question"
              title={q.question}
              description={q.reason}
              sourcePages={q.relatedPages}
              onOpenSourcePage={handleOpenSourcePage}
            />
          ))}

          {/* Empty Search/Filter State */}
          {filteredFacts.length === 0 &&
            filteredClues.length === 0 &&
            filteredInconsistencies.length === 0 &&
            filteredGaps.length === 0 &&
            filteredQuestions.length === 0 && (
              <div className="bg-white rounded-xl border border-surface-border p-12 text-center space-y-2">
                <FileText className="w-8 h-8 mx-auto text-slate-300" />
                <h4 className="text-sm font-bold text-navy-900">No findings match this filter</h4>
                <p className="text-xs text-ink-muted">
                  Try switching tabs or clearing your search term &quot;{searchQuery}&quot;.
                </p>
              </div>
            )}
        </div>
      </div>

      {/* Analytical Limitations & Legal Disclaimer Box */}
      <div className="rounded-xl border border-surface-border bg-white p-6 space-y-3">
        <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-status-warning">
          <Info className="w-4 h-4 text-status-warning" />
          <span>Analytical Limitations & Legal Disclaimer</span>
        </div>
        <ul className="list-disc list-inside space-y-1 text-xs text-ink-muted">
          {analysis.limitations?.map((lim, lIdx) => (
            <li key={lIdx}>{lim}</li>
          ))}
          <li>
            This tool assists with preliminary document review. AI-generated findings may be incomplete or incorrect and
            must be verified against the original documents. It does not replace professional legal judgment and does not
            guarantee any legal outcome.
          </li>
        </ul>
      </div>

      {/* Source Viewer Modal */}
      <SourceViewerModal
        isOpen={inspectorOpen}
        onClose={() => setInspectorOpen(false)}
        pages={pages}
        initialPageNumber={selectedPageNum}
        highlightQuote={selectedHighlightQuote}
        filename={metadata.filename}
      />
    </div>
  );
}
