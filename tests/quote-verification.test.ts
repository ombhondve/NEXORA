import { describe, it, expect } from 'vitest';
import { verifyQuoteInPage, verifyAndAnnotateFindings } from '../src/lib/verification/quote-verifier';
import { ExtractedPage, RawAnalysisOutput } from '../src/types/analysis';

describe('Quote & Page Reference Verification', () => {
  const samplePageText = `
    THIS AGREEMENT is made this 12th day of June 2024 by and between
    Apex Innovations LLC ("Buyer") and Zenith Logistics Inc ("Seller").
    The total purchase price shall be $450,000 payable upon receipt of shipment.
    Shipment shall be delivered to warehouse 4B by August 15, 2024.
  `;

  it('verifies exact verbatim quotation', () => {
    const quote = 'total purchase price shall be $450,000';
    expect(verifyQuoteInPage(quote, samplePageText)).toBe(true);
  });

  it('verifies quote with minor whitespace or case differences', () => {
    const quote = 'Apex Innovations LLC ("Buyer") and Zenith Logistics Inc';
    expect(verifyQuoteInPage(quote, samplePageText)).toBe(true);
  });

  it('flags unsupported quote not found in source page', () => {
    const fakeQuote = 'The contract may be terminated at will without notice';
    expect(verifyQuoteInPage(fakeQuote, samplePageText)).toBe(false);
  });

  it('annotates and bounds findings across multi-page document', () => {
    const pages: ExtractedPage[] = [
      {
        pageNumber: 1,
        text: samplePageText,
        charCount: samplePageText.length,
        isUnreadableOrEmpty: false,
      },
      {
        pageNumber: 2,
        text: 'Page 2: Notice shall be sent to legal@apex.test within 48 hours.',
        charCount: 65,
        isUnreadableOrEmpty: false,
      },
    ];

    const mockAnalysis: RawAnalysisOutput = {
      documentSummary: 'Summary of agreement.',
      importantFacts: [
        {
          title: 'Purchase Price',
          description: 'States price is $450,000.',
          sourcePage: 1,
          sourceQuote: 'total purchase price shall be $450,000 payable upon receipt',
          confidence: 'high',
          quoteVerified: false,
        },
        {
          title: 'Invented Fact',
          description: 'Claims non-existent penalty clause.',
          sourcePage: 1,
          sourceQuote: 'penalty of 50 percent applies immediately',
          confidence: 'high',
          quoteVerified: false,
        },
      ],
      potentialClues: [],
      inconsistencies: [],
      informationGaps: [],
      investigationQuestions: [],
      keyEntities: [],
      limitations: [],
    };

    const { verifiedAnalysis, verifiedCount, unverifiedCount } = verifyAndAnnotateFindings(
      mockAnalysis,
      pages
    );

    expect(verifiedCount).toBe(1);
    expect(unverifiedCount).toBe(1);
    expect(verifiedAnalysis.importantFacts[0].quoteVerified).toBe(true);
    expect(verifiedAnalysis.importantFacts[1].quoteVerified).toBe(false);
  });
});
