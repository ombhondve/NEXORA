import { describe, it, expect } from 'vitest';
import { extractPdfPages, PdfExtractionError } from '../src/lib/pdf/extractor';
import { PDFDocument, StandardFonts } from 'pdf-lib';

describe('PDF Text Extraction', () => {
  it('extracts structured pages and preserves page numbers', async () => {
    const doc = await PDFDocument.create();
    const font = await doc.embedFont(StandardFonts.Helvetica);

    const page1 = doc.addPage([600, 400]);
    page1.drawText('Page 1 Content: Fictional contract between Corporation A and Vendor B signed May 4, 2023.', {
      x: 50,
      y: 350,
      size: 12,
      font,
    });

    const page2 = doc.addPage([600, 400]);
    page2.drawText('Page 2 Content: Section 8 states that payment must be finalized within 15 business days.', {
      x: 50,
      y: 350,
      size: 12,
      font,
    });

    const pdfBytes = await doc.save();
    const result = await extractPdfPages(Buffer.from(pdfBytes));

    expect(result.totalPages).toBe(2);
    expect(result.readablePages).toBe(2);
    expect(result.pages.length).toBe(2);

    expect(result.pages[0].pageNumber).toBe(1);
    expect(result.pages[0].text).toContain('Corporation A and Vendor B');

    expect(result.pages[1].pageNumber).toBe(2);
    expect(result.pages[1].text).toContain('Section 8');
  });

  it('rejects image-only / scanned PDFs with no readable text', async () => {
    const doc = await PDFDocument.create();
    // Blank page with no text
    doc.addPage([600, 400]);
    const pdfBytes = await doc.save();

    await expect(extractPdfPages(Buffer.from(pdfBytes))).rejects.toThrow(
      /No readable text was detected in this PDF/
    );
  });

  it('enforces maximum 50-page limit', async () => {
    const doc = await PDFDocument.create();
    const font = await doc.embedFont(StandardFonts.Helvetica);

    // Create 51 pages
    for (let i = 0; i < 51; i++) {
      const p = doc.addPage([600, 400]);
      p.drawText(`Page content for page ${i + 1}`, { x: 50, y: 350, size: 10, font });
    }

    const pdfBytes = await doc.save();
    await expect(extractPdfPages(Buffer.from(pdfBytes))).rejects.toThrow(
      /exceeding the 50-page maximum limit/
    );
  });
});
