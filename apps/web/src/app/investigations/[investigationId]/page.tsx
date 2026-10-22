'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Navbar } from '@/components/layout/Navbar';
import { EvidenceCard } from '@/components/evidence/EvidenceCard';
import { api } from '@/lib/api-client';
import {
  Investigation,
  InvestigationEvent,
  EvidenceRecord,
  SourceDocument,
  ExtractedEntity,
  InvestigationReport,
} from '@/types';
import {
  Compass,
  ArrowLeft,
  Activity,
  Layers,
  StopCircle,
  FileDown,
  Globe,
  Database,
  Terminal,
  ShieldCheck,
  CheckCircle2,
  Clock,
  ExternalLink,
  RefreshCw,
} from 'lucide-react';

export default function InvestigationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const investigationId = params.investigationId as string;

  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [events, setEvents] = useState<InvestigationEvent[]>([]);
  const [evidence, setEvidence] = useState<EvidenceRecord[]>([]);
  const [documents, setDocuments] = useState<SourceDocument[]>([]);
  const [entities, setEntities] = useState<ExtractedEntity[]>([]);
  const [report, setReport] = useState<InvestigationReport | null>(null);

  const [activeTab, setActiveTab] = useState<'evidence' | 'events' | 'entities' | 'sources' | 'report'>('evidence');
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const loadData = useCallback(async () => {
    if (!investigationId) return;
    try {
      const [inv, evts, evds, docs, ents] = await Promise.all([
        api.getInvestigation(investigationId),
        api.getEvents(investigationId),
        api.getEvidence(investigationId),
        api.getDocuments(investigationId),
        api.getEntities(investigationId),
      ]);
      setInvestigation(inv);
      setEvents(evts);
      setEvidence(evds);
      setDocuments(docs);
      setEntities(ents);
    } catch (err) {
      console.error('Failed to load investigation details:', err);
    } finally {
      setLoading(false);
    }
  }, [investigationId]);

  useEffect(() => {
    loadData();
    // Poll while running
    const interval = setInterval(() => {
      if (investigation?.status === 'running') {
        loadData();
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [loadData, investigation?.status]);

  const handleCancel = async () => {
    if (!investigation) return;
    setActionLoading(true);
    try {
      const updated = await api.cancelInvestigation(investigation.id);
      setInvestigation(updated);
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleFetchReport = async () => {
    if (!investigation) return;
    setActionLoading(true);
    try {
      const rep = await api.getReport(investigation.id);
      setReport(rep);
      setActiveTab('report');
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading && !investigation) {
    return (
      <div className="min-h-screen flex flex-col bg-cyber-bg">
        <Navbar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-3 font-mono text-sm text-cyber-cyan">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-cyber-cyan" />
            <p>Loading Recursive Investigation Dossier...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!investigation) {
    return (
      <div className="min-h-screen flex flex-col bg-cyber-bg">
        <Navbar />
        <div className="flex-1 flex items-center justify-center text-center p-6">
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-white">Investigation Not Found</h2>
            <Link href="/dashboard" className="text-xs font-mono text-cyber-cyan hover:underline">
              Return to Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-cyber-bg">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Navigation Breadcrumb & Back */}
        <div className="flex items-center justify-between">
          <Link
            href="/dashboard"
            className="flex items-center space-x-1.5 text-xs font-mono text-slate-400 hover:text-cyber-cyan transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Investigations</span>
          </Link>

          <div className="flex items-center space-x-3">
            {investigation.status === 'running' && (
              <button
                onClick={handleCancel}
                disabled={actionLoading}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-mono text-rose-300 bg-rose-950/60 border border-rose-800/80 hover:bg-rose-900 transition-all disabled:opacity-50"
              >
                <StopCircle className="w-3.5 h-3.5" />
                <span>Halt Expansion</span>
              </button>
            )}

            <button
              onClick={handleFetchReport}
              disabled={actionLoading}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-mono text-slate-950 bg-cyber-cyan hover:bg-cyan-400 font-semibold shadow-glow-cyan transition-all disabled:opacity-50"
            >
              <FileDown className="w-3.5 h-3.5 stroke-[2.5]" />
              <span>Synthesize Report</span>
            </button>
          </div>
        </div>

        {/* Dossier Header Card */}
        <div className="glass-panel rounded-xl p-6 border border-cyber-border space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="flex items-center space-x-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-cyan-950 text-cyber-cyan border border-cyber-cyan/30">
                  {investigation.clue_type}
                </span>
                <span className="text-xs font-mono text-slate-400">ID: {investigation.id.substring(0, 8)}...</span>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-white mt-1">{investigation.title}</h1>
            </div>

            {/* Status indicator */}
            <div>
              {investigation.status === 'running' ? (
                <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-mono bg-cyan-950/80 text-cyber-cyan border border-cyber-cyan/40">
                  <span className="w-2 h-2 rounded-full bg-cyber-cyan animate-ping"></span>
                  <span>DISCOVERY ACTIVE</span>
                </div>
              ) : (
                <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-mono bg-emerald-950/80 text-cyber-emerald border border-cyber-emerald/40">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>DISCOVERY FINALIZED</span>
                </div>
              )}
            </div>
          </div>

          {/* Clue and Reason */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono bg-cyber-card/50 p-4 rounded-lg border border-cyber-border/60">
            <div>
              <span className="text-slate-400">Target Clue:</span>{' '}
              <span className="text-white font-bold">{investigation.target_clue}</span>
            </div>
            <div>
              <span className="text-slate-400">Termination Reason:</span>{' '}
              <span className="text-cyber-cyan">{investigation.stop_reason || 'Autonomous expansion ongoing...'}</span>
            </div>
          </div>

          {/* Progress Bar & Counters */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-mono text-slate-400">
              <span className="flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-cyber-cyan" />
                Recursion Depth: {investigation.current_depth} / {investigation.max_depth}
              </span>
              <span>Budget Utilized: {investigation.progress_percent}%</span>
            </div>
            <div className="w-full h-2 bg-cyber-bg rounded-full overflow-hidden border border-cyber-border/60">
              <div
                className="h-full bg-gradient-to-r from-cyber-cyan to-cyber-emerald rounded-full transition-all duration-500"
                style={{ width: `${investigation.progress_percent}%` }}
              ></div>
            </div>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-center font-mono">
            <div className="p-2.5 rounded-lg bg-cyber-card/30 border border-cyber-border/40">
              <div className="text-lg font-bold text-white">{evidence.length}</div>
              <div className="text-[10px] text-slate-400 uppercase">Correlated Evidence</div>
            </div>
            <div className="p-2.5 rounded-lg bg-cyber-card/30 border border-cyber-border/40">
              <div className="text-lg font-bold text-white">{entities.length}</div>
              <div className="text-[10px] text-slate-400 uppercase">Discovered Entities</div>
            </div>
            <div className="p-2.5 rounded-lg bg-cyber-card/30 border border-cyber-border/40">
              <div className="text-lg font-bold text-white">{documents.length}</div>
              <div className="text-[10px] text-slate-400 uppercase">Scanned Documents</div>
            </div>
            <div className="p-2.5 rounded-lg bg-cyber-card/30 border border-cyber-border/40">
              <div className="text-lg font-bold text-white">{events.length}</div>
              <div className="text-[10px] text-slate-400 uppercase">Audit Events</div>
            </div>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="flex border-b border-cyber-border/80 space-x-2 text-xs font-mono overflow-x-auto pb-1">
          {[
            { id: 'evidence', label: `Correlated Evidence (${evidence.length})`, icon: ShieldCheck },
            { id: 'entities', label: `Entities (${entities.length})`, icon: Database },
            { id: 'sources', label: `Sources (${documents.length})`, icon: Globe },
            { id: 'events', label: `Live Timeline (${events.length})`, icon: Terminal },
            { id: 'report', label: 'Executive Report', icon: FileDown },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 px-4 py-2.5 rounded-t-lg transition-all border-b-2 whitespace-nowrap ${
                  isActive
                    ? 'border-cyber-cyan text-cyber-cyan bg-cyber-card/70 font-bold'
                    : 'border-transparent text-slate-400 hover:text-white'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Contents */}
        <div className="space-y-4">
          {/* Evidence Tab */}
          {activeTab === 'evidence' && (
            <div className="space-y-4">
              {evidence.length === 0 ? (
                <div className="glass-panel p-8 rounded-xl text-center text-slate-400 text-xs font-mono">
                  No evidence records synthesized yet. If scan is active, findings will appear dynamically.
                </div>
              ) : (
                evidence.map((ev) => <EvidenceCard key={ev.id} evidence={ev} />)
              )}
            </div>
          )}

          {/* Entities Tab */}
          {activeTab === 'entities' && (
            <div className="glass-panel rounded-xl border border-cyber-border overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-cyber-card border-b border-cyber-border text-slate-400 uppercase text-[10px]">
                    <tr>
                      <th className="px-4 py-3">Category</th>
                      <th className="px-4 py-3">Entity Value</th>
                      <th className="px-4 py-3">Confidence</th>
                      <th className="px-4 py-3">Context Snippet</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-cyber-border/40 text-slate-300">
                    {entities.map((e) => (
                      <tr key={e.id} className="hover:bg-cyber-card/30 transition-colors">
                        <td className="px-4 py-2.5">
                          <span className="px-2 py-0.5 rounded bg-cyber-card text-cyber-cyan text-[10px] border border-cyber-border">
                            {e.entity_type}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 font-bold text-white">{e.entity_value}</td>
                        <td className="px-4 py-2.5">
                          <span className="text-emerald-400">{(e.confidence * 100).toFixed(0)}%</span>
                        </td>
                        <td className="px-4 py-2.5 text-slate-400 max-w-md truncate">
                          {e.context_snippet || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Sources Tab */}
          {activeTab === 'sources' && (
            <div className="glass-panel rounded-xl border border-cyber-border overflow-hidden divide-y divide-cyber-border/40">
              {documents.map((doc) => (
                <div key={doc.id} className="p-4 flex items-center justify-between gap-4 hover:bg-cyber-card/30 transition-colors">
                  <div className="space-y-1 max-w-3xl">
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyber-card text-cyber-cyan border border-cyber-border uppercase">
                        {doc.connector_name}
                      </span>
                      {doc.publication_date && (
                        <span className="text-[10px] font-mono text-slate-400">
                          Published: {doc.publication_date}
                        </span>
                      )}
                    </div>
                    <h4 className="text-sm font-bold text-white line-clamp-1">{doc.title}</h4>
                    <p className="text-xs text-slate-400 line-clamp-2">{doc.snippet}</p>
                  </div>
                  <a
                    href={doc.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-1 text-xs font-mono text-cyber-cyan hover:underline flex-shrink-0"
                  >
                    <span>Visit Source</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              ))}
            </div>
          )}

          {/* Timeline / Events Tab */}
          {activeTab === 'events' && (
            <div className="glass-panel rounded-xl border border-cyber-border p-6 space-y-4">
              <div className="relative border-l border-cyber-border/80 pl-6 space-y-6">
                {events.map((evt) => (
                  <div key={evt.id} className="relative group">
                    <span className="absolute -left-[31px] top-1 w-2.5 h-2.5 rounded-full bg-cyber-cyan ring-4 ring-cyber-bg"></span>
                    <div className="text-xs font-mono text-slate-400">
                      {new Date(evt.created_at).toLocaleTimeString()}
                    </div>
                    <div className="text-xs font-mono font-bold text-white mt-0.5">{evt.message}</div>
                    {evt.details_json && Object.keys(evt.details_json).length > 0 && (
                      <pre className="text-[10px] font-mono bg-cyber-card/70 p-2 rounded mt-1.5 text-slate-400 overflow-x-auto">
                        {JSON.stringify(evt.details_json, null, 2)}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Report Tab */}
          {activeTab === 'report' && (
            <div className="glass-panel rounded-xl border border-cyber-border p-6 space-y-4">
              {report ? (
                <div className="prose prose-invert max-w-none text-xs font-mono whitespace-pre-wrap leading-relaxed text-slate-200 bg-cyber-bg/80 p-6 rounded-lg border border-cyber-border">
                  {report.summary_markdown}
                </div>
              ) : (
                <div className="text-center py-8 space-y-3 font-mono text-xs text-slate-400">
                  <p>Click &quot;Synthesize Report&quot; above to compile verified findings and provenance data.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
