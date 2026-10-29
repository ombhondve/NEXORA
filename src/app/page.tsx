'use client';

import React, { useState, useRef } from 'react';
import Navbar from '@/components/Navbar';
import DocumentUpload from '@/components/DocumentUpload';
import AnalysisProgress from '@/components/AnalysisProgress';
import ResultsDashboard from '@/components/ResultsDashboard';
import { AnalysisMode, CompleteAnalysisResult } from '@/types/analysis';
import {
  Search,
  Scale,
  FileCheck,
  AlertOctagon,
  HelpCircle,
  ShieldCheck,
  ArrowRight,
  BookOpen,
  FileUp,
  Cpu,
  Download,
  AlertTriangle,
} from 'lucide-react';
import Link from 'next/link';

export default function HomePage() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzingFilename, setAnalyzingFilename] = useState<string>('');
  const [analysisResult, setAnalysisResult] = useState<CompleteAnalysisResult | null>(null);
  const [generalError, setGeneralError] = useState<string | null>(null);

  const uploadSectionRef = useRef<HTMLDivElement>(null);

  const scrollToUpload = () => {
    uploadSectionRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleStartAnalysis = async (file: File, mode: AnalysisMode) => {
    setGeneralError(null);
    setAnalyzingFilename(file.name);
    setIsAnalyzing(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('mode', mode);

      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to complete document analysis.');
      }

      setAnalysisResult(data as CompleteAnalysisResult);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'An error occurred during analysis.';
      setGeneralError(msg);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleReset = () => {
    setAnalysisResult(null);
    setGeneralError(null);
    setIsAnalyzing(false);
    setAnalyzingFilename('');
  };

  return (
    <>
      <Navbar onReset={analysisResult ? handleReset : undefined} />

      <main className="flex-1">
        {/* If Results Dashboard is active, render dashboard view */}
        {analysisResult ? (
          <div className="py-8 px-4 sm:px-6 lg:px-8">
            <ResultsDashboard result={analysisResult} onReset={handleReset} />
          </div>
        ) : isAnalyzing ? (
          /* Processing State */
          <div className="py-20 px-4 sm:px-6 lg:px-8">
            <AnalysisProgress filename={analyzingFilename} />
          </div>
        ) : (
          /* Standard Landing & Upload Interface */
          <div>
            {/* HERO SECTION */}
            <section className="relative overflow-hidden bg-white border-b border-surface-border py-16 sm:py-24">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
                <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-primary-light text-primary text-xs font-semibold border border-blue-200">
                  <Scale className="w-3.5 h-3.5" />
                  <span>Preliminary Legal Intelligence Platform</span>
                </div>

                <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black text-navy-900 tracking-tight max-w-4xl mx-auto leading-tight">
                  Find the Details That Matter in Your Legal Documents.
                </h1>

                <p className="text-base sm:text-lg text-ink-muted max-w-2xl mx-auto leading-relaxed">
                  Analyze legal documents with AI to identify important facts, potential inconsistencies, overlooked
                  details, and questions that deserve further investigation.
                </p>

                <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
                  <button
                    onClick={scrollToUpload}
                    className="inline-flex items-center space-x-2 px-6 py-3 rounded-lg text-sm font-semibold bg-primary hover:bg-primary-hover text-white shadow-sm transition-all"
                  >
                    <span>Analyze a Document</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>

                  <Link
                    href="/how-it-works"
                    className="inline-flex items-center space-x-2 px-6 py-3 rounded-lg text-sm font-semibold border border-surface-border bg-white hover:bg-surface-hover text-navy-900 transition-colors"
                  >
                    <BookOpen className="w-4 h-4 text-ink-muted" />
                    <span>How It Works</span>
                  </Link>
                </div>
              </div>
            </section>

            {/* ERROR NOTIFICATION IF PREVIOUS ATTEMPT FAILED */}
            {generalError && (
              <div className="max-w-4xl mx-auto px-4 sm:px-6 mt-6">
                <div className="rounded-xl bg-red-50 border border-red-200 p-5 flex items-start space-x-3 text-left">
                  <AlertTriangle className="w-5 h-5 text-status-error flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <h4 className="text-sm font-bold text-status-error">Analysis Error</h4>
                    <p className="text-xs text-red-800 mt-1 leading-relaxed">{generalError}</p>
                    <button
                      onClick={() => setGeneralError(null)}
                      className="mt-3 text-xs font-semibold text-status-error hover:underline"
                    >
                      Dismiss and try again
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* DOCUMENT UPLOAD SECTION */}
            <section ref={uploadSectionRef} className="py-12 px-4 sm:px-6 lg:px-8">
              <div className="max-w-4xl mx-auto space-y-4">
                <div className="text-center space-y-1 mb-6">
                  <h2 className="text-xl font-bold text-navy-900">Upload Legal Document</h2>
                  <p className="text-xs text-ink-muted">
                    Supports text-based contracts, pleadings, affidavits, depositions, or correspondence (PDF only)
                  </p>
                </div>

                <DocumentUpload onStartAnalysis={handleStartAnalysis} isLoading={isAnalyzing} />
              </div>
            </section>

            {/* CAPABILITY CARDS SECTION */}
            <section className="py-16 bg-white border-t border-surface-border">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
                <div className="text-center space-y-2">
                  <h2 className="text-2xl font-bold text-navy-900">Comprehensive Legal Document Intelligence</h2>
                  <p className="text-sm text-ink-muted max-w-xl mx-auto">
                    Built for rigorous, evidence-grounded review. Every observation is cross-referenced with exact
                    page numbers and verbatim quotes.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {/* Card 1 */}
                  <div className="p-6 rounded-xl border border-surface-border bg-surface-bg hover:border-slate-300 transition-all space-y-3">
                    <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center text-primary">
                      <Search className="w-5 h-5" />
                    </div>
                    <h3 className="text-base font-bold text-navy-900">Potential Clue Detection</h3>
                    <p className="text-xs text-ink-muted leading-relaxed">
                      Highlights subtle transactional details, unusual timeline sequences, or qualification clauses
                      that may indicate unstated conditions or tactical leverage.
                    </p>
                  </div>

                  {/* Card 2 */}
                  <div className="p-6 rounded-xl border border-surface-border bg-surface-bg hover:border-slate-300 transition-all space-y-3">
                    <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center text-status-warning">
                      <AlertOctagon className="w-5 h-5" />
                    </div>
                    <h3 className="text-base font-bold text-navy-900">Inconsistency Analysis</h3>
                    <p className="text-xs text-ink-muted leading-relaxed">
                      Flags conflicting factual claims or timeline dates across separate pages, while presenting
                      plausible alternative explanations for objective evaluation.
                    </p>
                  </div>

                  {/* Card 3 */}
                  <div className="p-6 rounded-xl border border-surface-border bg-surface-bg hover:border-slate-300 transition-all space-y-3">
                    <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center text-status-success">
                      <FileCheck className="w-5 h-5" />
                    </div>
                    <h3 className="text-base font-bold text-navy-900">Important Fact Extraction</h3>
                    <p className="text-xs text-ink-muted leading-relaxed">
                      Extracts foundational stipulations, executed terms, dates, and covenants directly stated in the
                      text, accompanied by exact source page citations.
                    </p>
                  </div>

                  {/* Card 4 */}
                  <div className="p-6 rounded-xl border border-surface-border bg-surface-bg hover:border-slate-300 transition-all space-y-3">
                    <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center text-purple-700">
                      <HelpCircle className="w-5 h-5" />
                    </div>
                    <h3 className="text-base font-bold text-navy-900">Evidence Gap Identification</h3>
                    <p className="text-xs text-ink-muted leading-relaxed">
                      Identifies missing schedules, absent signatory verifications, unaddressed conditions precedent, or
                      conspicuously omitted exhibits.
                    </p>
                  </div>

                  {/* Card 5 */}
                  <div className="p-6 rounded-xl border border-surface-border bg-surface-bg hover:border-slate-300 transition-all space-y-3">
                    <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center text-indigo-700">
                      <Scale className="w-5 h-5" />
                    </div>
                    <h3 className="text-base font-bold text-navy-900">Investigation Questions</h3>
                    <p className="text-xs text-ink-muted leading-relaxed">
                      Formulates tactical, objective inquiry questions designed for witness depositions, interrogatories,
                      or pre-trial discovery requests.
                    </p>
                  </div>

                  {/* Card 6 */}
                  <div className="p-6 rounded-xl border border-surface-border bg-surface-bg hover:border-slate-300 transition-all space-y-3">
                    <div className="w-10 h-10 rounded-lg bg-slate-200 flex items-center justify-center text-navy-900">
                      <ShieldCheck className="w-5 h-5" />
                    </div>
                    <h3 className="text-base font-bold text-navy-900">Source-Based Verification</h3>
                    <p className="text-xs text-ink-muted leading-relaxed">
                      Every finding is verified against the document text to eliminate model hallucination. An
                      interactive inspector highlights quotations in context.
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* HOW IT WORKS SECTION */}
            <section className="py-16 bg-surface-bg border-t border-surface-border">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
                <div className="text-center space-y-2">
                  <h2 className="text-2xl font-bold text-navy-900">How It Works</h2>
                  <p className="text-sm text-ink-muted">Four simple steps from raw PDF to structured investigation report</p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                  {/* Step 1 */}
                  <div className="p-6 bg-white rounded-xl border border-surface-border shadow-xs space-y-3 text-left">
                    <div className="w-8 h-8 rounded-full bg-navy-900 text-white flex items-center justify-center text-xs font-bold">
                      1
                    </div>
                    <h3 className="text-sm font-bold text-navy-900">Upload a PDF</h3>
                    <p className="text-xs text-ink-muted leading-relaxed">
                      Drag and drop your case document (up to 8 MB, 50 pages). File stays in memory and is never permanently written to disk.
                    </p>
                  </div>

                  {/* Step 2 */}
                  <div className="p-6 bg-white rounded-xl border border-surface-border shadow-xs space-y-3 text-left">
                    <div className="w-8 h-8 rounded-full bg-navy-900 text-white flex items-center justify-center text-xs font-bold">
                      2
                    </div>
                    <h3 className="text-sm font-bold text-navy-900">Extract Document Text</h3>
                    <p className="text-xs text-ink-muted leading-relaxed">
                      Server extracts page boundaries, detects scanned content, and indexes layout so findings cite exact page numbers.
                    </p>
                  </div>

                  {/* Step 3 */}
                  <div className="p-6 bg-white rounded-xl border border-surface-border shadow-xs space-y-3 text-left">
                    <div className="w-8 h-8 rounded-full bg-navy-900 text-white flex items-center justify-center text-xs font-bold">
                      3
                    </div>
                    <h3 className="text-sm font-bold text-navy-900">Analyze with Groq AI</h3>
                    <p className="text-xs text-ink-muted leading-relaxed">
                      Server-side Groq LLM analyzes document logic under strict adversarial prompts designed to prevent hallucination.
                    </p>
                  </div>

                  {/* Step 4 */}
                  <div className="p-6 bg-white rounded-xl border border-surface-border shadow-xs space-y-3 text-left">
                    <div className="w-8 h-8 rounded-full bg-navy-900 text-white flex items-center justify-center text-xs font-bold">
                      4
                    </div>
                    <h3 className="text-sm font-bold text-navy-900">Review & Download Report</h3>
                    <p className="text-xs text-ink-muted leading-relaxed">
                      Inspect findings in the interactive dashboard, view quotations in source text, and export an official PDF investigation report.
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* MANDATORY LEGAL DISCLAIMER */}
            <section className="py-8 bg-white border-t border-surface-border">
              <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center space-y-2">
                <p className="text-xs text-ink-muted leading-relaxed">
                  <strong>Important Notice:</strong> This tool assists with preliminary document review. AI-generated
                  findings may be incomplete or incorrect and must be verified against the original documents. It does
                  not replace professional legal judgment and does not guarantee that a lawyer will win a case.
                </p>
              </div>
            </section>
          </div>
        )}
      </main>

      {/* FOOTER */}
      <footer className="border-t border-surface-border bg-white py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-ink-muted">
          <div className="flex items-center space-x-2">
            <Scale className="w-4 h-4 text-primary" />
            <span className="font-semibold text-navy-900">AI Legal Clue Finder</span>
            <span>• Powered by Groq AI</span>
          </div>
          <div className="flex items-center space-x-4">
            <Link href="/how-it-works" className="hover:text-navy-900 transition-colors">
              How It Works
            </Link>
            <Link href="/privacy" className="hover:text-navy-900 transition-colors">
              Privacy & Security
            </Link>
          </div>
        </div>
      </footer>
    </>
  );
}

