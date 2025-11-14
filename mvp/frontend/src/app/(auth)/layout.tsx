/**
 * Auth Layout - Hybrid Approach (Sneat BlankLayout + MVP Auth)
 * Uses Sneat's BlankLayout for login/register pages
 */

// Type Imports
import type { ChildrenType } from '@core/types';

// Layout Imports
import BlankLayout from '@layouts/BlankLayout';

// HOC Imports
import GuestOnlyRoute from '@/hocs/GuestOnlyRoute';

// Util Imports
import { getSystemMode } from '@core/utils/serverHelpers';

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default async function AuthLayout({ children }: ChildrenType) {
  // Vars
  const systemMode = await getSystemMode();

  return (
    <GuestOnlyRoute>
      <BlankLayout systemMode={systemMode}>
        {children}
      </BlankLayout>
    </GuestOnlyRoute>
  );
}
