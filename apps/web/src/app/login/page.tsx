'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Shield, Key, Mail, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api-client';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('demo@example.org');
  const [password, setPassword] = useState('password123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.login(email, password);
      if (typeof window !== 'undefined') {
        localStorage.setItem('osint_token', res.access_token);
      }
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-cyber-bg cyber-grid">
      <div className="w-full max-w-md glass-panel rounded-2xl border border-cyber-border p-8 shadow-2xl space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-cyber-card border border-cyber-cyan/40 shadow-glow-cyan flex items-center justify-center mx-auto text-cyber-cyan">
            <Shield className="w-6 h-6" />
          </div>
          <h1 className="text-xl font-bold font-mono text-white">NEXORA OSINT</h1>
          <p className="text-xs text-slate-400 font-mono">Sign in to authenticate recursive intelligence session</p>
        </div>

        {error && (
          <div className="flex items-center space-x-2 p-3 text-xs text-rose-300 bg-rose-950/60 border border-rose-800/80 rounded-lg">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-mono uppercase text-slate-400 mb-1">Analyst Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-cyber-card border border-cyber-border rounded-lg pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-cyber-cyan font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-slate-400 mb-1">Password</label>
            <div className="relative">
              <Key className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-cyber-card border border-cyber-border rounded-lg pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-cyber-cyan font-mono"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-cyber-cyan hover:bg-cyan-400 text-slate-950 font-bold py-2.5 rounded-lg text-sm shadow-glow-cyan transition-all disabled:opacity-50"
          >
            {loading ? 'Authenticating...' : 'Establish Secure Session'}
          </button>
        </form>

        <div className="text-center pt-2 border-t border-cyber-border/40">
          <p className="text-[11px] font-mono text-slate-400">
            Default test account pre-filled: <span className="text-cyber-cyan">demo@example.org</span>
          </p>
        </div>
      </div>
    </div>
  );
}
