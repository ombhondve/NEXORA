'use client';

import React, { useState } from 'react';
import { AIQuestionResponse, EvidenceRecord } from '@/types';
import { api } from '@/lib/api-client';
import {
  MessageSquare,
  Send,
  RefreshCw,
  AlertCircle,
  HelpCircle,
  CheckCircle2,
  ExternalLink,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';

interface AskNexoraTabProps {
  investigationId: string;
  evidence: EvidenceRecord[];
}

export function AskNexoraTab({ investigationId, evidence }: AskNexoraTabProps) {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<AIQuestionResponse[]>([]);

  const exampleQuestions = [
    'What are the strongest verified findings in this investigation?',
    'What key entities and organizations were uncovered?',
    'Are there conflicting claims or source contradictions?',
    'What critical information or leads are still missing?',
  ];

  const handleAsk = async (queryText?: string) => {
    const q = (queryText || question).trim();
    if (!q || loading) return;

    setLoading(true);
    setError(null);
    try {
      const response = await api.askInvestigation(investigationId, q);
      setHistory((prev) => [response, ...prev]);
      if (!queryText) setQuestion('');
    } catch (err: any) {
      console.error('Ask NEXORA error:', err);
      setError(
        err?.message ||
          'Failed to query AI assistant. Verify that GEMINI_API_KEY or GROQ_API_KEY is configured in backend environment.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 font-mono text-xs">
      {/* Search / Question Prompt Bar */}
      <div className="glass-panel p-5 rounded-xl border border-cyber-border space-y-4">
        <div className="flex items-center space-x-2 text-white">
          <MessageSquare className="w-4 h-4 text-cyber-cyan" />
          <h2 className="text-sm font-bold">Ask NEXORA (Evidence-Grounded Q&A)</h2>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAsk();
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question strictly grounded in this investigation's collected evidence..."
            className="flex-1 px-4 py-2.5 rounded-lg bg-cyber-bg/80 border border-cyber-border/80 text-white placeholder-slate-500 focus:outline-none focus:border-cyber-cyan text-xs"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="px-5 py-2.5 rounded-lg bg-cyber-cyan text-slate-950 font-bold hover:bg-cyan-400 transition-all shadow-glow-cyan flex items-center space-x-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <span>Inquire</span>
                <Send className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </form>

        {/* Quick Example Prompt Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-[10px] text-slate-500">Quick inquiries:</span>
          {exampleQuestions.map((ex, idx) => (
            <button
              key={idx}
              onClick={() => {
                setQuestion(ex);
                handleAsk(ex);
              }}
              disabled={loading}
              className="px-2.5 py-1 rounded bg-cyber-card/40 border border-cyber-border/60 text-slate-400 hover:text-cyber-cyan hover:border-cyber-cyan/40 text-[10px] transition-colors"
            >
              {ex}
            </button>
          ))}
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl border border-rose-800/80 bg-rose-950/30 text-rose-300 space-y-2">
          <div className="flex items-center space-x-2 font-bold">
            <AlertCircle className="w-4 h-4 text-rose-400" />
            <span>AI Provider Connection Failed</span>
          </div>
          <p className="text-[11px] leading-relaxed">{error}</p>
        </div>
      )}

      {/* Loading state indicator */}
      {loading && (
        <div className="glass-panel p-6 rounded-xl border border-cyber-border text-center space-y-2">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-cyber-cyan" />
          <p className="text-white text-xs font-bold">Reasoning Over Investigation Evidence...</p>
          <p className="text-slate-400 text-[10px]">
            Synthesizing facts and verifying supporting source citations.
          </p>
        </div>
      )}

      {/* Answers History */}
      {history.length === 0 && !loading && (
        <div className="glass-panel p-8 rounded-xl border border-cyber-border/60 text-center space-y-3">
          <HelpCircle className="w-8 h-8 text-slate-600 mx-auto" />
          <h3 className="text-sm font-bold text-white">Ask Anything About This Investigation</h3>
          <p className="text-slate-400 text-[11px] max-w-md mx-auto">
            The AI assistant answers solely based on verified evidence records collected in this dossier. It will refuse to speculate if evidence is insufficient.
          </p>
        </div>
      )}

      {history.map((item, idx) => (
        <div
          key={idx}
          className="glass-panel p-6 rounded-xl border border-cyber-border space-y-4 font-mono text-xs"
        >
          {/* Question Header */}
          <div className="flex items-center justify-between text-slate-400 border-b border-cyber-border/40 pb-2">
            <div className="flex items-center space-x-2">
              <span className="text-cyber-cyan font-bold">Q:</span>
              <span className="text-white font-semibold text-sm">{item.question}</span>
            </div>
            <span
              className={`px-2 py-0.5 rounded text-[9px] uppercase ${
                item.confidence_assessment === 'high'
                  ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                  : 'bg-amber-950 text-amber-400 border border-amber-800'
              }`}
            >
              Confidence: {item.confidence_assessment}
            </span>
          </div>

          {/* Insufficient Evidence Warning Banner */}
          {item.insufficient_evidence && (
            <div className="p-3.5 rounded-lg bg-amber-950/40 border border-amber-800/80 text-amber-300 flex items-start space-x-2.5">
              <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div className="space-y-0.5">
                <span className="font-bold text-[11px] uppercase tracking-wide">
                  Insufficient Evidence Notice
                </span>
                <p className="text-[11px] text-amber-200/90 leading-relaxed font-sans">
                  The evidence currently gathered does not contain conclusive facts to answer this inquiry directly. The response below notes the limitation rather than speculating.
                </p>
              </div>
            </div>
          )}

          {/* Answer Text */}
          <div className="text-slate-200 text-sm leading-relaxed font-sans whitespace-pre-wrap">
            {item.answer}
          </div>

          {/* Supporting Evidence Citations */}
          {(item.supporting_evidence_ids.length > 0 ||
            item.supporting_source_urls.length > 0) && (
            <div className="pt-3 border-t border-cyber-border/40 space-y-2">
              <span className="text-[10px] uppercase font-bold text-slate-400">
                Ground-Truth Citations:
              </span>
              <div className="flex flex-wrap gap-2">
                {item.supporting_evidence_ids.map((eid) => (
                  <span
                    key={eid}
                    className="px-2 py-1 rounded bg-cyber-card border border-cyber-border text-cyber-cyan text-[10px]"
                  >
                    Evidence: {eid.substring(0, 8)}...
                  </span>
                ))}
                {item.supporting_source_urls.map((url, uidx) => (
                  <a
                    key={uidx}
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-1 px-2 py-1 rounded bg-cyan-950/40 border border-cyan-800/40 text-cyber-cyan hover:underline text-[10px]"
                  >
                    <ExternalLink className="w-3 h-3" />
                    <span>{new URL(url).hostname}</span>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
