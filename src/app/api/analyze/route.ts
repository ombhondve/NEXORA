import { NextRequest, NextResponse } from 'next/server';
import { extractPdfPages, PdfExtractionError } from '@/lib/pdf/extractor';
import { analyzeLegalDocument, GroqServiceError } from '@/lib/ai/groq';
import { verifyAndAnnotateFindings } from '@/lib/verification/quote-verifier';
import { sanitizeFilename } from '@/lib/utils';
import { AnalysisMode, CompleteAnalysisResult } from '@/types/analysis';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const file = formData.get('file') as File | null;
    const mode = (formData.get('mode') as AnalysisMode) || 'detailed';

    if (!file) {
      return NextResponse.json(
        { error: 'No document was selected. Please upload a PDF file.' },
        { status: 400 }
      );
    }

    // Quick client-provided metadata check (note: server buffer check will strictly enforce it)
    if (file.size === 0) {
      return NextResponse.json(
        { error: 'The uploaded file is empty. Please upload a valid PDF document.' },
        { status: 400 }
      );
    }

    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    const sanitizedName = sanitizeFilename(file.name || 'document.pdf');

    // 1. Server-side PDF Text Extraction & Validation
    const extractionResult = await extractPdfPages(buffer);

    // 2. Call Groq AI for structured analysis
    const { rawAnalysis, modelUsed } = await analyzeLegalDocument(
      extractionResult.pages,
      mode
    );

    // 3. Verify Source Quotes & Page Numbers against extracted text
    const { verifiedAnalysis, verifiedCount, unverifiedCount } = verifyAndAnnotateFindings(
      rawAnalysis,
      extractionResult.pages
    );

    // Add extraction warnings to limitations if any pages were unreadable
    if (extractionResult.warning) {
      verifiedAnalysis.limitations.unshift(extractionResult.warning);
    }

    const totalFindings =
      verifiedAnalysis.importantFacts.length +
      verifiedAnalysis.potentialClues.length +
      verifiedAnalysis.inconsistencies.length +
      verifiedAnalysis.informationGaps.length +
      verifiedAnalysis.investigationQuestions.length;

    const completeResult: CompleteAnalysisResult = {
      metadata: {
        filename: sanitizedName,
        fileSizeBytes: buffer.length,
        totalPages: extractionResult.totalPages,
        analyzedPages: extractionResult.readablePages,
        unreadablePages: extractionResult.unreadablePages,
        analysisMode: mode,
        analyzedAt: new Date().toISOString(),
        modelUsed,
        totalFindings,
        verifiedQuotesCount: verifiedCount,
        unverifiedQuotesCount: unverifiedCount,
      },
      analysis: verifiedAnalysis,
      pages: extractionResult.pages,
    };

    return NextResponse.json(completeResult, { status: 200 });
  } catch (err: unknown) {
    if (err instanceof PdfExtractionError) {
      return NextResponse.json(
        { error: err.message },
        { status: err.statusCode }
      );
    }

    if (err instanceof GroqServiceError) {
      return NextResponse.json(
        { error: err.message },
        { status: err.statusCode }
      );
    }

    const message = err instanceof Error ? err.message : 'An unexpected error occurred.';
    return NextResponse.json(
      { error: `Document analysis failed: ${message}` },
      { status: 500 }
    );
  }
}
