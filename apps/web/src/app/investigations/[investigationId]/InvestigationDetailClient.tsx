'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Navbar } from '@/components/layout/Navbar';
import { EvidenceCard } from '@/components/evidence/EvidenceCard';
import { LeadGraphView } from '@/components/investigations/LeadGraphView';
import { api } from '@/lib/api-client';
import {
  Investigation,
  InvestigationEvent,
  EvidenceRecord,
  SourceDocument,
  ExtractedEntity,
  InvestigationReport,
  LeadGraphResponse,
  AIInvestigationAnalysis,
} from '@/types';
import { AIIntelligenceTab } from '@/components/ai/AIIntelligenceTab';
import { AskNexoraTab } from '@/components/ai/AskNexoraTab';
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
  Network,
  AlertCircle,
  Brain,
  MessageSquare,
  Sparkles,
} from 'lucide-react';

interface ComponentProps {
  params?: {
    investigationId?: string;
  };
}

export default function InvestigationDetailClient({ params }: ComponentProps) {
  const clientParams = useParams();
  const router = useRouter();

  const rawId = params?.investigationId || clientParams?.investigationId;
  const investigationId = (Array.isArray(rawId) ? rawId[0] : rawId) || '';

  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [events, setEvents] = useState<InvestigationEvent[]>([]);
  const [evidence, setEvidence] = useState<EvidenceRecord[]>([]);
  const [documents, setDocuments] = useState<SourceDocument[]>([]);
  const [entities, setEntities] = useState<ExtractedEntity[]>([]);
  const [report, setReport] = useState<InvestigationReport | null>(null);
  const [graph, setGraph] = useState<LeadGraphResponse | null>(null);
  const [aiAnalysis, setAiAnalysis] = useState<AIInvestigationAnalysis | null>(null);

  const [activeTab, setActiveTab] = useState<'graph' | 'ai_analysis' | 'ai_qa' | 'evidence' | 'entities' | 'sources' | 'events' | 'report'>('graph');
  const [loading, setLoading] = useState(true);
  const [graphLoading, setGraphLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isNotFound, setIsNotFound] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const loadData = useCallback(async () => {
    if (!investigationId) {
      setLoading(false);
      return;
    }
    setLoadError(null);
    setIsNotFound(false);
    try {
      // Load core investigation record first
      const inv = await api.getInvestigation(investigationId);
      setInvestigation(inv);

      // Load related collections with non-fatal fallbacks
      const [evts, evds, docs, ents, grph, analysis] = await Promise.all([
        api.getEvents(investigationId).catch(() => [] as InvestigationEvent[]),
        api.getEvidence(investigationId).catch(() => [] as EvidenceRecord[]),
        api.getDocuments(investigationId).catch(() => [] as SourceDocument[]),
        api.getEntities(investigationId).catch(() => [] as ExtractedEntity[]),
        api.getLeadGraph(investigationId).catch(() => null),
        api.getInvestigationAnalysis(investigationId).catch(() => null),
      ]);

      setEvents(evts);
      setEvidence(evds);
      setDocuments(docs);
      setEntities(ents);
      setGraph(grph);
      setAiAnalysis(analysis);
    } catch (err: any) {
      console.error('Failed to load investigation details:', err);
      const msg = err?.message || '';
      if (msg.includes('not found') || msg.includes('404')) {
        setIsNotFound(true);
      } else {
        setLoadError(msg || 'Failed to communicate with investigation database.');
      }
    } finally {
      setLoading(false);
      setGraphLoading(false);
    }
  }, [investigationId]);

  useEffect(() => {
    loadData();
    const interval = setInterval(() => {
      if (investigation?.status === 'running') {
        loadData();
      }
    }, 4000);
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

  const handleFetchAIReport = async () => {
    if (!investigation) return;
    setActionLoading(true);
    try {
      const rep = await api.getAIReport(investigation.id);
      setReport(rep);
      setActiveTab('report');
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleAIAnalysisComplete = useCallback(async (analysis: AIInvestigationAnalysis) => {
    setAiAnalysis(analysis);
    try {
      const updatedGraph = await api.getLeadGraph(investigationId);
      setGraph(updatedGraph);
    } catch (err) {
      console.warn('Failed to refresh lead graph after AI analysis:', err);
    }
  }, [investigationId]);


  if (loading && !investigation && !isNotFound && !loadError) {
    return (
      <div className="min-h-screen flex flex-col bg-cyber-bg">
        <Navbar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-3 font-mono text-sm text-cyber-cyan">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-cyber-cyan" />
            <p>Loading Recursive Investigation Dossier...</p>
            <span className="text-xs text-slate-500 font-mono">
              Querying ID: {investigationId || 'pending'}
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (isNotFound) {
    return (
      <div className="min-h-screen flex flex-col bg-cyber-bg">
        <Navbar />
        <div className="flex-1 flex items-center justify-center text-center p-6">
          <div className="glass-panel max-w-md w-full p-8 rounded-xl border border-cyber-border space-y-4 font-mono">
            <Compass className="w-10 h-10 text-slate-500 mx-auto" />
            <h2 className="text-lg font-bold text-white">Investigation Not Found (404)</h2>
            <p className="text-xs text-slate-400 leading-relaxed">
              No investigation record matches ID: <code className="text-cyber-cyan">{investigationId}</code>.
              The investigation may have been deleted, or the identifier is incorrect.
            </p>
            <div className="pt-2 flex items-center justify-center space-x-3">
              <button
                onClick={loadData}
                className="px-4 py-2 bg-cyber-card border border-cyber-border rounded-lg text-xs text-white hover:border-cyber-cyan transition-colors"
              >
                Retry
              </button>
              <Link
                href="/dashboard"
                className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs bg-cyber-card border border-cyber-border text-cyber-cyan hover:underline"
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

  if (loadError && !investigation) {
    return (
      <div className="min-h-screen flex flex-col bg-cyber-bg">
        <Navbar />
        <div className="flex-1 flex items-center justify-center text-center p-6">
          <div className="glass-panel max-w-md w-full p-8 rounded-xl border border-rose-900/60 bg-rose-950/20 space-y-4 font-mono">
            <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
            <h2 className="text-base font-bold text-white">Investigation Retrieval Failed</h2>
            <p className="text-xs text-rose-300/80 leading-relaxed">{loadError}</p>
            <div className="flex items-center justify-center space-x-3 pt-2">
              <button
                onClick={loadData}
                className="px-4 py-2 bg-cyber-card border border-cyber-border rounded-lg text-xs text-white hover:border-cyber-cyan transition-colors"
              >
                Retry Request
              </button>
              <Link
                href="/dashboard"
                className="px-4 py-2 bg-transparent text-xs text-slate-400 hover:text-white transition-colors"
              >
                Return to Dashboard
              </Link>
            </div>
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
          <div className="glass-panel max-w-md w-full p-8 rounded-xl border border-cyber-border space-y-4 font-mono">
            <Compass className="w-10 h-10 text-slate-500 mx-auto" />
            <h2 className="text-lg font-bold text-white">Investigation Not Found</h2>
            <p className="text-xs text-slate-400 leading-relaxed">
              No investigation record matches ID: <code className="text-cyber-cyan">{investigationId}</code>.
            </p>
            <div className="pt-2">
              <Link
                href="/dashboard"
                className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs bg-cyber-card border border-cyber-border text-cyber-cyan hover:underline"
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

  const renderStatusBadge = () => {
    switch (investigation.status) {
      case 'running':
        return (
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-mono bg-cyan-950/80 text-cyber-cyan border border-cyber-cyan/40">
            <span className="w-2 h-2 rounded-full bg-cyber-cyan animate-ping"></span>
            <span>DISCOVERY ACTIVE</span>
          </div>
        );
      case 'completed':
        return (
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-mono bg-emerald-950/80 text-cyber-emerald border border-cyber-emerald/40">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>DISCOVERY FINALIZED</span>
          </div>
        );
      case 'partial':
        return (
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-mono bg-amber-950/80 text-amber-300 border border-amber-500/40">
            <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
            <span>PARTIAL FINDINGS</span>
          </div>
        );
      case 'failed':
        return (
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-mono bg-rose-950/80 text-rose-300 border border-rose-600/40">
            <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
            <span>DISCOVERY FAILED</span>
          </div>
        );
      case 'cancelled':
        return (
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-mono bg-slate-800 text-slate-300 border border-slate-700">
            <span>CANCELLED</span>
          </div>
        );
      default:
        return (
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-mono bg-amber-950/80 text-cyber-amber border border-cyber-amber/40">
            <Clock className="w-3.5 h-3.5" />
            <span>QUEUED FOR DISCOVERY</span>
          </div>
        );
    }
  };

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
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-mono text-slate-300 bg-cyber-card border border-cyber-border hover:border-slate-500 font-semibold transition-all disabled:opacity-50"
            >
              <FileDown className="w-3.5 h-3.5" />
              <span>Standard Report</span>
            </button>

            <button
              onClick={handleFetchAIReport}
              disabled={actionLoading}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-mono text-slate-950 bg-cyber-cyan hover:bg-cyan-400 font-semibold shadow-glow-cyan transition-all disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5 stroke-[2.5]" />
              <span>Synthesize AI Report</span>
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
                <span className="text-xs font-mono text-slate-400">
                  ID: {investigation.id.length > 8 ? `${investigation.id.substring(0, 8)}...` : investigation.id}
                </span>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-white mt-1">{investigation.title}</h1>
            </div>

            {/* Status indicator */}
            <div>
              {renderStatusBadge()}
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
              <span className="text-cyber-cyan">
                {investigation.stop_reason ||
                  (investigation.status === 'completed'
                    ? 'Lead discovery completed.'
                    : investigation.status === 'partial'
                    ? 'Partial findings retained.'
                    : investigation.status === 'failed'
                    ? 'Investigation failed.'
                    : 'Autonomous expansion ongoing...')}
              </span>
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
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2 text-center font-mono">
            <div className="p-2.5 rounded-lg bg-cyber-card/30 border border-cyber-border/40">
              <div className="text-lg font-bold text-cyber-cyan">{graph?.total_nodes || 0}</div>
              <div className="text-[10px] text-slate-400 uppercase">Graph Nodes</div>
            </div>
            <div className="p-2.5 rounded-lg bg-cyber-card/30 border border-cyber-border/40">
              <div className="text-lg font-bold text-white">{evidence.length}</div>
              <div className="text-[10px] text-slate-400 uppercase">Evidence Records</div>
            </div>
            <div className="p-2.5 rounded-lg bg-cyber-card/30 border border-cyber-border/40">
              <div className="text-lg font-bold text-white">{entities.length}</div>
              <div className="text-[10px] text-slate-400 uppercase">Discovered Entities</div>
            </div>
            <div className="p-2.5 rounded-lg bg-cyber-card/30 border border-cyber-border/40">
              <div className="text-lg font-bold text-white">{documents.length}</div>
              <div className="text-[10px] text-slate-400 uppercase">Scanned Sources</div>
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
            { id: 'graph', label: `Lead Graph (${graph?.total_nodes || 0})`, icon: Network },
            { id: 'ai_analysis', label: 'AI Intelligence', icon: Brain },
            { id: 'ai_qa', label: 'Ask NEXORA', icon: MessageSquare },
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
          {/* Lead Graph Tab (Primary Discovery Topology) */}
          {activeTab === 'graph' && (
            <LeadGraphView
              graph={graph}
              loading={graphLoading}
              error={null}
              onRetry={loadData}
            />
          )}

          {/* AI Intelligence Tab */}
          {activeTab === 'ai_analysis' && (
            <AIIntelligenceTab
              investigationId={investigation.id}
              evidence={evidence}
              initialAnalysis={aiAnalysis}
              onAnalysisComplete={handleAIAnalysisComplete}
            />
          )}

          {/* Ask NEXORA (Evidence-Grounded Q&A) */}
          {activeTab === 'ai_qa' && (
            <AskNexoraTab
              investigationId={investigation.id}
              evidence={evidence}
            />
          )}

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
                    {entities.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="px-4 py-8 text-center text-slate-400">
                          No discrete entities extracted yet.
                        </td>
                      </tr>
                    ) : (
                      entities.map((e) => (
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
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Sources Tab */}
          {activeTab === 'sources' && (
            <div className="glass-panel rounded-xl border border-cyber-border overflow-hidden divide-y divide-cyber-border/40">
              {documents.length === 0 ? (
                <div className="p-8 text-center text-slate-400 text-xs font-mono">
                  No source documents indexed yet for this investigation.
                </div>
              ) : (
                documents.map((doc) => (
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
                ))
              )}
            </div>
          )}

          {/* Timeline / Events Tab */}
          {activeTab === 'events' && (
            <div className="glass-panel rounded-xl border border-cyber-border p-6 space-y-4">
              {events.length === 0 ? (
                <div className="text-center py-8 text-slate-400 text-xs font-mono">
                  No audit events recorded.
                </div>
              ) : (
                <div className="relative border-l border-cyber-border/80 pl-6 space-y-6">
                  {events.map((evt) => (
                    <div key={evt.id} className="relative group">
                      <span className="absolute -left-[31px] top-1 w-2.5 h-2.5 rounded-full bg-cyber-cyan ring-4 ring-cyber-bg"></span>
                      <div className="text-xs font-mono text-slate-400">
                        {evt.created_at ? new Date(evt.created_at).toLocaleTimeString() : 'Recent'}
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
              )}
            </div>
          )}

          {/* Report Tab */}
          {activeTab === 'report' && (
            <div className="glass-panel rounded-xl border border-cyber-border p-6 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-cyber-border/60">
                <div className="flex items-center space-x-2">
                  <FileDown className="w-4 h-4 text-cyber-cyan" />
                  <span className="font-bold text-white text-xs">Investigation Dossier Synthesis</span>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleFetchReport}
                    disabled={actionLoading}
                    className="px-3 py-1.5 rounded-lg text-[11px] font-mono text-slate-300 bg-cyber-card border border-cyber-border hover:border-slate-500 transition-all disabled:opacity-50"
                  >
                    Standard Report
                  </button>
                  <button
                    onClick={handleFetchAIReport}
                    disabled={actionLoading}
                    className="px-3 py-1.5 rounded-lg text-[11px] font-mono text-slate-950 bg-cyber-cyan hover:bg-cyan-400 font-bold shadow-glow-cyan transition-all flex items-center space-x-1 disabled:opacity-50"
                  >
                    <Sparkles className="w-3 h-3" />
                    <span>Synthesize AI Intelligence Dossier</span>
                  </button>
                </div>
              </div>

              {report ? (
                <div className="prose prose-invert max-w-none text-xs font-mono whitespace-pre-wrap leading-relaxed text-slate-200 bg-cyber-bg/80 p-6 rounded-lg border border-cyber-border">
                  {report.summary_markdown}
                </div>
              ) : (
                <div className="text-center py-8 space-y-3 font-mono text-xs text-slate-400">
                  <p>Choose an option above to generate a deterministic OSINT report or an AI-assisted intelligence dossier.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
