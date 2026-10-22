'use client';

import React, { useEffect } from 'react';
import Link from 'next/link';
import { Navbar } from '@/components/layout/Navbar';
import { AlertCircle, RefreshCw, ArrowLeft } from 'lucide-react';

export default function InvestigationError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Next.js Investigation Route Error caught by boundary:', error);
  }, [error]);

  return (
    <div className="min-h-screen flex flex-col bg-cyber-bg">
      <Navbar />
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="glass-panel max-w-lg w-full p-8 rounded-xl border border-rose-900/60 bg-rose-950/20 text-center space-y-4 font-mono">
          <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
          <h2 className="text-base font-bold text-white">Investigation Dossier Render Error</h2>
          <p className="text-xs text-rose-300/80 leading-relaxed">
            {error?.message || 'An unexpected error occurred while rendering the investigation topology.'}
          </p>
          {error?.digest && (
            <span className="text-[10px] text-slate-500 block">
              Error Digest: {error.digest}
            </span>
          )}
          <div className="flex items-center justify-center space-x-3 pt-2">
            <button
              onClick={() => reset()}
              className="flex items-center space-x-1.5 px-4 py-2 bg-cyber-card border border-cyber-border rounded-lg text-xs text-white hover:border-cyber-cyan transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Component</span>
            </button>
            <Link
              href="/dashboard"
              className="flex items-center space-x-1 px-4 py-2 text-xs text-slate-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Return to Dashboard</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
