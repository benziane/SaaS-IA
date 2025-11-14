/**
 * Auth Layout - Grade S++
 * Layout for authentication pages (login, register)
 */

import type { ReactNode } from 'react';

/* ========================================================================
   TYPES
   ======================================================================== */

interface AuthLayoutProps {
  children: ReactNode;
}

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default function AuthLayout({ children }: AuthLayoutProps): JSX.Element {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      {children}
    </div>
  );
}

