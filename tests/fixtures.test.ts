import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';
import { extractPdfPages } from '../src/lib/pdf/extractor';

describe('Fixture Documents Verification', () => {
  const fixturesDir = path.resolve(__dirname, '../fixtures');

  it('correctly processes short text PDF', async () => {
    const buffer = fs.readFileSync(path.join(fixturesDir, 'short_text.pdf'));
    const result = await extractPdfPages(buffer);
    expect(result.totalPages).toBe(1);
    expect(result.pages[0].text).toContain('Fictional Dynamics Inc');
  });

  it('correctly processes contradictory statements PDF preserving 3 pages', async () => {
    const buffer = fs.readFileSync(path.join(fixturesDir, 'contradictory_statements.pdf'));
    const result = await extractPdfPages(buffer);
    expect(result.totalPages).toBe(3);
    expect(result.pages[0].text).toContain('Base Monthly Rent is agreed at $12,500');
    expect(result.pages[1].text).toContain('improvement allowance of $60,000');
    expect(result.pages[2].text).toContain('monthly rent of $15,000');
  });

  it('correctly processes 5-page deposition PDF preserving all 5 pages', async () => {
    const buffer = fs.readFileSync(path.join(fixturesDir, 'multipage_deposition.pdf'));
    const result = await extractPdfPages(buffer);
    expect(result.totalPages).toBe(5);
    expect(result.pages[4].pageNumber).toBe(5);
  });

  it('gracefully rejects scanned_image_only PDF with OCR guidance error', async () => {
    const buffer = fs.readFileSync(path.join(fixturesDir, 'scanned_image_only.pdf'));
    await expect(extractPdfPages(buffer)).rejects.toThrow(
      /No readable text was detected in this PDF. This version supports text-based PDFs. OCR support can be added in a future version./
    );
  });
});
