import React from 'react';
import { Navbar } from '@/components/layout/Navbar';
import { RefreshCw } from 'lucide-react';

export default function InvestigationLoading() {
  return (
    <div className="min-h-screen flex flex-col bg-cyber-bg">
      <Navbar />
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-3 font-mono text-sm text-cyber-cyan">
          <RefreshCw className="w-7 h-7 animate-spin mx-auto text-cyber-cyan" />
          <p>Loading Recursive Investigation Dossier & Lead Topology...</p>
        </div>
      </div>
    </div>
  );
}
