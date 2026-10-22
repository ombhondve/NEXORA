'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Navbar } from '@/components/layout/Navbar';
import { api } from '@/lib/api-client';
import { Investigation } from '@/types';
import { Terminal, FileDown, ArrowRight, ShieldCheck, RefreshCw } from 'lucide-react';

export default function ReportsPage() {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchList = async () => {
      try {
        setLoading(true);
        const data = await api.listInvestigations();
        setInvestigations(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchList();
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-cyber-bg">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold font-mono text-white">Investigation Reports & Provenance</h1>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Consolidated executive reports with full source attribution, uncertainty scores, and evidence provenance.
          </p>
        </div>

        <div className="glass-panel rounded-xl border border-cyber-border overflow-hidden divide-y divide-cyber-border/40">
          {loading ? (
            <div className="p-8 text-center text-xs font-mono text-cyber-cyan">
              <RefreshCw className="w-5 h-5 animate-spin mx-auto text-cyber-cyan mb-2" />
              <span>Loading Reports Index...</span>
            </div>
          ) : investigations.length > 0 ? (
            investigations.map((inv) => (
              <div key={inv.id} className="p-5 flex items-center justify-between gap-4 hover:bg-cyber-card/30 transition-colors">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyber-card text-cyber-cyan border border-cyber-border uppercase">
                      {inv.clue_type}
                    </span>
                    <span className="text-[11px] font-mono text-slate-400">
                      Created: {new Date(inv.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-white">{inv.title}</h3>
                  <p className="text-xs font-mono text-slate-400">Target: {inv.target_clue}</p>
                </div>

                <Link
                  href={`/investigations/${inv.id}`}
                  className="flex items-center space-x-2 bg-cyber-card hover:bg-cyber-border text-white text-xs font-mono px-4 py-2 rounded-lg border border-cyber-border transition-colors flex-shrink-0"
                >
                  <FileDown className="w-4 h-4 text-cyber-cyan" />
                  <span>View Full Dossier</span>
                </Link>
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-xs font-mono text-slate-400">
              No reports available. Run an investigation to generate a synthesized report.
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
