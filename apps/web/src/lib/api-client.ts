import {
  Investigation,
  InvestigationEvent,
  EvidenceRecord,
  SourceDocument,
  ExtractedEntity,
  SearchResultItem,
  SourceConnectorStatus,
  InvestigationReport,
} from '@/types';
import { frontendConfig } from './config';

const API_BASE = frontendConfig.apiUrl;

class ApiClient {
  private getHeaders(): HeadersInit {
    return {
      'Content-Type': 'application/json',
    };
  }


  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}/api/v1${endpoint}`;
    const res = await fetch(url, {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...options.headers,
      },
    });

    if (!res.ok) {
      let errorMsg = `HTTP Error ${res.status}`;
      try {
        const data = await res.json();
        errorMsg = data.message || data.detail || errorMsg;
      } catch (_) {}
      throw new Error(errorMsg);
    }

    return res.json() as Promise<T>;
  }

  // Auth
  async login(email: string, password: string) {
    return this.request<{ access_token: string; user: any }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async getMe() {
    return this.request<any>('/auth/me');
  }

  // Investigations
  async listInvestigations(): Promise<Investigation[]> {
    return this.request<Investigation[]>('/investigations');
  }

  async getInvestigation(id: string): Promise<Investigation> {
    return this.request<Investigation>(`/investigations/${id}`);
  }

  async createInvestigation(data: {
    title: string;
    description?: string;
    target_clue: string;
    clue_type: string;
    max_depth?: number;
    max_total_queries?: number;
  }): Promise<Investigation> {
    return this.request<Investigation>('/investigations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async startInvestigation(id: string): Promise<Investigation> {
    return this.request<Investigation>(`/investigations/${id}/start`, {
      method: 'POST',
    });
  }

  async cancelInvestigation(id: string): Promise<Investigation> {
    return this.request<Investigation>(`/investigations/${id}/cancel`, {
      method: 'POST',
    });
  }

  async getEvents(id: string): Promise<InvestigationEvent[]> {
    return this.request<InvestigationEvent[]>(`/investigations/${id}/events`);
  }

  async getEvidence(id: string): Promise<EvidenceRecord[]> {
    return this.request<EvidenceRecord[]>(`/investigations/${id}/evidence`);
  }

  async getDocuments(id: string): Promise<SourceDocument[]> {
    return this.request<SourceDocument[]>(`/investigations/${id}/documents`);
  }

  async getEntities(id: string): Promise<ExtractedEntity[]> {
    return this.request<ExtractedEntity[]>(`/investigations/${id}/entities`);
  }

  async getReport(id: string): Promise<InvestigationReport> {
    return this.request<InvestigationReport>(`/investigations/${id}/report`);
  }

  // Search
  async search(query: string, maxResults: number = 10): Promise<{ query: string; total_results: number; execution_time_ms: number; results: SearchResultItem[] }> {
    return this.request('/search', {
      method: 'POST',
      body: JSON.stringify({ query, max_results: maxResults }),
    });
  }

  // Sources
  async listSources(): Promise<SourceConnectorStatus[]> {
    return this.request<SourceConnectorStatus[]>('/sources');
  }
}

export const api = new ApiClient();
