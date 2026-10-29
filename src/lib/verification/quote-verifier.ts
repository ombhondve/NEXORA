import { ExtractedPage, RawAnalysisOutput } from '@/types/analysis';

function cleanForMatching(str: string): string {
  return str
    .toLowerCase()
    .replace(/[^\w\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Checks if a quotation is present in the text of a specific page
 */
export function verifyQuoteInPage(quote: string, pageText: string): boolean {
  if (!quote || !pageText) return false;

  const normalizedQuote = cleanForMatching(quote);
  const normalizedPage = cleanForMatching(pageText);

  if (normalizedQuote.length === 0) return false;

  // 1. Direct normalized substring check
  if (normalizedPage.includes(normalizedQuote)) {
    return true;
  }

  // 2. Token-based sub-phrase match for long quotes that might have punctuation or line-break discrepancies
  const quoteWords = normalizedQuote.split(' ');
  if (quoteWords.length > 5) {
    // Check first 5 words and last 5 words
    const startPhrase = quoteWords.slice(0, 5).join(' ');
    const endPhrase = quoteWords.slice(-5).join(' ');

    if (normalizedPage.includes(startPhrase) && normalizedPage.includes(endPhrase)) {
      return true;
    }

    // Window sliding match: 70% word sequence
    const minMatchWords = Math.ceil(quoteWords.length * 0.7);
    const subSnippet = quoteWords.slice(0, minMatchWords).join(' ');
    if (normalizedPage.includes(subSnippet)) {
      return true;
    }
  }

  return false;
}

/**
 * Validates and verifies all page references and quotations across the AI response.
 * Guarantees that citations refer to real pages and flags unverified quotes.
 */
export function verifyAndAnnotateFindings(
  analysis: RawAnalysisOutput,
  pages: ExtractedPage[]
): {
  verifiedAnalysis: RawAnalysisOutput;
  verifiedCount: number;
  unverifiedCount: number;
} {
  const pageMap = new Map<number, string>();
  pages.forEach((p) => pageMap.set(p.pageNumber, p.text));
  const maxPage = pages.length;

  let verifiedCount = 0;
  let unverifiedCount = 0;

  // 1. Verify Important Facts
  const verifiedFacts = analysis.importantFacts.map((fact, index) => {
    // Clamp or validate pageNumber
    let validPage = fact.sourcePage;
    if (validPage < 1 || validPage > maxPage) {
      validPage = Math.max(1, Math.min(validPage, maxPage));
    }

    const pageText = pageMap.get(validPage) || '';
    const isVerified = verifyQuoteInPage(fact.sourceQuote, pageText);

    if (isVerified) {
      verifiedCount++;
    } else {
      unverifiedCount++;
    }

    return {
      ...fact,
      id: fact.id || `fact-${index + 1}`,
      sourcePage: validPage,
      quoteVerified: isVerified,
    };
  });

  // 2. Verify Potential Clues
  const verifiedClues = analysis.potentialClues.map((clue, index) => {
    const validPages = clue.sourcePages
      .map((p) => Math.max(1, Math.min(p, maxPage)))
      .filter((p, i, arr) => arr.indexOf(p) === i);

    let allQuotesVerified = true;
    clue.sourceQuotes.forEach((quote, qIndex) => {
      const targetPage = validPages[qIndex] || validPages[0] || 1;
      const pageText = pageMap.get(targetPage) || '';
      const ok = verifyQuoteInPage(quote, pageText);
      if (ok) {
        verifiedCount++;
      } else {
        unverifiedCount++;
        allQuotesVerified = false;
      }
    });

    return {
      ...clue,
      id: clue.id || `clue-${index + 1}`,
      sourcePages: validPages.length > 0 ? validPages : [1],
      quoteVerified: allQuotesVerified,
    };
  });

  // 3. Verify Inconsistencies
  const verifiedInconsistencies = analysis.inconsistencies.map((inc, index) => {
    const validPages = inc.sourcePages
      .map((p) => Math.max(1, Math.min(p, maxPage)))
      .filter((p, i, arr) => arr.indexOf(p) === i);

    let allQuotesVerified = true;
    inc.sourceQuotes.forEach((quote, qIndex) => {
      // Check against cited page or any of the inconsistency's cited pages
      let found = false;
      for (const pNum of validPages) {
        const pageText = pageMap.get(pNum) || '';
        if (verifyQuoteInPage(quote, pageText)) {
          found = true;
          break;
        }
      }
      if (found) {
        verifiedCount++;
      } else {
        unverifiedCount++;
        allQuotesVerified = false;
      }
    });

    return {
      ...inc,
      id: inc.id || `inc-${index + 1}`,
      sourcePages: validPages.length > 0 ? validPages : [1],
      quoteVerified: allQuotesVerified,
    };
  });

  // 4. Verify Information Gaps & Questions related pages
  const verifiedGaps = analysis.informationGaps.map((gap, index) => ({
    ...gap,
    id: gap.id || `gap-${index + 1}`,
    relatedPages: gap.relatedPages
      .map((p) => Math.max(1, Math.min(p, maxPage)))
      .filter((p, i, arr) => arr.indexOf(p) === i),
  }));

  const verifiedQuestions = analysis.investigationQuestions.map((q, index) => ({
    ...q,
    id: q.id || `q-${index + 1}`,
    relatedPages: q.relatedPages
      .map((p) => Math.max(1, Math.min(p, maxPage)))
      .filter((p, i, arr) => arr.indexOf(p) === i),
  }));

  return {
    verifiedAnalysis: {
      ...analysis,
      importantFacts: verifiedFacts,
      potentialClues: verifiedClues,
      inconsistencies: verifiedInconsistencies,
      informationGaps: verifiedGaps,
      investigationQuestions: verifiedQuestions,
    },
    verifiedCount,
    unverifiedCount,
  };
}
