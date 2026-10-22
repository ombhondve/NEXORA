'use client';

import React, { useEffect, useState } from 'react';
import { Navbar } from '@/components/layout/Navbar';
import { api } from '@/lib/api-client';
import { SourceConnectorStatus } from '@/types';
import { Database, CheckCircle2, AlertCircle, Shield, Globe, RefreshCw, Key } from 'lucide-react';

export default function SourcesPage() {
  const [sources, setSources] = useState<SourceConnectorStatus[]>([]);
  const [loading, setLoading] = useState(true);

  const loadSources = async () => {
    try {
      setLoading(true);
      const data = await api.listSources();
      setSources(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSources();
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-cyber-bg">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold font-mono text-white">Source Connectors Registry</h1>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Pluggable data adapters with pre-flight SSRF protection, robots.txt courtesy, and strict rate limits.
            </p>
          </div>
          <button
            onClick={loadSources}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-cyber-card border border-cyber-border rounded-lg text-xs font-mono text-slate-300 hover:text-white transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Status</span>
          </button>
        </div>

        {/* Connectors Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {sources.map((src) => (
            <div key={src.name} className="glass-panel rounded-xl p-6 border border-cyber-border space-y-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-lg bg-cyber-card border border-cyber-border flex items-center justify-center text-cyber-cyan">
                    <Database className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">{src.display_name}</h3>
                    <span className="text-[10px] font-mono uppercase text-slate-400 bg-cyber-bg px-2 py-0.5 rounded border border-cyber-border">
                      {src.connector_type}
                    </span>
                  </div>
                </div>

                {src.is_simulated || src.health_status === 'simulated' ? (
                  <span className="flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-mono bg-purple-950 text-purple-300 border border-purple-800">
                    <Shield className="w-3.5 h-3.5 text-purple-400" />
                    <span>SIMULATED</span>
                  </span>
                ) : src.health_status === 'offline' ? (
                  <span className="flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-mono bg-rose-950 text-rose-300 border border-rose-800">
                    <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
                    <span>OFFLINE</span>
                  </span>
                ) : src.is_configured ? (
                  <span className="flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-mono bg-emerald-950 text-emerald-300 border border-emerald-800">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>ONLINE</span>
                  </span>
                ) : (
                  <span className="flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-mono bg-amber-950 text-amber-300 border border-amber-800">
                    <Key className="w-3.5 h-3.5 text-amber-400" />
                    <span>KEY REQUIRED</span>
                  </span>
                )}
              </div>

              <p className="text-xs text-slate-300 leading-relaxed font-mono bg-cyber-bg/50 p-3 rounded-lg border border-cyber-border/40">
                {src.coverage_info}
              </p>

              <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-2 border-t border-cyber-border/40">
                <span>Rate Limit: {src.rate_limit_per_minute} req/min</span>
                <span>SSRF Verified: Active</span>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
