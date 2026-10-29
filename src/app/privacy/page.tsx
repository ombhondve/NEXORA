import React from 'react';
import Navbar from '@/components/Navbar';
import Link from 'next/link';
import { ArrowLeft, Shield, Lock, EyeOff, Server, AlertCircle } from 'lucide-react';

export default function PrivacyPage() {
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
            <h1 className="text-3xl font-black text-navy-900 tracking-tight">Privacy, Security & AI Limitations</h1>
            <p className="text-sm text-ink-muted mt-2 leading-relaxed">
              Transparent policies detailing data transmission, temporary processing, third-party AI considerations, and
              legal disclaimers.
            </p>
          </div>

          {/* Zero Storage Notice */}
          <div className="bg-white rounded-xl border border-surface-border p-6 shadow-xs space-y-4">
            <div className="flex items-center space-x-2 text-primary font-bold text-base">
              <EyeOff className="w-5 h-5" />
              <h2>Zero Permanent Storage Architecture</h2>
            </div>
            <p className="text-xs text-ink-muted leading-relaxed">
              <strong>AI Legal Clue Finder does not maintain any persistent database.</strong> There is no MongoDB,
              PostgreSQL, MySQL, Redis, or cloud storage bucket connected to this application.
            </p>
            <ul className="space-y-2 text-xs text-ink-muted">
              <li>
                • <strong>In-Memory Processing:</strong> Uploaded PDFs are parsed in ephemeral server memory during the
                HTTP request lifecycle and released immediately after extraction.
              </li>
              <li>
                • <strong>No User Tracking:</strong> This version does not require user accounts, passwords, or personal
                profiles.
              </li>
              <li>
                • <strong>No File Logging:</strong> Full document text and sensitive extracted findings are never logged to
                server monitoring or deployment logs.
              </li>
            </ul>
          </div>

          {/* Third-Party AI Data Transmission */}
          <div className="bg-white rounded-xl border border-surface-border p-6 shadow-xs space-y-4">
            <div className="flex items-center space-x-2 text-navy-900 font-bold text-base">
              <Server className="w-5 h-5 text-blue-600" />
              <h2>Groq AI API Integration Notice</h2>
            </div>
            <p className="text-xs text-ink-muted leading-relaxed">
              To analyze the substance of your document, the extracted digital text is transmitted via encrypted HTTPS
              directly to Groq&apos;s cloud API services.
            </p>
            <div className="p-4 rounded-lg bg-surface-bg border border-surface-border text-xs text-ink-muted space-y-2">
              <p>
                <strong>Operator Responsibility:</strong> Before processing confidential or privileged client documents,
                legal operators must independently evaluate Groq&apos;s commercial terms of service, zero-data-retention (ZDR)
                commitments, and security posture in accordance with their jurisdiction&apos;s attorney-client privilege and
                professional conduct rules.
              </p>
              <p>
                We do not claim or represent that third-party AI providers permanently refrain from data retention unless
                an explicit enterprise agreement is executed with that provider.
              </p>
            </div>
          </div>

          {/* Key Security Controls */}
          <div className="bg-white rounded-xl border border-surface-border p-6 shadow-xs space-y-4">
            <div className="flex items-center space-x-2 text-navy-900 font-bold text-base">
              <Lock className="w-5 h-5 text-emerald-600" />
              <h2>Key Security Controls</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-ink-muted">
              <div className="p-3.5 rounded-lg border border-surface-border bg-surface-bg">
                <h3 className="font-bold text-navy-900 mb-1">Server-Side Secret Isolation</h3>
                <p>The Groq API key is stored strictly on the server and is never exposed to browser bundles or client code.</p>
              </div>
              <div className="p-3.5 rounded-lg border border-surface-border bg-surface-bg">
                <h3 className="font-bold text-navy-900 mb-1">Security Headers</h3>
                <p>Every response enforces nosniff, frameguard (DENY), and strict referrer-policy protection headers.</p>
              </div>
              <div className="p-3.5 rounded-lg border border-surface-border bg-surface-bg">
                <h3 className="font-bold text-navy-900 mb-1">Input Boundaries</h3>
                <p>Strict 8 MB file size and 50-page limits prevent memory denial-of-service and context overflow.</p>
              </div>
              <div className="p-3.5 rounded-lg border border-surface-border bg-surface-bg">
                <h3 className="font-bold text-navy-900 mb-1">XSS Prevention</h3>
                <p>Extracted document text and quotations are never rendered as raw HTML or injected into untrusted DOM.</p>
              </div>
            </div>
          </div>

          {/* AI Limitations & Legal Disclaimer */}
          <div className="rounded-xl border border-amber-200 bg-amber-50/60 p-6 space-y-3">
            <div className="flex items-center space-x-2 text-status-warning font-bold text-sm">
              <AlertCircle className="w-5 h-5" />
              <h2>AI Limitations & Disclaimer</h2>
            </div>
            <p className="text-xs text-slate-700 leading-relaxed">
              This tool provides preliminary document review assistance. AI-generated findings may be incomplete,
              misinterpreted, or incorrect and must always be corroborated against original source materials. This
              software does not provide formal legal advice, does not establish guilt or fraud, and does not guarantee
              success in any negotiation, dispute, or litigation.
            </p>
          </div>
        </div>
      </main>
    </>
  );
}
