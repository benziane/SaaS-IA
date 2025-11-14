/**
 * Auth Layout - Hybrid Approach (Sneat BlankLayout + MVP Auth)
 * Uses Sneat's BlankLayout for login/register pages - REFONTE
 */

// Type Imports
import type { ChildrenType } from '@core/types';

// Layout Imports
import BlankLayout from '@layouts/BlankLayout';

// Util Imports
import { getSystemMode } from '@core/utils/serverHelpers';

// Client Component
import AuthLayoutClient from './layout-client';

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default async function AuthLayout({ children }: ChildrenType) {
  // Vars
  const systemMode = await getSystemMode();

  return (
    <BlankLayout systemMode={systemMode}>
      <AuthLayoutClient>
        {children}
      </AuthLayoutClient>
    </BlankLayout>
  );
}
