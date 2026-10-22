import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    outputFileTracingRoot: path.join(__dirname, '../../'),
  },
  async rewrites() {
    const backendTarget =
      process.env.NEXT_PUBLIC_API_URL ||
      (process.env.VERCEL || process.env.NODE_ENV === 'production'
        ? 'https://nexora-backend.vercel.app'
        : 'http://localhost:8000');

    return [
      {
        source: '/api/:path*',
        destination: `${backendTarget.replace(/\/+$/, '')}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
