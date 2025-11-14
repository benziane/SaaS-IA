import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  /* Basic Config */
  reactStrictMode: true,
  poweredByHeader: false,
  compress: true,
  
  /* TypeScript Config - Grade S++ */
  typescript: {
    ignoreBuildErrors: false, // Strict: fail build on TS errors
    tsconfigPath: './tsconfig.json',
  },
  
  /* ESLint Config - Grade S++ */
  eslint: {
    ignoreDuringBuilds: false, // Strict: fail build on ESLint errors
    dirs: ['src'],
  },
  
  /* Image Optimization */
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
    formats: ['image/avif', 'image/webp'],
  },
  
  /* Headers - Security Grade S++ */
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload',
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
        ],
      },
    ];
  },
  
  /* Redirects */
  async redirects() {
    return [];
  },
  
  /* Experimental Features */
  experimental: {
    optimizePackageImports: ['@mui/material', '@mui/icons-material'],
  },
};

export default nextConfig;

