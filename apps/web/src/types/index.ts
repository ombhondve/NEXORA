export type ClueType = 'text' | 'name' | 'domain' | 'url' | 'image' | 'pdf';

export type InvestigationStatus = 'pending' | 'queued' | 'running' | 'completed' | 'partial' | 'cancelled' | 'failed';

export interface Investigation {
  id: string;
  user_id?: string | null;
  title: string;
  description?: string | null;
  target_clue: string;
  clue_type: ClueType;
  status: InvestigationStatus;
  max_depth: number;
  current_depth: number;
  max_total_queries: number;
  progress_percent: number;
  stop_reason?: string | null;
  created_at: string;
  updated_at: string;
}

export interface InvestigationEvent {
  id: string;
  investigation_id: string;
  event_type: string;
  message: string;
  details_json: Record<string, any>;
  created_at: string;
}

export interface EvidenceRecord {
  id: string;
  investigation_id: string;
  document_id?: string;
  title: string;
  extracted_passage: string;
  relevance_score: number;
  uncertainty_score: number;
  confidence_level: 'high' | 'medium' | 'low' | 'unverified';
  why_included: string;
  is_verified_source_statement: boolean;
  contradictions_noted?: string;
  created_at: string;
  // Provenance & Quality properties
  source_url?: string;
  source_title?: string;
  connector_name?: string;
  retrieved_at?: string;
  publication_date?: string;
  source_verification_status?: 'primary' | 'secondary' | 'simulated' | 'unverified';
  is_simulated?: boolean;
}

export interface SourceDocument {
  id: string;
  investigation_id: string;
  connector_name: string;
  title: string;
  url: string;
  canonical_url: string;
  snippet: string;
  mime_type: string;
  publication_date?: string;
  retrieved_at: string;
}

export interface ExtractedEntity {
  id: string;
  investigation_id: string;
  document_id?: string;
  entity_type: 'person' | 'organization' | 'domain' | 'email' | 'location' | 'date' | 'identifier';
  entity_value: string;
  normalized_value: string;
  confidence: number;
  context_snippet?: string;
  created_at: string;
}

export interface SearchResultItem {
  title: string;
  url: string;
  snippet: string;
  source_name: string;
  publication_date?: string;
  relevance_score: number;
  metadata?: Record<string, any>;
}

export interface SourceConnectorStatus {
  name: string;
  display_name: string;
  connector_type: string;
  is_enabled: boolean;
  rate_limit_per_minute: number;
  coverage_info: string;
  requires_api_key: boolean;
  is_configured: boolean;
  health_status?: 'online' | 'offline' | 'simulated' | 'unconfigured';
  is_simulated?: boolean;
}

export interface InvestigationReport {
  investigation_id: string;
  title: string;
  target_clue: string;
  status: string;
  summary_markdown: string;
  total_sources_scanned: number;
  total_evidence_collected: number;
  total_entities_correlated: number;
  generated_at: string;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  depth: number;
  status: string;
  confidence?: number;
  metadata?: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  confidence?: number;
  relationship_kind?: 'direct' | 'inferred' | 'unverified';
  evidence_id?: string;
  evidence_title?: string;
  source_url?: string;
  confidence_rationale?: string;
  origin?: 'source_derived' | 'deterministic' | 'ai_inferred';
}

export interface LeadGraphResponse {
  investigation_id: string;
  target_clue: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_nodes: number;
  total_edges: number;
  is_empty: boolean;
}

export interface AIHealthResponse {
  status: 'ready' | 'fallback_active' | 'rate_limited' | 'quota_exhausted' | 'configuration_error' | 'disabled' | 'unavailable' | 'error';
  provider: string;
  model: string;
  primary_provider?: string;
  fallback_provider?: string;
  details: string;
  gemini_configured?: boolean;
  groq_configured?: boolean;
  gemini_status?: string;
  groq_status?: string;
}

export interface AIEvidenceSummaryItem {
  evidence_id: string;
  source_title: string;
  main_subject: string;
  key_facts: string[];
  relevance_to_investigation: string;
  limitations?: string | null;
}

export interface AIEntityCandidate {
  entity_type: string;
  entity_value: string;
  normalized_value: string;
  evidence_ids: string[];
  context_snippet: string;
  confidence: number;
}

export interface AIRelationshipCandidate {
  source_entity: string;
  target_entity: string;
  relationship_type: string;
  relationship_kind: string;
  evidence_ids: string[];
  explanation: string;
  confidence: number;
}

export interface AIInvestigationAnalysis {
  investigation_id: string;
  model_name: string;
  objective: string;
  executive_summary: string;
  key_findings: string[];
  evidence_summaries: AIEvidenceSummaryItem[];
  entities: AIEntityCandidate[];
  relationships: AIRelationshipCandidate[];
  conflicts_and_limitations: string[];
  missing_information: string[];
  unverified_claims: string[];
  analyzed_evidence_count: number;
  created_at?: string;
}

export interface AIQuestionResponse {
  investigation_id: string;
  question: string;
  answer: string;
  supporting_evidence_ids: string[];
  supporting_source_urls: string[];
  insufficient_evidence: boolean;
  confidence_assessment: string;
}
