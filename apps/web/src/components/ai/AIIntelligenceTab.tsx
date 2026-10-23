'use client';

import React, { useState, useEffect } from 'react';
import {
  AIInvestigationAnalysis,
  EvidenceRecord,
  AIHealthResponse,
} from '@/types';
import { api } from '@/lib/api-client';
import {
  Brain,
  Sparkles,
  RefreshCw,
  AlertTriangle,
  ShieldCheck,
  CheckCircle2,
  HelpCircle,
  ExternalLink,
  ChevronRight,
  Layers,
  ArrowRight,
  Wifi,
  WifiOff,
} from 'lucide-react';

interface AIIntelligenceTabProps {
  investigationId: string;
  evidence: EvidenceRecord[];
  initialAnalysis?: AIInvestigationAnalysis | null;
  onSelectEvidence?: (evidenceId: string) => void;
  onAnalysisComplete?: (analysis: AIInvestigationAnalysis) => void;
}

export function AIIntelligenceTab({
  investigationId,
  evidence,
  initialAnalysis,
  onSelectEvidence,
  onAnalysisComplete,
}: AIIntelligenceTabProps) {
  const [analysis, setAnalysis] = useState<AIInvestigationAnalysis | null>(initialAnalysis || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [providerHealth, setProviderHealth] = useState<AIHealthResponse | null>(null);

  // Safely check AI provider readiness on mount
  useEffect(() => {
    let mounted = true;
    api.getAIHealth()
      .then((health) => {
        if (mounted) setProviderHealth(health);
      })
      .catch(() => {
        if (mounted) {
          setProviderHealth({
            status: 'unreachable',
            provider: 'ollama',
            model: 'qwen3:4b',
            ollama_base_url: 'unconfigured',
            details: 'AI health endpoint unreachable.',
          });
        }
      });
    return () => {
      mounted = false;
    };
  }, []);

  const handleRunAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.analyzeInvestigation(investigationId);
      setAnalysis(result);
      if (onAnalysisComplete) {
        onAnalysisComplete(result);
      }
    } catch (err: any) {
      console.error('AI analysis error:', err);
      const msg = err?.message || 'Failed to complete AI analysis.';
      setError(msg);
      // Notice: previous successful analysis is preserved in state and not discarded!
    } finally {
      setLoading(false);
    }
  };

  const isProviderReady = providerHealth?.status === 'ready';

  return (
    <div className="space-y-6 font-mono text-xs">
      {/* Action / Status Header */}
      <div className="glass-panel p-5 rounded-xl border border-cyber-border/80 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-cyber-cyan/10 border border-cyber-cyan/30 text-cyber-cyan">
            <Brain className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-sm font-bold text-white">AI Evidence Intelligence</h2>
              <span className="px-2 py-0.5 rounded text-[10px] bg-cyan-950/80 text-cyber-cyan border border-cyber-cyan/30">
                {providerHealth?.model || 'qwen3:4b'} @ {providerHealth?.provider || 'Ollama'}
              </span>
              {providerHealth && (
                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] border ${
                    providerHealth.status === 'ready'
                      ? 'bg-emerald-950/80 text-emerald-400 border-emerald-600/40'
                      : providerHealth.status === 'disabled'
                      ? 'bg-slate-900 text-slate-400 border-slate-700'
                      : 'bg-amber-950/80 text-amber-300 border-amber-600/40'
                  }`}
                  title={providerHealth.details}
                >
                  {providerHealth.status === 'ready' ? (
                    <Wifi className="w-3 h-3 text-emerald-400" />
                  ) : (
                    <WifiOff className="w-3 h-3 text-amber-400" />
                  )}
                  <span className="capitalize">{providerHealth.status.replace('_', ' ')}</span>
                </span>
              )}
            </div>
            <p className="text-slate-400 text-[11px] mt-0.5">
              Grounded OSINT summarization, contextual entity extraction, and relationship discovery
            </p>
          </div>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={loading || evidence.length === 0}
          className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-cyber-cyan text-slate-950 font-semibold hover:bg-cyan-400 transition-all shadow-glow-cyan disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Analyzing Evidence...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-3.5 h-3.5" />
              <span>{analysis ? 'Re-Analyze Evidence' : 'Analyze Evidence'}</span>
            </>
          )}
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl border border-rose-800/80 bg-rose-950/30 text-rose-300 space-y-3 font-mono">
          <div className="flex items-center space-x-2 font-bold text-rose-200">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <span>AI Provider Notice</span>
          </div>
          <p className="text-[11px] leading-relaxed">{error}</p>

          {error.includes('OLLAMA_BASE_URL') && (
            <div className="p-3 bg-cyber-bg/80 border border-cyber-border/70 rounded-lg space-y-2 text-[10px] text-slate-300">
              <div className="font-bold text-cyber-cyan flex items-center gap-1.5">
                <span>Required Vercel Configuration Key:</span>
                <code className="px-1.5 py-0.5 rounded bg-slate-900 border border-cyber-cyan/40 text-cyber-cyan font-bold">
                  OLLAMA_BASE_URL
                </code>
              </div>
              <p className="text-slate-400">
                In cloud deployments (Vercel), serverless functions run in isolated AWS Lambda containers.
                Set <code className="text-white">OLLAMA_BASE_URL</code> in your Vercel Project Settings &rarr; Environment Variables to your reachable HTTPS Ollama host (e.g. Cloudflare Tunnel, ngrok tunnel, or cloud GPU instance).
              </p>
              <div className="font-mono text-slate-400 bg-slate-950 p-2 rounded border border-cyber-border/50 text-[10px]">
                OLLAMA_BASE_URL=https://your-reachable-ollama-host
              </div>
            </div>
          )}

          <div className="pt-1 flex items-center space-x-3">
            <button
              onClick={handleRunAnalysis}
              disabled={loading}
              className="px-3 py-1.5 rounded bg-rose-900/60 border border-rose-700 text-white hover:bg-rose-800 transition-colors disabled:opacity-50 text-xs font-semibold"
            >
              Retry Analysis
            </button>
            {analysis && (
              <span className="text-[10px] text-slate-400">
                (Previously synthesized analysis remains available below)
              </span>
            )}
          </div>
        </div>
      )}

      {/* Loading Placeholder for re-analysis */}
      {loading && analysis && (
        <div className="p-3 rounded-lg border border-cyber-cyan/30 bg-cyber-card/40 flex items-center space-x-3 text-cyber-cyan">
          <RefreshCw className="w-4 h-4 animate-spin" />
          <span className="text-[11px]">Re-synthesizing intelligence findings from updated evidence records...</span>
        </div>
      )}

      {/* Loading Placeholder for initial analysis */}
      {loading && !analysis && (
        <div className="glass-panel p-10 rounded-xl border border-cyber-border text-center space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-cyber-cyan" />
          <p className="text-white font-bold text-sm">Evaluating OSINT Evidence Passages...</p>
          <p className="text-slate-400 text-[11px] max-w-md mx-auto">
            Extracting entities, validating source citations, and mapping relational candidates using {providerHealth?.model || 'qwen3:4b'}.
          </p>
        </div>
      )}

      {/* Empty State before first analysis */}
      {!loading && !analysis && !error && (
        <div className="glass-panel p-8 rounded-xl border border-cyber-border/60 text-center space-y-4">
          <Brain className="w-10 h-10 text-slate-600 mx-auto" />
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-white">No AI Analysis Run Yet</h3>
            <p className="text-slate-400 text-[11px] max-w-lg mx-auto">
              NEXORA has gathered {evidence.length} evidence records. Click &quot;Analyze Evidence&quot; to synthesize executive findings and extract contextual entity relationships.
            </p>
          </div>
          {evidence.length === 0 && (
            <p className="text-amber-400/90 text-[11px]">
              Note: At least 1 verified evidence record is required to run AI analysis.
            </p>
          )}
        </div>
      )}

      {/* Analysis Results Display */}
      {analysis && (
        <div className="space-y-6">
          {/* Executive Summary Card */}
          <div className="glass-panel p-6 rounded-xl border border-cyber-cyan/30 bg-cyber-card/60 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-bold text-cyber-cyan tracking-wider">
                Executive Intelligence Synthesis
              </span>
              <span className="text-slate-500 text-[10px]">
                {analysis.created_at ? new Date(analysis.created_at).toLocaleString() : 'Recent'}
              </span>
            </div>
            <p className="text-slate-200 text-sm leading-relaxed font-sans">
              {analysis.executive_summary}
            </p>
            <div className="flex items-center space-x-2 text-[10px] text-slate-400 pt-2 border-t border-cyber-border/40">
              <ShieldCheck className="w-3.5 h-3.5 text-cyber-emerald" />
              <span>Objective: {analysis.objective}</span>
              <span className="text-slate-600">•</span>
              <span>Analyzed Sources: {analysis.analyzed_evidence_count}</span>
            </div>
          </div>

          {/* Key Verifiable Findings */}
          <div className="glass-panel p-5 rounded-xl border border-cyber-border space-y-3">
            <h3 className="text-xs font-bold uppercase text-white flex items-center space-x-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-cyber-cyan" />
              <span>Key Grounded Findings ({analysis.key_findings.length})</span>
            </h3>
            <div className="space-y-2">
              {analysis.key_findings.map((finding, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-cyber-bg/60 border border-cyber-border/60 text-slate-200 text-xs flex items-start space-x-2.5 font-sans"
                >
                  <span className="font-mono text-cyber-cyan font-bold">{idx + 1}.</span>
                  <div className="flex-1 leading-relaxed">
                    <span>{finding}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Contextual Discovered Relationships */}
          {analysis.relationships && analysis.relationships.length > 0 && (
            <div className="glass-panel p-5 rounded-xl border border-cyber-border space-y-3">
              <h3 className="text-xs font-bold uppercase text-white flex items-center space-x-2">
                <Layers className="w-3.5 h-3.5 text-cyber-emerald" />
                <span>Contextual Relationship Candidates ({analysis.relationships.length})</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {analysis.relationships.map((rel, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-lg bg-cyber-bg/70 border border-cyber-border/70 space-y-2"
                  >
                    <div className="flex items-center justify-between text-[11px]">
                      <div className="flex items-center space-x-1.5 font-bold text-white">
                        <span>{rel.source_entity}</span>
                        <ArrowRight className="w-3 h-3 text-cyber-cyan" />
                        <span>{rel.target_entity}</span>
                      </div>
                      <span
                        className={`px-1.5 py-0.5 rounded text-[9px] uppercase ${
                          rel.relationship_kind === 'direct'
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            : 'bg-indigo-950 text-indigo-300 border border-indigo-800'
                        }`}
                      >
                        {rel.relationship_kind}
                      </span>
                    </div>

                    <div className="text-[11px] text-cyber-cyan font-semibold">
                      Relation: <span className="text-white">{rel.relationship_type}</span>
                    </div>

                    <p className="text-[11px] text-slate-300 font-sans leading-relaxed">
                      {rel.explanation}
                    </p>

                    <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-cyber-border/40">
                      <span>Confidence: {(rel.confidence * 100).toFixed(0)}%</span>
                      {rel.evidence_ids.length > 0 && (
                        <span className="text-cyber-cyan">
                          Evidence: {rel.evidence_ids.join(', ')}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Discovered Contextual Entities */}
          {analysis.entities && analysis.entities.length > 0 && (
            <div className="glass-panel p-5 rounded-xl border border-cyber-border space-y-3">
              <h3 className="text-xs font-bold uppercase text-white">
                Contextual Entities ({analysis.entities.length})
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                {analysis.entities.map((ent, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-cyber-card/40 border border-cyber-border/50 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="px-1.5 py-0.5 rounded text-[9px] uppercase bg-cyan-950/70 text-cyber-cyan border border-cyber-cyan/30">
                          {ent.entity_type}
                        </span>
                        <span className="text-[10px] text-slate-400 font-bold">
                          {(ent.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="font-bold text-white text-xs mt-1 truncate">
                        {ent.entity_value}
                      </div>
                    </div>
                    {ent.context_snippet && (
                      <p className="text-[10px] text-slate-400 mt-1 line-clamp-2 italic font-sans">
                        &quot;{ent.context_snippet}&quot;
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Limitations, Information Gaps & Unverified Claims */}
          {(analysis.conflicts_and_limitations.length > 0 ||
            analysis.unverified_claims.length > 0 ||
            analysis.missing_information.length > 0) && (
            <div className="glass-panel p-5 rounded-xl border border-amber-800/60 bg-amber-950/10 space-y-3">
              <div className="flex items-center space-x-2 text-amber-400 font-bold text-xs uppercase">
                <AlertTriangle className="w-4 h-4" />
                <span>Intelligence Limitations & Information Gaps</span>
              </div>

              {analysis.conflicts_and_limitations.length > 0 && (
                <div className="space-y-1">
                  <span className="text-slate-300 font-semibold text-[11px]">
                    Contradictions & Source Caveats:
                  </span>
                  <ul className="list-disc list-inside text-slate-400 text-[11px] space-y-0.5">
                    {analysis.conflicts_and_limitations.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {analysis.unverified_claims.length > 0 && (
                <div className="space-y-1 pt-1">
                  <span className="text-slate-300 font-semibold text-[11px]">
                    Unverified Claims Requiring Corroboration:
                  </span>
                  <ul className="list-disc list-inside text-slate-400 text-[11px] space-y-0.5">
                    {analysis.unverified_claims.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {analysis.missing_information.length > 0 && (
                <div className="space-y-1 pt-1">
                  <span className="text-slate-300 font-semibold text-[11px]">
                    Identified Intelligence Gaps:
                  </span>
                  <ul className="list-disc list-inside text-slate-400 text-[11px] space-y-0.5">
                    {analysis.missing_information.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
