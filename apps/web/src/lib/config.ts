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
  if (rawUrl && rawUrl.trim()) {
    const trimmed = rawUrl.trim();
    if (
      typeof window !== 'undefined' &&
      window.location.hostname !== 'localhost' &&
      window.location.hostname !== '127.0.0.1'
    ) {
      if (trimmed.includes('localhost') || trimmed.includes('127.0.0.1')) {
        console.warn(
          '[Config Warning]: In production browser environment but NEXT_PUBLIC_API_URL points to localhost. Falling back to origin.'
        );
        return window.location.origin;
      }
    }
    return trimmed.replace(/\/+$/, '');
  }

  if (typeof window !== 'undefined') {
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      return window.location.origin;
    }
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
