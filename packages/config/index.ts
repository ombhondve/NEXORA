export const APP_CONFIG = {
  APP_NAME: 'Recursive OSINT Discovery Engine',
  API_V1_PREFIX: '/api/v1',
  DEFAULT_MAX_DEPTH: 3,
  DEFAULT_MAX_QUERIES: 25,
  DEFAULT_TIMEOUT_MS: 15000,
  SUPPORTED_CLUE_TYPES: ['text', 'name', 'domain', 'url', 'pdf', 'image'] as const,
};
