/**
 * Providers Component - Hybrid Approach (MVP + Sneat)
 * 
 * Combines:
 * - Auth Context (MVP - REFONTE)
 * - TanStack Query (MVP)
 * - Sonner Toasts (MVP)
 * - Sneat Theme System
 * - Sneat Settings Context
 * - Sneat Vertical Nav Context
 */

'use client';

// React Imports
import type { ReactNode } from 'react';

// Auth Imports (MVP - REFONTE)
import { AuthProvider } from '@/contexts/AuthContext';

// TanStack Query Imports (MVP)
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

// Sneat Imports
import { VerticalNavProvider } from '@menu/contexts/verticalNavContext';
import { SettingsProvider } from '@core/contexts/settingsContext';
import ThemeProvider from '@components/theme';

// Toast Imports (MVP)
import { Toaster } from 'sonner';

// Lib Imports
import { queryClient } from '@/lib/queryClient';

// Type Imports
import type { Direction, Mode, SystemMode } from '@core/types';

/* ========================================================================
   TYPES
   ======================================================================== */

interface ProvidersProps {
  children: ReactNode;
  direction?: Direction;
  mode?: Mode;
  systemMode?: SystemMode;
  settingsCookie?: any;
}

/* ========================================================================
   COMPONENT
   ======================================================================== */

export function Providers({ 
  children, 
  direction = 'ltr',
  mode,
  systemMode,
  settingsCookie 
}: ProvidersProps): JSX.Element {
  return (
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <VerticalNavProvider>
          <SettingsProvider settingsCookie={settingsCookie} mode={mode}>
            <ThemeProvider direction={direction} systemMode={systemMode ?? 'light'}>
              {children}
              
              {/* Toast Notifications - Grade S++ (MVP) */}
              <Toaster
                position="top-right"
                expand={false}
                richColors
                closeButton
                duration={6000}
              />
              
              {/* React Query Devtools - Development Only (MVP) */}
              {process.env.NODE_ENV === 'development' && (
                <ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-right" />
              )}
            </ThemeProvider>
          </SettingsProvider>
        </VerticalNavProvider>
      </QueryClientProvider>
    </AuthProvider>
  );
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default Providers;

