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
    const rawTarget = process.env.NEXT_PUBLIC_API_URL?.trim();
    const isProd = Boolean(process.env.VERCEL) || process.env.NODE_ENV === 'production';
    let backendTarget = 'http://localhost:8000';

    if (rawTarget) {
      if (isProd && (rawTarget.includes('localhost') || rawTarget.includes('127.0.0.1'))) {
        backendTarget = 'https://nexora-backend.vercel.app';
      } else {
        backendTarget = rawTarget;
      }
    } else if (isProd) {
      backendTarget = 'https://nexora-backend.vercel.app';
    }

    return [
      {
        source: '/api/:path*',
        destination: `${backendTarget.replace(/\/+$/, '')}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
