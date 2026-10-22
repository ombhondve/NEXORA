'use client';

import React, { useEffect } from 'react';
import Link from 'next/link';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';

export default function RootError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Next.js Root Error Boundary caught exception:', error);
  }, [error]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-cyber-bg p-6 text-slate-100 font-mono">
      <div className="glass-panel max-w-lg w-full p-8 rounded-xl border border-rose-900/60 bg-rose-950/20 text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-rose-400 mx-auto" />
        <h1 className="text-lg font-bold text-white">NEXORA System Error</h1>
        <p className="text-xs text-rose-300/80 leading-relaxed">
          {error?.message || 'An unexpected rendering error occurred.'}
        </p>
        {error?.digest && (
          <span className="text-[10px] text-slate-500 block">
            Digest: {error.digest}
          </span>
        )}
        <div className="flex items-center justify-center space-x-3 pt-3">
          <button
            onClick={() => reset()}
            className="flex items-center space-x-1.5 px-4 py-2 bg-cyber-card border border-cyber-border rounded-lg text-xs text-white hover:border-cyber-cyan transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry</span>
          </button>
          <Link
            href="/dashboard"
            className="flex items-center space-x-1 px-4 py-2 bg-cyber-cyan text-slate-950 font-bold rounded-lg text-xs hover:bg-cyan-400 transition-colors"
          >
            <Home className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
