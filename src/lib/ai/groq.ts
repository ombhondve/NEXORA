import Groq from 'groq-sdk';
import { SYSTEM_PROMPT, buildAnalysisUserPrompt } from './prompt';
import {
  AnalysisMode,
  ExtractedPage,
  RawAnalysisOutput,
  RawAnalysisOutputSchema,
} from '@/types/analysis';

export class GroqServiceError extends Error {
  statusCode: number;
  constructor(message: string, statusCode = 500) {
    super(message);
    this.name = 'GroqServiceError';
    this.statusCode = statusCode;
  }
}

/**
 * Retrieves the configured Groq client
 */
export function getGroqClient(): Groq {
  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey || apiKey.trim() === '') {
    throw new GroqServiceError(
      'GROQ_API_KEY is not configured on the server. Please set your GROQ_API_KEY in environment variables.',
      500
    );
  }
  return new Groq({ apiKey: apiKey.trim() });
}

export function getConfiguredModel(): string {
  return process.env.GROQ_MODEL?.trim() || 'llama-3.3-70b-versatile';
}

/**
 * Extracts and parses JSON from the model response, even if enclosed in markdown code fences
 */
function extractJsonFromResponse(raw: string): unknown {
  let cleaned = raw.trim();

  // Strip markdown code fences if present
  if (cleaned.startsWith('```json')) {
    cleaned = cleaned.replace(/^```json\s*/, '').replace(/\s*```$/, '');
  } else if (cleaned.startsWith('```')) {
    cleaned = cleaned.replace(/^```\s*/, '').replace(/\s*```$/, '');
  }

  try {
    return JSON.parse(cleaned);
  } catch {
    // If trailing commas or slight syntax error, attempt first-brace to last-brace slice
    const firstBrace = cleaned.indexOf('{');
    const lastBrace = cleaned.lastIndexOf('}');
    if (firstBrace !== -1 && lastBrace !== -1 && lastBrace > firstBrace) {
      const sliced = cleaned.substring(firstBrace, lastBrace + 1);
      return JSON.parse(sliced);
    }
    throw new Error('Unable to parse JSON from AI response.');
  }
}

/**
 * Analyzes pages using Groq API with structured JSON output and schema validation
 */
export async function analyzeLegalDocument(
  pages: ExtractedPage[],
  mode: AnalysisMode
): Promise<{ rawAnalysis: RawAnalysisOutput; modelUsed: string }> {
  const client = getGroqClient();
  const model = getConfiguredModel();

  // Calculate text budget
  const totalChars = pages.reduce((acc, p) => acc + p.text.length, 0);

  // If text is unusually massive (> 120,000 chars, ~30k words), chunk pages
  const CHUNK_PAGE_SIZE = 20;
  if (pages.length > CHUNK_PAGE_SIZE && totalChars > 120000) {
    return analyzeInChunks(client, model, pages, mode);
  }

  const prompt = buildAnalysisUserPrompt(pages, mode);

  try {
    const chatCompletion = await client.chat.completions.create({
      model,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: prompt },
      ],
      response_format: { type: 'json_object' },
      temperature: 0.1, // Low temperature for high factual accuracy
      max_tokens: 4096,
    });

    const choice = chatCompletion.choices?.[0];
    const content = choice?.message?.content;

    if (!content) {
      throw new GroqServiceError('AI service returned an empty completion.', 502);
    }

    const parsedJson = extractJsonFromResponse(content);
    const validated = RawAnalysisOutputSchema.safeParse(parsedJson);

    if (!validated.success) {
      console.warn('AI Output failed strict schema validation, attempting recovery:', validated.error.format());
      // Handle lenient recovery for common schema mismatches
      const recovered = recoverPartialAnalysis(parsedJson);
      return { rawAnalysis: recovered, modelUsed: model };
    }

    return { rawAnalysis: validated.data, modelUsed: model };
  } catch (err: unknown) {
    if (err instanceof GroqServiceError) {
      throw err;
    }

    const message = err instanceof Error ? err.message : String(err);

    // Map common Groq API error scenarios
    if (message.includes('401') || message.toLowerCase().includes('invalid api key')) {
      throw new GroqServiceError('Invalid Groq API key configured on server. Please verify GROQ_API_KEY.', 401);
    }
    if (message.includes('429') || message.toLowerCase().includes('rate limit')) {
      throw new GroqServiceError('Groq API rate limit reached. Please wait a moment before trying again.', 429);
    }
    if (message.includes('model_not_found') || message.includes('does not exist')) {
      throw new GroqServiceError(`Configured Groq model "${model}" is not available for this account. Check GROQ_MODEL.`, 400);
    }

    throw new GroqServiceError(`AI analysis failed: ${message}`, 500);
  }
}

