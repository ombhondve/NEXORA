/**
 * Frontend environment configuration and runtime validation.
 * Ensures required NEXT_PUBLIC_* environment variables are validated.
 * Prevents leakage of backend secrets to the browser bundle.
 */

export interface FrontendConfig {
  readonly appName: string;
  readonly apiUrl: string;
}

function sanitizeApiUrl(rawUrl: string | undefined): string {
  const isProduction =
    Boolean(process.env.VERCEL) ||
    process.env.NODE_ENV === 'production' ||
    (typeof window !== 'undefined' &&
      window.location.hostname !== 'localhost' &&
      window.location.hostname !== '127.0.0.1');

  if (rawUrl && rawUrl.trim()) {
    const trimmed = rawUrl.trim().replace(/\/+$/, '');
    if (isProduction && (trimmed.includes('localhost') || trimmed.includes('127.0.0.1'))) {
      return 'https://nexora-backend.vercel.app';
    }
    return trimmed;
  }

  if (isProduction) {
    return 'https://nexora-backend.vercel.app';
  }

  return 'http://localhost:8000';
}

export function getFrontendConfig(): FrontendConfig {
  const appName = process.env.NEXT_PUBLIC_APP_NAME || 'NEXORA';
  const apiUrl = sanitizeApiUrl(process.env.NEXT_PUBLIC_API_URL);

  return {
    appName,
    apiUrl,
  };
}

export const frontendConfig = getFrontendConfig();
