export const MAX_FILE_SIZE_BYTES = 8 * 1024 * 1024; // 8 MB
export const MAX_PAGE_COUNT = 50;

export interface ValidationResult {
  valid: boolean;
  error?: string;
  statusCode?: number;
}

export function validatePdfBuffer(buffer: Buffer | Uint8Array, filename?: string): ValidationResult {
  if (!buffer || buffer.length === 0) {
    return {
      valid: false,
      error: 'The uploaded file is empty. Please select a valid PDF document with readable text.',
      statusCode: 400,
    };
  }

  if (buffer.length > MAX_FILE_SIZE_BYTES) {
    return {
      valid: false,
      error: `The file exceeds the 8 MB size limit (current size: ${(buffer.length / (1024 * 1024)).toFixed(1)} MB). To analyze this document, please split it into smaller sections or compress the PDF.`,
      statusCode: 413,
    };
  }

  // Check magic bytes: standard PDF files start with "%PDF-"
  const header = Buffer.from(buffer.slice(0, 8)).toString('ascii');
  if (!header.startsWith('%PDF-')) {
    return {
      valid: false,
      error: 'Invalid file format. The file does not have a valid PDF header signature (%PDF-). Please upload an authentic PDF document.',
      statusCode: 400,
    };
  }

  // Check for common encryption markers without running a full parser
  // /Encrypt flag in PDF catalog or trailer
  const bufferString = Buffer.from(buffer.slice(0, Math.min(buffer.length, 100000))).toString('binary');
  if (bufferString.includes('/Encrypt')) {
    // Note: unpdf or pdfjs will throw on password-protected PDFs; we also handle it during extraction
  }

  return { valid: true };
}

