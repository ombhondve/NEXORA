import React from 'react';
import InvestigationDetailClient from './InvestigationDetailClient';

export async function generateStaticParams() {
  const knownIds = [
    '8417f95a-f3fe-41ce-8f4d-918c61e4dd3f',
    '2541c77d-f474-4024-a759-2713987ba78f',
  ];

  try {
    const res = await fetch('https://nexora-backend.vercel.app/api/v1/investigations', {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    });
    if (res.ok) {
      const data = await res.json();
      const items = Array.isArray(data) ? data : data.items || [];
      const fetchedIds = items.map((inv: any) => inv.id).filter(Boolean);
      const combined = Array.from(new Set([...knownIds, ...fetchedIds]));
      return combined.map((id) => ({ investigationId: String(id) }));
    }
  } catch (_) {
    // Graceful fallback to known IDs if network is unreachable during build
  }

  return knownIds.map((id) => ({ investigationId: id }));
}

export const dynamicParams = true;

interface PageProps {
  params: {
    investigationId: string;
  };
}

export default function InvestigationDetailPage({ params }: PageProps) {
  return <InvestigationDetailClient params={params} />;
}
