/**
 * Root Layout - Hybrid Approach (MVP + Sneat)
 * Main application layout with Sneat theme system
 */

import type { Metadata, Viewport } from 'next';
import type { ReactNode } from 'react';

// Component Imports
import Providers from '@/components/Providers';

// Util Imports
import { getMode, getSettingsFromCookie, getSystemMode } from '@core/utils/serverHelpers';

// Style Imports
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

export default async function RootLayout({ children }: RootLayoutProps): Promise<JSX.Element> {
  // Vars
  const direction = 'ltr'; // TODO: Add i18n support later
  const mode = await getMode();
  const settingsCookie = await getSettingsFromCookie();
  const systemMode = await getSystemMode();

  return (
    <html lang="en" dir={direction} suppressHydrationWarning>
      <head>
        {/* Security Headers are in next.config.ts */}
      </head>
      <body>
        <Providers 
          direction={direction}
          mode={mode}
          settingsCookie={settingsCookie}
          systemMode={systemMode}
        >
          {children}
        </Providers>
      </body>
    </html>
  );
}

