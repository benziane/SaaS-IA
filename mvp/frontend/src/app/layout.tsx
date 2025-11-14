/**
 * Root Layout - Grade S++
 * Main application layout
 */

import type { Metadata, Viewport } from 'next';
import type { ReactNode } from 'react';

import Providers from '@/components/Providers';

import './globals.css';

/* ========================================================================
   METADATA - Grade S++
   ======================================================================== */

export const metadata: Metadata = {
  title: {
    default: 'SaaS-IA - AI Platform',
    template: '%s | SaaS-IA',
  },
  description: 'Modular AI SaaS Platform with YouTube Transcription and more',
  keywords: ['AI', 'SaaS', 'Transcription', 'YouTube', 'Machine Learning'],
  authors: [{ name: 'SaaS-IA Team' }],
  creator: 'SaaS-IA',
  publisher: 'SaaS-IA',
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://saas-ia.com',
    siteName: 'SaaS-IA',
    title: 'SaaS-IA - AI Platform',
    description: 'Modular AI SaaS Platform',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SaaS-IA - AI Platform',
    description: 'Modular AI SaaS Platform',
  },
};

/* ========================================================================
   VIEWPORT - Next.js 15+ Requirement
   ======================================================================== */

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#1a1a1a' },
  ],
};

/* ========================================================================
   TYPES
   ======================================================================== */

interface RootLayoutProps {
  children: ReactNode;
}

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default function RootLayout({ children }: RootLayoutProps): JSX.Element {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Security Headers are in next.config.ts */}
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

