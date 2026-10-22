'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();

  useEffect(() => {
    // Authentication is removed by default; redirect directly to dashboard
    router.replace('/dashboard');
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-cyber-bg text-slate-400 font-mono text-xs">
      <span>Redirecting to NEXORA Dashboard...</span>
    </div>
  );
}

