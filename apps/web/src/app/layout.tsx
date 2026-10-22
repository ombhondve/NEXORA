import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Recursive OSINT Discovery Engine | NEXORA',
  description: 'Enterprise Autonomous Recursive Intelligence and Source Correlation Engine',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-cyber-bg text-slate-100 min-h-screen cyber-grid antialiased">
        {children}
      </body>
    </html>
  );
}
