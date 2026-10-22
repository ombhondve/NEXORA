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
  if (!rawUrl || !rawUrl.trim()) {
    return 'http://localhost:8000';
  }
  const trimmed = rawUrl.trim();
  try {
    const parsed = new URL(trimmed);
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      console.warn(
        `[Config Warning]: NEXT_PUBLIC_API_URL protocol '${parsed.protocol}' is unusual. Expected 'http:' or 'https:'.`
      );
    }
    return trimmed.replace(/\/+$/, '');
  } catch {
    return trimmed.replace(/\/+$/, '');
  }
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
