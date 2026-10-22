'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Navbar } from '@/components/layout/Navbar';
import { NewInvestigationModal } from '@/components/investigations/NewInvestigationModal';
import { InvestigationCard } from '@/components/investigations/InvestigationCard';
import { api } from '@/lib/api-client';
import { Investigation } from '@/types';
import {
  Compass,
  Search,
  Activity,
  Layers,
  Database,
  ShieldCheck,
  Plus,
  RefreshCw,
  FolderOpen,
} from 'lucide-react';

export default function DashboardPage() {
  const router = useRouter();
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [filter, setFilter] = useState<'all' | 'running' | 'completed' | 'partial' | 'failed'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await api.listInvestigations();
      setInvestigations(data);
    } catch (err) {
      console.error('Error fetching investigations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 6000);
    return () => clearInterval(interval);
  }, []);

  const runningCount = investigations.filter((i) => i.status === 'running').length;
  const completedCount = investigations.filter((i) => i.status === 'completed').length;
  const partialCount = investigations.filter((i) => i.status === 'partial').length;
  const failedCount = investigations.filter((i) => i.status === 'failed').length;
  const queuedCount = investigations.filter((i) => i.status === 'pending' || i.status === 'queued').length;

  const filteredInvestigations = investigations.filter((inv) => {
    const matchesFilter = filter === 'all' ? true : inv.status === filter;
    const matchesSearch =
      (inv.title || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (inv.target_clue || '').toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="min-h-screen flex flex-col bg-cyber-bg">
      <Navbar onNewInvestigation={() => setIsModalOpen(true)} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Top Metric Header */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="glass-panel rounded-xl p-5 border border-cyber-border/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400 uppercase">Active Scans</span>
              <Activity className="w-4 h-4 text-cyber-cyan" />
            </div>
            <div className="mt-2 flex items-baseline space-x-2">
              <span className="text-2xl font-bold font-mono text-white">{runningCount}</span>
              <span className="text-xs text-cyber-cyan font-mono">
                {queuedCount > 0 ? `${queuedCount} queued` : 'running now'}
              </span>
            </div>
          </div>

          <div className="glass-panel rounded-xl p-5 border border-cyber-border/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400 uppercase">Completed Scans</span>
              <ShieldCheck className="w-4 h-4 text-cyber-emerald" />
            </div>
            <div className="mt-2 flex items-baseline space-x-2">
              <span className="text-2xl font-bold font-mono text-white">{completedCount}</span>
              <span className="text-xs text-cyber-emerald font-mono">synthesized</span>
            </div>
          </div>

          <div className="glass-panel rounded-xl p-5 border border-cyber-border/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400 uppercase">Partial / Failed</span>
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
            </div>
            <div className="mt-2 flex items-baseline space-x-2">
              <span className="text-2xl font-bold font-mono text-white">{partialCount + failedCount}</span>
              <span className="text-xs text-amber-300 font-mono">
                {partialCount} partial, {failedCount} failed
              </span>
            </div>
          </div>

          <div className="glass-panel rounded-xl p-5 border border-cyber-border/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400 uppercase">Total Operations</span>
              <Compass className="w-4 h-4 text-slate-300" />
            </div>
            <div className="mt-2 flex items-baseline space-x-2">
              <span className="text-2xl font-bold font-mono text-white">{investigations.length}</span>
              <span className="text-xs text-slate-400 font-mono">persisted records</span>
            </div>
          </div>
        </div>

        {/* Action / Search & Filter Controls */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Filter by title, domain, clue..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-cyber-card border border-cyber-border rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyber-cyan transition-all font-mono"
            />
          </div>

          <div className="flex items-center space-x-2 w-full sm:w-auto justify-end">
            <div className="flex bg-cyber-card p-1 rounded-lg border border-cyber-border text-xs font-mono flex-wrap gap-1">
              <button
                onClick={() => setFilter('all')}
                className={`px-3 py-1 rounded transition-colors ${
                  filter === 'all' ? 'bg-cyber-bg text-cyber-cyan border border-cyber-cyan/30' : 'text-slate-400 hover:text-white'
                }`}
              >
                All ({investigations.length})
              </button>
              <button
                onClick={() => setFilter('running')}
                className={`px-3 py-1 rounded transition-colors ${
                  filter === 'running' ? 'bg-cyber-bg text-cyber-cyan border border-cyber-cyan/30' : 'text-slate-400 hover:text-white'
                }`}
              >
                Running ({runningCount})
              </button>
              <button
                onClick={() => setFilter('completed')}
                className={`px-3 py-1 rounded transition-colors ${
                  filter === 'completed' ? 'bg-cyber-bg text-cyber-emerald border border-cyber-emerald/30' : 'text-slate-400 hover:text-white'
                }`}
              >
                Completed ({completedCount})
              </button>
              {partialCount > 0 && (
                <button
                  onClick={() => setFilter('partial')}
                  className={`px-3 py-1 rounded transition-colors ${
                    filter === 'partial' ? 'bg-cyber-bg text-amber-300 border border-amber-400/40' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Partial ({partialCount})
                </button>
              )}
              {failedCount > 0 && (
                <button
                  onClick={() => setFilter('failed')}
                  className={`px-3 py-1 rounded transition-colors ${
                    filter === 'failed' ? 'bg-cyber-bg text-rose-300 border border-rose-500/40' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Failed ({failedCount})
                </button>
              )}
            </div>

            <button
              onClick={loadData}
              title="Refresh"
              className="p-2 bg-cyber-card border border-cyber-border rounded-lg text-slate-400 hover:text-white hover:border-slate-500 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Investigations Grid */}
        {loading && investigations.length === 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="glass-panel rounded-xl p-5 border border-cyber-border animate-pulse h-48"></div>
            ))}
          </div>
        ) : filteredInvestigations.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredInvestigations.map((inv) => (
              <InvestigationCard key={inv.id} investigation={inv} />
            ))}
          </div>
        ) : (
          <div className="glass-panel rounded-xl p-12 text-center border border-dashed border-cyber-border space-y-4">
            <div className="w-12 h-12 rounded-full bg-cyber-card border border-cyber-border mx-auto flex items-center justify-center text-slate-400">
              <FolderOpen className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">No Investigations Found</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                Start by initiating your first autonomous recursive discovery run with a clue or identifier.
              </p>
            </div>
            <button
              onClick={() => setIsModalOpen(true)}
              className="inline-flex items-center space-x-2 bg-cyber-cyan hover:bg-cyan-400 text-slate-950 font-semibold px-4 py-2 rounded-lg text-xs shadow-glow-cyan transition-all"
            >
              <Plus className="w-4 h-4 stroke-[2.5]" />
              <span>Launch First Investigation</span>
            </button>
          </div>
        )}
      </main>

      {/* New Investigation Modal */}
      <NewInvestigationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreated={(id) => router.push(`/investigations/${id}`)}
      />
    </div>
  );
}
