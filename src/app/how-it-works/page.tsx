import React from 'react';
import Navbar from '@/components/Navbar';
import Link from 'next/link';
import { ArrowLeft, CheckCircle2, Shield, Search, AlertOctagon, HelpCircle, Layers, ArrowRight } from 'lucide-react';

export default function HowItWorksPage() {
  return (
    <>
      <Navbar />
      <main className="flex-1 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto space-y-10">
          <div>
            <Link
              href="/"
              className="inline-flex items-center space-x-1.5 text-xs font-semibold text-primary hover:text-primary-hover mb-4"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Analysis</span>
            </Link>
            <h1 className="text-3xl font-black text-navy-900 tracking-tight">How AI Legal Clue Finder Works</h1>
            <p className="text-sm text-ink-muted mt-2 leading-relaxed">
              An architectural breakdown of our zero-retention legal document extraction, adversarial AI verification,
              and quotation corroboration pipeline.
            </p>
          </div>

          {/* Section 1: Memory-Based Processing */}
          <div className="bg-white rounded-xl border border-surface-border p-6 shadow-xs space-y-4">
            <div className="flex items-center space-x-2 text-primary font-bold text-base">
              <Shield className="w-5 h-5" />
              <h2>1. Ephemeral In-Memory Document Processing</h2>
            </div>
            <p className="text-xs text-ink-muted leading-relaxed">
              When a PDF is uploaded, it is held strictly in temporary serverless execution memory. We do not use any
              database (no PostgreSQL, MongoDB, Prisma, or Redis). The original document is never persisted to disk or
              permanent blob storage.
            </p>
            <ul className="space-y-2 text-xs text-ink-muted">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-status-success flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Server-side PDF validation:</strong> Checks magic bytes (<code>%PDF-</code>), detects
                  password encryption, and enforces an 8 MB / 50-page limit.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-status-success flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Page Boundary Preservation:</strong> Extracted text is indexed by true 1-based PDF page numbers,
                  ensuring citations correspond to real physical pages in the source document.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-status-success flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Scanned Document Detection:</strong> If a PDF contains insufficient extractable characters
                  (such as an image-only scan), the system alerts the user that text-based PDFs are required in v1.0.
                </span>
              </li>
            </ul>
          </div>

          {/* Section 2: Groq AI Integration */}
          <div className="bg-white rounded-xl border border-surface-border p-6 shadow-xs space-y-4">
            <div className="flex items-center space-x-2 text-navy-900 font-bold text-base">
              <Search className="w-5 h-5 text-blue-600" />
              <h2>2. Adversarial Prompting & Groq AI Analysis</h2>
            </div>
            <p className="text-xs text-ink-muted leading-relaxed">
              The application leverages high-throughput Groq AI inference with low-temperature settings to prioritize
              factual fidelity over creative speculation.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="p-4 rounded-lg bg-surface-bg border border-surface-border space-y-2">
                <h3 className="text-xs font-bold text-navy-900">Untrusted Input Containment</h3>
                <p className="text-[11.5px] text-ink-muted leading-relaxed">
                  The system prompt instructs the model to treat the document strictly as data, neutralizing any prompt
                  injection instructions embedded in uploaded files.
                </p>
              </div>
              <div className="p-4 rounded-lg bg-surface-bg border border-surface-border space-y-2">
                <h3 className="text-xs font-bold text-navy-900">Alternative Explanations</h3>
                <p className="text-[11.5px] text-ink-muted leading-relaxed">
                  Rather than prematurely alleging deception or fraud, the model is required to provide plausible benign
                  reasons (such as clerical oversights, revised deadlines, or conflicting drafts).
                </p>
              </div>
            </div>
          </div>

          {/* Section 3: Verification */}
          <div className="bg-white rounded-xl border border-surface-border p-6 shadow-xs space-y-4">
            <div className="flex items-center space-x-2 text-status-warning font-bold text-base">
              <AlertOctagon className="w-5 h-5" />
              <h2>3. Verbatim Citation Corroboration</h2>
            </div>
            <p className="text-xs text-ink-muted leading-relaxed">
              To eliminate AI hallucination, every finding returned by Groq is subjected to an automated verification
              algorithm:
            </p>
            <ol className="list-decimal list-inside space-y-2 text-xs text-ink-muted">
              <li>
                <strong>Page Boundary Check:</strong> Ensures cited pages fall strictly within the 1..N page range of the document.
              </li>
              <li>
                <strong>Verbatim Substring Search:</strong> Locates the cited quotation in the extracted text of the cited page.
              </li>
              <li>
                <strong>Badging & Transparency:</strong> Findings where the quotation matches the source are badged as{' '}
                <span className="font-semibold text-status-success">Verified in Source</span>. Any discrepancies are flagged
                for attorney review.
              </li>
            </ol>
          </div>

          {/* CTA Box */}
          <div className="bg-navy-900 text-white rounded-xl p-8 text-center space-y-4">
            <h3 className="text-xl font-bold">Ready to analyze your case files?</h3>
            <p className="text-xs text-slate-300 max-w-lg mx-auto">
              Upload your PDF document to receive an immediate structured breakdown of facts, clues, and potential inconsistencies.
            </p>
            <div>
              <Link
                href="/"
                className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-lg text-sm font-semibold bg-primary hover:bg-primary-hover text-white transition-colors"
              >
                <span>Upload a Document Now</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
