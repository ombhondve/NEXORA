import { NextRequest, NextResponse } from 'next/server';
import { generateLegalReportPdf } from '@/lib/report/generator';
import { sanitizeFilename } from '@/lib/utils';
import { CompleteAnalysisResult } from '@/types/analysis';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as CompleteAnalysisResult;

    if (!body || !body.analysis || !body.metadata) {
      return NextResponse.json(
        { error: 'Invalid report data provided. Please submit valid analysis results.' },
        { status: 400 }
      );
    }

    const pdfBytes = await generateLegalReportPdf(body);
    const sanitizedBase = sanitizeFilename(body.metadata.filename.replace(/\.pdf$/i, ''));
    const downloadFilename = `Investigation_Report_${sanitizedBase || 'Analysis'}.pdf`;

    return new NextResponse(Buffer.from(pdfBytes), {
      status: 200,
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': `attachment; filename="${downloadFilename}"`,
        'Cache-Control': 'no-store, max-age=0',
      },
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Unknown error during report generation';
    return NextResponse.json(
      { error: `Report generation failed: ${message}` },
      { status: 500 }
    );
  }
}

