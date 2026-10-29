import { describe, it, expect } from 'vitest';
import { RawAnalysisOutputSchema } from '../src/types/analysis';

describe('AI Response Schema Validation', () => {
  it('validates compliant AI analysis response', () => {
    const validPayload = {
      documentSummary: 'A fictional supply agreement between Party X and Party Y.',
      importantFacts: [
        {
          title: 'Agreement Date',
          description: 'The agreement was entered into on March 1, 2024.',
          sourcePage: 1,
          sourceQuote: 'Entered into as of March 1, 2024',
          confidence: 'high',
        },
      ],
      potentialClues: [
        {
          title: 'Undefined Exclusivity',
          description: 'The clause references Exhibit B which was not attached.',
          significance: 'medium',
          sourcePages: [2],
          sourceQuotes: ['as defined in Exhibit B'],
          verificationNeeded: true,
        },
      ],
      inconsistencies: [
        {
          title: 'Contradictory Delivery Date',
          description: 'Page 1 cites delivery on April 10, whereas Page 3 specifies April 25.',
          sourcePages: [1, 3],
          sourceQuotes: ['delivery shall occur on April 10', 'delivery is scheduled for April 25'],
          alternativeExplanations: ['Typographical error in final execution version'],
        },
      ],
      informationGaps: [
        {
          question: 'Where is Exhibit B located?',
          reason: 'Exhibit B defines the core operational milestones.',
          relatedPages: [2],
        },
      ],
      investigationQuestions: [
        {
          question: 'Did both parties agree to the amended April 25 delivery date in writing?',
          reason: 'To clarify whether late delivery liquidated damages apply.',
          relatedPages: [1, 3],
        },
      ],
      keyEntities: [
        {
          category: 'person_organization',
          name: 'Party X Corp',
          context: 'Buyer of services',
          sourcePage: 1,
        },
      ],
      limitations: ['Analysis is restricted to the text within this 4-page excerpt.'],
    };

    const parsed = RawAnalysisOutputSchema.safeParse(validPayload);
    expect(parsed.success).toBe(true);
  });

  it('fails validation when documentSummary is missing', () => {
    const invalidPayload = {
      importantFacts: [],
    };

    const parsed = RawAnalysisOutputSchema.safeParse(invalidPayload);
    expect(parsed.success).toBe(false);
  });
});
