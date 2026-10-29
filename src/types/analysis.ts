import { z } from 'zod';

export type AnalysisMode = 'quick' | 'detailed';

export type ReviewPriority = 'high' | 'medium' | 'low';
export type ConfidenceLevel = 'high' | 'medium' | 'low';

// Schema for Extracted PDF Page
export const ExtractedPageSchema = z.object({
  pageNumber: z.number().int().positive(),
  text: z.string(),
  charCount: z.number().int().nonnegative(),
  isUnreadableOrEmpty: z.boolean().default(false),
});

export type ExtractedPage = z.infer<typeof ExtractedPageSchema>;

// Important Fact Schema
export const ImportantFactSchema = z.object({
  id: z.string().optional(),
  title: z.string().min(1, 'Fact title is required'),
  description: z.string().min(1, 'Fact description is required'),
  sourcePage: z.number().int().positive(),
  sourceQuote: z.string().min(1, 'Supporting quotation is required'),
  confidence: z.enum(['high', 'medium', 'low']).default('high'),
  quoteVerified: z.boolean().default(false),
});

export type ImportantFact = z.infer<typeof ImportantFactSchema>;

// Potential Clue Schema
export const PotentialClueSchema = z.object({
  id: z.string().optional(),
  title: z.string().min(1, 'Clue title is required'),
  description: z.string().min(1, 'Clue description is required'),
  significance: z.enum(['high', 'medium', 'low']).default('medium'),
  sourcePages: z.array(z.number().int().positive()).min(1),
  sourceQuotes: z.array(z.string().min(1)).min(1),
  verificationNeeded: z.boolean().default(true),
  quoteVerified: z.boolean().default(false),
});

export type PotentialClue = z.infer<typeof PotentialClueSchema>;

// Inconsistency Schema
export const InconsistencySchema = z.object({
  id: z.string().optional(),
  title: z.string().min(1, 'Inconsistency title is required'),
  description: z.string().min(1, 'Discrepancy explanation is required'),
  sourcePages: z.array(z.number().int().positive()).min(1),
  sourceQuotes: z.array(z.string().min(1)).min(1),
  alternativeExplanations: z.array(z.string()).default([]),
  quoteVerified: z.boolean().default(false),
});

export type Inconsistency = z.infer<typeof InconsistencySchema>;

// Information Gap Schema
export const InformationGapSchema = z.object({
  id: z.string().optional(),
  question: z.string().min(1, 'Gap question is required'),
  reason: z.string().min(1, 'Reason is required'),
  relatedPages: z.array(z.number().int().positive()).default([]),
});

export type InformationGap = z.infer<typeof InformationGapSchema>;

// Investigation Question Schema
export const InvestigationQuestionSchema = z.object({
  id: z.string().optional(),
  question: z.string().min(1, 'Question is required'),
  reason: z.string().min(1, 'Reason is required'),
  relatedPages: z.array(z.number().int().positive()).default([]),
});

export type InvestigationQuestion = z.infer<typeof InvestigationQuestionSchema>;

// Key Entity Schema (Names, Dates, Locations, Financial Amounts)
export const KeyEntitySchema = z.object({
  category: z.enum(['person_organization', 'date', 'location', 'financial_amount', 'other']),
  name: z.string(),
  context: z.string(),
  sourcePage: z.number().int().positive(),
});

export type KeyEntity = z.infer<typeof KeyEntitySchema>;

// Raw AI Output Schema from Groq
export const RawAnalysisOutputSchema = z.object({
  documentSummary: z.string().min(1, 'Document summary is required'),
  importantFacts: z.array(ImportantFactSchema).default([]),
  potentialClues: z.array(PotentialClueSchema).default([]),
  inconsistencies: z.array(InconsistencySchema).default([]),
  informationGaps: z.array(InformationGapSchema).default([]),
  investigationQuestions: z.array(InvestigationQuestionSchema).default([]),
  keyEntities: z.array(KeyEntitySchema).default([]),
  limitations: z.array(z.string()).default([]),
});

export type RawAnalysisOutput = z.infer<typeof RawAnalysisOutputSchema>;

// Analysis Metadata
export interface AnalysisMetadata {
  filename: string;
  fileSizeBytes: number;
  totalPages: number;
  analyzedPages: number;
  unreadablePages: number[];
  analysisMode: AnalysisMode;
  analyzedAt: string;
  modelUsed: string;
  totalFindings: number;
  verifiedQuotesCount: number;
  unverifiedQuotesCount: number;
}

// Complete Analysis Result Returned to Client
export interface CompleteAnalysisResult {
  metadata: AnalysisMetadata;
  analysis: RawAnalysisOutput;
  pages: ExtractedPage[];
}

