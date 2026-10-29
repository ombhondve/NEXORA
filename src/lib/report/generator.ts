import { PDFDocument, rgb, StandardFonts, PDFFont, PDFPage } from 'pdf-lib';
import { CompleteAnalysisResult } from '@/types/analysis';

interface TextLayoutOptions {
  fontSize?: number;
  font?: PDFFont;
  color?: ReturnType<typeof rgb>;
  lineHeight?: number;
  maxWidth?: number;
  indent?: number;
}

export async function generateLegalReportPdf(analysisResult: CompleteAnalysisResult): Promise<Uint8Array> {
  const doc = await PDFDocument.create();
  const fontRegular = await doc.embedFont(StandardFonts.Helvetica);
  const fontBold = await doc.embedFont(StandardFonts.HelveticaBold);
  const fontItalic = await doc.embedFont(StandardFonts.HelveticaOblique);

  const PAGE_WIDTH = 595.28; // Standard A4
  const PAGE_HEIGHT = 841.89;
  const MARGIN_LEFT = 50;
  const MARGIN_RIGHT = 50;
  const CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT;
  const MARGIN_TOP = 50;
  const MARGIN_BOTTOM = 50;

  const colorNavy = rgb(0.08, 0.13, 0.24); // #14213D
  const colorBlue = rgb(0.15, 0.39, 0.92); // #2563EB
  const colorText = rgb(0.09, 0.13, 0.20); // #172033
  const colorMuted = rgb(0.39, 0.45, 0.55); // #64748B
  const colorBorder = rgb(0.89, 0.91, 0.94); // #E2E8F0
  const colorCardBg = rgb(0.97, 0.98, 0.99); // #F8FAFC
  const colorWarning = rgb(0.71, 0.33, 0.04); // #B45309

  let currentPage: PDFPage = doc.addPage([PAGE_WIDTH, PAGE_HEIGHT]);
  let currentY = PAGE_HEIGHT - MARGIN_TOP;

  function wrapText(text: string, font: PDFFont, fontSize: number, maxWidth: number): string[] {
    const lines: string[] = [];
    const paragraphs = text.split('\n');

    for (const paragraph of paragraphs) {
      if (!paragraph.trim()) {
        lines.push('');
        continue;
      }

      const words = paragraph.split(' ');
      let currentLine = '';

      for (const word of words) {
        const testLine = currentLine ? `${currentLine} ${word}` : word;
        const width = font.widthOfTextAtSize(testLine, fontSize);
        if (width <= maxWidth) {
          currentLine = testLine;
        } else {
          if (currentLine) lines.push(currentLine);
          currentLine = word;
        }
      }
      if (currentLine) {
        lines.push(currentLine);
      }
    }

    return lines;
  }

  function ensureSpace(neededHeight: number): PDFPage {
    if (currentY - neededHeight < MARGIN_BOTTOM) {
      currentPage = doc.addPage([PAGE_WIDTH, PAGE_HEIGHT]);
      currentY = PAGE_HEIGHT - MARGIN_TOP;
    }
    return currentPage;
  }

  function writeLines(lines: string[], options: TextLayoutOptions = {}) {
    const fontSize = options.fontSize || 10;
    const font = options.font || fontRegular;
    const color = options.color || colorText;
    const lineHeight = options.lineHeight || fontSize * 1.35;
    const indent = options.indent || 0;

    for (const line of lines) {
      ensureSpace(lineHeight);
      if (line.trim()) {
        currentPage.drawText(line, {
          x: MARGIN_LEFT + indent,
          y: currentY - fontSize,
          size: fontSize,
          font,
          color,
        });
      }
      currentY -= lineHeight;
    }
  }

  function writeSectionHeader(title: string, badge?: string) {
    ensureSpace(45);
    currentY -= 15;

    // Line indicator
    currentPage.drawRectangle({
      x: MARGIN_LEFT,
      y: currentY - 14,
      width: 4,
      height: 16,
      color: colorBlue,
    });

    currentPage.drawText(title, {
      x: MARGIN_LEFT + 12,
      y: currentY - 13,
      size: 13,
      font: fontBold,
      color: colorNavy,
    });

    if (badge) {
      const badgeWidth = fontRegular.widthOfTextAtSize(badge, 8) + 10;
      currentPage.drawRectangle({
        x: PAGE_WIDTH - MARGIN_RIGHT - badgeWidth,
        y: currentY - 14,
        width: badgeWidth,
        height: 14,
        color: colorCardBg,
        borderColor: colorBorder,
        borderWidth: 0.5,
      });
      currentPage.drawText(badge, {
        x: PAGE_WIDTH - MARGIN_RIGHT - badgeWidth + 5,
        y: currentY - 10,
        size: 8,
        font: fontBold,
        color: colorMuted,
      });
    }

    currentY -= 22;
  }

  const { metadata, analysis } = analysisResult;

  // --- REPORT TITLE & HEADER ---
  currentPage.drawText('AI LEGAL CLUE FINDER', {
    x: MARGIN_LEFT,
    y: currentY - 16,
    size: 16,
    font: fontBold,
    color: colorNavy,
  });

  currentPage.drawText('CONFIDENTIAL PRELIMINARY DOCUMENT ANALYSIS', {
    x: MARGIN_LEFT,
    y: currentY - 30,
    size: 8,
    font: fontBold,
    color: colorBlue,
  });

  currentY -= 45;

  // Document Metadata Box
  currentPage.drawRectangle({
    x: MARGIN_LEFT,
    y: currentY - 60,
    width: CONTENT_WIDTH,
    height: 60,
    color: colorCardBg,
    borderColor: colorBorder,
    borderWidth: 1,
  });

  const colWidth = CONTENT_WIDTH / 3;
  const metaY = currentY - 20;

  // Col 1
  currentPage.drawText('SOURCE DOCUMENT:', { x: MARGIN_LEFT + 10, y: metaY, size: 7.5, font: fontBold, color: colorMuted });
  currentPage.drawText(metadata.filename.length > 25 ? metadata.filename.slice(0, 22) + '...' : metadata.filename, {
    x: MARGIN_LEFT + 10,
    y: metaY - 12,
    size: 9,
    font: fontBold,
    color: colorNavy,
  });
  currentPage.drawText(`Pages: ${metadata.totalPages} (${metadata.analyzedPages} analyzed)`, {
    x: MARGIN_LEFT + 10,
    y: metaY - 24,
    size: 8,
    font: fontRegular,
    color: colorText,
  });

  // Col 2
  currentPage.drawText('ANALYSIS MODE & MODEL:', { x: MARGIN_LEFT + colWidth + 10, y: metaY, size: 7.5, font: fontBold, color: colorMuted });
  currentPage.drawText(metadata.analysisMode.toUpperCase() + ' REVIEW', {
    x: MARGIN_LEFT + colWidth + 10,
    y: metaY - 12,
    size: 9,
    font: fontBold,
    color: colorBlue,
  });
  currentPage.drawText(`Model: ${metadata.modelUsed}`, {
    x: MARGIN_LEFT + colWidth + 10,
    y: metaY - 24,
    size: 8,
    font: fontRegular,
    color: colorText,
  });

  // Col 3
  currentPage.drawText('GENERATION TIMESTAMP:', { x: MARGIN_LEFT + colWidth * 2 + 10, y: metaY, size: 7.5, font: fontBold, color: colorMuted });
  currentPage.drawText(new Date(metadata.analyzedAt).toLocaleString(), {
    x: MARGIN_LEFT + colWidth * 2 + 10,
    y: metaY - 12,
    size: 8.5,
    font: fontRegular,
    color: colorNavy,
  });
  currentPage.drawText(`Verified Quotes: ${metadata.verifiedQuotesCount}/${metadata.verifiedQuotesCount + metadata.unverifiedQuotesCount}`, {
    x: MARGIN_LEFT + colWidth * 2 + 10,
    y: metaY - 24,
    size: 8,
    font: fontRegular,
    color: colorText,
  });

  currentY -= 75;

  // --- EXECUTIVE SUMMARY ---
  writeSectionHeader('1. Executive Document Summary');
  const summaryLines = wrapText(analysis.documentSummary, fontRegular, 9.5, CONTENT_WIDTH);
  writeLines(summaryLines, { fontSize: 9.5, font: fontRegular, lineHeight: 14 });

  // --- IMPORTANT FACTS ---
  if (analysis.importantFacts.length > 0) {
    writeSectionHeader('2. Key Established Facts', `${analysis.importantFacts.length} Found`);

    for (const fact of analysis.importantFacts) {
      ensureSpace(60);
      currentY -= 6;

      // Title & Page Badge
      currentPage.drawText(`• ${fact.title}`, {
        x: MARGIN_LEFT,
        y: currentY - 10,
        size: 9.5,
        font: fontBold,
        color: colorNavy,
      });

      const pageBadge = `Page ${fact.sourcePage} [${fact.quoteVerified ? 'Quote Verified' : 'Citation Check'}]`;
      currentPage.drawText(pageBadge, {
        x: PAGE_WIDTH - MARGIN_RIGHT - fontRegular.widthOfTextAtSize(pageBadge, 8),
        y: currentY - 10,
        size: 8,
        font: fontItalic,
        color: colorBlue,
      });
      currentY -= 15;

      const descLines = wrapText(fact.description, fontRegular, 9, CONTENT_WIDTH - 15);
      writeLines(descLines, { fontSize: 9, font: fontRegular, indent: 12, lineHeight: 13 });

      // Verbatim Quote block
      if (fact.sourceQuote) {
        const quoteLines = wrapText(`"${fact.sourceQuote}"`, fontItalic, 8.5, CONTENT_WIDTH - 25);
        currentY -= 3;
        writeLines(quoteLines, { fontSize: 8.5, font: fontItalic, color: colorMuted, indent: 20, lineHeight: 12 });
      }
      currentY -= 5;
    }
  }

  // --- POTENTIAL CLUES ---
  if (analysis.potentialClues.length > 0) {
    writeSectionHeader('3. Potential Investigative Clues', `${analysis.potentialClues.length} Items`);

    for (const clue of analysis.potentialClues) {
      ensureSpace(60);
      currentY -= 6;

      currentPage.drawText(`• ${clue.title}`, {
        x: MARGIN_LEFT,
        y: currentY - 10,
        size: 9.5,
        font: fontBold,
        color: colorNavy,
      });

      const priorityText = `Priority: ${clue.significance.toUpperCase()} | Pages: ${clue.sourcePages.join(', ')}`;
      currentPage.drawText(priorityText, {
        x: PAGE_WIDTH - MARGIN_RIGHT - fontRegular.widthOfTextAtSize(priorityText, 8),
        y: currentY - 10,
        size: 8,
        font: fontBold,
        color: clue.significance === 'high' ? colorWarning : colorBlue,
      });
      currentY -= 15;

      const descLines = wrapText(clue.description, fontRegular, 9, CONTENT_WIDTH - 15);
      writeLines(descLines, { fontSize: 9, font: fontRegular, indent: 12, lineHeight: 13 });

      if (clue.sourceQuotes && clue.sourceQuotes.length > 0) {
        for (const q of clue.sourceQuotes) {
          const qLines = wrapText(`"${q}"`, fontItalic, 8.5, CONTENT_WIDTH - 25);
          currentY -= 2;
          writeLines(qLines, { fontSize: 8.5, font: fontItalic, color: colorMuted, indent: 20, lineHeight: 12 });
        }
      }
      currentY -= 5;
    }
  }

  // --- INCONSISTENCIES ---
  if (analysis.inconsistencies.length > 0) {
    writeSectionHeader('4. Potential Inconsistencies & Contradictions', `${analysis.inconsistencies.length} Detected`);

    for (const inc of analysis.inconsistencies) {
      ensureSpace(70);
      currentY -= 6;

      currentPage.drawText(`• ${inc.title}`, {
        x: MARGIN_LEFT,
        y: currentY - 10,
        size: 9.5,
        font: fontBold,
        color: colorNavy,
      });

      const incPages = `Source Pages: ${inc.sourcePages.join(', ')}`;
      currentPage.drawText(incPages, {
        x: PAGE_WIDTH - MARGIN_RIGHT - fontRegular.widthOfTextAtSize(incPages, 8),
        y: currentY - 10,
        size: 8,
        font: fontItalic,
        color: colorWarning,
      });
      currentY -= 15;

      const descLines = wrapText(inc.description, fontRegular, 9, CONTENT_WIDTH - 15);
      writeLines(descLines, { fontSize: 9, font: fontRegular, indent: 12, lineHeight: 13 });

      if (inc.sourceQuotes && inc.sourceQuotes.length > 0) {
        for (let qi = 0; qi < inc.sourceQuotes.length; qi++) {
          const qLines = wrapText(`Passage ${qi + 1}: "${inc.sourceQuotes[qi]}"`, fontItalic, 8.5, CONTENT_WIDTH - 25);
          currentY -= 2;
          writeLines(qLines, { fontSize: 8.5, font: fontItalic, color: colorMuted, indent: 20, lineHeight: 12 });
        }
      }

      if (inc.alternativeExplanations && inc.alternativeExplanations.length > 0) {
        for (const alt of inc.alternativeExplanations) {
          const altLines = wrapText(`Potential benign explanation: ${alt}`, fontRegular, 8.5, CONTENT_WIDTH - 25);
          currentY -= 2;
          writeLines(altLines, { fontSize: 8.5, font: fontRegular, color: colorText, indent: 20, lineHeight: 12 });
        }
      }
      currentY -= 5;
    }
  }

  // --- INFORMATION GAPS ---
  if (analysis.informationGaps.length > 0) {
    writeSectionHeader('5. Information Gaps & Unanswered Questions', `${analysis.informationGaps.length} Items`);

    for (const gap of analysis.informationGaps) {
      ensureSpace(45);
      currentY -= 5;

      currentPage.drawText(`? ${gap.question}`, {
        x: MARGIN_LEFT,
        y: currentY - 10,
        size: 9,
        font: fontBold,
        color: colorNavy,
      });
      currentY -= 14;

      const reasonLines = wrapText(`Significance: ${gap.reason}`, fontRegular, 8.5, CONTENT_WIDTH - 15);
      writeLines(reasonLines, { fontSize: 8.5, font: fontRegular, indent: 12, lineHeight: 12 });
      currentY -= 4;
    }
  }

  // --- INVESTIGATION QUESTIONS ---
  if (analysis.investigationQuestions.length > 0) {
    writeSectionHeader('6. Strategic Investigation & Deposition Questions', `${analysis.investigationQuestions.length} Questions`);

    for (const q of analysis.investigationQuestions) {
      ensureSpace(45);
      currentY -= 5;

      currentPage.drawText(`Q: ${q.question}`, {
        x: MARGIN_LEFT,
        y: currentY - 10,
        size: 9,
        font: fontBold,
        color: colorNavy,
      });
      currentY -= 14;

      const reasonLines = wrapText(`Objective: ${q.reason}`, fontRegular, 8.5, CONTENT_WIDTH - 15);
      writeLines(reasonLines, { fontSize: 8.5, font: fontRegular, indent: 12, lineHeight: 12 });
      currentY -= 4;
    }
  }

  // --- ANALYTICAL LIMITATIONS ---
  writeSectionHeader('7. Analytical Limitations');
  const limitations = [
    ...analysis.limitations,
    `Document text extraction: ${metadata.analyzedPages} of ${metadata.totalPages} pages contained readable digital text.`,
    'Findings are derived algorithmically using Groq AI and do not account for external evidence, jurisdictional statutes, or unrecorded facts.',
  ];

  for (const lim of limitations) {
    ensureSpace(30);
    const limLines = wrapText(`• ${lim}`, fontRegular, 8.5, CONTENT_WIDTH - 10);
    writeLines(limLines, { fontSize: 8.5, font: fontRegular, color: colorMuted, indent: 5, lineHeight: 12 });
    currentY -= 3;
  }

  // --- LEGAL DISCLAIMER BOX ---
  ensureSpace(80);
  currentY -= 15;

  currentPage.drawRectangle({
    x: MARGIN_LEFT,
    y: currentY - 55,
    width: CONTENT_WIDTH,
    height: 55,
    color: colorCardBg,
    borderColor: colorBorder,
    borderWidth: 1,
  });

  currentPage.drawText('IMPORTANT LEGAL DISCLAIMER', {
    x: MARGIN_LEFT + 10,
    y: currentY - 14,
    size: 8,
    font: fontBold,
    color: colorNavy,
  });

  const disclaimerText =
    'This tool assists with preliminary document review. AI-generated findings may be incomplete or incorrect and must be verified against original documents. This document does not constitute legal advice, does not establish guilt or wrongdoing, does not guarantee legal outcomes, and does not replace professional legal judgment.';
  const disclaimerLines = wrapText(disclaimerText, fontRegular, 7.5, CONTENT_WIDTH - 20);

  let discY = currentY - 26;
  for (const dl of disclaimerLines) {
    currentPage.drawText(dl, {
      x: MARGIN_LEFT + 10,
      y: discY,
      size: 7.5,
      font: fontRegular,
      color: colorMuted,
    });
    discY -= 10;
  }

  // --- PAGE NUMBERS & FOOTER ON ALL PAGES ---
  const totalPages = doc.getPageCount();
  for (let i = 0; i < totalPages; i++) {
    const page = doc.getPage(i);
    const footerText = `AI Legal Clue Finder  |  Page ${i + 1} of ${totalPages}  |  CONFIDENTIAL`;
    page.drawText(footerText, {
      x: PAGE_WIDTH / 2 - fontRegular.widthOfTextAtSize(footerText, 7.5) / 2,
      y: MARGIN_BOTTOM - 25,
      size: 7.5,
      font: fontRegular,
      color: colorMuted,
    });
  }

  return await doc.save();
}
