/**
 * Root Layout - Hybrid Approach (MVP + Sneat)
 * Main application layout with Sneat theme system
 */

import type { Metadata, Viewport } from 'next';
import type { ReactNode } from 'react';
import { Inter, JetBrains_Mono } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains',
  display: 'swap',
});

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
  manifest: '/manifest.json',
  icons: {
    icon: [
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
      { url: '/icons/icon-192x192.png', sizes: '192x192', type: 'image/png' },
      { url: '/icons/icon-512x512.png', sizes: '512x512', type: 'image/png' },
    ],
    apple: [
      { url: '/apple-touch-icon.png', type: 'image/png' },
      { url: '/icons/icon-152x152.png', sizes: '152x152', type: 'image/png' },
      { url: '/icons/icon-192x192.png', sizes: '192x192', type: 'image/png' },
    ],
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'SaaS-IA',
  },
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
  maximumScale: 1,
  userScalable: false,
  themeColor: '#05C3DB',
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

export default async function RootLayout({ children }: RootLayoutProps) {
  // Vars
  const direction = 'ltr'; // TODO: Add i18n support later
  const mode = await getMode();
  const settingsCookie = await getSettingsFromCookie();
  const systemMode = await getSystemMode();

  return (
    <html lang="en" dir={direction} data-recipe="saas-ia" className={`${inter.variable} ${jetbrainsMono.variable}`} suppressHydrationWarning>
      <head>
        {/* Iconify API for Tabler Icons (sidebar menu icons) */}
        <script src="https://code.iconify.design/iconify-icon/2.3.0/iconify-icon.min.js" defer />
        {/* Tabler Icons CSS for className-based rendering */}
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/dist/tabler-icons.min.css" />

        {/* Theme initialization script - prevents flash */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var cookieName = 'saas-ia-mui-template-settings';
                  var cookies = document.cookie.split(';');
                  var settingsCookie = null;
                  
                  for (var i = 0; i < cookies.length; i++) {
                    var cookie = cookies[i].trim();
                    if (cookie.startsWith(cookieName + '=')) {
                      settingsCookie = JSON.parse(decodeURIComponent(cookie.substring(cookieName.length + 1)));
                      break;
                    }
                  }
                  
                  var mode = settingsCookie?.mode || '${mode}';
                  var systemMode = '${systemMode}';
                  
                  if (mode === 'system') {
                    var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                    mode = prefersDark ? 'dark' : 'light';
                  }
                  
                  document.documentElement.setAttribute('data-mui-color-scheme', mode);
                  document.documentElement.setAttribute('data-mode', mode);
                  document.documentElement.style.colorScheme = mode;
                } catch (e) {
                  console.error('Theme init error:', e);
                }
              })();
            `,
          }}
        />
        
        {/* Security Headers are in next.config.ts */}

        {/* Service Worker Registration */}
        <script
          dangerouslySetInnerHTML={{ __html: `
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
      navigator.serviceWorker.register('/sw.js').catch(function() {});
    });
  }
` }}
        />
      </head>
      <body suppressHydrationWarning>
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

