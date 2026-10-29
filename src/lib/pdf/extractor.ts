import { extractText } from 'unpdf';
import { MAX_PAGE_COUNT, validatePdfBuffer } from './validator';
import { normalizeWhitespace } from '../utils';
import { ExtractedPage } from '@/types/analysis';

export interface ExtractionResult {
  pages: ExtractedPage[];
  totalPages: number;
  readablePages: number;
  unreadablePages: number[];
  totalChars: number;
  isPartiallyUnreadable: boolean;
  warning?: string;
}

export class PdfExtractionError extends Error {
  statusCode: number;
  constructor(message: string, statusCode = 400) {
    super(message);
    this.name = 'PdfExtractionError';
    this.statusCode = statusCode;
  }
}

/**
 * Extracts structured page-by-page text from a PDF buffer.
 * Enforces size, format, encryption, page count limits, and text detectability.
 */
export async function extractPdfPages(fileBuffer: Buffer | Uint8Array): Promise<ExtractionResult> {
  // 1. Initial format and size validation
  const validation = validatePdfBuffer(fileBuffer);
  if (!validation.valid) {
    throw new PdfExtractionError(validation.error || 'Invalid PDF file.', validation.statusCode || 400);
  }

  // 2. Perform text extraction using unpdf
  let extractionRaw: { totalPages: number; text: string[] | string };
  try {
    // unpdf strictly requires a Uint8Array view
    const uint8Data = new Uint8Array(fileBuffer.buffer, fileBuffer.byteOffset, fileBuffer.byteLength);
    extractionRaw = await extractText(uint8Data, { mergePages: false });
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    if (errorMsg.toLowerCase().includes('password') || errorMsg.toLowerCase().includes('encrypted')) {
      throw new PdfExtractionError(
        'This PDF document is encrypted or password-protected. Please provide an unencrypted version for analysis.',
        422
      );
    }
    if (errorMsg.toLowerCase().includes('invalid pdf') || errorMsg.toLowerCase().includes('corrupted')) {
      throw new PdfExtractionError(
        'The uploaded PDF appears to be corrupted or malformed. Please verify the file integrity and try again.',
        400
      );
    }
    throw new PdfExtractionError(`Failed to parse PDF document: ${errorMsg}`, 400);
  }

  const totalPages = extractionRaw.totalPages || 0;

  if (totalPages === 0) {
    throw new PdfExtractionError(
      'The PDF document contains 0 pages or could not be parsed.',
      400
    );
  }

  if (totalPages > MAX_PAGE_COUNT) {
    throw new PdfExtractionError(
      `This document has ${totalPages} pages, exceeding the 50-page maximum limit. Please split the document into parts with up to 50 pages each.`,
      413
    );
  }

  const rawPagesList = Array.isArray(extractionRaw.text) ? extractionRaw.text : [extractionRaw.text];

  const pages: ExtractedPage[] = [];
  const unreadablePages: number[] = [];
  let totalChars = 0;

  for (let i = 0; i < totalPages; i++) {
    const pageNumber = i + 1;
    const rawPageText = rawPagesList[i] || '';
    const cleanedText = normalizeWhitespace(rawPageText);
    const charCount = cleanedText.length;
    totalChars += charCount;

    // Detect pages with little or no extractable text (< 25 characters usually indicates scanned or blank page)
    const isUnreadableOrEmpty = charCount < 25;
    if (isUnreadableOrEmpty) {
      unreadablePages.push(pageNumber);
    }

    pages.push({
      pageNumber,
      text: cleanedText,
      charCount,
      isUnreadableOrEmpty,
    });
  }

  // Detect scanned / image-only PDFs
  // If the entire document has virtually no extractable text
  if (totalChars < 50) {
    throw new PdfExtractionError(
      'No readable text was detected in this PDF. This version supports text-based PDFs. OCR support can be added in a future version.',
      422
    );
  }

  const readablePages = totalPages - unreadablePages.length;
  const isPartiallyUnreadable = unreadablePages.length > 0;
  let warning: string | undefined;

  if (isPartiallyUnreadable) {
    warning = `Pages ${unreadablePages.join(', ')} contain little or no extractable text and may be scanned or image-based. Findings for these pages may be incomplete.`;
  }

  return {
    pages,
    totalPages,
    readablePages,
    unreadablePages,
    totalChars,
    isPartiallyUnreadable,
    warning,
  };
}
