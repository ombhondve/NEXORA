export type ClueType = 'text' | 'name' | 'domain' | 'url' | 'image' | 'pdf';

export type InvestigationStatus = 'pending' | 'running' | 'completed' | 'cancelled' | 'failed';

export interface Investigation {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  target_clue: string;
  clue_type: ClueType;
  status: InvestigationStatus;
  max_depth: number;
  current_depth: number;
  max_total_queries: number;
  progress_percent: number;
  stop_reason?: string;
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
