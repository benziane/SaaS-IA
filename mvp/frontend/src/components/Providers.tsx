/**
 * Providers Component - Grade S++
 * Global providers for the application
 */

'use client';

import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import type { ReactNode } from 'react';
import { Toaster } from 'sonner';

import { queryClient } from '@/lib/queryClient';

/* ========================================================================
   TYPES
   ======================================================================== */

interface ProvidersProps {
  children: ReactNode;
}

/* ========================================================================
   COMPONENT
   ======================================================================== */

export function Providers({ children }: ProvidersProps): JSX.Element {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      
      {/* Toast Notifications - Grade S++ */}
      <Toaster
        position="top-right"
        expand={false}
        richColors
        closeButton
        duration={6000}
        toastOptions={{
          error: {
            duration: 8000, // Errors stay longer
          },
        }}
      />
      
      {/* React Query Devtools - Development Only */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} position="bottom-right" />
      )}
    </QueryClientProvider>
  );
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default Providers;

