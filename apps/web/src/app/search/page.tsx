'use client';

import React, { useState } from 'react';
import { Navbar } from '@/components/layout/Navbar';
import { api } from '@/lib/api-client';
import { SearchResultItem } from '@/types';
import { Search, ExternalLink, Globe, Clock, ShieldCheck, RefreshCw } from 'lucide-react';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [totalResults, setTotalResults] = useState(0);
  const [executionTime, setExecutionTime] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    try {
      const res = await api.search(query.trim(), 15);
      setResults(res.results);
      setTotalResults(res.total_results);
      setExecutionTime(res.execution_time_ms);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-cyber-bg">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold font-mono text-white">Live Multi-Source Search</h1>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Execute single-hop, aggregated search queries across all active permitted connectors.
          </p>
        </div>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
            <input
              type="text"
              required
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search across Wikipedia, Internet Archive, Scholarly Datasets..."
              className="w-full bg-cyber-card border border-cyber-border rounded-xl pl-12 pr-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyber-cyan focus:ring-1 focus:ring-cyber-cyan font-mono transition-all"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="flex items-center space-x-2 bg-cyber-cyan hover:bg-cyan-400 text-slate-950 font-bold px-6 py-3 rounded-xl text-sm shadow-glow-cyan transition-all disabled:opacity-50"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4 stroke-[2.5]" />}
            <span>Query Sources</span>
          </button>
        </form>

        {/* Results summary */}
        {searched && (
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 border-b border-cyber-border/60 pb-3">
            <span>
              Discovered <span className="text-cyber-cyan font-bold">{totalResults}</span> records for &quot;{query}&quot;
            </span>
            {executionTime && <span>Execution Time: {executionTime.toFixed(1)} ms</span>}
          </div>
        )}

        {/* Results List */}
        <div className="space-y-4">
          {loading ? (
            <div className="text-center py-12 space-y-3 font-mono text-xs text-cyber-cyan">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto text-cyber-cyan" />
              <p>Querying Pluggable Connectors with SSRF Validation...</p>
            </div>
          ) : results.length > 0 ? (
            results.map((item, idx) => (
              <div key={idx} className="glass-panel rounded-xl p-5 border border-cyber-border space-y-2 hover:border-slate-500 transition-colors">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-cyan-950 text-cyber-cyan border border-cyber-cyan/30">
                      {item.source_name}
                    </span>
                    {item.publication_date && (
                      <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {item.publication_date}
                      </span>
                    )}
                  </div>
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-1 text-xs font-mono text-cyber-cyan hover:underline"
                  >
                    <span>Visit Source</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>

                <h3 className="text-base font-bold text-white hover:text-cyber-cyan transition-colors">
                  <a href={item.url} target="_blank" rel="noopener noreferrer">
                    {item.title}
                  </a>
                </h3>

                <p className="text-xs text-slate-300 font-mono leading-relaxed bg-cyber-bg/50 p-3 rounded-lg border border-cyber-border/40">
                  {item.snippet}
                </p>
              </div>
            ))
          ) : searched ? (
            <div className="glass-panel rounded-xl p-8 text-center text-xs font-mono text-slate-400">
              No matching records discovered across active connectors.
            </div>
          ) : null}
        </div>
      </main>
    </div>
  );
}
