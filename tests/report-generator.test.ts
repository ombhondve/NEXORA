import { describe, it, expect } from 'vitest';
import { generateLegalReportPdf } from '../src/lib/report/generator';
import { CompleteAnalysisResult } from '../src/types/analysis';

describe('PDF Report Generator', () => {
  it('generates a valid binary PDF document with metadata and findings', async () => {
    const mockPayload: CompleteAnalysisResult = {
      metadata: {
        filename: 'Settlement_Agreement_Draft.pdf',
        fileSizeBytes: 245000,
        totalPages: 3,
        analyzedPages: 3,
        unreadablePages: [],
        analysisMode: 'detailed',
        analyzedAt: new Date().toISOString(),
        modelUsed: 'llama-3.3-70b-versatile',
        totalFindings: 4,
        verifiedQuotesCount: 3,
        unverifiedQuotesCount: 1,
      },
      analysis: {
        documentSummary: 'Comprehensive settlement agreement between Fictional Corp and Jane Smith.',
        importantFacts: [
          {
            title: 'Settlement Sum',
            description: 'Settlement amount is $125,000.',
            sourcePage: 1,
            sourceQuote: 'sum of $125,000 shall be paid',
            confidence: 'high',
            quoteVerified: true,
          },
        ],
        potentialClues: [
          {
            title: 'Broad Release Carveout',
            description: 'Section 4 excludes intellectual property claims.',
            significance: 'high',
            sourcePages: [2],
            sourceQuotes: ['excluding any and all patents or pending IP applications'],
            verificationNeeded: true,
            quoteVerified: true,
          },
        ],
        inconsistencies: [
          {
            title: 'Conflicting Effective Dates',
            description: 'Introductory clause cites June 1, but signature page states July 15.',
            sourcePages: [1, 3],
            sourceQuotes: ['effective as of June 1', 'signed and sealed this 15th day of July'],
            alternativeExplanations: ['Backdated agreement or delayed closing'],
            quoteVerified: true,
          },
        ],
        informationGaps: [
          {
            question: 'Was an escrow agent appointed for the funds?',
            reason: 'Critical for determining escrow release mechanics.',
            relatedPages: [1],
          },
        ],
        investigationQuestions: [
          {
            question: 'Why was the intellectual property clause excluded from the mutual release?',
            reason: 'Determine if future trademark litigation is anticipated.',
            relatedPages: [2],
          },
        ],
        keyEntities: [],
        limitations: ['Preliminary automated review.'],
      },
      pages: [],
    };

    const pdfBytes = await generateLegalReportPdf(mockPayload);

    expect(pdfBytes).toBeDefined();
    expect(pdfBytes.length).toBeGreaterThan(1000);

    // Verify valid PDF header
    const header = Buffer.from(pdfBytes.slice(0, 5)).toString('ascii');
    expect(header).toBe('%PDF-');
  });
});
