'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Scale, FileSearch, Shield, HelpCircle, PlusCircle } from 'lucide-react';

export default function Navbar({ onReset }: { onReset?: () => void }) {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 w-full border-b border-surface-border bg-white/95 backdrop-blur">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <Link
            href="/"
            onClick={onReset}
            className="flex items-center space-x-3 group transition-opacity hover:opacity-90"
          >
            <div className="w-10 h-10 rounded-lg bg-navy-900 flex items-center justify-center text-white shadow-sm transition-transform group-hover:scale-105">
              <Scale className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="text-base font-bold text-navy-900 tracking-tight">AI Legal Clue Finder</span>
                <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-primary-light text-primary">
                  v1.0
                </span>
              </div>
              <p className="text-xs text-ink-muted hidden sm:block">Evidence-Based Document Intelligence</p>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="flex items-center space-x-1 sm:space-x-4">
            <Link
              href="/"
              onClick={onReset}
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                pathname === '/'
                  ? 'bg-primary-light text-primary font-semibold'
                  : 'text-ink-muted hover:text-navy-900 hover:bg-surface-hover'
              }`}
            >
              <FileSearch className="w-4 h-4" />
              <span>Analysis</span>
            </Link>

            <Link
              href="/how-it-works"
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                pathname === '/how-it-works'
                  ? 'bg-primary-light text-primary font-semibold'
                  : 'text-ink-muted hover:text-navy-900 hover:bg-surface-hover'
              }`}
            >
              <HelpCircle className="w-4 h-4" />
              <span>How It Works</span>
            </Link>

            <Link
              href="/privacy"
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                pathname === '/privacy'
                  ? 'bg-primary-light text-primary font-semibold'
                  : 'text-ink-muted hover:text-navy-900 hover:bg-surface-hover'
              }`}
            >
              <Shield className="w-4 h-4" />
              <span>Privacy & Security</span>
            </Link>

            {onReset && (
              <button
                onClick={onReset}
                className="hidden md:inline-flex items-center space-x-1.5 ml-3 px-3.5 py-1.5 rounded-md text-sm font-medium bg-navy-900 text-white hover:bg-navy-800 transition-colors shadow-sm"
              >
                <PlusCircle className="w-4 h-4 text-blue-400" />
                <span>New Analysis</span>
              </button>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}

