import { describe, it, expect, vi } from 'vitest';
import { POST as analyzeHandler } from '../src/app/api/analyze/route';
import { POST as reportHandler } from '../src/app/api/report/route';
import { NextRequest } from 'next/server';
import { PDFDocument, StandardFonts } from 'pdf-lib';
import * as groqModule from '../src/lib/ai/groq';

describe('API Route Handlers', () => {
  it('POST /api/analyze returns 400 when no file is uploaded', async () => {
    const formData = new FormData();
    const req = new NextRequest('http://localhost:3000/api/analyze', {
      method: 'POST',
      body: formData,
    });

    const res = await analyzeHandler(req);
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toContain('No document was selected');
  });

  it('POST /api/analyze extracts text, invokes Groq, verifies quotes, and returns structured result', async () => {
    // Generate valid 2-page test PDF
    const doc = await PDFDocument.create();
    const font = await doc.embedFont(StandardFonts.Helvetica);
    const p1 = doc.addPage([600, 400]);
    p1.drawText('Clause 1: The loan principal of $1,000,000 shall be repaid by December 31, 2025.', {
      x: 50,
      y: 350,
      size: 12,
      font,
    });
    const p2 = doc.addPage([600, 400]);
    p2.drawText('Clause 2: Repayment schedule shall follow Exhibit A.', {
      x: 50,
      y: 350,
      size: 12,
      font,
    });
    const pdfBytes = await doc.save();

    // Mock Groq AI response
    vi.spyOn(groqModule, 'analyzeLegalDocument').mockResolvedValueOnce({
      modelUsed: 'llama-3.3-70b-versatile',
      rawAnalysis: {
        documentSummary: 'Loan agreement specifying repayment by end of 2025.',
        importantFacts: [
          {
            title: 'Loan Principal',
            description: 'Principal amount is $1,000,000.',
            sourcePage: 1,
            sourceQuote: 'loan principal of $1,000,000 shall be repaid',
            confidence: 'high',
            quoteVerified: false,
          },
        ],
        potentialClues: [
          {
            title: 'Missing Exhibit A',
            description: 'Repayment schedule relies on an unattached exhibit.',
            significance: 'medium',
            sourcePages: [2],
            sourceQuotes: ['Repayment schedule shall follow Exhibit A'],
            verificationNeeded: true,
            quoteVerified: false,
          },
        ],
        inconsistencies: [],
        informationGaps: [],
        investigationQuestions: [],
        keyEntities: [],
        limitations: [],
      },
    });

    const file = new File([pdfBytes], 'Sample_Loan_Agreement.pdf', { type: 'application/pdf' });
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', 'detailed');

    const req = new NextRequest('http://localhost:3000/api/analyze', {
      method: 'POST',
      body: formData,
    });

    const res = await analyzeHandler(req);
    expect(res.status).toBe(200);

    const json = await res.json();
    expect(json.metadata.filename).toBe('Sample_Loan_Agreement.pdf');
    expect(json.metadata.totalPages).toBe(2);
    expect(json.metadata.verifiedQuotesCount).toBe(2);
    expect(json.analysis.importantFacts[0].quoteVerified).toBe(true);
    expect(json.analysis.potentialClues[0].quoteVerified).toBe(true);
  });

  it('POST /api/report returns a downloadable PDF binary', async () => {
    const mockReportData = {
      metadata: {
        filename: 'Contract_Audit.pdf',
        fileSizeBytes: 50000,
        totalPages: 1,
        analyzedPages: 1,
        unreadablePages: [],
        analysisMode: 'quick',
        analyzedAt: new Date().toISOString(),
        modelUsed: 'llama-3.3-70b-versatile',
        totalFindings: 1,
        verifiedQuotesCount: 1,
        unverifiedQuotesCount: 0,
      },
      analysis: {
        documentSummary: 'Summary of fictional audit.',
        importantFacts: [
          {
            title: 'Audit Finding',
            description: 'Description of finding.',
            sourcePage: 1,
            sourceQuote: 'Audit finding text',
            confidence: 'high',
            quoteVerified: true,
          },
        ],
        potentialClues: [],
        inconsistencies: [],
        informationGaps: [],
        investigationQuestions: [],
        keyEntities: [],
        limitations: [],
      },
      pages: [],
    };

    const req = new NextRequest('http://localhost:3000/api/report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(mockReportData),
    });

    const res = await reportHandler(req);
    expect(res.status).toBe(200);
    expect(res.headers.get('Content-Type')).toBe('application/pdf');
    expect(res.headers.get('Content-Disposition')).toContain('attachment; filename=');

    const arrayBuf = await res.arrayBuffer();
    expect(arrayBuf.byteLength).toBeGreaterThan(500);
  });
});
