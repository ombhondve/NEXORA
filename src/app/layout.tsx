import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI Legal Clue Finder | Evidence-Based Document Intelligence',
  description:
    'Assist lawyers and legal professionals in analyzing case documents, detecting internal inconsistencies, extracting key facts, finding potential clues, and generating verifiable reports.',
  keywords: ['legal tech', 'clue finder', 'inconsistency analysis', 'evidence extraction', 'groq', 'pdf legal review'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col bg-surface-bg text-ink selection:bg-primary-light selection:text-primary">
        {children}
      </body>
    </html>
  );
}

