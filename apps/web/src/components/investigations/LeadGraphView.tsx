'use client';

import React, { useState, useMemo } from 'react';
import { LeadGraphResponse, GraphNode, GraphEdge } from '@/types';
import {
  Compass,
  Layers,
  Network,
  RefreshCw,
  AlertCircle,
  ExternalLink,
  Shield,
  Tag,
  ArrowRight,
  Filter,
  Maximize2,
} from 'lucide-react';

interface LeadGraphViewProps {
  graph: LeadGraphResponse | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

export const LeadGraphView: React.FC<LeadGraphViewProps> = ({
  graph,
  loading,
  error,
  onRetry,
}) => {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [filterType, setFilterType] = useState<string>('all');
  const [zoomLevel, setZoomLevel] = useState<number>(1);

  // Filter nodes based on selected category, ensuring root seed node is never hidden unexpectedly
  const filteredNodes = useMemo(() => {
    if (!graph || !graph.nodes) return [];
    if (filterType === 'all') return graph.nodes;
    const isSeed = (n: GraphNode) => n.type === 'seed' || n.id.startsWith('seed:') || n.depth === 0;
    if (filterType === 'leads') {
      return graph.nodes.filter((n) => isSeed(n) || (!n.id.startsWith('ent:') && n.status !== 'extracted'));
    }
    if (filterType === 'entities') {
      return graph.nodes.filter((n) => isSeed(n) || n.id.startsWith('ent:') || n.status === 'extracted');
    }
    return graph.nodes.filter((n) => isSeed(n) || n.type === filterType);
  }, [graph, filterType]);

  const activeNodeIds = useMemo(() => {
    return new Set(filteredNodes.map((n) => n.id));
  }, [filteredNodes]);

  const filteredEdges = useMemo(() => {
    if (!graph || !graph.edges) return [];
    return graph.edges.filter(
      (e) => activeNodeIds.has(e.source) && activeNodeIds.has(e.target)
    );
  }, [graph, activeNodeIds]);

  // Compute 2D node layout positions
  const { nodePositions, canvasHeight } = useMemo(() => {
    const positions = new Map<string, { x: number; y: number }>();
    if (!filteredNodes.length) return { nodePositions: positions, canvasHeight: 520 };

    // Group by depth
    const depthGroups = new Map<number, GraphNode[]>();
    filteredNodes.forEach((node) => {
      const d = node.depth || 0;
      if (!depthGroups.has(d)) depthGroups.set(d, []);
      depthGroups.get(d)!.push(node);
    });

    const maxDepth = Math.max(1, ...Array.from(depthGroups.keys()));
    const canvasWidth = 840;
    const computedHeight = Math.max(520, (maxDepth + 1) * 140);

    depthGroups.forEach((nodesInDepth, depth) => {
      const y = 60 + (depth / (maxDepth + 0.5)) * (computedHeight - 120);
      const count = nodesInDepth.length;
      nodesInDepth.forEach((node, index) => {
        const x = count === 1 ? canvasWidth / 2 : 80 + (index / (count - 1)) * (canvasWidth - 160);
        positions.set(node.id, { x, y });
      });
    });

    return { nodePositions: positions, canvasHeight: computedHeight };
  }, [filteredNodes]);

  if (loading) {
    return (
      <div className="glass-panel rounded-xl border border-cyber-border p-12 text-center space-y-4">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-cyber-cyan" />
        <p className="text-sm font-mono text-slate-300">
          Synthesizing Autonomous Lead Discovery Graph...
        </p>
        <span className="text-xs font-mono text-slate-500">
          Correlating parent leads, entity links, and depth lineage
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-panel rounded-xl border border-rose-900/60 p-8 text-center space-y-4 bg-rose-950/20">
        <AlertCircle className="w-8 h-8 mx-auto text-rose-400" />
        <div className="space-y-1">
          <h4 className="text-sm font-bold text-white font-mono">Failed to Load Lead Graph</h4>
          <p className="text-xs text-rose-300/80 font-mono">{error}</p>
        </div>
        <button
          onClick={onRetry}
          className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-mono bg-cyber-card border border-cyber-border text-slate-200 hover:text-white hover:border-cyber-cyan transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry Connection</span>
        </button>
      </div>
    );
  }

  if (filteredNodes.length === 0 && (graph?.nodes?.length || 0) > 0) {
    return (
      <div className="glass-panel rounded-xl border border-cyber-border p-12 text-center space-y-4 font-mono">
        <Filter className="w-8 h-8 mx-auto text-slate-500" />
        <div className="space-y-1 max-w-md mx-auto">
          <h4 className="text-sm font-bold text-white">No Items in Selected Filter</h4>
          <p className="text-xs text-slate-400">
            No graph nodes match filter category &quot;{filterType}&quot;.
          </p>
        </div>
        <button
          onClick={() => setFilterType('all')}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs bg-cyber-card border border-cyber-border text-cyber-cyan hover:underline"
        >
          <span>Reset Filter to All ({graph?.total_nodes || 0} nodes)</span>
        </button>
      </div>
    );
  }

  if (!graph || graph.is_empty || !graph.nodes || (graph.nodes.length <= 1 && (graph.edges?.length || 0) === 0)) {
    return (
      <div className="glass-panel rounded-xl border border-cyber-border p-12 text-center space-y-4">
        <Network className="w-10 h-10 mx-auto text-slate-500 stroke-[1.5]" />
        <div className="space-y-1 max-w-md mx-auto">
          <h4 className="text-sm font-bold text-white font-mono">No Lead Branches Discovered Yet</h4>
          <p className="text-xs text-slate-400 font-mono leading-relaxed">
            Target clue &quot;{graph?.target_clue || 'Investigation'}&quot; has not spawned multi-hop
            lead relationships. Active discovery leads and entity correlations will populate this
            topology automatically.
          </p>
        </div>
        <button
          onClick={onRetry}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-mono text-cyber-cyan bg-cyber-card border border-cyber-border hover:bg-cyber-card/80 transition-all"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Graph</span>
        </button>
      </div>
    );
  }

  const getNodeColor = (node: GraphNode) => {
    if (node.type === 'seed' || node.status === 'root') {
      return {
        fill: '#06202a',
        stroke: '#00f2ff',
        text: '#00f2ff',
        badge: 'bg-cyan-950 text-cyber-cyan border-cyber-cyan/40',
      };
    }
    if (node.id.startsWith('ent:') || ['person', 'organization', 'domain'].includes(node.type)) {
      return {
        fill: '#0f172a',
        stroke: '#10b981',
        text: '#34d399',
        badge: 'bg-emerald-950 text-emerald-300 border-emerald-700/60',
      };
    }
    return {
      fill: '#1e1b4b',
      stroke: '#818cf8',
      text: '#c7d2fe',
      badge: 'bg-indigo-950 text-indigo-300 border-indigo-700/60',
    };
  };

  return (
    <div className="space-y-4">
      {/* Controls & Filter Bar */}
      <div className="glass-panel rounded-xl p-4 border border-cyber-border flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center space-x-2">
          <span className="text-slate-400 flex items-center gap-1">
            <Filter className="w-3.5 h-3.5" /> Filter:
          </span>
          {['all', 'leads', 'entities'].map((category) => (
            <button
              key={category}
              onClick={() => setFilterType(category)}
              className={`px-2.5 py-1 rounded capitalize transition-all ${
                filterType === category
                  ? 'bg-cyber-cyan text-slate-950 font-bold shadow-glow-cyan'
                  : 'bg-cyber-card text-slate-400 hover:text-white border border-cyber-border'
              }`}
            >
              {category}
            </button>
          ))}
        </div>

        <div className="flex items-center space-x-3 text-slate-400">
          <span>Nodes: <strong className="text-white">{filteredNodes.length}</strong></span>
          <span>Edges: <strong className="text-white">{filteredEdges.length}</strong></span>
          <div className="flex items-center space-x-1 border-l border-cyber-border/60 pl-3">
            <button
              onClick={() => setZoomLevel((z) => Math.max(0.7, z - 0.1))}
              className="px-2 py-0.5 bg-cyber-card rounded border border-cyber-border hover:text-white"
              title="Zoom Out"
            >
              -
            </button>
            <span className="text-[11px] w-12 text-center">{(zoomLevel * 100).toFixed(0)}%</span>
            <button
              onClick={() => setZoomLevel((z) => Math.min(1.5, z + 0.1))}
              className="px-2 py-0.5 bg-cyber-card rounded border border-cyber-border hover:text-white"
              title="Zoom In"
            >
              +
            </button>
            <button
              onClick={() => setZoomLevel(1)}
              className="p-1 bg-cyber-card rounded border border-cyber-border hover:text-white ml-1"
              title="Reset Zoom"
            >
              <Maximize2 className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      {/* Interactive Visual Graph Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 glass-panel rounded-xl border border-cyber-border overflow-hidden relative bg-[#060a12]/90 min-h-[500px]">
          <div className="absolute top-3 left-3 z-10 flex items-center space-x-2 text-[10px] font-mono text-slate-500 pointer-events-none">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-cyber-cyan"></span> Seed Clue
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-indigo-400"></span> Discovered Lead
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span> Extracted Entity
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-amber-400"></span> AI Inferred Link
            </span>
          </div>

          <div
            className="w-full h-full overflow-auto flex items-center justify-center p-4"
            style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'top center' }}
          >
            <svg
              className="w-full"
              viewBox={`0 0 840 ${canvasHeight}`}
              style={{ minWidth: '760px', height: `${canvasHeight}px` }}
            >
              <defs>
                <marker
                  id="arrow"
                  viewBox="0 0 10 10"
                  refX="18"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#38bdf8" opacity="0.7" />
                </marker>
                <marker
                  id="arrow-green"
                  viewBox="0 0 10 10"
                  refX="18"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981" opacity="0.7" />
                </marker>
                <marker
                  id="arrow-amber"
                  viewBox="0 0 10 10"
                  refX="18"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#f59e0b" opacity="0.8" />
                </marker>
              </defs>

              {/* Render Connection Edges */}
              {filteredEdges.map((edge) => {
                const srcPos = nodePositions.get(edge.source);
                const tgtPos = nodePositions.get(edge.target);
                if (!srcPos || !tgtPos) return null;

                const isAI = edge.origin === 'ai_inferred';
                const isEntity = edge.source.startsWith('ent:') || edge.target.startsWith('ent:');
                const isSelected =
                  selectedNode && (selectedNode.id === edge.source || selectedNode.id === edge.target);

                const strokeColor = isSelected
                  ? '#00f2ff'
                  : isAI
                  ? '#f59e0b'
                  : isEntity
                  ? '#10b981'
                  : '#38bdf8';
                const marker = isAI
                  ? 'url(#arrow-amber)'
                  : isEntity
                  ? 'url(#arrow-green)'
                  : 'url(#arrow)';

                return (
                  <g key={edge.id} className="transition-all">
                    <line
                      x1={srcPos.x}
                      y1={srcPos.y}
                      x2={tgtPos.x}
                      y2={tgtPos.y}
                      stroke={strokeColor}
                      strokeWidth={isSelected ? 2 : 1.2}
                      strokeDasharray={isAI ? '4 3' : isEntity ? '3 3' : 'none'}
                      opacity={isSelected ? 0.95 : 0.5}
                      markerEnd={marker}
                    />
                    <text
                      x={(srcPos.x + tgtPos.x) / 2}
                      y={(srcPos.y + tgtPos.y) / 2 - 4}
                      fill={isAI ? '#f59e0b' : '#64748b'}
                      fontSize="9"
                      fontFamily="monospace"
                      textAnchor="middle"
                    >
                      {edge.label}
                    </text>
                  </g>
                );
              })}

              {/* Render Graph Nodes */}
              {filteredNodes.map((node) => {
                const pos = nodePositions.get(node.id);
                if (!pos) return null;

                const colors = getNodeColor(node);
                const isSelected = selectedNode?.id === node.id;
                const isRoot = node.type === 'seed' || node.status === 'root';
                const nodeRadius = isRoot ? 26 : 20;

                return (
                  <g
                    key={node.id}
                    className="cursor-pointer group"
                    onClick={() => setSelectedNode(node)}
                    transform={`translate(${pos.x}, ${pos.y})`}
                  >
                    {/* Outer Glow */}
                    <circle
                      r={nodeRadius + 4}
                      fill="none"
                      stroke={colors.stroke}
                      strokeWidth={isSelected ? 2.5 : 1}
                      opacity={isSelected ? 0.8 : 0.25}
                      className={isSelected ? 'animate-pulse' : ''}
                    />

                    {/* Node Core */}
                    <circle
                      r={nodeRadius}
                      fill={colors.fill}
                      stroke={colors.stroke}
                      strokeWidth={isSelected ? 2 : 1.5}
                    />

                    {/* Node Label & Subtext */}
                    <text
                      y={4}
                      fill={colors.text}
                      fontSize={isRoot ? '10' : '9'}
                      fontWeight="bold"
                      fontFamily="monospace"
                      textAnchor="middle"
                    >
                      {node.label.length > 14 ? `${node.label.substring(0, 12)}…` : node.label}
                    </text>

                    <text
                      y={nodeRadius + 14}
                      fill="#94a3b8"
                      fontSize="8"
                      fontFamily="monospace"
                      textAnchor="middle"
                      className="opacity-75 group-hover:opacity-100"
                    >
                      d:{node.depth} [{node.type}]
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>

        {/* Selected Node Details Panel */}
        <div className="glass-panel rounded-xl border border-cyber-border p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-cyber-border/60">
            <h4 className="text-xs font-mono font-bold text-white uppercase flex items-center gap-1.5">
              <Compass className="w-3.5 h-3.5 text-cyber-cyan" /> Node Inspector
            </h4>
            {selectedNode && (
              <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${getNodeColor(selectedNode).badge}`}>
                {selectedNode.type}
              </span>
            )}
          </div>

          {selectedNode ? (
            <div className="space-y-4 text-xs font-mono">
              <div>
                <span className="text-[10px] text-slate-400 uppercase">Lead / Entity Value</span>
                <div className="text-white font-bold text-sm mt-0.5 break-all">
                  {selectedNode.label}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] bg-cyber-card/40 p-3 rounded-lg border border-cyber-border/40">
                <div>
                  <span className="text-slate-400">Recursion Depth:</span>
                  <div className="text-cyber-cyan font-bold">{selectedNode.depth}</div>
                </div>
                <div>
                  <span className="text-slate-400">Relationship:</span>
                  <div className="text-emerald-400 uppercase font-bold">
                    {selectedNode.metadata?.relationship_kind || (selectedNode.depth <= 1 ? 'direct' : 'inferred')}
                  </div>
                </div>
                {selectedNode.confidence !== undefined && selectedNode.confidence !== null && (
                  <div className="col-span-2 pt-1 border-t border-cyber-border/30">
                    <span className="text-slate-400">Confidence Score:</span>
                    <div className="text-white font-bold">{(selectedNode.confidence * 100).toFixed(0)}%</div>
                  </div>
                )}
              </div>

              {/* Supporting Evidence Excerpt */}
              {selectedNode.metadata?.evidence_excerpt && (
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-bold">Supporting Text Excerpt</span>
                  <blockquote className="bg-cyber-card/60 p-2.5 rounded-lg border-l-2 border-cyber-cyan text-[11px] text-slate-300 mt-1 italic leading-relaxed">
                    &quot;{String(selectedNode.metadata.evidence_excerpt)}&quot;
                  </blockquote>
                </div>
              )}

              {/* Source Link */}
              {selectedNode.metadata?.source_url && (
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-bold">Original Source Document</span>
                  <div className="mt-1">
                    <a
                      href={selectedNode.metadata.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded bg-cyber-card border border-cyber-border text-[11px] text-cyber-cyan hover:underline hover:border-cyber-cyan transition-colors break-all"
                    >
                      <ExternalLink className="w-3 h-3 flex-shrink-0" />
                      <span className="truncate max-w-[200px]">{selectedNode.metadata.source_title || selectedNode.metadata.source_url}</span>
                    </a>
                  </div>
                </div>
              )}

              {selectedNode.metadata && Object.keys(selectedNode.metadata).length > 0 && (
                <div>
                  <span className="text-[10px] text-slate-400 uppercase">Provenance Metadata</span>
                  <div className="bg-cyber-card/70 p-3 rounded-lg border border-cyber-border/40 mt-1 space-y-1.5 text-[11px] text-slate-300">
                    {Object.entries(selectedNode.metadata)
                      .filter(([k]) => !['evidence_excerpt', 'source_url', 'source_title'].includes(k))
                      .map(([k, v]) => (
                        <div key={k} className="flex justify-between gap-2">
                          <span className="text-slate-400 capitalize">{k.replace(/_/g, ' ')}:</span>
                          <span className="text-white truncate max-w-[180px]">{String(v)}</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              <button
                onClick={() => setSelectedNode(null)}
                className="w-full text-center py-1.5 rounded bg-cyber-card border border-cyber-border text-[11px] text-slate-400 hover:text-white transition-colors"
              >
                Clear Selection
              </button>
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500 font-mono text-xs space-y-2">
              <Network className="w-8 h-8 mx-auto text-slate-600 stroke-[1.5]" />
              <p>Click any node in the topology graph to inspect its recursion lineage and metadata.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
