import { describe, it, expect } from 'vitest';
import { validatePdfBuffer, MAX_FILE_SIZE_BYTES } from '../src/lib/pdf/validator';

describe('PDF Validation', () => {
  it('rejects empty buffer', () => {
    const result = validatePdfBuffer(Buffer.alloc(0));
    expect(result.valid).toBe(false);
    expect(result.error).toContain('empty');
  });

  it('rejects files larger than 8 MB', () => {
    const largeBuffer = Buffer.alloc(MAX_FILE_SIZE_BYTES + 1024);
    // Add PDF magic byte to isolate size check
    largeBuffer.write('%PDF-1.4');
    const result = validatePdfBuffer(largeBuffer);
    expect(result.valid).toBe(false);
    expect(result.statusCode).toBe(413);
    expect(result.error).toContain('8 MB');
  });

  it('rejects non-PDF files missing %PDF- header', () => {
    const fakeBuffer = Buffer.from('This is a plain text file, not a real PDF.');
    const result = validatePdfBuffer(fakeBuffer);
    expect(result.valid).toBe(false);
    expect(result.statusCode).toBe(400);
    expect(result.error).toContain('%PDF-');
  });

  it('accepts valid PDF header and size', () => {
    const validHeader = Buffer.from('%PDF-1.7\n%âãÏÓ\n1 0 obj\n<<>>\nendobj');
    const result = validatePdfBuffer(validHeader);
    expect(result.valid).toBe(true);
  });
});
