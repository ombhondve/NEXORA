'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Shield, Search, Database, Terminal, Compass, Plus, Activity } from 'lucide-react';

interface NavbarProps {
  onNewInvestigation?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onNewInvestigation }) => {
  const pathname = usePathname();

  const navItems = [
    { label: 'Investigations', href: '/dashboard', icon: Compass },
    { label: 'Live Search', href: '/search', icon: Search },
    { label: 'Sources & Connectors', href: '/sources', icon: Database },
    { label: 'Reports', href: '/reports', icon: Terminal },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-cyber-border/60 bg-cyber-bg/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <Link href="/dashboard" className="flex items-center space-x-3 group">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-lg bg-cyber-card border border-cyber-cyan/40 shadow-glow-cyan transition-all group-hover:scale-105">
            <Shield className="w-5 h-5 text-cyber-cyan" />
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyber-cyan opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-cyber-cyan"></span>
            </span>
          </div>
          <div>
            <span className="font-mono font-bold text-lg tracking-wider text-slate-100 flex items-center gap-1.5">
              NEXORA <span className="text-xs px-1.5 py-0.5 rounded bg-cyan-950 text-cyber-cyan border border-cyber-cyan/30">OSINT</span>
            </span>
            <p className="text-[10px] text-slate-400 font-mono tracking-tight uppercase">Recursive Discovery Engine</p>
          </div>
        </Link>

        {/* Navigation Items */}
        <nav className="hidden md:flex items-center space-x-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-md text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-cyber-card text-cyber-cyan border border-cyber-cyan/30 shadow-sm'
                    : 'text-slate-300 hover:text-white hover:bg-cyber-card/50'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyber-cyan' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Action Controls */}
        <div className="flex items-center space-x-3">
          <div className="hidden sm:flex items-center space-x-2 text-xs font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-2.5 py-1.5 rounded-full">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>CONNECTORS ONLINE</span>
          </div>

          {onNewInvestigation && (
            <button
              onClick={onNewInvestigation}
              className="flex items-center space-x-2 bg-cyber-cyan hover:bg-cyan-400 text-slate-950 font-semibold px-4 py-2 rounded-lg text-sm shadow-glow-cyan transition-all transform active:scale-95"
            >
              <Plus className="w-4 h-4 stroke-[2.5]" />
              <span>New Investigation</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