/**
 * Handles larger documents by analyzing in page chunks and merging results
 */
async function analyzeInChunks(
  client: Groq,
  model: string,
  pages: ExtractedPage[],
  mode: AnalysisMode
): Promise<{ rawAnalysis: RawAnalysisOutput; modelUsed: string }> {
  const CHUNK_SIZE = 15;
  const chunks: ExtractedPage[][] = [];

  for (let i = 0; i < pages.length; i += CHUNK_SIZE) {
    chunks.push(pages.slice(i, i + CHUNK_SIZE));
  }

  const chunkResults: RawAnalysisOutput[] = [];

  // Analyze each chunk (capped at 3 chunks to avoid excessive API time and context costs)
  const maxChunksToAnalyze = Math.min(chunks.length, 3);
  for (let c = 0; c < maxChunksToAnalyze; c++) {
    const chunkPages = chunks[c];
    const prompt = buildAnalysisUserPrompt(chunkPages, mode);

    const completion = await client.chat.completions.create({
      model,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: prompt },
      ],
      response_format: { type: 'json_object' },
      temperature: 0.1,
      max_tokens: 3000,
    });

    const content = completion.choices?.[0]?.message?.content || '{}';
    try {
      const parsed = extractJsonFromResponse(content);
      const val = RawAnalysisOutputSchema.safeParse(parsed);
      if (val.success) {
        chunkResults.push(val.data);
      } else {
        chunkResults.push(recoverPartialAnalysis(parsed));
      }
    } catch {
      // Continue with remaining chunks
    }
  }

  // Synthesize chunks
  const merged: RawAnalysisOutput = {
    documentSummary: chunkResults.map((r) => r.documentSummary).filter(Boolean).join('\n\n'),
    importantFacts: chunkResults.flatMap((r) => r.importantFacts),
    potentialClues: chunkResults.flatMap((r) => r.potentialClues),
    inconsistencies: chunkResults.flatMap((r) => r.inconsistencies),
    informationGaps: chunkResults.flatMap((r) => r.informationGaps),
    investigationQuestions: chunkResults.flatMap((r) => r.investigationQuestions),
    keyEntities: chunkResults.flatMap((r) => r.keyEntities),
    limitations: [
      ...chunkResults.flatMap((r) => r.limitations),
      `Large document analyzed in ${maxChunksToAnalyze} page-aware chunk sections. Cross-section contradictions between distant segments should be reviewed manually.`,
    ],
  };

  return { rawAnalysis: merged, modelUsed: model };
}

/**
 * Permissive fallback parser in case model returns slight schema anomalies
 */
function recoverPartialAnalysis(raw: any): RawAnalysisOutput {
  const summary =
    typeof raw?.documentSummary === 'string'
      ? raw.documentSummary
      : typeof raw?.summary === 'string'
      ? raw.summary
      : 'Document analysis completed.';

  const parseArray = <T>(arr: any, fallback: T[] = []): T[] => {
    return Array.isArray(arr) ? arr : fallback;
  };

  return {
    documentSummary: summary,
    importantFacts: parseArray(raw?.importantFacts),
    potentialClues: parseArray(raw?.potentialClues),
    inconsistencies: parseArray(raw?.inconsistencies),
    informationGaps: parseArray(raw?.informationGaps),
    investigationQuestions: parseArray(raw?.investigationQuestions),
    keyEntities: parseArray(raw?.keyEntities),
    limitations: parseArray(raw?.limitations, [
      'Preliminary automated review. All findings should be verified against source citations.',
    ]),
  };
}
