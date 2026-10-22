export type ClueType = 'text' | 'name' | 'domain' | 'url' | 'image' | 'pdf';

export type InvestigationStatus = 'pending' | 'running' | 'completed' | 'cancelled' | 'failed';

export interface InvestigationContract {
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

export interface EvidenceContract {
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
