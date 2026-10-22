'use client';

import React, { useState } from 'react';
import { X, Search, Globe, User, Link as LinkIcon, FileText, Cpu, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api-client';
import { ClueType } from '@/types';

interface NewInvestigationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (investigationId: string) => void;
}

export const NewInvestigationModal: React.FC<NewInvestigationModalProps> = ({
  isOpen,
  onClose,
  onCreated,
}) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [targetClue, setTargetClue] = useState('');
  const [clueType, setClueType] = useState<ClueType>('text');
  const [maxDepth, setMaxDepth] = useState(3);
  const [maxQueries, setMaxQueries] = useState(20);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const clueOptions: { type: ClueType; label: string; icon: any; placeholder: string }[] = [
    { type: 'text', label: 'Keyword / Phrase', icon: Search, placeholder: 'e.g. Sovereign AI Alliance' },
    { type: 'domain', label: 'Domain / FQDN', icon: Globe, placeholder: 'e.g. nexora-defense.org' },
    { type: 'name', label: 'Person / Entity', icon: User, placeholder: 'e.g. Dr. Jane Doe' },
    { type: 'url', label: 'Public Web URL', icon: LinkIcon, placeholder: 'https://example.org/publication' },
    { type: 'pdf', label: 'Document Clue', icon: FileText, placeholder: 'Document title, CVE, or report reference' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetClue.trim()) {
      setError('Please provide a target search clue.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const inv = await api.createInvestigation({
        title: title.trim() || `Investigation: ${targetClue.trim()}`,
        description: description.trim() || undefined,
        target_clue: targetClue.trim(),
        clue_type: clueType,
        max_depth: maxDepth,
        max_total_queries: maxQueries,
      });

      // Automatically trigger discovery run
      await api.startInvestigation(inv.id);
      onCreated(inv.id);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to start investigation.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-xl glass-panel bg-cyber-surface border border-cyber-border rounded-xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-cyber-border bg-cyber-bg/50">
          <div className="flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-cyber-cyan" />
            <h2 className="text-lg font-bold font-mono text-white">Initiate Recursive Discovery</h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-cyber-card transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="flex items-center space-x-2 p-3 text-sm text-rose-300 bg-rose-950/50 border border-rose-800/60 rounded-lg">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Target Clue Type Selection */}
          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-slate-300 mb-2">
              1. Clue Category
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {clueOptions.map((opt) => {
                const Icon = opt.icon;
                const isSelected = clueType === opt.type;
                return (
                  <button
                    type="button"
                    key={opt.type}
                    onClick={() => setClueType(opt.type)}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-xs font-medium border transition-all text-left ${
                      isSelected
                        ? 'border-cyber-cyan bg-cyan-950/40 text-cyber-cyan shadow-sm'
                        : 'border-cyber-border bg-cyber-card/60 text-slate-300 hover:border-slate-500'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                    <span className="truncate">{opt.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Primary Search Clue */}
          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-slate-300 mb-2">
              2. Target Clue / Identifier *
            </label>
            <input
              type="text"
              required
              value={targetClue}
              onChange={(e) => setTargetClue(e.target.value)}
              placeholder={clueOptions.find((o) => o.type === clueType)?.placeholder}
              className="w-full bg-cyber-card border border-cyber-border rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyber-cyan focus:ring-1 focus:ring-cyber-cyan transition-all font-mono"
            />
          </div>

          {/* Title & Notes */}
          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-slate-300 mb-2">
              3. Investigation Title (Optional)
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Operation Sovereign Infrastructure"
              className="w-full bg-cyber-card border border-cyber-border rounded-lg px-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyber-cyan transition-all"
            />
          </div>

          {/* Budget Limits Grid */}
          <div className="grid grid-cols-2 gap-4 pt-1">
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">
                Max Recursion Depth: <span className="text-cyber-cyan font-bold">{maxDepth}</span>
              </label>
              <input
                type="range"
                min="1"
                max="5"
                value={maxDepth}
                onChange={(e) => setMaxDepth(parseInt(e.target.value))}
                className="w-full accent-cyber-cyan bg-cyber-card cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>1 (Direct)</span>
                <span>3 (Recommended)</span>
                <span>5 (Deep)</span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">
                Max Total Queries: <span className="text-cyber-cyan font-bold">{maxQueries}</span>
              </label>
              <input
                type="range"
                min="5"
                max="50"
                step="5"
                value={maxQueries}
                onChange={(e) => setMaxQueries(parseInt(e.target.value))}
                className="w-full accent-cyber-cyan bg-cyber-card cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>5</span>
                <span>20 (Standard)</span>
                <span>50</span>
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <div className="pt-3 border-t border-cyber-border flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center space-x-2 bg-cyber-cyan hover:bg-cyan-400 text-slate-950 font-semibold px-5 py-2 rounded-lg text-sm shadow-glow-cyan transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></span>
                  <span>Initiating Engine...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4 stroke-[2.5]" />
                  <span>Launch Discovery</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
